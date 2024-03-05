import datetime
import logging
import os
import time
from sys import prefix

import numpy as np
import pandas as pd
import pydicom
import pydicom._storage_sopclass_uids
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import ExplicitVRLittleEndian
from ROOT import TGeoManager
from data import get_example_data_file as get_data_file

#G4_WAter
#G4_Galactic
#self._hounsfield_units_dictionary = {'Vacuum': 0, 'PMMA': 123.87,'Lung':-1000}

class CtScanSvc(Svc):
    __output_path = None

# -------------------------------- Init -----------------------------------------
    def __init__(self, label="sample", value=None,log=1):
        super().set_verbose_level(log)
        self._hounsfield_units_dictionary = {'G4_WATER': 0, 'PMMA': 123.87, 'RMPS470':143.0, 'Usr_G4AIR20C':-995 , 'G4_Galactic':-1000, 'Vacuum':-1000, 'RW3':245}
        self._image_type_dictionary = {'CT': '1.2.840.10008.5.1.4.1.1.2.'} # Kiedyś dodam więcej modalności
        self._geom = value
        self.label = label
        self.output_array = np.zeros((1, 1, 1))
        self.__generate_sheet = False
        self.__generate_struct = False
        self.__generate_CT = True
        self.plain_data = np.zeros(shape = (70*70*70, 3, )) 
        df1 = pd.DataFrame(self.plain_data,columns=['x','y','z']) 
        temp = {'D3D_ID':[]}
        df2 = pd.DataFrame(temp,dtype=object) 
        self.data_array = df1.join(df2)
        self.__x_min = 0
        self.__x_max = 0
        self.__y_min = 0
        self.__y_max = 0
        self.__z_min = 0
        self.__z_max = 0
        self.__pixel_in_x = 0
        self.__pixel_in_y = 0
        self.__pixel_in_z = 0
        self.__step_x = 0
        self.__step_y = 0
        self.__step_z = 0
        self.__borders_have_been_defined = False
        self.__voxels_size_have_been_defined = False
        self.__std_x_y_z = [70,70,70]

        # RT-Struct dev notes:
        # dcm_ct.StudyInstanceUID         #Study Unical Id
        # dcm_ct.SeriesInstanceUID        #Series Unical ID
        # dcm_ct.FrameOfReferenceUID      #Frame of Reference UID
        # dcm_ct.ImagePositionPatient     #Position
        # dcm_ct.ImageOrientationPatient  #Matrix ortogonisation for X and Y versor
        # dcm_ct.SliceThickness           #Slice thickness
        # dcm_ct.PixelSpacing             #Pixel Spacing
        # dcm_ct.PixelData                #Pixell Hounsfield array
        # dcm_ct.Rows                     #Num of rows
        # dcm_ct.Columns                  #Num of Columns

# -------------------------------- User Interface Methods -----------------------

    @classmethod
    def set_output_path(cls, path):

        cls.__output_path = path
        if cls.__output_path[-1] != "/":
            cls.__output_path=cls.__output_path+"/"
        try:
            os.makedirs(cls.__output_path)
        except FileExistsError:
            # directory already exists
            pass
        return cls.__output_path



    def define_border_size(self, xmin, xmax, ymin, ymax, zmin, zmax):
        self.__border_setter(x_min = xmin, x_max= xmax, y_min=ymin, y_max= ymax, z_min= zmin, z_max= zmax)
        return True

    def define_voxel_size(self, x_step, ystep, zstep):
        self.__voxel_setter(x_step, ystep, zstep)


