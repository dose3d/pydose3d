import pydicom
import numpy as np
import os
import cv2
import nibabel as nib
from svc.utils import timer_func
from svc.dicom.__core.svc import Svc
from svc.exceptions import WrongDicomFormatException, NotADicomFileException
from svc.exceptions import NotEqualMasksSizes, RequestedSlicesIndexOutofRange, IndexesHaveNotCorrectType
import logging
from data import get_example_data_dir as get_data_dir

# new dependencies: nibabel, cv2

##TODO
# add logging into utils.timer_func
# fix problem with get_data_dir
# comments and types def (?)
# convert all patient to nifti automatically
# merge to 1
# refactor create_roi_mask3d to make it prettier


# New 
# TODO!!! 
# From logging to loguru 


class DicomSvc(Svc):
    """ THE TOP LEVEL INTERFACE FOR DATA MANIPULATION SERVICE.

        Data reading
        ============
        The origin of the data being called is examined automatically.
        Logger verbose levels:
        set_verbose_level(1) - deafult:  logging.INFO
        set_verbose_level(2) - switch to logging.DEBUG
    """
    def __init__(self, name, dicom_dir, log=1):
        super().__init__("DataSvc")
        super().set_verbose_level(log)
        self.name = name
        self.__dicom_dir = dicom_dir
        self.__dicom_files = self.__get_DICOM_files()

        self.__ct_files = self.__get_CTfiles()
        self.__struct_files = self.__get_structfiles()
        self.__plan_files = self.__get_planfiles()
        self.__dose_files = self.__get_dosefiles()

        self.__CT = self.__get_CT()
        self.__RTStruct = self.__get_RTStruct()
        self.__RTDose = self.__get_RTDose()
        self.__RTPlan = self.__get_RTPlan()
        self.log().debug(f"Initialized...")

    def __str__(self):
        return (f"Patient '{self.name}' contains: \n\t {len(self.__ct_files)} CT files \n \
        {len(self.__struct_files)} RTStruct file with {len(self.ROIs) } ROIs, \n \
        {len(self.__dose_files)} RTDose file, \n \
        {len(self.__plan_files)} RTPlan file.")


    def __repr__(self) -> str:
        return str({"CT files": len(self.__ct_files), "CT Image Slice Size": self.get_slice_size(),
                "RTStruct files": len(self.__struct_files), "RTDose files": len(self.__dose_files), 
                "RTPlan files": len(self.__struct_files), "Voxel dim": self.get_vox_dim(), "ROIs": self.ROIs})
    

