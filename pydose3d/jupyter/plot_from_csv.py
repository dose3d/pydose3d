
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
fig, ax = plt.subplots()

df_0 = pd.read_csv("/home/g4rt/installation_files/pydose3d/flsz_propagation_study_voxelised_cell_dose_cp-0.csv")

new_df_sorted = df_0.copy()
new_df_sorted = new_df_sorted.sort_values(by = ['X [mm]', 'Y [mm]', 'Z [mm]'])
new_df_sorted['Dose'] = new_df_sorted['Dose']/new_df_sorted['Dose'].max()
v = (new_df_sorted['Dose'].apply(np.cbrt).values).reshape(30,30,400)

from matplotlib import pyplot as plt

x_values = new_df_sorted['X [mm]'].unique()
y_values = new_df_sorted['Y [mm]'].unique()
z_values = new_df_sorted['Z [mm]'].unique()

print('x values:', x_values, 'y values:', y_values, 'z values:', z_values)
# Select the XZ plane (Y = 0)
xz_plane = v[:, 19, :].T

# Extract X, Z coordinates and dose values
x_coords = np.tile(x_values, len(z_values))
z_coords = np.repeat(z_values, len(x_values))
dose_values = xz_plane.flatten()

plt.scatter(x_coords, z_coords, c=dose_values, cmap='viridis', s=150)
plt.colorbar()
plt.xlabel('Y [mm]')
plt.ylabel('X [mm]')
plt.title('YX Plane')
plt.show()