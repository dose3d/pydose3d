from ROOT import TFile, TIter, TH2Poly, TCanvas, gStyle, gROOT, gStyle # type: ignore
import pydose3d.data as data
from loguru import logger



class RootObjStore:
    def __init__(self):
        self.__root_objects_store = {}
        
    def root_file_iterator(self, input_file_name, root_dir="Dose3D_LayerPads"):
        
        input_file = TFile . Open(input_file_name," READ ") # type: ignore
        directory_tree = input_file . Get( root_dir )
        print ( directory_tree )

        directory_list = directory_tree . GetListOfKeys()

        cancounter = 0
        for key in directory_list:
            obj = key . ReadObj()
            obj_Name = key . ReadObj() . ClassName()
            if obj_Name == "TH2Poly":
                name = key.ReadObj().GetTitle()
                # Wrape me in Add to obj store....
                self.__root_objects_store[f"{name}"] = key.ReadObj()
            if obj_Name == "TDirectoryFile":
                lover_Level_List = obj . GetListOfKeys()
                for val in lover_Level_List:
                    lover_Lvl_obj = val.ReadObj()
                    lover_Lvl_obj_name = val.ReadObj().ClassName()
                    if lover_Lvl_obj_name == "TH2Poly":
                        name = val.ReadObj().GetTitle()
                        self.__root_objects_store[f"{name}"] = val.ReadObj()

        print(self.__root_objects_store)

    def __fill_bin(self, poly_histogram, value, position_in_x, position_in_z):

        nbin = poly_histogram.FindBin(float(position_in_x),float(position_in_z))
        poly_histogram.SetBinContent(nbin,value)
        return poly_histogram



    def fill_poly_histogram(self, grouped_dataframe, module_layer, cell_layer = -1):
        
        if cell_layer == -1:
            prefix = "Cell"
            name = f"Dose3D_MLayer_{module_layer}"
        else:
            prefix = "Voxel"
            name = f"Dose3D_MLayer_{module_layer}_CLayer_{cell_layer}"


        for row in grouped_dataframe.rows:
            self.__root_objects_store[name] = self.__fill_bin(self.__root_objects_store[name],row[f"{prefix}Dose"] ,row[f"{prefix}PosX"],row[f"{prefix}PosZ"])




    def get_Th2Poly(self, module_layer, cell_layer = -1):

            if cell_layer == -1:
                name = f"Dose3D_MLayer_{module_layer}"
            else:
                name = f"Dose3D_MLayer_{module_layer}_CLayer_{cell_layer}"
                
            print(type(self.__root_objects_store[name]))
            
            return self.__root_objects_store[name]