#! /usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""
Classe compoment of **EGMS toolkit**

The module contains the classe and the methods to manage the Sentinel-1 Burst-ID maps required by to run `EGMStoolkit`.

    (From `EGMStoolkit` package)

Changelog:
    * 0.2.0: Script structuring, Jan. 2024, Alexis Hrysiewicz
    * 0.1.0: Initial version, Nov. 2023

"""

import datetime 
import os 
import wget
import zipfile
import urllib.request  
from typing import Optional, Union

from EGMStoolkit import usermessage
from EGMStoolkit import constants

################################################################################
## Creation of a class to manage the Sentinel-1 burst ID map
################################################################################
class S1burstIDmap:
    """`S1burstIDmap` class.
        
    Attributes:

        date_str_init (str): First date to search the S1-Burst-ID map [Default: '29/05/2022']
        dirmap (str): Directory of the S1-Burst-ID map 
        pathIDmap (str or None): Full path of the S1-Burst-ID map [Default: `None`]
        list_date (list): List of the date to search the S1-Burst-ID map [Default: empty]
        verbose (bool): Verbose [Default: `True`]
        log (str or None): Loggin mode [Default: `None`]

     """ 

    ################################################################################
    ## Initialistion of the class
    ################################################################################
    def __init__(self, 
                date_str_init: Optional[str] = '29/05/2022',
                dirmap: Optional[str] = constants.__pathS1map__,
                pathIDmap: Optional[Union[str, None]] = None,
                list_date: Optional[list] = [],
                verbose: Optional[bool] = True,
                log: Optional[Union[str, None]] = None): 
        
        """`S1burstIDmap` initialisation.
        
        Args:

            date_str_init (str, Optional): First date to search the S1-Burst-ID map [Default: '29/05/2022']
            dirmap (str, Optional): Directory of the S1-Burst-ID map 
            pathIDmap (str or None, Optional): Full path of the S1-Burst-ID map [Default: `None`]
            list_date (list, Optional): List of the date to search the S1-Burst-ID map [Default: empty]
            verbose (bool, Optional): Verbose [Default: `True`]
            log (str or None, Optional): Loggin mode [Default: `None`]

        Return

            `S1burstIDmap` class

        """ 
        
        usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Initialisation of the S1burstIDmap class',log,verbose)

        self.date_str_init = date_str_init
        self.dirmap = dirmap
        self.pathIDmap = pathIDmap
        self.list_date = list_date
        self.verbose = verbose
        self.log = log
        
        usermessage.egmstoolkitprint('\tdone.',self.log,self.verbose)

        self.checkfile()

    ################################################################################
    ## Function to print the attributes
    ################################################################################
    def print(self):
        """Print the class attributes

        Return 

            `S1burstIDmap` class

        """ 

        attrs = vars(self)
        print(', '.join("%s: %s" % item for item in attrs.items()))

    ################################################################################
    ## Check the avaibility of the maps
    ################################################################################
    def checkfile(self, verbose: Optional[Union[bool,None]] = None):
        """Check the available map(s) stored.
        
        Args:

            verbose (bool or None, Optional): Verbose if `None`, use the verbose mode of the job [Default: `None`]

        Return

            `S1burstIDmap` class

        """ 

        if verbose == None:
            verbose = self.verbose
        if not isinstance(verbose,bool):
            raise ValueError(usermessage.errormsg(__name__,'checkfile',__file__,constants.__copyright__,'Verbose must be True or False',self.log))
        
        usermessage.openingmsg(__name__,'checkfile',__file__,constants.__copyright__,'Check the available S1-Burst-ID map',self.log,verbose)

        ## Create the list of dates
        self.list_date = []; 
        datei = datetime.datetime.strptime(self.date_str_init, '%d/%m/%Y')

        while datei <=  datetime.datetime.now(): 
            datei = datei + datetime.timedelta(days=1)
            self.list_date.append(datei.strftime("%Y%m%d"))

        ## Check if the directory exists
        for i1 in self.list_date:
            if os.path.isdir("%s%sS1_burstid_%s" %(self.dirmap,os.sep,i1)):
                self.pathIDmap = "%s%sS1_burstid_%s" %(self.dirmap,os.sep,i1)

                usermessage.egmstoolkitprint('Detection of the directory: %s' % (self.pathIDmap),self.log,verbose)

        if self.pathIDmap == None:
            usermessage.warningmsg(__name__,'checkfile',__file__,'No detection of the directory...\nTry to download the .zip file.',self.log,True)
            self.downloadfile()

        return self

    ################################################################################
    ## Donwload the latest map
    ################################################################################
    def downloadfile(self, verbose: Optional[Union[bool,None]] = None): 
        """Download the available map(s) stored.
        
        Args:

            verbose (bool or None, Optional): Verbose if `None`, use the verbose mode of the job [Default: `None`]

        Return

            `S1burstIDmap` class

        """ 

        if verbose == None:
            verbose = self.verbose
        if not isinstance(verbose,bool):
            raise ValueError(usermessage.errormsg(__name__,'downloadfile',__file__,constants.__copyright__,'Verbose must be True or False',self.log))
        
        usermessage.openingmsg(__name__,'downloadfile',__file__,constants.__copyright__,'Donwload the latest S1-burst-ID map',self.log,verbose)

        h = 0
        while self.pathIDmap == None:
            i1 = self.list_date[h]
            try:
                status = urllib.request.urlopen("https://sar-mpc.eu/files/S1_burstid_%s.zip" %(i1)).getcode()
                self.pathIDmap = "https://sar-mpc.eu/files/S1_burstid_%s.zip" %(i1)
                usermessage.egmstoolkitprint("Check the https://sar-mpc.eu/files/S1_burstid_%s.zip link ==> DETECTED" %(i1),self.log,verbose)
            except:
                usermessage.egmstoolkitprint("Check the https://sar-mpc.eu/files/S1_burstid_%s.zip link ==> NO DETECTED" %(i1),self.log,verbose)

            h = h + 1
            if h == len(self.list_date):
                raise ValueError(usermessage.errormsg(__name__,'downloadfile',__file__,constants.__copyright__,'No detection of S1 burst ID map...',self.log))

            try:
                filename = wget.download(self.pathIDmap, out=self.dirmap)
                usermessage.egmstoolkitprint(f"File downloaded: {filename}",self.log,verbose)

            except Exception as e:
                raise ValueError(usermessage.errormsg(__name__,'downloadfile',__file__,constants.__copyright__,f"An error occurred: {e}",self.log))

            usermessage.egmstoolkitprint("\tUnzip the .zip file %s in %s" %(self.dirmap,i1),self.log,verbose)

            with zipfile.ZipFile("%s/S1_burstid_%s.zip" %(self.dirmap,i1), 'r') as zip_ref:
                zip_ref.extractall(self.dirmap)
                
            usermessage.egmstoolkitprint("\tDelete the .zip file %s in %s" %(self.dirmap,i1),self.log,verbose)
            os.remove("%s/S1_burstid_%s.zip" %(self.dirmap,i1))

        self.checkfile()

        return self