# -------------------------------- User Interface Methods -----------------------
    @timer_func
    def create_roi_mask3d(self, roi_id, color=None):
        """ Create Masks (by struct_id) in the form of 3D numpy arrays (masks not contours). """
        self.log().info(f"Selected ROI: {self.ROIs[roi_id]}")
        #TODO color cannot be 0
        if color == None:
            color = 128
        im_size = self.CTimg3d.shape
        ct_position_dict = {ct.SliceLocation: ct for ct in self.CT} 
        roi_numbers = list(self.ROIs.keys())
        struct_id = roi_numbers.index(roi_id)        
        ROI = [self.RTStruct.ROIContourSequence[u].ContourSequence for u in range(len(self.RTStruct.ROIContourSequence)) if
              self.RTStruct.ROIContourSequence[u].ReferencedROINumber
              == self.RTStruct.StructureSetROISequence[struct_id].ROINumber][0]
        dum = np.zeros(im_size, dtype=np.uint8)
        for seq in ROI:
            dic_image = ct_position_dict[seq.ContourData[2]]
            M = np.zeros((3, 3), dtype=np.float32)
            M[0, 0] = dic_image[0x0020, 0x0037].value[1] * dic_image[0x0028, 0x0030].value[0]
            M[1, 0] = dic_image[0x0020, 0x0037].value[0] * dic_image[0x0028, 0x0030].value[0]
            M[0, 1] = dic_image[0x0020, 0x0037].value[4] * dic_image[0x0028, 0x0030].value[1]
            M[1, 1] = dic_image[0x0020, 0x0037].value[3] * dic_image[0x0028, 0x0030].value[1]
            M[0, 2] = dic_image[0x0020, 0x0032].value[0]
            M[1, 2] = dic_image[0x0020, 0x0032].value[1]
            M[2, 2] = 1.0
            M = np.linalg.inv(M)
            points = np.swapaxes(np.reshape(seq.ContourData, (-1, 3)), 0, 1)
            points[2, :].fill(1)
            points = np.dot(M, points)[:2, :]

            big = int(self.RTStruct.StructureSetROISequence[struct_id].ROINumber)  # 255
            CTSlice = int(dic_image[0x0020, 0x0013].value) - 1  # numery sliców w Dicom startują od 1
            dum2D = np.zeros(im_size[0:2], dtype=np.uint8)
            for id in range(points.shape[1] - 1):
                cv2.line(dum2D, (int(points[1, id]), int(points[0, id])), (int(points[1, id + 1]), int(points[0, id + 1])),
                        big, 1)
                cv2.line(dum2D, (int(points[1, points.shape[1] - 1]), int(points[0, points.shape[1] - 1])),
                        (int(points[1, 0]), int(points[0, 0])), big, 1)

            im_flood_fill = dum2D.copy()
            h, w = dum2D.shape[:2]
            mask = np.zeros((h + 2, w + 2), np.uint8)
            im_flood_fill = im_flood_fill.astype("uint8")
            cv2.floodFill(im_flood_fill, mask, (0, 0), color)
            dum2D[im_flood_fill != color] = big
            np.copyto(dum[:, :, CTSlice], dum2D)
        dum[dum != 0] = color
        return dum
    
    def get_slices_with_organ(self, mask: np.ndarray) -> list:
        "Get the the slices (in the form of list of indexes) that presents organ."
        array_zeros = np.zeros(mask.shape)
        results = np.all(mask == array_zeros, axis=(0, 1))
        return list(np.where(results==False)[0])
    
    def get_slices_with_organs(self, masks: list) -> list:
        "Get the the slices (in the form of list of indexes) that presents organs."
        all_slices = []
        for mask in masks:
            slices = self.get_slices_with_organ(mask)
            all_slices = all_slices + slices
        all_slices = set(all_slices)
        return list(all_slices)

    def convert2nift_ct(self, output_path, custom_fname_prefix=None, slices=[]):
        """ Convert patient data from DICOM to NIfTI. """
        if custom_fname_prefix == None:
            custom_fname_prefix = self.name
        path = output_path + "/" + custom_fname_prefix + ".nii.gz"
        dicom3d = np.array(self.CTimg3d, dtype=np.float32)
        if slices != []: dicom3d = dicom3d[:, :, slices[0]:slices[-1]+1]
        self.log().info(f"Image with dimension {dicom3d.shape} to be saved.")
        nifti_file = nib.Nifti1Image(dicom3d, self.get_affine_RAS())
        slope = int(self.CT[0][(0x0028, 0x1053)].value)
        intercept = int(self.CT[0][(0x0028, 0x1052)].value)        
        nifti_file.header.set_slope_inter(slope, intercept)
        self.log().info(f"Image rescaled (HU) with slope: {slope}, intercept: {intercept}")
        nib.save(nifti_file, path)
        self.log().info(f"NIfTI file from CT saved in {path}")


    def convert2nift_struct(self, output_path, roi_id, color=1, 
                            custom_fname_prefix=None, slices=[]):
        """ Convert patient structures (in the form of masks) data from DICOM to NIfTI. """
        if custom_fname_prefix == None:
            custom_fname_prefix = self.name
        custom_fname_prefix = custom_fname_prefix + '_' + self.ROIs[roi_id]
        path = output_path + "/" + custom_fname_prefix + ".nii.gz"
        mask = self.create_roi_mask3d(roi_id, color)
        if slices != []: mask = mask[:, :, slices[0]:slices[-1]+1]
        self.log().info(f"Mask with dimension {mask.shape} to be saved.")
        nifti_file = nib.Nifti1Image(mask, self.get_affine_RAS())
        nib.save(nifti_file, path)
        self.log().info(f"NIfTI file from RT Struct saved in {path}")


    def convert2nift_struct_multi(self, output_path, name, masks, 
                                  custom_fname_prefix=None, slices=[]):
        """ Creates NIfTI file with patient structures but as few masks inside one file 
        (for example: lung right, lung left and heart) for multi organ segmentation purposes"""
        if custom_fname_prefix == None:
            custom_fname_prefix = self.name
        custom_fname_prefix = custom_fname_prefix + '_' + name
        path = output_path + "/" + custom_fname_prefix + ".nii.gz"
        #mask = self.create_roi_mask3d(roi_id, color)
        #all_slices = self.get_slices_with_organs(masks)
        merged = self.__merge_masks(masks)

        if slices != []: merged = merged[:, :, slices[0]:slices[-1]+1]
        nifti_file = nib.Nifti1Image(merged, self.get_affine_RAS())
        nib.save(nifti_file, path)
        self.log().info(f"NIfTI file {name} saved in {path}")

    
    #TODO - add organ extraction mode
    def convert2nift(self, output_path, name, custom_fname_prefix=None, convert_images=True, 
                     convert_struct=True, rois_selected=None, merge_to_1=False):
        """ Convert entire patient data (images and masks) from DICOM to NIfTI"""
        if convert_images:
            self.convert2nift_ct(output_path, custom_fname_prefix)
        if convert_struct:
            if rois_selected is None:
                rois_to_convert = list(self.ROIs.keys())
            if merge_to_1:
                masks = []
                for roi in rois_to_convert:
                    mask = self.create_roi_mask3d(roi)
                    masks.append(mask)
                self.convert2nift_struct_multi(output_path, name, masks)
            else:
                for roi in rois_to_convert:
                    self.convert2nift_struct(output_path, roi, custom_fname_prefix)

    @timer_func
    def get_affine_LPS(self):
        """ Get affine matrix LPS"""
        first_dataset = self.__CT[0]
        row_cosine, column_cosine, slice_cosine = self.__get_cosines()
        row_spacing, column_spacing = first_dataset.PixelSpacing
        slice_spacing = self.__get_slice_spacing()
        transform = np.identity(4, dtype=np.float32)
        transform[:3, 0] = row_cosine * column_spacing
        transform[:3, 1] = column_cosine * row_spacing
        transform[:3, 2] = slice_cosine * slice_spacing
        transform[:3, 3] = first_dataset.ImagePositionPatient
        return transform

    def get_affine_RAS(self):
        """ Get affine matrix RAS"""
        return np.diagflat([-1,-1,1,1]).dot(self.get_affine_LPS())

    def get_slice_size(self):
        """ Get size of slice. """
        if self.__CT is None:
            return None
        else:
            return self.__CT[0].pixel_array.shape

    def get_vox_dim(self):
        """ Get voxel size (pixel dimensions and slice spacing)."""
        if self.__CT is None:
            return None 
        else:
            return (self.__CT[0].PixelSpacing[0], self.__CT[0].PixelSpacing[1], abs(self.__get_slice_spacing()))

