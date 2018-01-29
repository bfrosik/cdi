cdi
===
Coherent Diffraction Imaging technique provides a reconstruction of image of a nanoscale structures. Refer to Wikipedia article CDI description for the technique details.
Project summary: Implement and parallelize genetic algorithms and phase retrieval methods for Bragg CDI techniques.

The CDI experiments are performed at the beamline 34-ID. The team currently uses tool written in Matlab. This tool provides multiple features, and includes newest scientific discoveries in the field. Recently, scientists in general, are shifting to Python written tools, as Python offers better performance, and is easier to maintain.

Goal of this project is to deliver fast tool, easy to maintain, that includes all the features currently available. There is a prospect to conduct research in the field, and add the new ideas/features when proved successful.
 
A genetic algorithm approach to CDI phase retrieval will improve coherent imaging in two aspects. The first is to enable the recovery of highly reproducible images from a given data set. The second is to render previously impossible to image samples amenable to CDI, opening the door to a greater scientific impact for the method. The basic idea is to do the same phasing process with tens to thousands of random starting points. The diversity of results is then exploited to arrive at a highly reproducible image of the sample. Another aspect of genetic algorithm approaches is in the “fitness” criterion used to evaluate the population of results. This can be tuned to enable phase retrieval of datasets that have previously been impossible to produce images from.
It is desired to implement and parallelize software for fast processing by non-expert beamline users. Current processing time of a 100 MB sample using serial MATLAB code takes 60 minutes using limited parameters. Current data acquisition time for a 100 MB data set is 20 minutes, and will decrease after the completion of the APS Upgrade. Attaining a robust image of a sample in a computation time nearer the data acquisition time will allow nearer real-time feedback into the experimental parameters. The experimenter may begin to do guided, carefully executed experiments. Currently, the vast majority of Bragg CDI users will benefit from semi-real-time phase retrieval for their data. It will also open the instrument up to far less sophisticated CDI users. This technique will be critical to one or more APS Upgrade beamlines.


Version
-------
0.0.1 - 10/25/2017

Pre-requisites
---------------
- ArrayFire library version 3.5.0 or higher
- Libconfig library version 1.5 or higher
- Python packages installation:
  - pip install tifffile
  - pip install pylibconfig2
  - conda install vtk
  - conda install traits
  - conda install traitsui
  - pip install mayavi

Author(s)
-------
Barbara Frosik - Principal Software Engineer at Argonne National Laboratory

License
-------
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.

C++ Libraries
-------------
- ArrayFire open source
- Libconfig open source

How to init
-----------
- clone the source from the repository: 
  - git clone https://github.com/advancedPhotonSource/cdi
  - cd cdi
- run interactive script to set enviroment variables and set the project:
  - source init.sh
  at the promt enter the following:
  - enter ArrayFire installation directory > (absolute path to ArrayFire installation dir)
  - enter LibConfig installation directory > (absolute path to LibConfig installation dir)
  - enter cuda installation directory > (absolute path to cuda installation dir)
  - enter data type (float/double) > double
 
How to run
----------
- python test.py (proc) (file name) (config file)
  - (proc) is processing ArrayFire library ('cpu', 'opencl', or 'cuda')
  - (file name) is data file name. It can be either tif file or numpy file. In the first case the file would contain original data, in the second case the numpy file would hold saved prepared data as ndarray.
  - (config file) is a name of configuration file. This repository contains 'config.test' configuration foe for your use.
 
example:python test.py 'opencl' '/directory/Staff14-3_S0149.tif' 'config.test'
  
How to compile
--------------
python setup.py build_ext --inplace

