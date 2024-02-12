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
from svc._core.svc import Svc

#G4_WAter
#G4_Galactic
#self._hounsfield_units_dictionary = {'Vacuum': 0, 'PMMA': 123.87,'Lung':-1000}

class CtScanSvc(Svc):
    __output_path = None

# -------------------------------- Init -----------------------------------------
    def __init__(self, label="sample", value=None,log=1):
        super().__init__("CtScanSvc")
        super().set_verbose_level(log)
        self._hounsfield_units_dictionary = {'G4_WAter': 0, 'PMMA': 123.87, 'G4_Galactic':0}
        self._image_type_dictionary = {'CT': '1.2.840.10008.5.1.4.1.1.2.'} # Kiedyś dodam więcej modalności
        self._geom = value
        self.label = label
        self.output_array = np.zeros((1, 1, 1))
        self.__generate_sheet = True
        self.__generate_dicom = True
        self.plain_data = {'x':[],'y':[],'z':[],'D3D_ID':[]}
        self.data_array = pd.DataFrame(self.plain_data)  
        self.series = self.__start_Dicom_series()
        self.instance_UID = self.series.SOPInstanceUID
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
        self.__voxels_have_been_defined = False

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

    @classmethod
    def define_borfer_size(self,xmin,xmax,ymin,ymax,zmin,zmax):
        self.__border_setter(xmin,xmax,ymin,ymax,zmin,zmax)
        return True

    def define_voxel_properties():
        return True