# ------------------------------- Priv Class Methods ----------------------------

    def __border_setter(self, x_min, x_max, y_min, y_max, z_min, z_max):
        self.__x_min = x_min
        self.__y_min = y_min
        self.__z_min = z_min
        self.__x_max = x_max
        self.__y_max = y_max
        self.__z_max = z_max
        if self.__voxels_size_have_been_defined == True:
            len_x = self.__x_max - self.__x_min
            len_y = self.__y_max - self.__y_min
            len_z = self.__z_max - self.__z_min
            x_tweaker = (self.__pixel_size_in_x - (len_x % self.__pixel_size_in_x))/2
            y_tweaker = (self.__pixel_size_in_y - (len_y % self.__pixel_size_in_y))/2
            z_tweaker = (self.__pixel_size_in_z - (len_z % self.__pixel_size_in_z))/2
            self.__x_max = self.__x_max + x_tweaker
            self.__y_max = self.__y_max + y_tweaker
            self.__z_max = self.__z_max + z_tweaker
            self.__x_min = self.__x_min - x_tweaker
            self.__y_min = self.__z_min - y_tweaker
            self.__z_min = self.__z_min - z_tweaker
            self.__pixel_count_in_x = int((self.__x_max - self.__x_min)/self.__pixel_size_in_x)
            self.__pixel_count_in_y = int((self.__y_max - self.__y_min)/self.__pixel_size_in_y)
            self.__pixel_count_in_z = int((self.__z_max - self.__z_min)/self.__pixel_size_in_z)

        self.__borders_have_been_defined = True



    def __voxel_setter(self,xslice,yslice,zslice):
        self.__pixel_size_in_x = xslice
        self.__pixel_size_in_y = yslice
        self.__pixel_size_in_z = zslice

        if self.__borders_have_been_defined == True:
            len_x = self.__x_max - self.__x_min
            len_y = self.__y_max - self.__y_min
            len_z = self.__z_max - self.__z_min
            x_tweaker = (xslice - (len_x % xslice))/2
            y_tweaker = (yslice - (len_y % yslice))/2
            z_tweaker = (zslice - (len_z % zslice))/2
            self.__x_max = self.__x_max + x_tweaker
            self.__y_max = self.__y_max + y_tweaker
            self.__z_max = self.__z_max + z_tweaker
            self.__x_min = self.__x_min - x_tweaker
            self.__y_min = self.__z_min - y_tweaker
            self.__z_min = self.__z_min - z_tweaker
            self.__pixel_count_in_x = int((self.__x_max - self.__x_min)/self.__pixel_size_in_x)
            self.__pixel_count_in_y = int((self.__y_max - self.__y_min)/self.__pixel_size_in_y)
            self.__pixel_count_in_z = int((self.__z_max - self.__z_min)/self.__pixel_size_in_z)
        self.__voxels_size_have_been_defined = True




    def __gdml_scaner(self,x,y,z):
        self._geom.SetCurrentPoint(x,y,z)
        node = self._geom.FindNode()
        dose3d_cell_id = node.GetVolume().GetName()
        meterial = node.GetVolume().GetMaterial().GetName()

        dose3d_cell_id = dose3d_cell_id.removeprefix('D3D_').removesuffix('LV').replace('_', ' ').split()
        return meterial, dose3d_cell_id


    def __start_Dicom_series(self):
        name = get_data_file("template/CT.dcm")
        ds = pydicom.dcmread(name)
        
        # --------------- overwrite metadata ----------------
        ds.file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid(prefix="1.2.826.0.1.3680043.8.498.997.")
        ds.file_meta.ImplementationClassUID = "1.2.826.0.1.3680043.8.498.997"
        ds.file_meta.ImplementationVersionName = "pydicom 2.2.2"
        ds.file_meta.SourceApplicationEntityTitle = "Dose-3D"
        
        # -------------- overwrite flesh ------------------
        ds.SOPClassUID = ds.file_meta.MediaStorageSOPClassUID
        ds.SOPInstanceUID = ds.file_meta.MediaStorageSOPInstanceUID
        ds.StudyTime = "123030"
        ds.SeriesTime = "123100"
        ds.StudyDate = datetime.datetime.now().strftime('%Y%m%d')
        ds.SeriesDate = datetime.datetime.now().strftime('%Y%m%d')
        ds.ContentDate = datetime.datetime.now().strftime('%Y%m%d')
        ds.Manufacturer = "Dose3D"
        ds.InstitutionName = "AGH WFiIS"
        ds.InstitutionAddress = "Kraków"
        ds.SeriesDescription = "Test slice of CT"
        ds.ManufacturerModelName = "DICOMaker v. alpha 0.09"
        ds.PatientName = self.label
        ds.PatientID = "0123456789"
        ds.SoftwareVersions = "DICOMaker alpha v0.09"
        ds.DistanceSourceToDetector = "1000"
        ds.DistanceSourceToPatient = "500"
        # ds.TableHeight = "To remove"
        # ds.RotationDirection = "To remove"
        # ds.ExposureTime = "0"
        # ds.XRayTubeCurrent = "0"
        # ds.Exposure = "0"
        # ds.FilterType = "0"
        # ds.GeneratorPower = "0"
        ds.StudyInstanceUID = pydicom.uid.generate_uid(prefix="1.2.826.0.1.3680043.8.498.997.")
        ds.SeriesInstanceUID  = pydicom.uid.generate_uid(prefix="1.2.826.0.1.3680043.8.498.997.")
        ds.StudyID = "1"
        ds.SeriesNumber = "1"
        ds.FrameOfReferenceUID = "1.2.840.10008.15.1.1"
        ds.PositionReferenceIndicator = "XY"
        ds.ImageOrientationPatient = r"1\0\0\0\1\0"
        
        ds.PixelRepresentation = 1
        ds.WindowCenter = r"125.0"
        ds.WindowWidth = r"600.0"
        ds.RescaleIntercept = r"0.0"
        return ds
    
    
    
    def __write_Dicom_ct_slice(self, image2d, sliceNumber):
        image2d = image2d.astype(np.uint16)
        ds = self.series
        ds.file_meta.MediaStorageSOPInstanceUID = self.instance_UID+".64156"+f"{sliceNumber*12}"
        ds.SOPInstanceUID = self.instance_UID+".64156"+f"{sliceNumber*12}"
        ds.Rows = image2d.shape[0]
        ds.Columns = image2d.shape[1]

        if self.__voxels_size_have_been_defined:
            ds.SliceThickness = f"{self.__pixel_size_in_x*10}" # TOFO: uzależnić od ustawionego pixel spacingu
        else:
            ds.SliceThickness = f"0.85"
        
        if self.__voxels_size_have_been_defined:
            ds.PixelSpacing = f"{self.__pixel_size_in_y*10}\{self.__pixel_size_in_z*10}" # TOFO: uzależnić od ustawionego pixel spacingu
        else:
            ds.PixelSpacing = r"0.85\0.85"
            
        if self.__voxels_size_have_been_defined:
            ds.ImagePositionPatient = f"{self.__y_min*self.__pixel_size_in_y*10}\{self.__z_min*self.__pixel_size_in_z*10}\{sliceNumber*self.__pixel_size_in_x*10}"
        else:
            ds.ImagePositionPatient = f"{-60+self.__z_min*0.85}\{-60+self.__y_min*0.85}\{-10+sliceNumber*0.85}"
        
        if self.__voxels_size_have_been_defined:
            ds.SliceLocation =f"{sliceNumber*self.__pixel_size_in_x*10}"
        else:
            ds.SliceLocation = f"{sliceNumber*0.85}"
        
        ds.InstanceCreationTime = datetime.datetime.now().strftime("%H%M%S.%f")[:-3]
        ds.ContentTime = datetime.datetime.now().strftime("%H%M%S")
        ds.InstanceNumber = sliceNumber
        ds.PixelData = image2d.tobytes()
        pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)
        ds.save_as(self.__output_path+self.label+f"{sliceNumber}"+r".dcm")

    def __write_whole_Dicom_ct(self):
        self.log().debug("Writing the whole DICOM CT")
        iter=0
        if self.__borders_have_been_defined == True:
            x = self.__pixel_count_in_x
        else:
            x = self.__std_x_y_z[0]
        for i in range(x):
            print(f"Writing slice {iter+1}")
            self.__write_Dicom_ct_slice(self.output_array[iter,:,:], iter+1)
            iter=iter+1
        return True


    def __gdml_iter(self, std_x=70, std_y=70, std_z=70, d3d_indexing_csv=False):
        
        iter = 0

        voxel_size = [0.85,0.85,0.85]
        if self.__voxels_size_have_been_defined == True:
            voxel_size = [self.__pixel_size_in_x, self.__pixel_size_in_y, self.__pixel_size_in_z]

        if self.__borders_have_been_defined == True:
            hounsfield_3d_array = np.zeros((self.__pixel_count_in_x,  self.__pixel_count_in_y,  self.__pixel_count_in_z))
            for x in range(self.__pixel_count_in_x):
                print(f"Slice {x}")
                for y in range(self.__pixel_count_in_y):
                    for z in range(self.__pixel_count_in_z):
                        material, d3d_id = self.__gdml_scaner((self.__x_min + (voxel_size[0]*x)), (self.__y_min + (voxel_size[1]*y)), (self.__z_min + (voxel_size[2]*z)))
                        hounsfield_3d_array[x, y, z] = self._hounsfield_units_dictionary[material]
            self.output_array = hounsfield_3d_array
            return self.output_array

        else:
            hounsfield_3d_array = np.zeros((std_x, std_y, std_z))
            for x in range(std_x):
                print(f"Processing slice {x}")
                for y in range(std_y):
                    for z in range(std_z):
                        material, d3d_id = self.__gdml_scaner((-5 + (voxel_size[0]*x)), (-5 + (voxel_size[1]*y)), (-5 + (voxel_size[2]*z)))
                        hounsfield_3d_array[x, y, z] = self._hounsfield_units_dictionary[material]
                        if d3d_indexing_csv:
                            if len(d3d_id) == 3:
                                self.data_array.loc[iter] = [x,y,z,d3d_id]
                            else:
                                self.data_array.loc[iter] = [x,y,z,[-1,-1,-1]]
                            iter = iter + 1

            if d3d_indexing_csv:
                self.data_array.to_csv(self.__output_path+'dose3d_module_indexing.csv',index=False)
            self.output_array = hounsfield_3d_array
            return self.output_array

# -------------------------------- Public Methods --------------------------------

    def import_gdml(self,frame):
        self._geom = TGeoManager.Import(frame)
        

    def generate_dicom_ct(self, struct=False):
        if not self.__output_path:
            self.log().error("The output path is not defined. Use method: Reader::set_output_path(\"path_to_out_dir\")")
            return None
        self.series = self.__start_Dicom_series()
        self.instance_UID = self.series.SOPInstanceUID
        self.__gdml_iter()
        self.__write_whole_Dicom_ct()
    
    def write_dose3d_dicom_ct(self, d3d_indexing=False, rt_struct=False):
        if not self.__output_path:
            self.log().error("The output path is not defined. Use method: Reader::set_output_path(\"path_to_out_dir\")")
            return None
        self.series = self.__start_Dicom_series()
        self.instance_UID = self.series.SOPInstanceUID
        self.__gdml_iter(d3d_indexing_csv=d3d_indexing)
        self.__write_whole_Dicom_ct()
