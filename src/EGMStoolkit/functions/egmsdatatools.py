#! /usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""
Module to add some functions post-process the data from EGMS, with **`EGMStoolkit`**

The module adds some functions, required by `EGMStoolkit` to post-process the EGMS data. 

    (From `EGMStoolkit` package)

Changelog:
    * 0.2.9: A correction of typo., Apr. 2024, Alexis Hrysiewicz
    * 0.2.6: Bug fixes regarding the windows system + GDAL version (some information), Feb. 2024, Alexis Hrysiewicz
    * 0.2.5: Add the interpolation processing for the .vrt file + optional function arguments for "duplicate" point and vrt files, Feb. 2024, Alexis Hrysiewicz
    * 0.2.4: Add the possibility to merge the L3 .csv file into a .vrt file and fix the problem with the L2 datasets, Feb. 2024, Alexis Hrysiewicz
    * 0.2.3: Add the possibility to merge the L2 .csv file into a .vrt file (but can fail), Feb. 2024, Alexis Hrysiewicz
    * 0.2.2: Optimisation of clipping based on ogr2ogr, Feb. 2024, Alexis Hrysiewicz
    * 0.2.1: Remove the duplicate points for L2 datasets, Feb. 2024, Alexis Hrysiewicz
    * 0.2.0: Script structuring, Jan. 2024, Alexis Hrysiewicz
    * 0.1.0: Initial version, Nov. 2023

