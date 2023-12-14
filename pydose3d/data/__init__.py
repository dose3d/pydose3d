import socket
import os
from pydose3d.utils.__displayable_path import DisplayablePath as dp
from pathlib import Path
import urllib.request
from loguru import logger


class NoDefinedRootFile(Exception):
    def __init__(self, file):
        error_txt = f"File '{file}' not defined in map."
        super().__init__(error_txt)

_ROOT = os.path.abspath(os.path.dirname(__file__))
_ROOT_LHCBD1 = f"/data3/TN-Dose3D/data"

files_local_dir = f"{_ROOT}/downloaded"
files_site = "https://figshare.com/ndownloader/files/"
files_map = {
    "g4rt_data_structure_11112023.root" : "43119367",
    "bad_test.root" : "431193611"
}

def get_test_data_list():
    return list(files_map.keys())

def get_test_data(file_name, dir_name=''):

    if file_name in files_map:
        remote_file_name = files_map[file_name]
    else:
        e = NoDefinedRootFile(file_name)
        logger.error(f"{e}")
        raise e
    files_output_dir = files_local_dir
    if dir_name != '':
        files_output_dir = dir_name
    else:  # create dir only if default parameter is omitted
        if not os.path.exists(files_output_dir):
            os.makedirs(files_output_dir)
    file_url = f"{files_site}/{remote_file_name}"
    file_path = f"{files_output_dir}/{file_name}"
    logger.debug(f"rfn: {remote_file_name}, fu: {file_url}, fp: {file_path}")
    if not os.path.exists(file_path):
        try:
            urllib.request.urlretrieve(file_url,file_path)
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error: {e.code} - {e.reason}")
            raise
        except Exception as e:
             logger.error(f"Error {e}")
             raise
    return file_path

def get_example_data(path):
    return os.path.join(_ROOT, path)

def get_lhcbd1_data(path):
    # check if user works at lhcbd1 filesystem first
    try:    
        assert (is_lhcbd1())
    except:
        print("[get_lhcbd1_data]:: You are not working at LHCbD1 machine!")
    return os.path.join(_ROOT_LHCBD1, path)

def list_data(the_path):
    paths = dp.make_tree(Path(the_path))
    for path in paths:
        print(path.displayable())

def list_example_data(subpath=""):
    list_data(_ROOT+subpath)

def list_lhcbd1_data(subpath=""):
    # check if user works at lhcbd1 filesystem first
    try:    
        assert (is_lhcbd1())
    except:
        print("[get_lhcbd1_data]:: You are not working at LHCbD1 machine!")
    list_data(_ROOT_LHCBD1+subpath)

def is_lhcbd1():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    if '172.30.0.176' in local_ip:
        return True
    else:
        return False

