#! /usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""
Classe compoment of **EGMS toolkit**

The module contains the classe and the methods to download the tile regarding a user ROI, required by to run `EGMStoolkit`.

    (From `EGMStoolkit` package)

Changelog:
    * 0.3.0: Delete the support of wget, Alexis Hrysiewicz, Oct. 2025
    * 0.2.15: Add the possibility to unzip files in parallel, Alexis Hrysiewicz, Apr. 2025
    * 0.2.12: Add the support of the 2019_2023 release, Nov. 2024, Alexis Hrysiewicz
    * 0.2.0: Script structuring, Jan. 2024, Alexis Hrysiewicz
    * 0.1.0: Initial version, Nov. 2023

"""

import os 
import zipfile
import numpy as np
import glob
import shutil
from typing import Optional, Union
from joblib import Parallel, delayed

from EGMStoolkit.functions import egmsapitools
from EGMStoolkit import usermessage
from EGMStoolkit import constants

################################################################################
## Creation of a class to manage the Sentinel-1 burst ID map
################################################################################
class egmsdownloader:
    """`egmsdownloader` class.
        
    Attributes:

        listL2a (list): Storage of available data [Default: empty]
        listL2alink (list): Storage of available data [Default: empty]
        listL2b (list): Storage of available data [Default: empty]
        listL2blink (list): Storage of available data [Default: empty]
        listL3UD (list): Storage of available data [Default: empty]
        listL3UDlink (list): Storage of available data [Default: empty]
        listL3EW (list): Storage of available data [Default: empty]
        listL3EWlink (list): Storage of available data [Default: empty]
        token (str): User token [Default: 'XXXXXXX--XXXXXXX']            
        verbose (bool): Verbose [Default: `True`]
        log (str or None): Loggin mode [Default: `None`]

    """ 

    ################################################################################
    ## Initialistion of the class
    ################################################################################
    def __init__(self, 
        listL2a: Optional[any] = [],        
        listL2alink: Optional[any] = [],
        listL2b: Optional[any] = [],
        listL2blink: Optional[any] = [],
        listL3UD: Optional[any] = [],
        listL3UDlink: Optional[any] = [],
        listL3EW: Optional[any] = [],
        listL3EWlink: Optional[any] = [],
        token: Optional[str] = 'XXXXXXX--XXXXXXX',
        verbose: Optional[bool] = True,
        log: Optional[Union[str, None]] = None): 
        """`egmsdownloader` initialisation.
        
        Args:

            listL2a (list, Optional): Storage of available data [Default: empty]
            listL2alink (list, Optional): Storage of available data [Default: empty]
            listL2b (list, Optional): Storage of available data [Default: empty]
            listL2blink (list, Optional): Storage of available data [Default: empty]
            listL3UD (list, Optional): Storage of available data [Default: empty]
            listL3UDlink (list, Optional): Storage of available data [Default: empty]
            listL3EW (list, Optional): Storage of available data [Default: empty]
            listL3EWlink (list, Optional): Storage of available data [Default: empty]
            token (str, Optional): User token [Default: 'XXXXXXX--XXXXXXX']            
            verbose (bool, Optional): Verbose [Default: `True`]
            log (str or None, Optional): Loggin mode [Default: `None`]

        Return `egmsdownloader` class

        """ 
        
        self.listL2a = listL2a
        self.listL2alink = listL2alink
        self.listL2b = listL2b
        self.listL2blink = listL2blink
        self.listL3UD = listL3UD
        self.listL3UDlink = listL3UDlink
        self.listL3EW = listL3EW
        self.listL3EWlink = listL3EWlink
        self.token = token
       
        self.verbose = verbose
        self.log = log

        self.checkparameter(verbose=False)

    ################################################################################
    ## Check parameters
    ################################################################################
    def checkparameter(self, verbose: Optional[Union[bool,None]] = None):
        """Check the parameter
        
        Args:

            verbose (bool or None, Optional): Verbose if `None`, use the verbose mode of the job [Default: `None`]

        Return

            `egmsdownloader` class

        """ 

        if verbose == None:
            verbose = self.verbose
        if not isinstance(verbose,bool):
            raise ValueError(usermessage.errormsg(__name__,'checkparameter',__file__,constants.__copyright__,'Verbose must be True or False',self.log))
        
        usermessage.openingmsg(__name__,'checkparameter',__file__,constants.__copyright__,'Check the parameter',self.log,verbose)

        if (self.token == 'XXXXXXX--XXXXXXX'):
            usermessage.warningmsg(__name__,'checkparameter',__file__,'The user token is not correct.',self.log,True)

    ################################################################################
    ## Function to print the attributes
    ################################################################################
    def print(self):
        """Print the class attributes

        Return 

            `egmsdownloader` class

        """ 

        attrs = vars(self)
        print(', '.join("%s: %s" % item for item in attrs.items()))

        return self

    ################################################################################
    ## Function to update ethe list of files
    ################################################################################
    def updatelist(self,infoS1ROIparameter, verbose: Optional[Union[bool,None]] = None):
        """Update the list of of EGMS files
        
        Args:

            infoS1ROIparameter: `S1ROIparameter` class
            verbose (bool or None, Optional): Verbose if `None`, use the verbose mode of the job [Default: `None`]

        Return

            `egmsdownloader` class

        """ 

        if verbose == None:
            verbose = self.verbose
        if not isinstance(verbose,bool):
            raise ValueError(usermessage.errormsg(__name__,'updatelist',__file__,constants.__copyright__,'Verbose must be True or False',self.log))
        
        self.checkparameter(verbose = False)

        usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Update the list of of EGMS files',self.log,verbose)

        release_para = egmsapitools.check_release(infoS1ROIparameter.release)

        if infoS1ROIparameter.egmsL3component == 'UD': 
            ext_3D = 'U'
        elif infoS1ROIparameter.egmsL3component == 'EW': 
            ext_3D = 'E'
        
        if infoS1ROIparameter.Data: 
            if infoS1ROIparameter.egmslevel == 'L2a' or infoS1ROIparameter.egmslevel == 'L2b': 
                for tracki in infoS1ROIparameter.Data:
                    for idx in ['1','2','3']: 
                        for iwi in infoS1ROIparameter.Data[tracki]['IW%s' %(idx)]:
                            name_zip = 'EGMS_%s_%03d_%04d_IW%s_VV%s.zip' % (infoS1ROIparameter.egmslevel,iwi['relative_orbit_number'],iwi['egms_burst_id'],idx,release_para[1])
                            link_zip = 'https://egms.land.copernicus.eu/insar-api/archive/download/%s' % (name_zip)
                            if infoS1ROIparameter.egmslevel == 'L2a':
                                self.listL2a.append(name_zip)
                                self.listL2alink.append(link_zip)
                            elif infoS1ROIparameter.egmslevel == 'L2b':
                                self.listL2b.append(name_zip)
                                self.listL2blink.append(link_zip)

        if infoS1ROIparameter.DataL3:
            if infoS1ROIparameter.egmslevel == 'L3':
                for tilei in infoS1ROIparameter.DataL3['polyL3']:
                
                    x = tilei.exterior.coords.xy[0].tolist()[0]/100000
                    y = tilei.exterior.coords.xy[1].tolist()[0]/100000

                    name_zip = 'EGMS_L3_E%2dN%2d_100km_%s%s.zip' % (y,x,ext_3D,release_para[1])
                    link_zip = 'https://egms.land.copernicus.eu/insar-api/archive/download/%s' % (name_zip)

                    if infoS1ROIparameter.egmsL3component == 'UD':
                        self.listL3UD.append(name_zip)
                        self.listL3UDlink.append(link_zip)
                    elif infoS1ROIparameter.egmsL3component == 'EW':
                        self.listL3EW.append(name_zip)
                        self.listL3EWlink.append(link_zip)

        self.listL2a = np.unique(self.listL2a).tolist()
        self.listL2alink = np.unique(self.listL2alink).tolist()
        self.listL2b = np.unique(self.listL2b).tolist()
        self.listL2blink = np.unique(self.listL2blink).tolist()
        self.listL3UD = np.unique(self.listL3UD).tolist()
        self.listL3UDlink = np.unique(self.listL3UDlink).tolist()
        self.listL3EW = np.unique(self.listL3EW).tolist()
        self.listL3EWlink = np.unique(self.listL3EWlink).tolist()


        self.printlist(verbose=verbose)

        return self

    ################################################################################
    ## Function to print the list(s) of files
    ################################################################################
    def printlist(self, 
        verbose: Optional[Union[bool,None]] = None):
        """Print the list(s) of EGMS files
        
        Args:

            verbose (bool or None, Optional): Verbose if `None`, use the verbose mode of the job [Default: `None`]

        Return

            `egmsdownloader` class

        """ 

        if verbose == None:
            verbose = self.verbose
        if not isinstance(verbose,bool):
            raise ValueError(usermessage.errormsg(__name__,'updatelist',__file__,constants.__copyright__,'Verbose must be True or False',self.log))
        
        self.checkparameter(verbose = False)

        usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Print the list(s) of EGMS files',self.log,verbose)

        for type in ['L2a', 'L2b', 'L3UD', 'L3EW']:
            datatmp = eval('self.list%s' % (type))
            datatmplink = eval('self.list%slink' % (type))
        
            if datatmp: 
                usermessage.egmstoolkitprint('For the EGMS data: %s' % (type),self.log,verbose)
                for idx in np.arange(len(datatmp)): 
                    release_para = egmsapitools.check_release_fromfile(datatmp[idx])
                    usermessage.egmstoolkitprint('\t File %d: %s (Release %s)' % (idx+1,datatmp[idx],release_para[0]),self.log,verbose)

        return self

    ################################################################################
    ## Function to download the files
    ################################################################################
    def download(self,
        outputdir: Optional[str] = '.%sOutput' % (os.sep),    
        unzipmode: Optional[bool] = False,
        cleanmode: Optional[bool] = False,
        force: Optional[bool] = True,
        verbose: Optional[Union[bool,None]] = None):
        """Download the EGMS files
        
        Args:

            outputdir (str, Optional): Path of the output directory [Default: './Output']
            unzipmode (bool, Optional): Unzip the file [Default: `False`]
            cleanmode (bool, Optional): Delete the file after unzipping [Default: `False`]
            force (bool, Optional): Replace the stored file [Default: `True`]
            verbose (bool or None, Optional): Verbose if `None`, use the verbose mode of the job [Default: `None`]

        Return

            `egmsdownloader` class

        """ 

        if verbose == None:
            verbose = self.verbose
        if not isinstance(verbose,bool):
            raise ValueError(usermessage.errormsg(__name__,'download',__file__,constants.__copyright__,'Verbose must be True or False',self.log))
        
        self.checkparameter(verbose = False)

        usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Download the EGMS files',self.log,verbose)

        if not os.path.isdir(outputdir): 
            os.mkdir(outputdir)

        total_len = len(self.listL2a) + len(self.listL2b) + len(self.listL3UD) + len(self.listL3EW)

        h = 1
        for type in ['L2a', 'L2b', 'L3UD', 'L3EW']:
            datatmp = eval('self.list%s' % (type))
            datatmplink = eval('self.list%slink' % (type))
        
            if datatmp: 
                if not os.path.isdir('%s%s%s' % (outputdir,os.sep,type)):
                    os.mkdir('%s%s%s' % (outputdir,os.sep,type))

                for idx in np.arange(len(datatmp)): 
                    usermessage.egmstoolkitprint('%d / %d files: Download the file: %s' % (h,total_len,datatmp[idx]),self.log,verbose)

                    release_para = egmsapitools.check_release_fromfile(datatmp[idx])

                    if not os.path.isdir('%s%s%s%s%s' % (outputdir,os.sep,type,os.sep,release_para[0])):
                        os.mkdir('%s%s%s%s%s' % (outputdir,os.sep,type,os.sep,release_para[0]))
                    pathdir = '%s%s%s%s%s' % (outputdir,os.sep,type,os.sep,release_para[0])

                    if not os.path.isfile('%s%s%s' % (pathdir,os.sep,datatmp[idx])): 
                        if (not ('%s%s%s%s%s%s' % (pathdir,os.sep,datatmp[idx].split('.')[0],os.sep,datatmp[idx].split('.')[0],'.csv'))) or force == True:

                            egmsapitools.download_file('%s?id=%s' % (datatmplink[idx],self.token),
                                    output_file = pathdir + os.sep + datatmplink[idx].split('/')[-1],
                                    verbose=verbose, 
                                    log = self.log)

                        else:
                            usermessage.egmstoolkitprint('\tAlready downloaded (detection of the .csv file)',self.log,verbose)        
                    else:                      
                        usermessage.egmstoolkitprint('\tAlready downloaded (detection of the .zip file)',self.log,verbose)  

                    h = h + 1

                    self.unzipfile(outputdir=outputdir,unzipmode=unzipmode,cleanmode=cleanmode,verbose=verbose)

        return self

    ################################################################################
    ## Function to unzip the files
    ################################################################################
    def unzipfile(self,
        outputdir: Optional[str] = '.%sOutput' % (os.sep),     
        unzipmode: Optional[bool] = True,
        nbworker: Optional[int] = 1,
        cleanmode: Optional[bool] = False,        
        verbose: Optional[Union[bool,None]] = None):
        """Unzip the EGMS files
        
        Args:

            outputdir (str, Optional): Path of the output directory [Default: './Output']
            unzipmode (bool, Optional): Unzip the file [Default: `True`]
            nbworker (int, Optional): Number of workers for unzipping [Default: 1]
            cleanmode (bool, Optional): Delete the file after unzipping [Default: `False`]
            verbose (bool or None, Optional): Verbose if `None`, use the verbose mode of the job [Default: `None`]

        Return

            `egmsdownloader` class

        """ 

        if verbose == None:
            verbose = self.verbose
        if not isinstance(verbose,bool):
            raise ValueError(usermessage.errormsg(__name__,'unzipfile',__file__,constants.__copyright__,'Verbose must be True or False',self.log))
        
        if not isinstance(nbworker,int):
            raise ValueError(usermessage.errormsg(__name__,'nbworker',__file__,constants.__copyright__,'nbworker must be an int.',self.log))
        else: 
            if nbworker < 1: 
                raise ValueError(usermessage.errormsg(__name__,'nbworker',__file__,constants.__copyright__,'nbworker must be >= 1.',self.log))

        self.checkparameter(verbose = False)

        usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Unzip the EGMS files',self.log,verbose)

        list_files = glob.glob('%s%s*%s*%s*.zip' % (outputdir,os.sep,os.sep,os.sep))

        ####################
        def unziponefile(fi,cleanmode,h): 
            pathsplit = fi.split(os.sep)
            namefile = fi.split(os.sep)[-1].split('.')[0]
            pathdirfile = ''
            for i1 in np.arange(len(pathsplit)-1):
                if i1 == 0:
                    pathdirfile = pathsplit[i1] 
                else:
                    pathdirfile = pathdirfile + os.sep + pathsplit[i1]     

            if not h == None:           
                usermessage.egmstoolkitprint('%d / %d files: Unzip the file: %s' % (h,len(list_files),pathsplit[-1]),self.log,verbose)
            else: 
                usermessage.egmstoolkitprint('Unzip the file: %s' % (pathsplit[-1]),self.log,verbose)

            with zipfile.ZipFile("%s" %(fi), 'r') as zip_ref:
                zip_ref.extractall('%s%s%s' % (pathdirfile,os.sep,namefile))

            if os.path.isdir('%s%s%s' % (pathdirfile,os.sep,namefile)) and (cleanmode): 
                os.remove(fi)
        ####################

        if unzipmode:
            if nbworker == 1: 
                h = 1
                for fi in list_files: 
                    unziponefile(fi,cleanmode,h)
                    h =+ 1
            else: 
                usermessage.egmstoolkitprint('Unzipping with %s workers' % (nbworker),self.log,verbose)  
                Parallel(n_jobs=nbworker)(delayed(unziponefile)(fi,cleanmode,None) for fi in list_files)
        else: 
                usermessage.egmstoolkitprint('\tNo processing.',self.log,verbose)  

        return self

    ################################################################################
    ## Function to clean the unused files
    ################################################################################
    def clean(self,
        outputdir: Optional[str] = '.%sOutput' % (os.sep),     
        verbose: Optional[Union[bool,None]] = None):
        """Clean the unused files (based on the list(s))
        
        Args:

            outputdir (str, Optional): Path of the output directory [Default: './Output']
            verbose (bool or None, Optional): Verbose if `None`, use the verbose mode of the job [Default: `None`]

        Return

            `egmsdownloader` class

        """ 

        if verbose == None:
            verbose = self.verbose
        if not isinstance(verbose,bool):
            raise ValueError(usermessage.errormsg(__name__,'clean',__file__,constants.__copyright__,'Verbose must be True or False',self.log))
        
        self.checkparameter(verbose = False)

        usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Clean the unused files (based on the list(s))',self.log,verbose)

        if not os.path.isdir(outputdir): 
            raise ValueError(usermessage.errormsg(__name__,'clean',__file__,constants.__copyright__,'Impossible to find the output directory',self.log))

        listdirall = []
        listfileall = []
        for type in ['L2a', 'L2b', 'L3UD', 'L3EW']:
            datatmp = eval('self.list%s' % (type))
            if datatmp: 
                for idx in np.arange(len(datatmp)): 
                    release_para = egmsapitools.check_release_fromfile(datatmp[idx])
                    listdirall.append('%s%s%s%s%s%s%s' % (outputdir,os.sep,type,os.sep,release_para[0],os.sep,datatmp[idx].split('.')[0]))
                    listfileall.append('%s%s%s%s%s%s%s' % (outputdir,os.sep,type,os.sep,release_para[0],os.sep,datatmp[idx]))

        liststored = glob.glob('%s%s*%s*%s*' % (outputdir,os.sep,os.sep,os.sep))
        liststoredDIR = []
        liststoredFILE = []
        for li in liststored: 
            if os.path.isfile(li):
                liststoredFILE.append(li)
            else: 
                liststoredDIR.append(li)

        for li in liststoredDIR: 
            if not li in listdirall:
                usermessage.egmstoolkitprint('The directory %s is not in the list(s), it will be removed...' % (li),self.log,verbose)  
                shutil.rmtree(li)
            else:
                usermessage.egmstoolkitprint('The directory %s is in the list(s), it will be kept...' % (li),self.log,verbose)  

        for li in liststoredFILE: 
            if not li in listfileall: 
                usermessage.egmstoolkitprint('The .zip file %s is not in the list(s), it will be removed...' % (li),self.log,verbose)  
                os.remove(li)
            else:
                usermessage.egmstoolkitprint('The .zip file %s is in the list(s), it will be kept...' % (li),self.log,verbose)  

        #  Clean the empty directories 
        for i1 in ['L2a', 'L2b', 'L3UD', 'L3EW']:
            for i2 in ['2015_2021', '2018_2022', '2019_2023']:
                if os.path.isdir('%s%s%s%s%s' % (outputdir,os.sep,i1,os.sep,i2)):
                    if len(os.listdir('%s%s%s%s%s' % (outputdir,os.sep,i1,os.sep,i2))) == 0: 
                        shutil.rmtree('%s%s%s%s%s' % (outputdir,os.sep,i1,os.sep,i2))

            if os.path.isdir('%s%s%s' % (outputdir,os.sep,i1)):
                if len(os.listdir('%s%s%s' % (outputdir,os.sep,i1))) == 0: 
                    shutil.rmtree('%s%s%s' % (outputdir,os.sep,i1))
        
        return self