"""

import numpy as np
import glob
import pandas as pd 
import subprocess
import os
import fiona
from shapely.geometry import Polygon, mapping, shape, LineString, Point
import pyproj
import shutil
from typing import Optional, Union
from matplotlib import path
import platform

from EGMStoolkit import usermessage
from EGMStoolkit import constants
from EGMStoolkit.functions import egmsapitools

try: 
    from concave_hull import concave_hull_indexes
except: 
    usermessage.warningmsg(__name__,__name__,__file__,'Impossible to import concave_hull, required for removing of duplicate points.',None,True)

from osgeo import __version__ as infoversiongdal
if int(infoversiongdal.split('.')[0]) < 3: 
    usermessage.warningmsg(__name__,__name__,__file__,'The GDAL is lower than 3.8.0 (user version : %s) but this version is required for data gridding.' % (infoversiongdal),None,True)
elif int(infoversiongdal.split('.')[1]) < 8: 
    usermessage.warningmsg(__name__,__name__,__file__,'The GDAL is lower than 3.8.0 (user version : %s) but this version is required for data gridding.' % (infoversiongdal),None,True)

source_crs = 'epsg:4326'
"""str: Source CRS.
"""

target_crs = 'epsg:3035'
"""str: Target CRS.
"""

latlon_to_meter = pyproj.Transformer.from_crs(source_crs, target_crs)
"""class: Pyproj class Lat/lon (epsg:4326) to meter (epsg:3035)
"""
meter_to_latlon = pyproj.Transformer.from_crs(target_crs,source_crs)
"""class: Pyproj class meter (epsg:3035) to Lat/lon (epsg:4326)
"""

################################################################################
## Function to convert .csv to another vector format
################################################################################
def convertcsv(outputdir: Optional[str] = '.'+os.sep+'Output',
    inputdir: Optional[str] = '.'+os.sep+'Output',
    namefile: Optional[Union[bool,None]] = 'all',
    format: Optional[Union[bool,None]] = 'ESRI Shapefile',
    verbose: Optional[bool] = True, 
    log: Optional[Union[str,None]] = None): 
    """Interpolation of the data into a .tif raster
        
    Args:

        outputdir (str, Optional): Output directory [Default: './Ouput']
        inputdir (str, Optional): Input directory [Default: './Ouput']
        namefile (str): File name for interpolation [Default: 'all']
        format (str): Format of the output file [Default: 'ESRI Shapefile']
        verbose (bool, Optional): Verbose [Default: `True`]
        log (str or None, Optional): Log file [Default: `None`]

    """ 

    if not os.path.isdir(outputdir):
        os.mkdir(outputdir)

    usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Convert the .csv files to another vector format',log,verbose)
 
    if namefile == 'all':
        list_filetmp = glob.glob('%s%s*.csv' %(inputdir,os.sep))

        list_noclip = []
        list_clip = []
        for li in list_filetmp:
            if 'clipped' in li:
                list_clip.append(li)
            else:
                list_noclip.append(li)
        
        if list_clip:
            list_file_final = list_clip
        else:
            list_file_final = list_noclip

    else:
        tmp = namefile.split(',')
        if not os.sep in namefile:
            list_file_final = []
            for ni in tmp:
                list_file_final.append(inputdir+'/'+ni)
        else:
            list_file_final = [namefile]

    if not list_file_final:
        raise ValueError(usermessage.errormsg(__name__,'convertcsv',__file__,constants.__copyright__,'The list of files is empty.',log))

    usermessage.egmstoolkitprint('\tList of files processed:',log,verbose)
    for li in list_file_final:
        usermessage.egmstoolkitprint('\t\t%s' %(li),log,verbose)

    if format == 'ESRI Shapefile': 
        ext_format = 'shp'
    elif format == 'GPKG':
        ext_format = 'gpkg'
    elif format == 'GeoJSON':
        ext_format = 'geojson'
    else: 
        raise ValueError(usermessage.errormsg(__name__,'convertcsv',__file__,constants.__copyright__,'This format is not supported. The option are : ESRI Shapefile, GPKG, GeoJSON',log))

    # Interpolation
    it = 1
    for fi in list_file_final:
        usermessage.egmstoolkitprint('\t%d / %d Processing of the file: %s:' %(it,len(list_file_final),fi),log,verbose)
        namefile = fi[0:-4].split('/')[-1]

        if not os.path.isfile('%s%s%s.%s' % (outputdir,os.sep,namefile,ext_format)):
            cmdi = "ogr2ogr -of '%s' -s_srs EPSG:3035 -t_srs EPSG:3035 -oo HEADERS=YES -oo SEPARATOR=SEMICOLON -oo X_POSSIBLE_NAMES=easting -oo Y_POSSIBLE_NAMES=northing %s%s%s.%s %s%s%s.csv" % (
                format,outputdir,os.sep,namefile,ext_format,outputdir,os.sep,namefile)

            usermessage.egmstoolkitprint('\t\tThe command will be: %s' % (cmdi),log,verbose)
            os.system(cmdi)
        else:
            usermessage.egmstoolkitprint('\t\tThe file has been detected. Please delete it for a new conversion.',log,verbose)

        it = it + 1

################################################################################
## Function to interpolate the data into a raster
################################################################################
def datagridding(paragrid,
    outputdir: Optional[str] = '.'+os.sep+'Output',
    inputdir: Optional[str] = '.'+os.sep+'Output',
    namefile: Optional[Union[bool,None]] = 'all',
    verbose: Optional[bool] = True, 
    log: Optional[Union[str,None]] = None): 
    """Interpolation of the data into a .tif raster
        
    Args:

        paragrid (dict): Dictionnary of the interpolation parameters
        outputdir (str, Optional): Output directory [Default: './Ouput']
        inputdir (str, Optional): Input directory [Default: './Ouput']
        namefile (str): File name for interpolation [Default: 'all']
        verbose (bool, Optional): Verbose [Default: `True`]
        log (str or None, Optional): Log file [Default: `None`]

    """ 

    if not os.path.isdir(outputdir):
        os.mkdir(outputdir)

    if paragrid['Xmin'] <= 0 or paragrid['Ymin'] <= 0 or paragrid['Xmin'] <= 0 or paragrid['Ymax'] <= 0 or paragrid['xres'] <= 0 or paragrid['yres'] <= 0: 
        raise ValueError(usermessage.errormsg(__name__,'datagridding',__file__,constants.__copyright__,'The paragrid parameter is not correct.',log))

    if (not 'invdist' in paragrid['algo']) and (not 'invdistnn' in paragrid['algo']) and (not 'average' in paragrid['algo']) and (not 'nearest' in paragrid['algo'])  and (not 'linear' in paragrid['algo']):
        raise ValueError(usermessage.errormsg(__name__,'datagridding',__file__,constants.__copyright__,'The paragrid parameter is not correct.',log))

    usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Interpolation of the data into a .tif raster',log,verbose)
    usermessage.egmstoolkitprint('\tThe file name is: %s' % (namefile),log,verbose)
    usermessage.egmstoolkitprint('\tInput Directory: %s' % (inputdir),log,verbose)
    usermessage.egmstoolkitprint('\tOutput Directory: %s' % (outputdir),log,verbose)
    usermessage.egmstoolkitprint('\tParameters for interpolation',log,verbose)
    usermessage.egmstoolkitprint('\t\t X min. (in EPGS:3035): %f' %(paragrid['Xmin']),log,verbose)
    usermessage.egmstoolkitprint('\t\t Y min. (in EPGS:3035): %f' %(paragrid['Ymin']),log,verbose)
    usermessage.egmstoolkitprint('\t\t X max. (in EPGS:3035): %f' %(paragrid['Xmax']),log,verbose)
    usermessage.egmstoolkitprint('\t\t Y max. (in EPGS:3035): %f' %(paragrid['Ymax']),log,verbose)
    usermessage.egmstoolkitprint('\t\t X resolution (in EPGS:3035): %f' %(paragrid['xres']),log,verbose)
    usermessage.egmstoolkitprint('\t\t Y resolution (in EPGS:3035): %f' %(paragrid['yres']),log,verbose)
    usermessage.egmstoolkitprint('\t\t Algorithm options: %s' %(paragrid['algo']),log,verbose)

    if namefile == 'all':
        list_filetmp = glob.glob('%s%s*.csv' %(inputdir,os.sep)) + glob.glob('%s%s*.vrt' %(inputdir,os.sep))

        list_noclip = []
        list_clip = []
        for li in list_filetmp:
            if 'clipped' in li:
                list_clip.append(li)
            else:
                list_noclip.append(li)
        
        if list_clip:
            list_file_final = list_clip
        else:
            list_file_final = list_noclip

    else:
        tmp = namefile.split(',')
        if not os.sep in namefile:
            list_file_final = []
            for ni in tmp:
                list_file_final.append(inputdir+'/'+ni)
        else:
            list_file_final = [namefile]

    if not list_file_final:
        raise ValueError(usermessage.errormsg(__name__,'datagridding',__file__,constants.__copyright__,'The list of files is empty.',log))

    usermessage.egmstoolkitprint('\tList of files processed:',log,verbose)
    for li in list_file_final:
        usermessage.egmstoolkitprint('\t\t%s' %(li),log,verbose)

    usermessage.egmstoolkitprint('\tList of parameters interpolated:',log,verbose)
    for li in paragrid['variable'].split(','):
        usermessage.egmstoolkitprint('\t\t%s' %(li),log,verbose)

    # Interpolation
    it = 1
    for fi in list_file_final:
        usermessage.egmstoolkitprint('\t%d / %d Processing of the file: %s:' %(it,len(list_file_final),fi),log,verbose)

        namefile = fi[0:-4].split('/')[-1]

        for parai in paragrid['variable'].split(','):
            usermessage.egmstoolkitprint('\t\tInterpolation for the variable: %s' % (parai),log,verbose)

            if not os.path.isfile('%s%s%s_%s.tif' % (outputdir,os.sep,namefile,parai)):

                if '.csv' in fi: 
                    cmdi = 'gdal_grid -zfield "%s" -a_srs EPSG:3035 -oo HEADERS=YES -oo SEPARATOR=SEMICOLON -oo X_POSSIBLE_NAMES=easting -oo Y_POSSIBLE_NAMES=northing -a %s -txe %f %f -tye %f %f -tr %f %f -of GTiff -l %s -ot Float64 %s%s%s.csv %s%s%s_%s.tif' % (parai,paragrid['algo'],paragrid['Xmin'],paragrid['Xmax'],paragrid['Ymin'],paragrid['Ymax'],paragrid['xres'],paragrid['yres'],namefile,outputdir,os.sep,namefile,outputdir,os.sep,namefile,parai)
                else: 
                    cmdi = 'gdal_grid -zfield "%s" -a_srs EPSG:3035 -oo HEADERS=YES -oo SEPARATOR=SEMICOLON -a %s -txe %f %f -tye %f %f -tr %f %f -of GTiff -l %s -ot Float64 %s%s%s.vrt %s%s%s_%s.tif' % (parai,paragrid['algo'],paragrid['Xmin'],paragrid['Xmax'],paragrid['Ymin'],paragrid['Ymax'],paragrid['xres'],paragrid['yres'],namefile,outputdir,os.sep,namefile,outputdir,os.sep,namefile,parai)
                

                usermessage.egmstoolkitprint('\t\tThe command will be: %s' % (cmdi),log,verbose)
                os.system(cmdi)
            else:
                usermessage.egmstoolkitprint('\t\tThe .tif file has been detected. Please delete it for a new interpolation.',log,verbose)

        it = it + 1

################################################################################
## Function to delete the raw data
################################################################################
def removerawdata(inputdir: Optional[str] = '.'+os.sep+'Output',
    forcemode: Optional[bool] = False,
    verbose: Optional[bool] = True, 
    log: Optional[Union[str,None]] = None): 
    """Delete the raw dataset(s) from EGMS
        
    Args:

        inputdir (str, Optional): Input directory [Default: './Ouput']
        forcemode (bool, Optional): Force mode [Default: `False`]
        verbose (bool, Optional): Verbose [Default: `True`]
        log (str or None, Optional): Log file [Default: `None`]

    """ 

    if not (os.path.isdir(inputdir)):
        raise ValueError(usermessage.errormsg(__name__,'removerawdata',__file__,constants.__copyright__,'The input directory %s is not a directory.' % (inputdir),log))

    usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Delete the raw dataset(s) from EGMS',log,verbose)
    usermessage.egmstoolkitprint('\tInput Directory: %s' % (inputdir),log,verbose)

    if not forcemode:
        answer = input('Can you confirm the removal of raw-data directories? [y or n]?')
    else:
        answer = 'y'

    if answer in ['y','Y','yes','Yes','YES','1']:
        usermessage.egmstoolkitprint('Deleting...',log,verbose)

        for i1 in ['L2a', 'L2b', 'L3UD', 'L3EW']:
            if os.path.isdir('%s/%s' % (inputdir,i1)):
                shutil.rmtree('%s/%s' % (inputdir,i1))

    li = glob.glob('bbox.*')
    if li:
        if not forcemode:
            answer = input('The bbox files have been detected. Can you confirm the removal of these files? [y or n]?')
        else:
            answer = 'yes'
        if answer in ['y','Y','yes','Yes','YES','1']:
            usermessage.egmstoolkitprint('Deleting...',log,verbose)
            for i1 in li:
                os.remove('%s' % (i1))

################################################################################
## Function to merge the datasets in csv format
################################################################################
def datamergingcsv(outputdir: Optional[str] = '.'+os.sep+'Output',
    inputdir: Optional[str] = '.'+os.sep+'Output',
    paratosave: Optional[any] = 'all',
    mode: Optional[str] = 'onlist',
    infoEGMSdownloader: Optional[any] = None,
    __removeduplicate__: Optional[bool] = True,
    __length_threshold__: Optional[int] = 1000,
    __usevrtmerging__: Optional[bool] = False,
    verbose: Optional[bool] = True, 
    log: Optional[Union[str,None]] = None): 
    """Merge the datasets in csv format
        
    Args:

        inputdir (str, Optional): Input directory [Default: './Ouput']
        outputdir (str, Optional): Input directory [Default: './Ouput']
        paratosave (str, Optional): Selected parameters [Default: 'all']
        mode (str, Optional): Mode on selection. Can be 'onlist' or 'onfiles' [Default: 'onlist']
        infoEGMSdownloader(str, Optional): Class of EGMSdownloader. Can be 'onlist' or 'onfiles' [Default: `None`]
        __removeduplicate__ (bool): Remove the duplicate points [Default: True]
        __length_threshold__ (int): Length for the concave hull [Default: 1000]
        __usevrtmerging__ (bool): Use the vrt for merging [Default: False]
        verbose (bool, Optional): Verbose [Default: `True`]
        log (str or None, Optional): Log file [Default: `None`]

    """ 
    
    ## Parameters
    if not mode in ['onlist', 'onfiles']: 
        raise ValueError(usermessage.errormsg(__name__,'datamergingcsv',__file__,constants.__copyright__,'The mode parameter is not correct.',log))
    if mode == 'onlist' and infoEGMSdownloader == True: 
            raise ValueError(usermessage.errormsg(__name__,'datamergingcsv',__file__,constants.__copyright__,'The output of EGMSdownloaderapi function is required with the "onlist" mode.',log))
    if not (verbose == True or verbose == False):
        raise ValueError(usermessage.errormsg(__name__,'datamergingcsv',__file__,constants.__copyright__,'bad parameter of the verbose parameter [True or False]',log))    
    if not (os.path.isdir(outputdir)):
        raise ValueError(usermessage.errormsg(__name__,'datamergingcsv',__file__,constants.__copyright__,'The output directory %s is not a directory.' % (outputdir),log))
    if not (os.path.isdir(inputdir)):
        raise ValueError(usermessage.errormsg(__name__,'datamergingcsv',__file__,constants.__copyright__,'The input directory %s is not a directory.' % (inputdir),log))

    usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Merge the datasets in csv format',log,verbose)
    usermessage.egmstoolkitprint('\tOutput Directory: %s' % (outputdir),log,verbose)
    usermessage.egmstoolkitprint('\tInput Directory: %s' % (inputdir),log,verbose)
    usermessage.egmstoolkitprint('\tSelected parameters: %s' % (paratosave),log,verbose)
    usermessage.egmstoolkitprint('\tMode: %s' % (mode),log,verbose)
    
    ## Creation of the list for merging
    if mode == 'onlist': # Based on the list
        listfiles = []
        for type in ['L2a', 'L2b', 'L3UD', 'L3EW']:
            datatmp = eval('infoEGMSdownloader.list%s' % (type))
            if datatmp: 
                for idx in np.arange(len(datatmp)): 
                    release_para = egmsapitools.check_release_fromfile(datatmp[idx])
                    listfiles.append('%s%s%s%s%s%s%s' % (inputdir,os.sep,type,os.sep,release_para[0],os.sep,datatmp[idx].split('.')[0]))
    else: # Based on the files
        listfiles = glob.glob('%s%s*%s*%s*%s*.csv' % (inputdir,os.sep,os.sep,os.sep,os.sep))

    if not listfiles:
        raise ValueError(usermessage.errormsg(__name__,'datamergingcsv',__file__,constants.__copyright__,'No files are detected.' % (inputdir),log))

    filedict, release, level, track, L3compall = listtodictmerged(listfiles)
    
    for ri in release:
        for li in level:
            if not li == 'L3':
                for ti in track:
                    try:
                        file_list = filedict[ri][li][ti]['Files']
                        name_file = filedict[ri][li][ti]['Name']
                        usermessage.egmstoolkitprint('Merging for %s...' % (name_file),log,verbose)
                        if __usevrtmerging__ == True: 
                            filemergingcsvvrt(inputdir,outputdir,name_file,file_list,paratosave,__removeduplicate__,__length_threshold__,verbose,log)
                        else: 
                            filemergingcsv(inputdir,outputdir,name_file,file_list,paratosave,__removeduplicate__,__length_threshold__,verbose,log)
                    except:
                        a = 'dummy'
            else:
                for ci in L3compall:
                    try:
                        file_list = filedict[ri][li][ci]['Files']
                        name_file = filedict[ri][li][ci]['Name']
                        usermessage.egmstoolkitprint('Merging for %s...' % (name_file),log,verbose)
                        if __usevrtmerging__ == True: 
                            filemergingcsvvrt(inputdir,outputdir,name_file,file_list,paratosave,False,False,verbose,log)
                        else:
                            filemergingcsv(inputdir,outputdir,name_file,file_list,paratosave,False,False,verbose,log) # .vrt is not available for the L3 dataset
                    except:
                        a = 'dummy'

################################################################################
## Function to merge the datasets
################################################################################
def datamergingtiff(outputdir: Optional[str] = '.'+os.sep+'Output',
    inputdir: Optional[str] = '.'+os.sep+'Output',
    paratosave: Optional[any] = 'all',
    mode: Optional[str] = 'onlist',
    infoEGMSdownloader: Optional[any] = None,
    verbose: Optional[bool] = True, 
    log: Optional[Union[str,None]] = None): 
    """Merge the datasets in tiff format (only for L3 level)
        
    Args:

        inputdir (str, Optional): Input directory [Default: './Ouput']
        outputdir (str, Optional): Input directory [Default: './Ouput']
        paratosave (str, Optional): Selected parameters [Default: 'all']
        mode (str, Optional): Mode on selection. Can be 'onlist' or 'onfiles' [Default: 'onlist']
        infoEGMSdownloader(str, Optional): Class of EGMSdownloader. Can be 'onlist' or 'onfiles' [Default: `None`]
        verbose (bool, Optional): Verbose [Default: `True`]
        log (str or None, Optional): Log file [Default: `None`]

    """ 
    
    ## Parameters
    if not mode in ['onlist', 'onfiles']: 
        raise ValueError(usermessage.errormsg(__name__,'datamergingtiff',__file__,constants.__copyright__,'The mode parameter is not correct.',log))
    if mode == 'onlist' and infoEGMSdownloader == True: 
            raise ValueError(usermessage.errormsg(__name__,'datamergingtiff',__file__,constants.__copyright__,'The output of EGMSdownloaderapi function is required with the "onlist" mode.',log))
    if not (verbose == True or verbose == False):
        raise ValueError(usermessage.errormsg(__name__,'datamergingtiff',__file__,constants.__copyright__,'bad parameter of the verbose parameter [True or False]',log))    
    if not (os.path.isdir(outputdir)):
        raise ValueError(usermessage.errormsg(__name__,'datamergingtiff',__file__,constants.__copyright__,'The output directory %s is not a directory.' % (outputdir),log))
    if not (os.path.isdir(inputdir)):
        raise ValueError(usermessage.errormsg(__name__,'datamergingtiff',__file__,constants.__copyright__,'The input directory %s is not a directory.' % (inputdir),log))

    usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Merge the datasets in tiff format (only for L3 level)',log,verbose)
    usermessage.egmstoolkitprint('\tOutput Directory: %s' % (outputdir),log,verbose)
    usermessage.egmstoolkitprint('\tInput Directory: %s' % (inputdir),log,verbose)
    usermessage.egmstoolkitprint('\tSelected parameters: %s' % (paratosave),log,verbose)
    usermessage.egmstoolkitprint('\tMode: %s' % (mode),log,verbose)

    ## Creation of the list for merging
    if mode == 'onlist': # Based on the list
        listfiles = []
        for type in ['L2a', 'L2b', 'L3UD', 'L3EW']:
            datatmp = eval('infoEGMSdownloader.list%s' % (type))
            if datatmp: 
                for idx in np.arange(len(datatmp)): 
                    release_para = egmsapitools.check_release_fromfile(datatmp[idx])
                    listfiles.append('%s%s%s%s%s%s%s' % (inputdir,os.sep,type,os.sep,release_para[0],os.sep,datatmp[idx].split('.')[0]))
    else: # Based on the files
        listfiles = glob.glob('%s%s*%s*%s*%s*.tiff' % (inputdir,os.sep,os.sep,os.sep,os.sep))
    
    if not listfiles:
        raise ValueError(usermessage.errormsg(__name__,'datamergingtiff',__file__,constants.__copyright__,'No files are detected.',log))

    filedict, release, level, track, L3compall = listtodictmerged(listfiles)
    
    for ri in release:
        for li in level:
            if li == 'L3':
                for ci in L3compall:
                    try:
                        file_list = filedict[ri][li][ci]['Files']
                        name_file = filedict[ri][li][ci]['Name']
                        usermessage.egmstoolkitprint('Merging for %s...' % (name_file),log,verbose)
                        filemergingtiff(inputdir,outputdir,name_file,file_list,verbose,log)
                    except:
                        a = 'dummy'

################################################################################
## Function to clip the data
################################################################################
def dataclipping(outputdir: Optional[str] = '.'+os.sep+'Output',
    inputdir: Optional[str] = '.'+os.sep+'Output',
    namefile: Optional[str] = 'all',
    shapefile: Optional[str] = 'bbox.shp',
    __clipuseogr2ogr__: Optional[bool] = False,
    verbose: Optional[bool] = True, 
    log: Optional[Union[str,None]] = None): 
    """Clip the datasets
        
    Args:

        inputdir (str, Optional): Input directory [Default: './Ouput']
        outputdir (str, Optional): Input directory [Default: './Ouput']
        namefile (str, Optional): Name of the selected file [Default: 'all']
        shapefile (str, Optional): Shapefile of the ROI [Default: 'bbox.sph']
        __clipuseogr2ogr__ (bool, optional): Use ogr2ogr for clipping [Default: False]
        verbose (bool, Optional): Verbose [Default: `True`]
        log (str or None, Optional): Log file [Default: `None`]

    """ 

    usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Clip the dataset(s)',log,verbose)
    usermessage.egmstoolkitprint('\tThe file name is: %s' % (namefile),log,verbose)
    usermessage.egmstoolkitprint('\tInput Directory: %s' % (inputdir),log,verbose)
    usermessage.egmstoolkitprint('\tOutput Directory: %s' % (outputdir),log,verbose)
    usermessage.egmstoolkitprint('\tShapefile: %s' % (shapefile),log,verbose)

    ## Create the list of files
    if namefile == 'all':
        list_file = glob.glob('%s%s*.csv' %(inputdir,os.sep)) + glob.glob('%s%s*.tiff' %(inputdir,os.sep)) + glob.glob('%s%s*.vrt' %(inputdir,os.sep))
    else:
        tmp = namefile.split(',')
        for namei in tmp: 
            if not os.sep in namei:
                list_file = []
                for ni in tmp:
                    list_file.append(inputdir+os.sep+ni)
            else:
                list_file.append(namei)

    if not list_file:
        raise ValueError(usermessage.errormsg(__name__,'dataclipping',__file__,constants.__copyright__,'No files are detected.',log))

    ## Cropping and clipping
    it = 1
    ittotal = 0
    for fi in list_file:
        if fi.split('.')[-1] == 'csv' and (not 'clipped' in fi):
            ittotal = ittotal+1
        elif fi.split('.')[-1] == 'tiff' and (not 'cropped' in fi):
            ittotal = ittotal+1
        elif fi.split('.')[-1] == 'vrt' and (not 'cropped' in fi):
            ittotal = ittotal+1

    for fi in list_file:
        
        if fi.split('.')[-1] == 'csv' and (not 'clipped' in fi):
            newname = outputdir+os.sep+fi[0:-4].split(os.sep)[-1]+'_clipped.csv'

            usermessage.egmstoolkitprint('\t%d / %d file(s): Clip the file %s to %s...' % (it,ittotal,fi,newname),log,verbose)

            ## Clipping using ogr2og
            if platform.system() == 'Windows' and __clipuseogr2ogr__ == True:
                raise ValueError(usermessage.errormsg(__name__,'dataclipping',__file__,constants.__copyright__,'The option __clipuseogr2ogr__ is not compatible with Windows system.',log))

            if __clipuseogr2ogr__ == True: 

                shapeinput = shapefile
                shapeoutput = shapefile.split('.')[0]+'_poly.shp'
                shapeoutput3035 = shapefile.split('.')[0]+'_poly_3035.shp'

                schema = {
                'geometry': 'Polygon',
                'properties' : {'id':'int'}
                }

                with fiona.open(shapeinput) as in_file, fiona.open(shapeoutput, 'w', 'ESRI Shapefile', schema, crs = "EPSG:4326") as out_file:
                    for index_line, row in enumerate(in_file):
                        line = shape(row['geometry'])
                        coordinates = []
                        if isinstance(line, LineString):
                            for index, point in enumerate(line.coords):
                                if index == 0:
                                    first_pt = point
                                coordinates.append(point)
                            coordinates.append(first_pt)
                            if len(coordinates) >= 3:
                                polygon = Polygon(coordinates)
                                out_file.write({
                                    'geometry': mapping(polygon),
                                    'properties': {'id': index_line},
                                })

                cmdi = "ogr2ogr -s_srs EPSG:4326 -t_srs EPSG:3035  %s %s -overwrite" % (shapeoutput3035,shapeoutput)
                os.system(cmdi)

                cmdi = "ogr2ogr -of CSV -clipsrc %s -s_srs EPSG:3035 -t_srs EPSG:3035 -oo HEADERS=YES -oo SEPARATOR=SEMICOLON -oo X_POSSIBLE_NAMES=easting -oo Y_POSSIBLE_NAMES=northing %s %s -overwrite" % (
                    shapeoutput3035,
                    newname, 
                    fi)
                usermessage.egmstoolkitprint('\t\tThe command will be: %s' % (cmdi),log,verbose)
                os.system(cmdi)

                #Delete de quote string 
                # if platform.system() == 'Windows': # for windows
                #     cmdi = 'get-content %s | %%{$_ -replace """,""}' % (newname)
                #     cmdibis = 'get-content %s | %%{$_ -replace ",",";"}' % (newname)
                if platform.system() == 'Linux': # for linux
                    cmdi = "sed -i 's/\"//g' %s" % (newname)
                    cmdibis = "sed -i 's/,/;/g' %s" % (newname)
                else: # for MacOS
                    cmdi = "sed 's/\"//g' %s > %s" % (newname,newname+'.tmp')
                    cmdibis = "sed 's/,/;/g' %s > %s" % (newname+'.tmp',newname+'.tmp2')

                os.system(cmdi)
                os.system(cmdibis)

                if os.path.isfile(newname+'.tmp2'): 
                    os.remove(newname+'.tmp')
                    os.rename(newname+'.tmp2',newname)

                if os.path.isfile(shapeoutput): 
                    os.remove(shapeoutput)
                if os.path.isfile(shapeoutput3035): 
                    os.remove(shapeoutput3035)

            else: 
                ## Clippping using the Python script
                listROI = []
                listROIepsg3035 = []

                schema = {
                    'geometry': 'Polygon',
                    'properties' : {'id':'int'}
                    }

                with fiona.open(shapefile,'r','ESRI Shapefile', schema) as shpfile:
                    for feature in shpfile:
                        coordinates = []
                        Xcoord = []
                        Ycoord = []
                        line = shape(feature['geometry'])
                        if isinstance(line, LineString):
                            for index, point in enumerate(line.coords):
                                if index == 0:
                                    first_pt = point
                                coordinates.append(point)
                                X, Y = latlon_to_meter.transform(point[1],point[0])
                                Xcoord.append(X)
                                Ycoord.append(Y)
                        if len(coordinates) >= 3:
                            listROI.append(Polygon(coordinates))
                            listROIepsg3035.append(Polygon(list(zip(Xcoord, Ycoord))))

                h = 0
                headerline = []
            
                outfile = open(newname,'w')
                outfile.close()
                with open(fi) as infile:
                    for line in infile:
                        if h == 0:
                            headerline = line
                            headerline = headerline.split(';')
                            nx = np.where('easting' == np.array(headerline))[0]  
                            ny = np.where('northing' == np.array(headerline))[0]  
                            with open(newname,'a') as outfile:
                                outfile.write(line)
                        else:
                            linelist = line.split(';')
                            pti = Point(float(linelist[ny[0]]),float(linelist[nx[0]]))

                            for ROi in listROIepsg3035:
                                if ROi.contains(pti):
                                    with open(newname,'a') as outfile:
                                        outfile.write(line)

                        h = h + 1

        elif fi.split('.')[-1] == 'vrt' and (not 'clipped' in fi):
            usermessage.egmstoolkitprint('\t%d / %d file(s): Clipping processing is not available for the .vrt files' % (it,ittotal),log,verbose)

        elif (fi.split('.')[-1] == 'tiff' or fi.split('.')[-1] == 'tif') and (not 'cropped' in fi):

            ## Create the polygon for cropping 
            name_bbox_clipping1 = '%s_forclipping1.GeoJSON' % (shapefile[0:-4])
            name_bbox_clipping2 = '%s_forclipping2.GeoJSON' % (shapefile[0:-4])
            schema = {
                'geometry': 'Polygon',
                'properties' : {'id':'int'}
                }
            cmdi = 'ogr2ogr -f "GeoJSON" -t_srs EPSG:3035 %s %s' % (name_bbox_clipping1,shapefile)
            os.system(cmdi)
            with fiona.open(name_bbox_clipping1) as in_file, fiona.open(name_bbox_clipping2, 'w', 'GeoJSON', schema) as out_file:
                for index, row in enumerate(in_file):
                    line = shape(row['geometry'])
                    hull = line.convex_hull
                    out_file.write({
                        'geometry': mapping(hull),
                        'properties': {'id': index},
                    })

            newname = outputdir+os.sep+fi[0:-5].split(os.sep)[-1]+'_cropped.tiff'

            usermessage.egmstoolkitprint('\t%d / %d file(s): Crop the file %s to %s...' % (it,ittotal,fi,newname),log,verbose)

            cmdi = 'rio mask %s %s --crop --geojson-mask %s --overwrite' %(fi,newname,name_bbox_clipping2)
            os.system(cmdi)
    
            if os.path.isfile(name_bbox_clipping1):
                os.remove(name_bbox_clipping1)
            if os.path.isfile(name_bbox_clipping2):
                os.remove(name_bbox_clipping2)

        elif 'cropped' in fi or 'clipped' in fi:
            usermessage.egmstoolkitprint('\t%d / %d file(s): The file %s is already cropped/clipped...' % (it,ittotal,fi),log,verbose)
        else:             
            usermessage.egmstoolkitprint('\t%d / %d file(s): The file %s has not been found...' % (it,ittotal,fi),log,verbose)

        it = it + 1
        
