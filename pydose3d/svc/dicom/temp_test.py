import pandas as pd
import numpy as np

import json

from pydose3d.utils.__displayable_path import DisplayablePath as dp
from pathlib import Path


def list_data(the_path):
    paths = dp.make_tree(Path(the_path))
    for path in paths:
        print(path.displayable())



data = pd.read_csv('pydose3d/svc/dicom/series_metadata.csv',header=None,index_col=0)
data_dict = data.to_dict(orient='dict')[1]
print(data_dict)
print(data_dict["x_resolution"])


dictionary = "/home/g4rt/instalki/pydose3d/pydose3d/data/d3d/settings/hounsfield_scale.json"

with open(dictionary) as jsn_file:
    multi_dictionary = json.load(jsn_file)


# ser = pd.Series(np.zeros(data_dict["x_resolution"]))
ser = pd.Series(np.zeros(26))
hounsfield_units_dictionary, image_type_dictionary = multi_dictionary

print(hounsfield_units_dictionary)
print(hounsfield_units_dictionary["PMMA"])


print(image_type_dictionary)
print(image_type_dictionary["CT"])


paths = (Path("/home/g4rt/workDir/develop/g4rt/output/new_phsp_test_4/geo/DikomlikeData"))
iterator = 0
for path in paths.iterdir():
    ser.iat[iterator] = (path.name)
    iterator +=1

print(ser.sort_values(ignore_index=True))

# list_data("/home/g4rt/workDir/develop/g4rt/output/new_phsp_test_4/geo/DikomlikeData")