import pandas as pd
import numpy as np

path = ""
out_path = ""
files = ["flsz_2x2_voxelised_3x3x40_10x1x10.csv"
         ,""
         ]

df = pd.read_csv("/home/g4rt/installation_files/pydose3d/flsz_2x2_voxelised_3x3x40_10x1x10.csv")
# df['Dose'] = df['Dose']/df['Dose'].max()
df_geo = df[df["MaskTag"]==1].reset_index()


print(df_geo)
df_geo["Weighted X [mm]"] = df_geo["X [mm]"]*df_geo["Dose"]
df_geo["Weighted Y [mm]"] = df_geo["Y [mm]"]*df_geo["Dose"]
df_geo["Weighted Z [mm]"] = df_geo["Z [mm]"]*df_geo["Dose"]
geo_cetre_x = (df_geo["Weighted X [mm]"].sum())/(df_geo["Dose"].sum())
geo_cetre_y = (df_geo["Weighted Y [mm]"].sum())/(df_geo["Dose"].sum())
geo_cetre_z = (df_geo["Weighted Z [mm]"].sum())/(df_geo["Dose"].sum())

print(f"Geo Centre x:  {geo_cetre_x}")
print(f"Geo Centre y:  {geo_cetre_y}")
print(f"Geo Centre z:  {geo_cetre_z}")


df['CorrectedGeoTag'] =  1./(((df["X [mm]"]-geo_cetre_x)*(df["X [mm]"]-geo_cetre_x) 
                + (df["Y [mm]"]-geo_cetre_y)*(df["Y [mm]"]-geo_cetre_y) 
                + (df["Z [mm]"]-geo_cetre_z)*(df["Z [mm]"]-geo_cetre_z)).apply(np.sqrt))


df['CorrectedGeoMaskTagDose'] = df["Dose"]/(df['CorrectedGeoTag']*df["MaskTag"])

df.drop(['GeoTag', 'GeoMaskTagDose'],axis=1,inplace=True)
df.rename(columns={"CorrectedGeoTag": "GeoTag", "CorrectedGeoMaskTagDose": "GeoMaskTagDose"},inplace=True)

print(df)