###############################################################################################################################################
###############################################################################################################################################
## SUBFUNCTIONS
###############################################################################################################################################
###############################################################################################################################################

################################################################################
## Sub-function to merge the .tiff files
################################################################################
def filemergingtiff(inputdir,outputdir,name,listfile,verbose,log):
    """Sub-function to merge the geotiff data
        
    Args:

        inputdir (str): Input directory
        outputdir (str): Input directory
        name (str): Name of the selected file
        listfile (list): List of files
        verbose (bool): Verbose
        log (str or None): Log file

    """ 

    if os.path.isfile("%s%s%s.tiff" % (outputdir,os.sep,name)):
        os.remove("%s%s%s.tiff" % (outputdir,os.sep,name))

    cmdi= ["gdal_merge.py", "-o", "%s%s%s.tiff" % (outputdir,os.sep,name), "-n -9999 -a_nodata -9999"]
    for fi in listfile:
        pathfi = glob.glob('%s%s*%s*%s*%s%s.tiff' % (inputdir,os.sep,os.sep,os.sep,os.sep,fi))[0]
        cmdi.append(pathfi)
    
    cmdi = ' '.join(cmdi)
    usermessage.egmstoolkitprint('Used command: %s' % (cmdi),log,verbose)
    if verbose:
        subprocess.call(cmdi,shell=True)  
    else:
        subprocess.call(cmdi,shell=True,stdout=open(os.devnull, 'wb'))  

