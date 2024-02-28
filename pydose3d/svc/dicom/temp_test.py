import pandas as pd
import numpy as np

import json

from pydose3d.utils.__displayable_path import DisplayablePath as dp
from pathlib import Path


def list_data(the_path):
    paths = dp.make_tree(Path(the_path))
    for path in paths:
        print(path.displayable())
        # pass

dictionary = "/home/g4rt/instalki/pydose3d/pydose3d/data/d3d/settings/hounsfield_scale.json"
with open(dictionary) as jsn_file:
    hounsfield_units_dictionary, image_type_dictionary = json.load(jsn_file)


# ser = pd.Series(np.zeros(data_dict["x_resolution"]))
ser = pd.Series(np.zeros(128))
ser2 = pd.Series(np.zeros(128))

paths = (Path("/home/g4rt/workDir/develop/g4rt/output/ct_test_13/geo/DikomlikeData/Images"))
iterator = 0
for path in paths.iterdir():
    print(path)
    if(iterator%4 == 0):
        ser.iat[iterator] = "Usr_G4AIR20C"
    if(iterator%4 == 1):
        ser.iat[iterator] = "Vacuum"
    if(iterator%4 == 2):
        ser.iat[iterator] = "PMMA"
    if(iterator%4 == 3):
        ser.iat[iterator] = "RMPS470"
    
    iterator +=1

df = pd.DataFrame()
df["Names"] = ser
df["HU"] = df["Names"].map(hounsfield_units_dictionary)

for path in paths.iterdir():
    ser2.iat[iterator] = (path.name)
    iterator +=1
print(ser.sort_values(ignore_index=True))



print(df)
# list_data("/home/g4rt/workDir/develop/g4rt/output/ct_test_13/geo/DikomlikeData")