# -------------------------------- Properties -----------------------

    @property
    def CT(self):
        return self.__CT

    @property
    def RTStruct(self):
        return self.__RTStruct

    @property
    def RTDose(self):
        return self.__RTDose

    @property
    def RTPlan(self):
        return self.__RTPlan

    @property
    def ct_files(self):
        return self.__ct_files

    @property
    def struct_files(self):
        return self.__struct_files

    @property
    def dose_files(self):
        return self.__dose_files

    @property
    def plan_files(self):
        return self.__plan_files

    @property
    def CTimg3d(self):
        self.__CTimg3d = self.__create_ct_img3d()
        return self.__CTimg3d

    @property
    def ROIs(self):
        self.__ROIs = self.__get_roi_ids_names()
        return self.__ROIs

    @property
    def struct_file(self):
        if len(self.__struct_files) == 0:
            self.__struct_file = None
        else:
            self.__struct_file = self.__struct_files[0]
        return self.__struct_file

    @struct_file.setter
    def struct_file(self, struct_path):
        if isinstance(struct_path, str) and struct_path.endswith(".dcm"):
            if self.get_dicom_type(struct_path) == "RT Structures":
                self.log().info(f"RT Struct File for this Patient: {struct_path}")
                self.__struct_file = struct_path
                self.__struct_files = [self.__struct_file]
                self.__RTStruct = self.__get_RTStruct()
            else:
                raise WrongDicomFormatException
        else:
            raise NotADicomFileException

    @struct_file.deleter
    def struct_file(self):
        del self.__struct_file
        self.__struct_files = []
        self.__RTStruct = None

    @property
    def dose_file(self):
        if len(self.__dose_files) == 0:
            self.__dose_file = None
        else:
            self.__dose_file = self.__dose_files[0]
        return self.__dose_file


    @dose_file.setter
    def dose_file(self, dose_path):
        if isinstance(dose_path, str) and dose_path.endswith(".dcm"):
            if self.get_dicom_type(dose_path) == "RT Dose":
                self.log().info(f"RT Dose File for this Patient: {dose_path}")
                self.__dose_file = dose_path
                self.__dose_files = [self.__dose_file]
                self.__RTDose = self.__get_RTDose()
            else:
                raise WrongDicomFormatException
        else:
            raise NotADicomFileException        

    @dose_file.deleter
    def dose_file(self):
        del self.__dose_file
        self.__dose_files = []
        self.__RTDose = None

    @property
    def plan_file(self):
        if len(self.__plan_files) == 0:
            self.__plan_file = None
        else:
            self.__plan_file = self.__plan_files[0]
        return self.__plan_file

    @plan_file.setter
    def plan_file(self, plan_path):
        if isinstance(plan_path, str) and plan_path.endswith(".dcm"):
            if self.get_dicom_type(plan_path) == "RT Plan":
                self.log().info(f"RT Plan File for this Patient: {plan_path}")
                self.__plan_file = plan_path
                self.__plan_files = [self.__dose_file]
                self.__RTPlan = self.__get_RTPlan()
            else:
                raise WrongDicomFormatException
        else:
            raise NotADicomFileException

    @plan_file.deleter
    def plan_file(self):
        del self.__plan_file
        self.__plan_files = []
        self.__RTPlan = None

