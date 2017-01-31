# Python 2.7
# This function is called from main.py if the user has a Cython installation
from distutils.core import setup
from Cython.Build import cythonize

setup(
	ext_modules = cythonize("helpers.pyx")	
)