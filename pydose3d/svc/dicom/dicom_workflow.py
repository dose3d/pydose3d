import pandas as pd
import numpy as np
from pathlib import Path
import json


dictionary = "/home/g4rt/instalki/pydose3d/pydose3d/data/d3d/settings/hounsfield_scale.json"
with open(dictionary) as jsn_file:
    hounsfield_units_dictionary, image_type_dictionary = json.load(jsn_file)


def create_ct_series(directory_path):
    images_path_string = directory_path + "/Images"
    images_paths = Path(images_path_string)
    
    # metadata = pd.read_csv(f'{self.__data_path}/series_metadata.csv',header=None,index_col=0)

    # 128 should be taken from metadata... 

    ser = pd.Series(np.zeros(128))
    iterator = 0
    for path in images_paths.iterdir():
        ser.iat[iterator] = (path.name)
        iterator +=1
    list = ser.sort_values(ignore_index=True).to_list()
    for element in list:
        print((pd.read_csv(f"{images_path_string}/{element}")["Material"]).map(hounsfield_units_dictionary).values.reshape(128,128))



if __name__=="__main__":
    create_ct_series("/home/g4rt/workDir/develop/g4rt/output/ct_test_13/geo/DikomlikeData")