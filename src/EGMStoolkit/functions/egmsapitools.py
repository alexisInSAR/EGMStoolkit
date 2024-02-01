#! /usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""
Module to add some functions to **`EGMStoolkit`**

The module adds some functions, required by to run `EGMStoolkit`.

    (From `EGMStoolkit` package)

Changelog:
    * 0.2.1: Remove the duplicate points for L2 datasets, Feb. 2024, Alexis Hrysiewicz
    * 0.2.0: Script structuring, Jan. 2024, Alexis Hrysiewicz
    * 0.1.0: Initial version, Nov. 2023

"""

from EGMStoolkit import usermessage
from EGMStoolkit import constants

################################################################################
## Function to create the extention for the release
################################################################################
def check_release(inputrelease): 
    """Check the release and get the file extension
        
    Args:

        inputrelease (str)

    Return

        list: release_para

    """ 
    
    if inputrelease == '2015_2021': 
        ext_release = ''
    elif inputrelease == '2018_2022':
        ext_release = '_2018_2022_1'
    else: 
        raise ValueError(usermessage.errormsg(__name__,'check_release',__file__,constants.__copyright__,'The release is not correct.',None))


    release_para = [inputrelease, ext_release]

    return release_para

################################################################################
## Function to define the release for the name file
################################################################################
def check_release_fromfile(namefile):
    """Check the release and get the file extension, from a file name
        
    Args:

        namefile (str): path of the file

    Return

        list: release_para

    """  
    
    ni = namefile.split('.')
    ni = ni[0].split('VV')
    
    if '_2018_2022_1' in ni[-1]: 
        inputrelease = '2018_2022'
        ext_release = '_2018_2022_1'
    else: 
        inputrelease = '2015_2021'
        ext_release = ''
    
    release_para = [inputrelease, ext_release]

    return release_para