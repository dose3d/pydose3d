import pydose3d
import pydose3d.data as data
from pydose3d.svc.ntuple_data import NTupleDataSvc
from pydose3d.svc.dose3d import Dose3DSvc
from pydose3d.svc.exceptions import *
from loguru import logger

NTupleDataSvc.ImplicitMT = True
pydose3d.set_log_level("DEBUG")

# data = "/home/geant4/projekty/pydose3d/pydose3d/data/d3d/sim/detector_shifted_4x4x4_in_air/angle_scn_5ctrl-pts_10e5.root"

d3dsvc = Dose3DSvc()

list = data.get_test_data_list()
logger.debug(list)
data.get_test_data("g4rt_data_structure_11112023.root")
# data.get_test_data("bad_test.root")
# data.get_test_data("bad_test2.root")

# try: 
#     d3dsvc.set_data(["/tmp/abc","xyz"])
# except Pydose3dException:
#     print ("Catched exception glob")