################################################################################
## Sub-function to merge the .csv files by using .vrt format
################################################################################
def filemergingcsvvrt(inputdir,outputdir,name,listfile,paratosave,mode_duplicate,length_duplicate,verbose,log): 
    """Sub-function to merge the data in .csv format by using the .vrt format (only for L2a/L2b datasets and constant headers)

    Warning: there is a bug with the raw .csv files if the duplicate mode is False and all parameters are saved. 
        
    Args:

        inputdir (str): Input directory
        outputdir (str): Input directory
        name (str): Name of the selected file
        listfile (list): List of files
        paratosave (list): Lists of saved parameters
        mode_duplicate (bool): Mode to remove the duplicate points
        length_duplicate (int): Length for concave hull
        verbose (bool): Verbose
        log (str or None): Log file

    """

    ## Detect the headers
    first_one = True
    date_ts = []
    for fi in listfile:

        # Detection of the file 
        pathfi = glob.glob('%s%s*%s*%s*%s%s.csv' % (inputdir,os.sep,os.sep,os.sep,os.sep,fi))[0]
        head = pd.read_csv(pathfi, index_col=0, nrows=0).columns.tolist()

        header_para = []
        header_ts = []
        for hi in head:
            if not '20' in hi:
                header_para.append(hi)
            else:
                header_ts.append(hi)
            
        date_ts = date_ts + header_ts

    date_ts = np.unique(date_ts)  

    header_final = header_para
    for ti in date_ts : 
        header_final.append(ti)

    ## Copy the files
    first_one = True
    h = 1

    for fi in listfile:
        # Detection of the file 
        pathfi = glob.glob('%s%s*%s*%s*%s%s.csv' % (inputdir,os.sep,os.sep,os.sep,os.sep,fi))[0]

        # Read the file
        datai = pd.read_csv(pathfi,index_col=0)
        # datai = pd.read_csv(pathfi,nrows=1000,index_col=0)

        # Path computation 
        if mode_duplicate == True:
            xpts = datai['easting'].to_list()
            ypts = datai['northing'].to_list()
            pts = np.array([np.array(xpts), np.array(ypts)]).T

            usermessage.egmstoolkitprint('\t\tComputation of the convace hull to remove the duplicate points',log,verbose)
            idxes = concave_hull_indexes(
                pts,
                length_threshold=length_duplicate)      
            pts_out = list(zip(pts[idxes][:,0],pts[idxes][:,1]))
            Poly_out_iter = Polygon(pts_out)

            if first_one == True: 
                Poly_out = Poly_out_iter
            else: 
                
                xs, ys = Poly_out.exterior.xy

                path_outlines = path.Path(list(zip(xs,ys)))
                test_intersection = path_outlines.contains_points(list(zip(xpts,ypts)))
                test_intersection_inv = [not elem for elem in test_intersection]


                Poly_out = Poly_out.union(Poly_out_iter)
                
                pourctest = (1 - list(test_intersection).count(True) / len(datai))* 100
                datai = datai[test_intersection_inv]
                usermessage.warningmsg(__name__,__name__,__file__,'Regarding the burst coverage: %f %% of the points inside this burst will be kept.' %(pourctest),log,verbose)

        datamatrix = dict()
        if paratosave == 'all':
            for hi in header_final:
                datamatrix[hi] = []

        else:
            # Mandatory parameters
            mand_para = ['latitude', 'longitude', 'easting', 'northing', 'height', 'height_wgs84']
            for hi in mand_para:
                datamatrix[hi] = []
            # Selected parameters
            if isinstance(paratosave,list):
                for hi in paratosave:
                    datamatrix[hi] = []
            else:
                for hi in paratosave.split(','):
                    datamatrix[hi] = []

        # Merging 
        list_save = list(datamatrix.keys())
        for mi in list_save:
            ni = np.where(mi == np.array(head))[0]          
            if not len(ni) == 0:
                datamatrix[mi] = datai[head[ni[0]]]
            else: 
                datamatrix[mi] = datai[head[-1]]
                datamatrix[mi] = np.where(np.isnan(datamatrix[mi])==0, np.nan, datamatrix[mi])
            
        pdfdframetosave = pd.DataFrame(data=datamatrix)

        # Create the sub-directory to store the .csv file
        if not os.path.isdir('%s%s%s' % (outputdir,os.sep,name)): 
            os.mkdir('%s%s%s' % (outputdir,os.sep,name))

        # Save the file 
        pdfdframetosave.to_csv('%s%s%s%s%s_%s.csv' % (outputdir,os.sep,name,os.sep,name,h), mode='w', sep=';', index=True, header = True)

        h = h + 1
        first_one = False

        del datai, datamatrix

    # Write the .vrt file
    with open('%s%s%s.vrt' % (outputdir,os.sep,name),'w') as fvrt:
        fvrt.write('<OGRVRTDataSource>\n') 
        fvrt.write('\t<OGRVRTUnionLayer name="%s">\n' % (name))
    	
        for idx, fi in enumerate(listfile):
            nametmp1 = '%s_%s' % (name,idx+1)
            nametmp2 = '%s%s%s_%s.csv' % (name,os.sep,name,idx+1)

            fvrt.write('\t\t<OGRVRTLayer name="%s">\n' % (nametmp1))
            fvrt.write('\t\t\t<SrcDataSource relativeToVRT="1">%s</SrcDataSource>\n' % (nametmp2))
            fvrt.write('\t\t\t<GeometryType>wkbPoint</GeometryType>\n')
            fvrt.write('\t\t\t<GeometryField encoding="PointFromColumns" x="easting" y="northing"/>\n')
            fvrt.write('\t\t\t<SrcSRS>EPSG:3035</SrcSRS>\n')
            fvrt.write('\t\t</OGRVRTLayer>\n')

        fvrt.write('\t\t<LayerSRS>EPSG:3035</LayerSRS>\n')
        fvrt.write('\t</OGRVRTUnionLayer>\n')
        fvrt.write('</OGRVRTDataSource>') 

