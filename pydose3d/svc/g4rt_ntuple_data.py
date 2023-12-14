from pydose3d.svc.ntuple_data import NTupleDataSvc
from ROOT import TFile # type: ignore
import pydose3d
import numpy as np
import pandas as pd
from loguru import logger
import matplotlib.pyplot as plt
import pydose3d.data as data

class G4RTNTupleSvc():
    ReadFromIntegratedStore = True
    
    def __init__(self, patient="None", file=None, ImplicitMT=False):
        self.ntuplesvc = NTupleDataSvc(patient, file, ImplicitMT)

    def get_scoring_positioning(self, scoring_type = "Cell"):
        input_file = self.ntuplesvc.get_tfile()
        vec_positioning = np.array([])
        vec_ID = np.array([])
        vec_voxel_ID = np.array([])
        for dir_key in input_file.GetListOfKeys():
            dir_obj = dir_key.ReadObj()
            dir_name = dir_obj.GetTitle()
            if(dir_name == "GEOMETRY" or dir_name == "Geometry"):
                for obj_key in dir_obj.GetListOfKeys():
                    # print("Tak, na pewno tu wchodzę.")
                    obj_name = obj_key.GetName()
                    if(obj_name == f"{scoring_type}Position"):
                        vec_positioning = dir_obj.Get(obj_name)
                    id_scope = {True:"Cell", False:"VoxelGlobal"}[scoring_type == "Cell"]
                    if(obj_name == f"{id_scope}ID"):
                        vec_ID = dir_obj.Get(obj_name)
                    if(obj_name == f"VoxelID"):
                        vec_voxel_ID = dir_obj.Get(obj_name)
        nvec_positioning = np.reshape(np.array(vec_positioning), (-1,3))
        nvec_id = np.reshape(np.array(vec_ID), (-1,3))
        pos_columns_list = ['X [mm]','Y [mm]','Z [mm]']
        pos_df = pd.DataFrame(nvec_positioning, columns = pos_columns_list)
        id_columns_list = ['Cell ID X','Cell ID Y','Cell ID Z']
        id_df = pd.DataFrame(nvec_id, columns=id_columns_list)
        if scoring_type == "Voxel":
            nvec_voxel_id = np.reshape(np.array(vec_voxel_ID), (-1,3))
            voxel_id_columns_list = ['Voxel ID X','Voxel ID Y','Voxel ID Z']
            voxel_id_df = pd.DataFrame(nvec_voxel_id, columns=voxel_id_columns_list)
            id_df = pd.concat([id_df,voxel_id_df],axis=1)
        return pd.concat([id_df,pos_df],axis=1).sort_values(pos_columns_list)

    def get_control_point_dose(self, scoring_type="Cell", control_point = -1):
        if G4RTNTupleSvc.ReadFromIntegratedStore:
            input_file = self.ntuplesvc.get_tfile()
            vec_dose = np.array([])
            for dir_key in input_file.GetListOfKeys():
                dir_obj = dir_key.ReadObj()
                dir_name = dir_obj.GetTitle()
                if(dir_name == "RT_Plan"):
                    for obj_key in dir_obj.GetListOfKeys():
                        data_dir_name = {True: "Total", False: f"CP_{control_point}"}[control_point==-1]
                        logger.debug(f"Returning the {data_dir_name} dose ({scoring_type} scoring)")
                        if(obj_key.GetName()==data_dir_name):
                            for dose_key in (obj_key.ReadObj().GetListOfKeys()):
                                if(dose_key.GetName() == f"{scoring_type}Dose"):
                                    vec_dose = np.array(obj_key.ReadObj().Get(dose_key.GetName()))
            return pd.DataFrame(vec_dose, columns=[f"Dose"])
        else:
            data_query = {True:  f"{scoring_type}Dose>0"
                        , False: f"{scoring_type}Dose>0 && RunId=={control_point}"}[control_point==-1]
            
            df = self.ntuplesvc.get_pdframe(columns=[f"{scoring_type}IdX"
                                                    ,f"{scoring_type}IdY"
                                                    ,f"{scoring_type}IdZ"
                                                    ,f"{scoring_type}Dose"],query_rdf=data_query)
            
            df_grby = df.groupby([f"{scoring_type}IdX",f"{scoring_type}IdY",f"{scoring_type}IdZ"])
            df_summed = df_grby.agg({f"{scoring_type}Dose":"sum"}).reset_index()
            df_summed = df_summed.rename(columns={f"{scoring_type}Dose":f"Dose"})
            return df_summed["Dose"]
    
    def __get_positioned_pdframe(self,scoring_volume, observable, entries=-1):
        col =  [f"CellIdX",
                f"CellIdY",
                f"CellIdZ",
                f"{scoring_volume}PositionX",
                f"{scoring_volume}PositionY",
                f"{scoring_volume}PositionZ",
                f"{scoring_volume}{observable}"
                ]
        if scoring_volume == "Voxel":
            col =  [f"CellIdX",
                f"CellIdY",
                f"CellIdZ",
                f"{scoring_volume}PositionX",
                f"{scoring_volume}PositionY",
                f"{scoring_volume}PositionZ",
                f"VoxelIdX",
                f"VoxelIdY",
                f"VoxelIdZ",
                f"{scoring_volume}{observable}"]
        return self.ntuplesvc.get_pdframe(columns=col,query_rdf=f"{scoring_volume}Dose>0.",entries=entries)

    def get_obserwable_pdframe(self, scoring, obserwable, entries=-1):
        df = self.__get_positioned_pdframe(scoring,f"{obserwable}",entries)
        df_col =[f"CellIdX",f"CellIdY",f"CellIdZ"]
        if scoring == "Voxel":
            df_col.extend([f"VoxelIdX",f"VoxelIdY",f"VoxelIdZ"])
        df_col.extend([f"{scoring}PositionX",f"{scoring}PositionY",f"{scoring}PositionZ"])
        df_gr = df.groupby(df_col).agg({f"{scoring}{obserwable}":"sum"},as_index=True, group_keys=False).reindex()
        df_gr.rename(columns={f"{scoring}{obserwable}":"{obserwable}"},inplace=True)
        return df_gr.reset_index()
        

