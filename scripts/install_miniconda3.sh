#!/bin/sh
MINICONDA_VERSION=py39_4.12.0-Linux-x86_64
BASE_LOCATION=~/conda
CONDA_LOCATION=${BASE_LOCATION}/miniconda3


if [ -e ${CONDA_LOCATION} ] ;
then
	echo "${CONDA_LOCATION} already exists. Check it out - remove or use already installed conda!"
	return
else
	echo "Installing Miniconda in ${CONDA_LOCATION} ..."
fi

if [ ! -e ${BASE_LOCATION} ] ;
then
	mkdir -p ${BASE_LOCATION}
fi


wget https://repo.anaconda.com/miniconda/Miniconda3-${MINICONDA_VERSION}.sh -P ${BASE_LOCATION}
bash ${BASE_LOCATION}/Miniconda3-${MINICONDA_VERSION}.sh -b -p ${CONDA_LOCATION}
${CONDA_LOCATION}/bin/conda init
echo "auto_activate_base: false" > ~/.condarc
echo "Removing instalation script Miniconda3-${MINICONDA_VERSION}.sh"
rm ${BASE_LOCATION}/Miniconda3-${MINICONDA_VERSION}.sh