################################################################################
## Sub-function to merge the .csv files
################################################################################
def filemergingcsv(inputdir,outputdir,name,listfile,paratosave,mode_duplicate,length_duplicate,verbose,log): 
    """Sub-function to merge the data in .csv format
        
    Args:

        inputdir (str): Input directory
        outputdir (str): Input directory
        name (str): Name of the selected file
        listfile (list): List of files
        paratosave (list): Lists of saved parameters
        mode_duplicate (bool): Mode to remove the duplicate points
        length_duplicate (int): Length for concave hull
        verbose (bool): Verbose
        log (str or None): Log file

    """ 

    ## Detect the headers
    first_one = True
    date_ts = []
    for fi in listfile:

        # Detection of the file 
        pathfi = glob.glob('%s%s*%s*%s*%s%s.csv' % (inputdir,os.sep,os.sep,os.sep,os.sep,fi))[0]
        head = pd.read_csv(pathfi, index_col=0, nrows=0).columns.tolist()

        header_para = []
        header_ts = []
        for hi in head:
            if not '20' in hi:
                header_para.append(hi)
            else:
                header_ts.append(hi)
            
        date_ts = date_ts + header_ts

    date_ts = np.unique(date_ts)  

    header_final = header_para
    for ti in date_ts : 
        header_final.append(ti)

    ## Merge the files
    first_one = True
    for fi in listfile:
        # Detection of the file 
        pathfi = glob.glob('%s%s*%s*%s*%s%s.csv' % (inputdir,os.sep,os.sep,os.sep,os.sep,fi))[0]

        # Read the file
        datai = pd.read_csv(pathfi,index_col=0)
        # datai = pd.read_csv(pathfi,nrows=250000,index_col=0)
        head = pd.read_csv(pathfi, index_col=0, nrows=0).columns.tolist()

        if mode_duplicate == True and first_one == False: 
            xtest = datai['easting'].to_list()
            ytest = datai['northing'].to_list()
            test_intersection = path_outlines.contains_points(list(zip(xtest,ytest)))
            test_intersection_inv = [not elem for elem in test_intersection]

            pourctest = (1 - list(test_intersection).count(True) / len(datai))* 100
            usermessage.warningmsg(__name__,__name__,__file__,'Regarding the burst coverage: %f %% of the points inside this burst will be kept.' %(pourctest),log,verbose)

            datai = datai[test_intersection_inv]

        datamatrix = dict()
        if paratosave == 'all':
            for hi in header_final:
                datamatrix[hi] = []

        else:
            # Mandatory parameters
            mand_para = ['latitude', 'longitude', 'easting', 'northing', 'height', 'height_wgs84']
            for hi in mand_para:
                datamatrix[hi] = []
            # Selected parameters
            if isinstance(paratosave,list):
                for hi in paratosave:
                    datamatrix[hi] = []
            else:
                for hi in paratosave.split(','):
                    datamatrix[hi] = []

        # Merging 
        list_save = list(datamatrix.keys())
        for mi in list_save:
            ni = np.where(mi == np.array(head))[0]          
            if not len(ni) == 0:
                datamatrix[mi] = datai[head[ni[0]]]
            else: 
                datamatrix[mi] = datai[head[-1]]
                datamatrix[mi] = np.where(np.isnan(datamatrix[mi])==0, np.nan, datamatrix[mi])
            
        pdfdframetosave = pd.DataFrame(data=datamatrix)
        # print(pdfdframetosave)

        # Save the file 
        if first_one:
            pdfdframetosave.to_csv('%s%s%s.csv' % (outputdir,os.sep,name), mode='w', sep=';', index=True, header = True)
        else:
            pdfdframetosave.to_csv('%s%s%s.csv' % (outputdir,os.sep,name), mode='a', sep=';', index=True, header = False)

        # Generation of the outlines
        if mode_duplicate: 
            xpts = pdfdframetosave['easting'].to_list()
            ypts = pdfdframetosave['northing'].to_list()
            pts = np.array([np.array(xpts), np.array(ypts)]).T

            usermessage.egmstoolkitprint('\t\tComputation of the convace hull to remove the duplicate points',log,verbose)
            idxes = concave_hull_indexes(
                pts,
                length_threshold=length_duplicate)      
            pts_out = list(zip(pts[idxes][:,0],pts[idxes][:,1]))
            path_outlines = path.Path(pts_out)

        first_one = False

