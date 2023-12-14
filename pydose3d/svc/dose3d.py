""" High level Dose-3D data manimulators
"""
import pydose3d
from ROOT import TFile, TIter, TH2Poly, TCanvas, gROOT, gStyle, gPad
from pydose3d.svc.ntuple_data import NTupleDataSvc
from pydose3d.svc.g4rt_ntuple_data import G4RTNTupleSvc
from pydose3d.svc.root import RootPlotSvc
from loguru import logger
import pathlib
import pydose3d.data as data
import pandas as pd
import numpy as np
import os
from pydose3d.svc.exceptions import *

class Dose3DSvc():
    
    def __init__(self):
        self.g4rtDataSvc = G4RTNTupleSvc(patient="Dose3D")
        self.__detector_cell_max_dose = None
        self.__current_data_path = None
        self.__stored_data_list = []

    def __set_data(self, file):
        self.__current_data_path = file
        self.g4rtDataSvc.ntuplesvc.set_data(file)

    @logger.catch(reraise=True)
    def set_data(self,files=[]):
        if not files:
            # logger.error("Setting data with empty files list is wrong...")
            raise Pydose3dEmptyFileList("Setting data with empty files list is wrong...")
        for file in files:
            if not pathlib.Path(file).is_file():
                raise Pydose3dFileNotFoundException(file)
        self.__stored_data_list = files
        self.__set_data(self.__stored_data_list[0])

    def get_detector_cell_max_dose(self):
        if self.__detector_cell_max_dose != None:
            return self.__detector_cell_max_dose
        self.__detector_cell_max_dose = self.g4rtDataSvc.get_control_point_dose("Cell",-1).max()
        return self.__detector_cell_max_dose

    def __get_detector_dimensions(self,scoring)->(int,int,int):
        df_pos = self.g4rtDataSvc.get_scoring_positioning(scoring)
        pos_x = df_pos['X [mm]'].unique()
        pos_y = df_pos['Y [mm]'].unique()
        pos_z = df_pos['Z [mm]'].unique()
        return len(pos_x), len(pos_y), len(pos_z)

    def get_cell_dose_z_profile_pdframe(self, MLayer, MColumn, normalized=False):
        scoring = "Cell"
        dose_pdframe = self.g4rtDataSvc.get_obserwable_pdframe(scoring,obserwable="Dose")
        logger.debug(f"Post \"dose_pdframe = self.get_obserwable_pdframe(scoring,obserwable=\"Dose\")\"")
        cell_dose_profile_pdframe = dose_pdframe[(dose_pdframe[f"{scoring}IdY"]==MLayer) & (dose_pdframe[f"{scoring}IdX"]==MColumn)].reset_index()
        if normalized:
            max = cell_dose_profile_pdframe['Dose'].max()
            cell_dose_profile_pdframe['Dose'] = cell_dose_profile_pdframe['Dose'] / max
        return cell_dose_profile_pdframe

    def get_cell_dose_z_profile_pdframe_from_csv(self, dose_pdframe, MLayer, MColumn, normalized=False):
        scoring = "Cell"
        cell_dose_profile_pdframe = dose_pdframe[(dose_pdframe[f"{scoring} IdY"]==MLayer) & (dose_pdframe[f"{scoring} IdX"]==MColumn)].reset_index()
        if normalized:
            max = cell_dose_profile_pdframe['Dose'].max()
            cell_dose_profile_pdframe['Dose'] = cell_dose_profile_pdframe['Dose'] / max
        return cell_dose_profile_pdframe

    def get_voxel_dose_z_profile_pdframe(self, MLayer, MColumn, CLayer, CColumn, normalized=False, sum_voxel=False):
        if CColumn == -1 or CLayer == -1:
            sum_voxel = True
        scoring = "Voxel"
        dose_pdframe = self.g4rtDataSvc.get_obserwable_pdframe(scoring,obserwable="Dose")
        scoring = "Cell" # Switching to Cell level of voxelization to select MLayer and MColumn data.
        cell_dose_profile_pdframe = dose_pdframe[(dose_pdframe[f"{scoring}IdY"]==MLayer) & (dose_pdframe[f"{scoring}IdX"]==MColumn)].reset_index()
        scoring = "Voxel" # Switching to Voxelized cell level of voxelization to select CLayer and CColumn data.
        if sum_voxel:
            voxel_dose_profile_pdframe = cell_dose_profile_pdframe.groupby(by=["CellIdZ","VoxelPositionZ"]).agg({"Dose":"sum"}).reset_index()
        else:
            voxel_dose_profile_pdframe = cell_dose_profile_pdframe[(cell_dose_profile_pdframe[f"{scoring}IdY"]==CLayer) & (cell_dose_profile_pdframe[f"{scoring}IdX"]==CColumn)].reset_index()
        if normalized:
            max = voxel_dose_profile_pdframe['Dose'].max()
            voxel_dose_profile_pdframe['Dose'] = voxel_dose_profile_pdframe['Dose'] / max
        return voxel_dose_profile_pdframe

    def get_voxel_z_profile_pdframe_from_csv(self, data, MLayer, MColumn, CLayer=-1, CColumn=-1, observable="Dose", normalized=False, sum_voxel=False):
        scoring = "Cell" # Switching to Cell level of voxelization to select MLayer and MColumn data.
        cell_dose_profile_pdframe = data[(data[f"{scoring} IdY"]==MLayer) & (data[f"{scoring} IdX"]==MColumn)].reset_index()
        scoring = "Voxel" # Switching to Voxelized cell level of voxelization to select CLayer and CColumn data.
        if sum_voxel:
            voxel_dose_profile_pdframe = cell_dose_profile_pdframe.groupby(by=["Cell IdZ","Z [mm]"]).agg({"Dose":"sum"}).reset_index()
        else:
            voxel_dose_profile_pdframe = cell_dose_profile_pdframe[(cell_dose_profile_pdframe[f"{scoring} IdY"]<=(CLayer+1)) & (cell_dose_profile_pdframe[f"{scoring} IdX"]<=(CColumn+1)) & (cell_dose_profile_pdframe[f"{scoring} IdY"]>=(CLayer-1)) & (cell_dose_profile_pdframe[f"{scoring} IdX"]>=(CColumn-1))].reset_index()
        if normalized:
            max = voxel_dose_profile_pdframe['Dose'].max()
            voxel_dose_profile_pdframe['Dose'] = voxel_dose_profile_pdframe['Dose'] / max
        return voxel_dose_profile_pdframe

    def __write_dose_voxel_z_profile_to_json(self, outFile, output_name, MLayer, MColumn, CLayer=-1, CColumn=-1, normalized=False):
        df = pd.DataFrame()
        # if CColumn == -1 or CLayer == -1:
        #     df = self.get_cell_dose_z_profile_pdframe(MLayer,MColumn,normalized)
        #     df = df.rename(columns={"CellPosZ":f"Z [mm]"})
        #     df['scoring'] = 'Cell'
        # else:
        df = self.get_voxel_dose_z_profile_pdframe(MLayer,MColumn,CLayer, CColumn ,normalized)
        df = df[["VoxelPositionZ","Dose"]]    
        df = df.rename(columns={"VoxelPositionZ":f"Z [mm]"})
        df['scoring'] = 'Voxel'
        df['name'] = output_name
            
        df = df[[f"Z [mm]","Dose"]]    
        df.to_json(outFile,orient="index", indent=4)

    def write_dose_z_profile_to_json(self, output_dir, output_name, MLayer, MColumn, CLayer=-1, CColumn=-1, normalized=False):
        print(self.__stored_data_list)
        if self.__stored_data_list:
            idx = 0
            for ifile in self.__stored_data_list:
                self.set_data(ifile)
                file = f"{output_dir}/{output_name}_{idx}.json"
                idx = idx + 1
                self.__write_dose_voxel_z_profile_to_json(file, output_name, MLayer, MColumn, CLayer, CColumn, normalized)
        else:
            file = f"{output_dir}/{output_name}.json"
            self.__write_dose_voxel_z_profile_to_json(file, output_name, MLayer, MColumn, CLayer, CColumn, normalized)

    def get_edeposit_profile_z_pdframe(self, layer, col, scoring='Voxel', normalized=False):
        pdframe = self.g4rtDataSvc.get_obserwable_pdframe(scoring,"EDeposit")
        layer_pdframe = pdframe[pdframe[f"{scoring}IdY"]==layer]
        profile_pdframe = layer_pdframe[layer_pdframe[f"{scoring}IdX"]==col].reset_index()
        if normalized:
            max = profile_pdframe['EDeposit'].max()
            profile_pdframe['EDeposit'] = profile_pdframe['EDeposit'] / max
        return profile_pdframe[[f"{scoring}IdZ",f"{scoring}PosZ",'EDeposit']]

    def get_dose_profile_x_pdframe(self, layer, row, scoring='Voxel', normalized=False):
        dose_pdframe = self.g4rtDataSvc.get_obserwable_pdframe(scoring,obserwable="Dose")
        dose_layer_pdframe = dose_pdframe[dose_pdframe[f"{scoring}IdY"]==layer]
        dose_profile_pdframe = dose_layer_pdframe[dose_layer_pdframe[f"{scoring}IdZ"]==row].reset_index()
        if normalized:
            max = dose_profile_pdframe['Dose'].max()
            dose_profile_pdframe['Dose'] = dose_profile_pdframe['Dose'] / max # TODO: add here JH types of normalization
        return dose_profile_pdframe[[f"{scoring}IdX",'Dose']]

    def get_cell_edeposit(self, layer, col, row):
        scoring = "Cell"
        pdframe = self.g4rtDataSvc.get_obserwable_pdframe(scoring,"EDeposit")
        return pdframe.loc[(pdframe[f"{scoring}IdY"]==layer) & (pdframe[f"{scoring}IdX"]==col) & (pdframe[f"{scoring}IdZ"]==row),"EDeposit"].values[0]

    def get_module_dose_map(self, ControlPoint = -1, DLayer = 0, DRow = 0, DCol = 0, MLayer=0, CLayer=-1):
        histpad: TH2Poly = self.__get_module_layerpad_hist(MLayer,CLayer)
        # by default we assume single cell voxelisation
        # if CLayer == -1:    # <- cell is not voxelised
        #     sc_volume = "Cell"
        # data = self.__get_positioned_pdframe(scoring_volume=sc_volume, observable="Dose")
        # if CLayer == -1:
        #     layer_data = data[(data[f"CellIdY"]==MLayer)].reset_index()
        # else:
        #     layer_data = data[(data[f"CellIdY"]==MLayer) & (data[f"VoxelIdY"]==CLayer)].reset_index()
        # df_gr = layer_data.groupby([f"{sc_volume}PositionX",
        #                     f"{sc_volume}PositionY",
        #                     f"{sc_volume}PositionZ"]).agg({f"{sc_volume}Dose":"sum"}).reset_index()
        if CLayer == -1:
            df_dose = self.g4rtDataSvc.get_control_point_dose("Cell",ControlPoint).reindex() # THIS IS 3D!!!
            df_pos = self.g4rtDataSvc.get_scoring_positioning("Cell").reindex()
            df_merged = pd.concat([df_dose, df_pos], axis=1) # Założenie - out of the box - są tak samo posortowane i odpowiadają sobie. Zapewnione po stronie G4RT
            df_merged = df_merged[df_merged[f"Cell ID Y"]==MLayer]
        else:
            df_dose = self.g4rtDataSvc.get_control_point_dose("Voxel",ControlPoint).reindex()  # THIS IS 3D!!!
            df_pos = self.g4rtDataSvc.get_scoring_positioning("Voxel").reindex() 
            df_merged = pd.concat([df_dose, df_pos], axis=1)  # Założenie - out of the box - są tak samo posortowane i odpowiadają sobie. Zapewnione po stronie G4RT
            df_merged = df_merged[(df_merged[f"Cell ID Y"]==MLayer ) & (df_merged[f"Voxel ID Y"]==CLayer)]
        nBins = histpad.GetNumberOfBins()
        for i in range(nBins):
            histpad.SetBinContent(i+1,0.0) # rest bins content
        for index, row in df_merged.iterrows():
            x = row[f"X [mm]"] # Layers are placed in XZ plane 
            y = row[f"Z [mm]"]
            nbin = histpad.FindBin(x,y)
            value = row[f"Dose"]
            histpad.SetBinContent(nbin,value)
        histpad.SetTitle(f"{histpad.GetTitle()};X [mm];Z [mm];Dose [Gy]")
        histpad.SetDirectory(0)
        return histpad

    def write_module_dose_map(self,file, DLayer = 0, DRow = 0, DCol = 0, MLayer=0, CLayer=-1):
        hfile = TFile( file, 'RECREATE', 'Dose-3D module dose map hist' )
        data_list = self.get_mcrun_info()
        def get_id(_file):
            for idx in data_list:
                if data_list[idx]['file'] == _file:
                    return idx
            return -1
        for file in self.__stored_data_list:
            self.__set_data(file)
            dose_map = self.get_module_dose_map(DLayer, DRow, DCol, MLayer, CLayer)
            current_name = dose_map.GetName()
            file_id = get_id(file)
            dose_map.SetName(f"File_{file_id}_{current_name}")
            dose_map.SetStats(0)
            dose_map.SetDirectory(hfile)
        hfile.Write()

    @logger.catch(reraise=True)
    def __get_module_layerpad_hist(self,MLayer, CLayer):
        hists = self.g4rtDataSvc.ntuplesvc.get_hist_list(top_dir="Dose3D_LayerPads", type="TH2Poly",  contained_in_name="Dose3D")
        if CLayer == -1:
            hist_name = f"Dose3D_MLayer_{MLayer}"
        else:
            hist_name = f"Dose3D_MLayer_{MLayer}_CLayer_{CLayer}"
        logger.debug(f"Reqest for {hist_name} layer pad")
        # Dev NOTE: update me to exception
        if hist_name not in hists:
            # logger.error("Requested layer doesn't exist in avalilable layer pads data")
            raise Pydose3dFileNoSuchLayerException(hist_name)
            os._exit(os.EX_OK)
            # DEV NOTE: in future this should returning empty object rather than exit
        return self.g4rtDataSvc.ntuplesvc.get_object(top_dir="Dose3D_LayerPads", name=hist_name)

    def print_run_info(self):
        """ In data gantry informaction are not defined yet."""
        pass 

    def get_mcrun_info(self):
        """ In MC data run informaction are stored as GantryAngle and G4RunId being kept in each event.
            Note:   G4RunId corresponds to single control point simulation 
                    (Number of ctrl.pts. can't be related to single gantry angle value)
        """
        mc_info = {}
        ifile = 0
        for file in self.__stored_data_list:
            self.__set_data(file)
            mc_info[ifile] = {}
            mc_info[ifile]["file"] = file
            run_info_pdframe = self.g4rtDataSvc.ntuplesvc.get_pdframe(['G4RunId','GantryAngle'])
            mc_info[ifile]["control_point_ids"] = run_info_pdframe['G4RunId'].unique().tolist()
            mc_info[ifile]["control_point_angles"] = run_info_pdframe['GantryAngle'].unique().tolist()
            '''
            The detection system geometry: 
            https://docs.cyfronet.pl/display/TNSIM/Detector+Geometry
            NOTE:
            Currently, the simulation geometry manipulation doesn't handling the detector
            level manipulation - everything is like a single module.
            * DAQ mapping to be considered here to automatically segment the 
            detection system into modules
            '''
            c_x,c_y,c_z = self.__get_detector_dimensions("Cell")
            v_x,v_y,v_z = self.__get_detector_dimensions("Voxel")
            
            logger.debug(f"cx {c_x}, cy{c_y}, cz{c_z}")
            logger.debug(f"vx {v_x}, vy{v_y}, vz{v_z}")
            mc_info[ifile]["detector_layout"] = {}
            mc_info[ifile]["detector_layout"]["DLayer"] = [0]
            mc_info[ifile]["detector_layout"]["DRow"] = [0]
            mc_info[ifile]["detector_layout"]["DCol"] = [0]
            mc_info[ifile]["detector_layout"]["MLayer"] = []
            mc_info[ifile]["detector_layout"]["CLayer"] = []
            for i in range(c_x):
                mc_info[ifile]["detector_layout"]["MLayer"].append(i)
            for i in range(v_x):
                mc_info[ifile]["detector_layout"]["CLayer"].append(i)
            ifile = ifile+1
        return mc_info

    def get_list_of_2dmaps(self):
        cp_list = []
        if G4RTNTupleSvc.ReadFromIntegratedStore:
            input_file = self.g4rtDataSvc.ntuplesvc.get_tfile()
            for dir_key in input_file.GetListOfKeys():
                dir_obj = dir_key.ReadObj()
                dir_name = dir_obj.GetTitle()
                if(dir_name == "RT_Plan"):
                    cp_list = dir_obj.GetListOfKeys()
        plots = {}
        ifile = 0
        # print(cp_list)
        for file in self.__stored_data_list:
            self.__set_data(file)
            plots[ifile] = {}
            plots[ifile]["file"] = file
            v_x,v_y,v_z = self.__get_detector_dimensions("Voxel")
            # print(v_x)
            c_x,c_y,c_z = self.__get_detector_dimensions("Cell")
            # print(c_x)
            plots[ifile]["plots"] = []
            for obj_key in cp_list:
                # print(obj_key.GetName())
                for i in range(c_x):
                    for j in range(v_x):
                        plots[ifile]["plots"].append(f"Dose_2D_{obj_key.GetName()}_MLayer-{i}_CLayer-{j}")
            ifile = ifile + 1
        # print(plots)
        return plots


if __name__=="__main__":
    from pydose3d.svc.root import RootPlotSvc as rpsvc
    pydose3d.set_log_level("DEBUG")
    logger.info("NTupleDataSvc:: Run on example data...")
    # ntuple_data = data.get_example_data("d3d/sim/detector_4x4x8_in_water_layer_pads.root")
    svc = Dose3DSvc()
    ntuple_data = ["/home/g4rt/test/g4rt/output/test_job_3/test_job.root"]
    svc.set_data(files=ntuple_data)
    info = svc.get_mcrun_info()
    print(info[0]['file'])
    def get_id(_file):
        for idx in info:
            if info[idx]['file'] == _file:
                return idx
        return -1
    id = get_id(ntuple_data[0])
    print(id)
    my_list = svc.get_list_of_2dmaps()
    
    hist = svc.get_module_dose_map(MLayer=0, CLayer=-1)
    rpsvc.TCanvas(obj=hist,opts="COLZ",title_z="Dose[Gy]",logscale=False,width=500).Draw()
    # print(my_list)
    print("End of main")