# -------------------------------- Private Methods ---------------------


    def __get_slice_spacing(self):
        if len(self.__CT) > 1:
            slice_cosine = self.__get_cosines()[2]
            slice_positions = [np.dot(slice_cosine, d.ImagePositionPatient) for d in self.__CT]
            slice_positions_diffs = np.diff(slice_positions)
            return np.median(slice_positions_diffs)

    def __get_cosines(self):
        image_orientation = self.CT[0].ImageOrientationPatient
        row_cosine = np.array(image_orientation[:3])
        column_cosine = np.array(image_orientation[3:])
        slice_cosine = np.cross(row_cosine, column_cosine)
        return row_cosine, column_cosine, slice_cosine

    def __create_ct_img3d(self) -> np.array:
        """ Returns 3d patient image (CT) in the form of 3d numpy array. """
        if len(self.__ct_files) == 0 or len(self.__ct_files) == 1:
            return None
        else: 
            #im3D = [ds.pixel_array for ds in self.__CT]
            im3D = []
            for ds in self.__CT:
                im3D.append(ds.pixel_array)
            im3D = np.asarray(im3D, dtype=np.int16)
            im3D = np.swapaxes(im3D, 0, 1)
            im3D = np.swapaxes(im3D, 1, 2)
            return im3D

    def __get_roi_ids_names(self):
        """ Get names and ROIs. """
        if self.RTStruct is None:
            return None
        else:
            rois = {struct.ROINumber: struct.ROIName for struct in self.RTStruct.StructureSetROISequence}
            return rois

    def __get_DICOM_files(self):
        dicom_files = []
        for root, d_names, f_names in os.walk(self.__dicom_dir):
            for f in f_names:
                if f.endswith(".dcm"):
                    dicom_files.append(os.path.join(root, f))
        return dicom_files

    def __get_CT(self):
        if len(self.__ct_files) == 0:
            return None
        else:
            return sorted([pydicom.dcmread(f) for f in self.__ct_files], key=lambda s: s.InstanceNumber)

    def __get_RTStruct(self):
        if len(self.__struct_files) == 0:
            return None
        else:
            if len(self.__struct_files) > 1:
                self.log().warning("More than 1 RT Struct File is in the Directory.")
            return pydicom.dcmread(self.__struct_files[0])

    def __get_RTPlan(self):
        if len(self.__plan_files) == 0:
            return None
        else:
            if len(self.__plan_files) > 1:
                self.log().warning("More than 1 RT Plan File is in the Directory.")
            return pydicom.dcmread(self.__plan_files[0])

    def __get_RTDose(self):
        if len(self.__dose_files) == 0:
            return None
        else:
            if len(self.__dose_files) > 1:
                self.log().warning("More than 1 RT Dose File is in the Directory.")
            return pydicom.dcmread(self.__dose_files[0])

    def __get_CTfiles(self):
        return [f for f in self.__dicom_files if self.get_dicom_type(f)=="CT Image"]

    def __get_structfiles(self):
        return [f for f in self.__dicom_files if self.get_dicom_type(f)=="RT Structures"]

    def __get_planfiles(self):
        return [f for f in self.__dicom_files if self.get_dicom_type(f)=="RT Plan"]

    def __get_dosefiles(self):
        return [f for f in self.__dicom_files if self.get_dicom_type(f)=="RT Dose"]

    def __merge_masks(self, masks):
        # verify if shape of masks are equal
        if len(set([mask.shape for mask in masks])) != 1:
            raise NotEqualMasksSizes
        else:
            merged = np.zeros(masks[0].shape)
            for n, mask in enumerate(masks):
                merged[np.where(mask != 0)] = n+1
            return merged
  