################################################################################
## Sub-function to convert the list to a merged dictionary
################################################################################
def listtodictmerged(list):
    """Sub-function to conver the list of a merged dictionary
        
    Args:

        list (list): List of files

    Returns:

        filedict (dict)
        release (str)
        level (str)
        track (str)
        L3compall (str)

    """ 

    release = []
    level = []
    track = []
    L3compall = []
    filedict = {}

    ## Extraction of the parameters
    for fi in list:
        namei = fi.split(os.sep)[-1].split('.')[0]
        ri = egmsapitools.check_release_fromfile(namei)

        if ri[1] == '':
            ri[1] = '_2015_2021'

        parai = namei.split('_')

        if '_U' in namei:
            L3comp = 'UD'
        elif '_E' in namei:
            L3comp = 'EW'
        else:
            L3comp = ''

        release.append(ri[0])
        level.append(parai[1])

        if not ri[0] in filedict:
            filedict[ri[0]] = {}
        if not parai[1] in filedict[ri[0]]:
                filedict[ri[0]][parai[1]] = {}
                   
        if not parai[1] == 'L3':
            if not parai[2] in filedict[ri[0]][parai[1]]:
                filedict[ri[0]][parai[1]][parai[2]] = {'Name': 'EGMS_%s_%s_VV%s' % (parai[1],parai[2],ri[1]),
                                                       'Files': []}
            filedict[ri[0]][parai[1]][parai[2]]['Files'].append(namei)    
            track.append(parai[2])
        else:
            if not L3comp in filedict[ri[0]][parai[1]]:
                filedict[ri[0]][parai[1]][L3comp] = {'Name': 'EGMS_%s%s_%s' % (parai[1],ri[1],L3comp),
                                                       'Files': []}
            filedict[ri[0]][parai[1]][L3comp]['Files'].append(namei)  
            L3compall.append(L3comp)

    release = np.unique(release)
    level = np.unique(level)
    track = np.unique(track)
    L3compall = np.unique(L3compall)

    return filedict, release, level, track, L3compall
