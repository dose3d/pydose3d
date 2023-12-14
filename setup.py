''' default instalation: pip install -e .
'''
from setuptools import setup, find_packages
import sys
if sys.version_info < (3,10):
    sys.exit('Sorry, Python < 3.10 is not supported')

setup(
    name='pydose3d',
    version='0.1.0',
    packages=find_packages(include=['pydose3d']),
    install_requires=[
        'loguru==0.7.0',
        'pandas==2.0.1',
        'seaborn==0.12.2',
        'pytest==7.3.1'
    ]
)