if __name__=="__main__":
    
    pydose3d.set_log_level("DEBUG")
    logger.info("NTupleDataSvc:: Run on example data...")
    ntuple_data = data.get_example_data("d3d/new_data_structure_11112023.root")
    logger.info(f"Data file: {ntuple_data}")
    
    d3dSvc = G4RTNTupleSvc("G4RT",ntuple_data)
    scoring = "Voxel"
    df_dose = d3dSvc.get_control_point_dose(scoring,0)
    df_pos = d3dSvc.get_scoring_positioning(scoring)
    # print(df_pos)
        
    pos_x = df_pos['X [mm]'].unique()
    pos_y = df_pos['Y [mm]'].unique()
    pos_z = df_pos['Z [mm]'].unique()
    
    # print(pos_x)
    
    v = df_dose['Dose'].values.reshape((len(pos_x), len(pos_y), len(pos_z)))
    # print(df0)
    
    # Select the XZ plane (Y = 0)
    xz_plane = v[:, 1, :].T

    # Extract X, Z coordinates and dose values
    x_coords = np.tile(pos_x, len(pos_z))
    z_coords = np.repeat(pos_z, len(pos_x))
    dose_values = xz_plane.flatten()

    plt.scatter(x_coords, z_coords, c=dose_values, cmap='viridis', s=150)
    plt.colorbar()
    plt.xlabel('Y [mm]')
    plt.ylabel('X [mm]')
    plt.title('YX Plane')
    plt.show()
    
    
    # detector_cell_dimensiality = [0,1,2]
    # detector_cell_dimensiality[0] = df3['ID x'].max()+1
    # detector_cell_dimensiality[1] = df3['ID y'].max()+1
    # detector_cell_dimensiality[2] = df3['ID z'].max()+1



    # print(detector_cell_dimensiality)
    
    # detector_voxel_dimensiality = [0,1,2]
    # detector_voxel_dimensiality[0] = df4['ID x'].max()+1
    # detector_voxel_dimensiality[1] = df4['ID y'].max()+1
    # detector_voxel_dimensiality[2] = df4['ID z'].max()+1

    # print(detector_voxel_dimensiality)
    