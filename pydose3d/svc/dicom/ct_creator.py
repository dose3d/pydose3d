import datetime
from loguru import logger
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
from pydose3d.data import get_example_data as get_data_file
import json



class CtScanSvc():
    __output_path = None
    
# -------------------------------- Init -----------------------------------------
    def __init__(self, label="img", data_path=None):
        dictionary = get_data_file("/d3d/settings/hounsfield_scale.json")
        with open(dictionary) as jsn_file:
            self.__hounsfield_units_dictionary, self.__image_type_dictionary = json.load(jsn_file)
        self.__label = label
        self.__generate_CT = True
        self.__output_array = np.zeros((1, 1, 1))
        self.__data_path = data_path
        self.__plain_data = np.zeros(shape = (1*1*1, 3, )) 
        self.__data_array  = pd.DataFrame(self.plain_data,columns=['x','y','z']) 
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
        self.__std_x_y_z = [self.__pixel_in_x,self.__pixel_in_y,self.__pixel_in_z]

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

    
    def __get_metadata_from_file(self):
        pass

    def __set_image_properties(self):
        pass



    def __start_Dicom_series(self):
        name = get_data_file("template/CT.dcm")
        ds = pydicom.dcmread(name)
        
        # --------------- overwrite metadata ----------------
        ds.file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid(prefix="1.2.826.0.1.3680043.8.498.1.")
        ds.file_meta.ImplementationClassUID = "1.2.826.0.1.3680043.8.498.1"
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
        ds.StudyInstanceUID = pydicom.uid.generate_uid(prefix="1.2.826.0.1.3680043.8.498.1.")
        ds.SeriesInstanceUID  = pydicom.uid.generate_uid(prefix="1.2.826.0.1.3680043.8.498.1.")
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
        
    def convert_to_dicom_ct(self, data_folder_path):
        # TODO: In folder names -> to list/dictionary
        # In folder serch for metadata.
        # Iterare over it and... Write every slice to DICOM.
        self.series = self.__start_Dicom_series()
        self.instance_UID = self.series.SOPInstanceUID
        

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