# ------------------------------- Priv Class Methods ----------------------------

    def __border_setter(self, xmin, xmax, ymin, ymax, zmin, zmax):
        self.__x_min = xmin
        self.__y_min = ymin
        self.__z_min = zmin
        self.__x_max = xmax
        self.__y_max = ymaxdefine_borfer_size
        self.__z_max = zmax
        if self.__voxels_have_been_defined == True:
            len_x = self.__x_max - self.__x_min
            len_y = self.__y_max - self.__y_min
            len_z = self.__z_max - self.__z_min
            x_tweaker = (self.__pixel_in_x - (len_x % self.__pixel_in_x))/2
            y_tweaker = (self.__pixel_in_y - (len_y % self.__pixel_in_y))/2
            z_tweaker = (self.__pixel_in_z - (len_z % self.__pixel_in_z))/2
            self.__x_max = self.__x_max + x_tweaker
            self.__y_max = self.__y_max + y_tweaker
            self.__z_max = self.__z_max + z_tweaker
            self.__x_min = self.__x_min - x_tweaker
            self.__y_min = self.__z_min - y_tweaker
            self.__z_min = self.__z_min - z_tweaker
        self.__borders_have_been_defined = True



    def __voxel_setter(self,xslice,yslice,zslice):
        self.__pixel_in_x = xslice
        self.__pixel_in_y = yslice
        self.__pixel_in_z = zslice

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
        self.__voxels_have_been_defined = True

    def __gdml_scaner(self,x,y,z):
        self._geom.SetCurrentPoint(x,y,z)
        node = self._geom.FindNode()
        dose3d_cell_id = node.GetVolume().GetName()
        meterial = node.GetVolume().GetMaterial().GetName()

        dose3d_cell_id = dose3d_cell_id.removeprefix('D3D_').removesuffix('LV').replace('_', ' ').split()
        return meterial, dose3d_cell_id


    def __start_Dicom_series(self):
        meta = pydicom.Dataset()
        ds = Dataset()
        meta.MediaStorageSOPClassUID = pydicom._storage_sopclass_uids.CTImageStorage
        meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
        ds.SeriesInstanceUID = pydicom.uid.generate_uid(prefix="1.2.840.10008.5.1.4.1.1.2.")
        ds.StudyInstanceUID = pydicom.uid.generate_uid(prefix="1.2.840.10008.5.1.4.1.1.2.")
        ds.file_meta = meta
        ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
        ds.SOPClassUID = pydicom._storage_sopclass_uids.CTImageStorage
        ds.FrameOfReferenceUID = pydicom.uid.generate_uid(prefix="1.2.840.10008.5.1.4.1.1.2.")
        ds.StudyID = r"1"
        return ds

    def __write_Dicom_ct_slice(self, image2d, sliceNumber):
        image2d = image2d.astype(np.uint16)

        ds = self.series
        ds.is_little_endian = True
        ds.is_implicit_VR = False
        ds.ContentDate = str(datetime.date.today()).replace('-','')
        ds.ContentTime = str(time.time())


        ds.SOPInstanceUID = self.instance_UID+".64156"+f"{sliceNumber*12}"
        ds.file_meta.MediaStorageSOPInstanceUID = self.instance_UID+".64156"+f"{sliceNumber*12}"
        ds.PatientName = "Test^Firstname"
        ds.PatientID = "123456"
        ds.Modality = "CT"
        ds.Manufacturer = "Dose3D"
        ds.InstitutionName = "AGH"


        ds.BitsStored = 16
        ds.BitsAllocated = 16
        ds.SamplesPerPixel = 1
        ds.HighBit = 15
        ds.ImagesInAcquisition = "1"
        ds.Rows = image2d.shape[0]
        ds.Columns = image2d.shape[1]
        ds.SeriesNumber = 1
        ds.InstanceNumber = sliceNumber
        ds.ImagePositionPatient = f"{-225+self.__z_min*0.88}\{-225+self.__y_min*0.88}\{sliceNumber*1.22}"
        ds.ImageOrientationPatient = r"1\0\0\0\1\0"
        ds.ImageType = r"ORIGINAL\PRIMARY\AXIAL"
        ds.SliceThickness = r"1.14" # TOFO: uzależnić od ustawionego pixel spacingu
        ds.KVP = r"120.0"
        ds.DataCollectionDiameter = r"500.0" # TOFO: uzależnić od ustawionego wymiaru
        ds.ReconstructionDiameter = r"500.0" # TOFO: uzależnić od ustawionego wymiaru
        ds.DistanceSourceToDetector = r"1000.0"
        ds.DistanceSourceToDetector = r"550.0"
        ds.TableHeight = r"0.0"
        ds.FocalSpots = r"0.1"
        ds.PatientPosition = r"HFS"
        ds.RescaleIntercept = "0"
        ds.RescaleSlope = "1"
        ds.RescaleType = r"HU"
        ds.PixelSpacing = r"0.946\0.946" # TOFO: uzależnić od ustawionego pixel spacingu
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.PixelRepresentation = 1
        ds.WindowCenter = r"120.0"
        ds.WindowWidth = r"600.0"
        ds.RescaleIntercept = r"0.0"
        ds.RescaleSlope = r"1"
        ds.SeriesNumber = 1
        ds.AcquisitionNumber = 1

        pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)

        print("Setting pixel data...")
        ds.PixelData = image2d.tobytes()
        print("Tobytes done.")
        ds.save_as(self.__output_path+self.label+f"{sliceNumber}"+r".dcm")
        print("One saved")

    def __write_whole_Dicom_ct(self):
        self.log().debug("Writing the whole DICOM CT")
        iter=0
        print(f"xxx {self.__x_max-self.__x_min}")
        for i in range(self.__x_max-self.__x_min):
            print("Slice nr", iter+1)
            self.__write_Dicom_ct_slice(self.output_array[iter,:,:], iter+1)
            iter=iter+1
        return True


    def __gdml_iter(self, std_x=70, std_y=70, std_z=70,gen_csv=False):
        if self.__borders_have_been_defined == True:
            hounsfield_3d_array = np.zeros((self.__z_max- self.__z_min,  self.__x_max- self.__x_min,  self.__y_max- self.__y_min))
            for x in range( self.__x_min, self.__x_max):
                for y in range( self.__y_min, self.__y_max):
                    for z in range( self.__z_min, self.__z_max,1):
                        material, d3d_id = self.__gdml_scaner((-124.785 + (1.22*x)), (-125.0 + (0.879*y)), (-20 + (0.879*z)))
                        hounsfield_3d_array[x, y, z] = self._hounsfield_units_dictionary[material]
            self.output_array = hounsfield_3d_array
            return self.output_array

        else:
            hounsfield_3d_array = np.zeros((std_x, std_y, std_z))
            for x in range(std_x):
                for y in range(std_y):
                    for z in range(std_z):
                        material, d3d_id = self.__gdml_scaner((-3.8 + (0.114*x)), (-3.1 + (0.0946*y)), (-6.4 + (0.0946*z)))
                        hounsfield_3d_array[x, y, z] = self._hounsfield_units_dictionary[material]
                        if gen_csv:
                            if len(d3d_id) == 3:
                                self.data_array.loc[len(self.data_array.index)] = [x,y,z,d3d_id]
                            else:
                                self.data_array.loc[len(self.data_array.index)] = [x,y,z,[-1,-1,-1]]
                if gen_csv:
                    self.data_array.to_csv(self.__output_path+'slice'+f'{x+1}'+'.csv',index=False)
                    self.data_array = pd.DataFrame(self.plain_data)  


            self.output_array = hounsfield_3d_array
            return self.output_array

# -------------------------------- Public Methods --------------------------------

    def import_gdml(self,frame):
        self._geom = TGeoManager.Import(frame)

    def generate_dicom_ct(self,csv=False, struct=False):
        if not self.__output_path:
            self.log().error("The output path is not defined. Use method: Reader::set_output_path(\"path_to_out_dir\")")
            return None
        self.__gdml_iter(gen_csv=csv)
        print("test")
        self.__write_whole_Dicom_ct()
