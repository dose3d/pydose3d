# PyDose3D - data handling and analysis tools

## The purpose of the package
* Keep all python tools in one place:  
* Working with "Don't repeat yourself (D.R.Y.)" rule
* External dependencies explicitly defined in the whole Dose3D analysis project

# Anaconda environment and package installation
It's assumed that the Anaconda packages manager is used to setup virtual environment.  
You can use the following script in install `miniconda3` in your home directory (Linux/WSL):
```
source scripts/install_miniconda3.sh
```

## Create / activate / update conda environment
All depandancies are being tracked with `yml` file. You can get it from here:  
```
wget https://github.com/dose3d/ppa/blob/main/share/conda_env.yml
```  

## Install pydose3d package
Pay attention for the environemt you work with

### Custom ennvironment
Go to the top dir of the package (where `setup.py` is placed). Run the command:
```
pip3 install -e .
```
The `-e` flag specifies that we want to install in editable mode, which means that when we edit the files in our package we do not need to re-install the package before the changes come into effect.

### The `g4rt` environment
Once you created your environment with above mentioned `yml` file, note that this package is automatically being installed for you. Hence, if you need to install this package in editable mode, first you need unistall previous installation:  
```
pip uninstall pydose3d
```
then, go to instruction for the installation in custom ennvironment.



# Google Colaboratory local jupy-server
You need extra packages to work with Google Colaboratory. You can install them in your environment with runnig the conda update from file:  
```
conda env update --file scripts/conda_colab_requirements.yml
```

After all you can simply run the following script to start local server on your machine for interactive work:  
```
source scripts/run_jupyter_colab.sh
```