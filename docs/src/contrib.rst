Contribution
##############

This page some contributions. The script can be done in the *contrib* direction (i.e., root/contrib). They are classified regarding the language used. 

The MATLAB *EGMStoolkitimport.m* script
=======================================

The MATAB script allows to import and display the EGMS results (in .csv format). The user needs to have a version of MATLAB installed and the Mapping Toolbox. The contrib direction should be in the MATLAB path. 

**First, the user can import any .csv dataset:**

.. code:: matlab 

    data = EGMStoolkitimport('EGMS_file.csv','delimiter',';','verbose',true);

The delimiter and verbose options are optional.

**Then, it is possible to display the dataset:**

.. code:: matlab

    data.plot('mean_velocity','geobasemap',true,'ts_plot',true); 

*geobasemap* (bool) will create the map with satellite imagery (optional, True by default). *ts_plot* (bool) will ask the user to create time series plot (optional, False by default). Both options are optional. We recommend using 'geobasemap=False' for large datasets. 

The Python *EGMStoolkitimport.py* script
========================================

Under development. 