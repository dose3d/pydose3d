
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

import pymedphys

# To run:
# conda install -c conda-forge pydicom
# pip install pymedphys

def print_full(x):
    pd.set_option('display.max_rows', 600)
    pd.set_option('display.max_columns', 20)
    pd.set_option('display.width', 2000)
    pd.set_option('display.float_format', '{:20,.5f}'.format)
    pd.set_option('display.max_colwidth', None)
    print(x.head(20))
    print(x.tail(20))
    pd.reset_option('display.max_rows')
    pd.reset_option('display.max_columns')
    pd.reset_option('display.width')
    pd.reset_option('display.float_format')
    pd.reset_option('display.max_colwidth')


if __name__=="__main__":
    
    print("Start")
    
    mlsp_data_file = "/home/g4rt/Data/MLSP_vs_SIM/noweDane_UNET_Scratch_GeoAndMaskDose_flsz-25mm.csv"
    # mlsp_data_file = "/home/g4rt/Data/MLSP_vs_SIM/sampleOutput_Dose_flsz-25mm.csv"
    sim_data_file = "/home/g4rt/Data/MLSP_vs_SIM/4x4x4_10x10x10_flsz-25mm.csv"
    
    mlsp_df = pd.read_csv(mlsp_data_file)

    # print_full(mlsp_df)
    
    mlsp_df = mlsp_df.drop(['Unnamed: 0'], axis=1)
    
    # print_full(mlsp_df)
    
    mlsp_df = mlsp_df.sort_values(['X [mm]', 'Y [mm]', 'Z [mm]'])
    
    dose_evaluation = mlsp_df['ModelOutput'].values.reshape((40, 40, 40))
    dose_reference  = mlsp_df['GeoAndMaskDose'].values.reshape((40, 40, 40))

    x_ref = mlsp_df['X [mm]'].unique()
    y_ref = mlsp_df['Y [mm]'].unique()
    z_ref = mlsp_df['Z [mm]'].unique()

    axes_reference = (z_ref,y_ref,x_ref)
    axes_evaluation = (z_ref,y_ref,x_ref)
    
    # In our case = reference pos == evaluation pos
    
    # ----------------------------------------------------------------------------------
    
    gamma_options = {
    'dose_percent_threshold': 3.0,
    'distance_mm_threshold': 1.5,
    'lower_percent_dose_cutoff': 20,
    'interp_fraction': 10,  # Should be 10 or more for more accurate results
    'max_gamma': 3,
    'random_subset': None,
    'local_gamma': True,
    'ram_available': 2**32  # 4 GB
}
    gamma = pymedphys.gamma(
            axes_reference, dose_reference, 
            axes_evaluation, dose_evaluation, 
            **gamma_options)
    
    valid_gamma = gamma[~np.isnan(gamma)]

    num_bins = (
        gamma_options['interp_fraction'] * gamma_options['max_gamma'])
    bins = np.linspace(0, gamma_options['max_gamma'], num_bins + 1)

    plt.hist(valid_gamma, bins, density=True)
    #if density is True, y value is probability density; otherwise, it is count in a bin
    plt.xlim([0, gamma_options['max_gamma']])
    plt.xlabel('gamma index')
    plt.ylabel('probability density')
        
    pass_ratio = np.sum(valid_gamma <= 1) / len(valid_gamma)

    if gamma_options['local_gamma']:
        gamma_norm_condition = 'Local gamma'
    else:
        gamma_norm_condition = 'Global gamma'

    plt.title(f"Dose cut: {gamma_options['lower_percent_dose_cutoff']}% | {gamma_norm_condition} ({gamma_options['dose_percent_threshold']}%/{gamma_options['distance_mm_threshold']}mm) | Pass Rate(\u03B3<=1): {pass_ratio*100:.2f}% \n ref pts: {len(z_ref)*len(y_ref)*len(x_ref)} | valid \u03B3 pts: {len(valid_gamma)}")

    plt.savefig('gamma_hist.png', dpi=300)
    plt.show()
