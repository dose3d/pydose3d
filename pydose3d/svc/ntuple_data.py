""" High level NTuple data reader and manimulator
"""
from ROOT import TFile, TIter, TH2Poly, TCanvas, gROOT, gStyle # type: ignore
import ROOT
import numpy as np
import pandas as pd
# import pydose3d.data as data
import pydose3d
import os
from loguru import logger
from functools import reduce

class NTupleDataSvc():
    ImplicitMT = False
    LengthUnit = "mm"
    DoseUnit = "Gy"
    EnergyUnit = "MeV"
    CellSize = 10.4 # mm
    NCpu = 2
    
    def __init__(self, patient="Dose3D", file=None, ImplicitMT=False):
        """
        NTupleDataSvc object constructor

        Args:
            patient (str, optional): _description_. Defaults to "Dose3D".
            file (filename.root, optional): _description_. Defaults to None.
            ImplicitMT (bool, optional): _description_. Defaults to False.
        """
        logger.debug(f"Initialization of high-level ROOT NTuple data reading, management and manipulation service.")
        
        if(ImplicitMT or NTupleDataSvc.ImplicitMT):
            NTupleDataSvc.ImplicitMT = ImplicitMT
            ROOT.EnableImplicitMT(); # type: ignore #Enable ROOT's implicit multi-threading
            logger.debug(f"ROOT's implicit multithreading is enabled.")
        
        self._file = file
        self._ttree = None
        self._hist_in_file = []
        # self.patient_type = patient # Dose3D / WaterPhantom / ...
        
        # self.normal_axis='Y'
        # self.full_pdframe = pd.DataFrame()
        
    def set_data(self, data):
        self._file = data
        self.set_ttree_name()
        
    def get_tfile(self):
        return TFile.Open(self._file,"READ")
    
    def set_ttree_name(self):
        input_file = TFile.Open(self._file," READ ") # type: ignore        
        directory_list = input_file.GetListOfKeys()
        if(directory_list.Contains("Dose3DVoxelisedTTree")):
            logger.success("The studied file contains a \"Dose3DVoxelisedTTree\" tree. \
            \nFurther work will be performed on the elements of this tree.")
            self._tree = "Dose3DVoxelisedTTree"
        elif(directory_list.Contains("Dose3DTTree")):
            logger.success("The studied file contains a \"Dose3DTTree\" tree. \
            \nFurther work will be performed on the elements of this tree.")
            logger.warning("The tree does not contain information about the voxelized structure, \
            \nany functions running on it will not work.")
            self._tree = "Dose3DTTree"
        else:
            logger.error("There is no TTree associated with Dose3D phantom in thease .root file")
            # os._exit(os.EX_OK)

        
    # def set_normal_axis(self,axis):
    #     self.normal_axis=axis
    
    def get_pdframe(self, columns=[], query_pdf=None, query_rdf=None, entries=-1):
        ''' query_rdf : filter applied on RDataframe
            query_pdf : filter applied on final Pandas DataFrame
        '''
        if(NTupleDataSvc.ImplicitMT and entries>0):
                logger.error("You cannot use limited number of events with ROOT.EnableImplicitMT()")
                return pd.DataFrame()
        logger.debug(f"Reading {self._file}:{self._tree}")
        if query_rdf:
            logger.debug(f"Reading query: {query_rdf}")
            rdf = ROOT.RDataFrame(self._tree, self._file, {"CellIdX","CellIdY","CellIdZ","CellPositionX","CellPositionY","CellPositionZ","CellDose","VoxelIdX","VoxelIdY","VoxelIdZ","VoxelPositionX","VoxelPositionY","VoxelPositionZ","VoxelDose"}).Filter(query_rdf)
        else:
            rdf = ROOT.RDataFrame(self._tree, self._file, {"CellIdX","CellIdY","CellIdZ","CellPositionX","CellPositionY","CellPositionZ","CellDose","VoxelIdX","VoxelIdY","VoxelIdZ","VoxelPositionX","VoxelPositionY","VoxelPositionZ","VoxelDose"})
        if(entries>0):
            rdf = rdf.Range(entries)
        
        logger.debug("Reading Data from ROOT File - Done")
        # Verify the type of data for given column list:
        # - if any of the column is RVec<type>, it's assumed all columns is the same type
        isRVec = False
        for col in columns:
            col_type = rdf.GetColumnType(col)
            if col_type.find("RVec") != -1:
                isRVec = True
        if isRVec:
            logger.debug("Given column list contain RVec<type> object. Processing all columns as RVec<type> data...")
        else: 
            nEvents = rdf.Count().GetValue()
            logger.debug(f"Number of events {nEvents}")
            # Convert from ROOT DatFrame to Pandas DataFrame:
            return pd.DataFrame(rdf.AsNumpy(columns))
        # Convert from ROOT DatFrame to NumPy:
        vec_nmpy = rdf.AsNumpy(columns)
        df_out_list = []
        for col in columns:
            logger.debug(f"Processing: '{col}' of type: {rdf.GetColumnType(col)}")
            df_out_list.append( pd.DataFrame(columns=[col]) )
            idx = len(df_out_list) - 1
            vec_col = vec_nmpy[col]
            for v_evt in vec_col:   # events loop for given column
                if v_evt.size() > 0:
                    for ival in v_evt:
                        df_out_list[idx].loc[len(df_out_list[idx])] = [ival]
        # Validate if all dataframes are the same size (they should be):
        df_sizes = []
        for df in df_out_list:
            df_sizes.append(df.size)
        df_sizes_uniques = reduce(lambda re, x: re+[x] if x not in re else re, df_sizes, [])
        if len(df_sizes_uniques) > 1:
            logger.error(f"For given column list obtain dimensions are not equal. Verify your list.")
            return pd.DataFrame()
        # User requested data with query_pdf:
        if query_pdf:
            return pd.concat(df_out_list, axis=1).query(query_pdf).reset_index()
        return pd.concat(df_out_list, axis=1)
    
    def get_hist_list(self, top_dir="", type="", contained_in_name=""):
        ''' NOTE: Curently iterating trough 2-levels in TDirectory is harcoded
            (number of for loops). TODO: Make this method recoursive!
        '''
        hist_in_file = []
        input_file = TFile.Open(self._file," READ ") # type: ignore        
        directory_tree = input_file.Get(top_dir)
        directory_list = directory_tree.GetListOfKeys()
        for key in directory_list:
            obj = key.ReadObj()
            obj_Name = key.ReadObj().ClassName()
            if obj_Name == type:
                name = key.ReadObj().GetTitle()
            if obj_Name != "TDirectoryFile":
                hist_in_file.append(name)
            if obj_Name == "TDirectoryFile":
                lover_Level_List = obj.GetListOfKeys()
                for val in lover_Level_List:
                    lover_Lvl_obj = val.ReadObj()
                    lover_Lvl_obj_name = val.ReadObj().ClassName()
                    if lover_Lvl_obj_name == type:
                        name = val.ReadObj().GetTitle()
                        hist_in_file.append(name)
        return hist_in_file
    
    def get_object(self, top_dir="", name=""):
        input_file = TFile.Open(self._file," READ ") # type: ignore   
        directory_tree = input_file.Get(top_dir)
        directory_list = directory_tree.GetListOfKeys()

        for key in directory_list:
            obj = key.ReadObj()
            obj_type = obj.ClassName()
            object_name = key.ReadObj().GetTitle()
            if object_name == name:
                # Remove a reference to this object from the list of in-memory objects for the current file or directory
                obj.SetDirectory(0)
                return obj
            if obj_type == "TDirectoryFile":
                lover_Level_List = obj.GetListOfKeys()
                for val in lover_Level_List:
                    lov_lvl_obj = val.ReadObj()
                    lover_Lvl_obj_name = lov_lvl_obj.GetTitle()
                    if lover_Lvl_obj_name == name:
                        lov_lvl_obj.SetDirectory(0)
                        return lov_lvl_obj