# -------------------------------- Static Methods -----------------------

    @staticmethod
    def get_dicom_type(dataFile):
        """ Check the type of input dicom."""
        ds = pydicom.dcmread(dataFile)
        #Plan 
        if ds.SOPClassUID == "1.2.840.10008.5.1.4.1.1.481.5":
            return "RT Plan"
        #Structurs
        elif ds.SOPClassUID == "1.2.840.10008.5.1.4.1.1.481.3":
            return "RT Structures"
        #Dose
        elif ds.SOPClassUID == "1.2.840.10008.5.1.4.1.1.481.2":
            return "RT Dose"
        #CT 
        elif ds.SOPClassUID == "1.2.840.10008.5.1.4.1.1.2":
            return "CT Image"
        else:
            return "Not defined type"
        
        
# -------------------------------- Methods to be implemented -----------------------
# Beam characteristics

# def get_gantry_angle(dataFile, current_beam):
#     ds = pydicom.dcmread(dataFile)
#     gantry_angle = ds[0x300a,0x00b0][current_beam][0x300a, 0x0110][0][0x300a,0x011e].value
#     return gantry_angle

# def get_colimator_angle(dataFile, current_beam):
#     ds = pydicom.dcmread(dataFile)
#     colimator_angle = ds[0x300a, 0x00b0][current_beam][0x300a, 0x0111][0][0x300a, 0x0120].value
#     return colimator_angle

# def get_jaws_position(dataFile, axis='X', current_beam=-1):
#     assert (axis!='X' and axis!='Y'), "Invalid axis given!"
#     axis_idx = 0 if axis=='X' else 1
#     ds = pydicom.dcmread(dataFile)
#     return ds[0x300a, 0x00b0][current_beam][0x300a, 0x0111][0x300a,0x011a][axis_idx][0x300a, 0x011c].value

# def get_isocenter(dataFile, current_beam):
#     ds = pydicom.dcmread(dataFile)
#     isocenter = ds[0x300a,0xb0][current_beam][0x300a, 0x111][0][0x300a, 0x012c].value
#     return isocenter

