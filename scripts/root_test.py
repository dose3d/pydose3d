import ROOT
from ROOT import TFile, TIter, TH2Poly, TCanvas # type: ignore
import numpy as np
import pandas as pd
import pydose3d.data as data
import pydose3d
import os
import sys
from loguru import logger

can_name_dict = {}
inputFileName = sys.argv[1]
print(" Reading from " , inputFileName )
inputFile = TFile.Open(inputFileName," READ ") # type: ignore
dżewo = inputFile.Get( "Dose3D_LayerPads" )
print ( dżewo )

mylist = dżewo . GetListOfKeys()

print("Printuje się po kluczach w folderze")
cancounter = 0
for key in mylist:
    print ( "\n" )
    obj = key.ReadObj()
    obj_Name = key.ReadObj().ClassName()
    print( obj_Name, ": ", key.ReadObj().GetTitle())
    if obj_Name == "TH2Poly":
        cancounter = cancounter +1
        name = obj_Name + f"{cancounter}"
        can_name_dict[f"{name}"] = TCanvas(name, name, 800, 800)
        can_name_dict[f"{name}"].cd()
        obj.Draw("COLZ")
    if obj_Name == "TDirectoryFile":
        lover_Level_List = obj . GetListOfKeys()
        for val in lover_Level_List:
            lover_Lvl_obj = val.ReadObj()
            lover_Lvl_obj_name = val.ReadObj().ClassName()
            print( lover_Lvl_obj_name, ": ", val.ReadObj().GetTitle())
            if lover_Lvl_obj_name == "TH2Poly":
                cancounter = cancounter +1
                name = lover_Lvl_obj_name + f"{cancounter}"
                can_name_dict[f"{name}"] = TCanvas(name, name, 800, 800)
                can_name_dict[f"{name}"].cd()
                lover_Lvl_obj.Draw("COLZ")
            












# iterator = TIter(mylist)

# print ( "\n\n\n\n\n" )


# print("Printuje się po kluczach w iteratorze - zgodnie z tutorialem")
# for val in iterator:
#     print ( "\n" )
#     print( val )
#     print( val.ClassName())
#     print( val.GetTitle())
#     print( val.ReadObj())
#     print( val.ReadObj().ClassName())
#     print( val.ReadObj().GetTitle()) # Lub GetName - u nas tutuł i nazwa są jednoznaczne. 
    
    
# # Output ideantyczny - nie ma różnicy którą metodą się iterujesz.