if __name__=="__main__":
    
    import seaborn as sns
    import matplotlib.pyplot as plt    
    from pydose3d.svc.dose3d import Dose3DSvc
        
    pydose3d.set_log_level("DEBUG")
    logger.info("NTupleDataSvc:: Run on example data...")
    # ntuple_data = "/home/g4rt/installation_files/pydose3d/pydose3d/data/d3d/sim/detector_4x8x10_in_water_layer_pads.root"
    ntuple_data = "/home/geant4/workspace/dose3d-geant4-linac/output/2023-06-14/single_file_tompl_run_test_13.root"
    # d3dsvc = Dose3DSvc()
    # d3dsvc.set_data(ntuple_data,"Dose3DVoxelisedTTree")
    # d3dsvc.set_data(ntuple_data,"Dose3DTTree")
    # lista = d3dsvc.dataSvc.get_hist_list(top_dir="Dose3D_LayerPads", type="TH2Poly",  contained_in_name="")
    # print(lista)
    
    ntupleSvc = NTupleDataSvc()
    ntupleSvc.set_data(ntuple_data,"PrimariesTree")
    # df = ntupleSvc.get_pdframe(columns={"primaryE"}, query="primaryE>0")
    df = ntupleSvc.get_pdframe(columns={"primaryX","primaryY"},query_pdf="primaryX>-10 & primaryX<10")
    # df = ntupleSvc.get_pdframe(columns={"primaryX","primaryY","primaryE"})
    print(df)
    sns.histplot(x='primaryX', data=df)
    plt.show()