# def get_ctrl_point_count(dataFile, current_beam):
#     """Get number of control points for a given beam."""
#     ds = pydicom.dcmread(dataFile)
#     ctrl_points_value = ds[0x300a, 0x00b0][current_beam][0x300a, 0x0110].value
#     return ctrl_points_value

# def get_ctrl_point_total_count(dataFile, current_beam):
#     """Total number of control points."""
#     ds = pydicom.dcmread(dataFile)
#     beam_counter = ds[0x300a, 0x0070][0][0x300a, 0x0080].value
#     total_nr_of_ctrl_points = 0
#     for k in range(0, beam_counter):
#         nr_of_ctrl_points_for_beam = ds[0x300a, 0x00b0][k][0x300a, 0x0110].value
#         total_nr_of_ctrl_points = total_nr_of_ctrl_points+nr_of_ctrl_points_for_beam
#     return total_nr_of_ctrl_points

# def get_ctrl_point_max_number(dataFile, number_of_beams): # old name: get_max_number_of_ctrl_points
#     ds = pydicom.dcmread(dataFile)
#     #number_of_beams = get_number_of_beams(dataFile)  
#     ctrl_points_max_value = 0
#     for i in range(0, number_of_beams):
#         if (ds[0x300a, 0x00b0][i][0x300a, 0x0110].value) > ctrl_points_max_value:
#             ctrl_points_max_value = ds[0x300a, 0x00b0][i][0x300a, 0x0110].value
#         else:
#             continue
#     return ctrl_points_max_value

# def get_ctrl_point_weight(dataFile, current_beam, current_controlpoint):
#     ds = pydicom.dcmread(dataFile)
#     ctrl_point_weight = ds[0x300a, 0x00b0][current_beam][0x300a, 0x0111][current_controlpoint][0x300a, 0x0134].value
#     return ctrl_point_weight

# # to VMAT
# def get_ctrl_point_gantry_angle(dataFile, current_beam, current_controlpoint):
#     # TODO: checkpoint for VMAT-like dataFile  
#     ds = pydicom.dcmread(dataFile)
#     controlpoint_angle = ds[0x300a, 0x00b0][current_beam][0x300a, 0x0111][current_controlpoint][0x300a, 0x011e].value
#     return controlpoint_angle

# #doses - maybe 
# def get_beam_dose(dataFile, current_beam):
#     ds = pydicom.dcmread(dataFile)
#     BeamDose = ds[0x300a, 0x0070][0][0x300c, 0x0004][current_beam][0x300a, 0x0086].value
#     return BeamDose

# def get_total_dose(dataFile):
#     ds = pydicom.dcmread(dataFile)
#     BeamCounter = ds[0x300a, 0x0070][0][0x300a, 0x0080].value
#     total_dose = 0
#     for k in range(0, BeamCounter):
#         BeamDose = ds[0x300a, 0x0070][0][0x300c, 0x0004][k][0x300a, 0x0086].value
#         total_dose = total_dose+BeamDose
#     return total_dose

# def get_ctrl_point_dose(dataFile, current_beam, current_controlpoint):
#     ds = pydicom.dcmread(dataFile)
#     BeamDose = ds[0x300a, 0x0070][0][0x300c, 0x0004][current_beam][0x300a, 0x0086].value
#     if current_controlpoint == 0:
#         controlpoint_dose = ds[0x300a, 0x00b0][current_beam][0x300a, 0x0111][current_controlpoint][0x300a, 0x0134].value
#         controlpoint_dose = (controlpoint_dose*BeamDose)
#     else:
#         cumulative_meterset_weight_in_previous_controlpoiny = ds[0x300a, 0x00b0][current_beam][0x300a, 0x0111][current_controlpoint-1][0x300a, 0x0134].value
#         cumulative_meterset_weight_in_current_controlpoiny = ds[0x300a, 0x00b0][current_beam][0x300a, 0x0111][current_controlpoint][0x300a, 0x0134].value
#         controlpoint_dose = cumulative_meterset_weight_in_current_controlpoiny - cumulative_meterset_weight_in_previous_controlpoiny
#         controlpoint_dose = (controlpoint_dose*BeamDose)
#     return controlpoint_dose