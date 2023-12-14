import pydose3d
from pydose3d.svc.ntuple_data import NTupleDataSvc
from pydose3d.svc.dose3d import Dose3DSvc
NTupleDataSvc.ImplicitMT = True
pydose3d.set_log_level("INFO")

if __name__=="__main__":
    ntuple_data ="/home/g4rt/instal/dose3d-geant4-linac/output/25mm/mlsp_4x4x4_10x10x10_flsz-25mm.root"
    d3dsvc = Dose3DSvc()
    d3dsvc.set_data(ntuple_data,"Dose3DVoxelisedTTree")

    data2 = d3dsvc.get_mlsp_pdframe(scoring="Voxel", squareFieldSize=25)
    data2.to_csv(float_format='%.4f',index=False,path_or_buf="/home/g4rt/installation_files/pydose3d/pydose3d/data/d3d/25mm1e8/mlsp_4x4x4_10x10x10_flsz-25mm_n-event_1e8.csv")