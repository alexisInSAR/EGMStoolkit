#! /usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""
Module from the `EGMStoolkit` constants

The module stores the different `EGMStoolkit` constants. 
    
    (From `EGMStoolkit` package)

Attributes:
    __name__ (str): Name of the Python package
    __author__ (str): Main authors of `EGMStoolkit`
    __copyright__ (str): Copyright
    __version__ (str): Current version
    __error__ (str): Header for the error message
    __warning__ (str): Header for the warning message
    __displayline1__ (str): String line (1)
    __displayline2__ (str): String line (2)
    __loggingmode__ (str): Logging level. **Can be modified by the user**. Can be ``NOTSET``, ``DEBUG``, ``INFO``, ``WARN``, ``ERROR``, ``CRITICAL``

Changelog:
        * 0.2.7: Add the __unlockfoliumtiles__ parameters, Apr. 2024, Alexis Hrysiewicz
        * 0.2.0: Initial version, Jan. 2024

"""

################################################################################
from EGMStoolkit import __namePackage__
from EGMStoolkit import __copyrightPackage__
from EGMStoolkit import __versionPackage__
from EGMStoolkit import __authorPackage__
import os 

################################################################################
__name__ =  __namePackage__
__author__ = __authorPackage__
__copyright__ = __copyrightPackage__
__version__ = __versionPackage__

__error__ = 'ERROR in EGMS-toolkit processing:'
__warning__ = 'WARNING in EGMS-toolkit processing:'

__displayline1__ = '################################################################################'
__displayline2__ = '--------------------------------------------------------------------------------'

################################################################################
## This part can be modified by the user
################################################################################
__loggingmode__ = 'INFO'
__pathS1map__ = os.path.dirname(__file__)+os.sep+'3rdparty'
__unlockfoliumtiles__ = False