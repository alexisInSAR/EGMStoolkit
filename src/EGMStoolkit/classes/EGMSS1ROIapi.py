#! /usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""
Classe compoment of **EGMS toolkit**

The module contains the classe and the methods to detect the tile regarding a user ROI, required by to run `EGMStoolkit`.

    (From `EGMStoolkit` package)

Changelog:
    * 0.2.1: Fix regarding the EGMS-ID bursts, Feb. 2024, Alexis Hrysiewicz
    * 0.2.0: Script structuring, Jan. 2024, Alexis Hrysiewicz
    * 0.1.0: Initial version, Nov. 2023

"""

import os 
from shapely.geometry import Polygon, mapping, shape, LineString
from osgeo import gdal
import fiona
import numpy as np
from shapely.wkt import loads
import glob
from alive_progress import alive_bar
import pickle
import pyproj
import plotly.graph_objects as go
from typing import Optional, Union

from EGMStoolkit.functions import esa2egmsburstID
from EGMStoolkit import usermessage
from EGMStoolkit import constants

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
## Creation of a class to manage the Sentinel-1 burst ID map
################################################################################
class S1ROIparameter:
    """`S1ROIparameter` class.
        
    Attributes:

        bbox (str or None): Bbox [Default: `None`]
        ROIs (any): ROI polygon 
        egmslevel (str): EGMS level of LOS-displacement data [Default: 'L2a']
        egmsL3component (str): EGMS level of 3D-displacement data [Default: 'UD']
        release (str): EGMS release code [Default: '2018_2022']
        Data (dict): Storage of available data [Default: empty]
        DataL3 (dict): Storage of available data [Default: empty]
        workdirectory (str): Full path of the work directory [Default: './']
        verbose (bool): Verbose [Default: `True`]
        log (str or None): Loggin mode [Default: `None`]

    """ 

    ################################################################################
    ## Initialistion of the class
    ################################################################################
    def __init__(self,
        bbox: Optional[Union[str,None]] = None,
        egmslevel: Optional[str] = 'L2a',
        egmsL3component: Optional[str] = 'UD',
        release: Optional[str] = '2018_2022',
        workdirectory: Optional[str] = '.'+os.sep,
        verbose: Optional[bool] = True,
        log: Optional[Union[str, None]] = None): 
        """`S1ROIparameter` initialisation.
        
        Args:

            bbox (str or None, Optional): Bbox [Default: `None`]
            egmslevel (str, Optional): EGMS level of LOS-displacement data [Default: 'L2a']
            egmsL3component (str, Optional): EGMS level of 3D-displacement data [Default: 'UD']
            release (str, Optional): EGMS release code [Default: '2018_2022']
            workdirectory (str, Optional): Full path of the work directory [Default: './']
            verbose (bool, Optional): Verbose [Default: `True`]
            log (str or None, Optional): Loggin mode [Default: `None`]

        Return

            `S1ROIparameter` class

        """ 

        usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Initialisation of the S1ROIparameter class',log,verbose)

        self.bbox = bbox
        self.ROIs = []
        self.egmslevel = egmslevel
        self.egmsL3component = egmsL3component
        self.release = release
        self.Data = dict()
        self.DataL3 = dict()
        self.workdirectory = workdirectory
        self.verbose = verbose 
        self.log = log

        usermessage.egmstoolkitprint('\tdone.',self.log,self.verbose)

        self.checkparameter(verbose=False)

    ################################################################################
    ## Function to print the attributes
    ################################################################################
    def print(self):
        """Print the class attributes

        Return 

            `S1ROIparameter` class

        """ 

        self.checkparameter(verbose=False)

        attrs = vars(self)
        print(', '.join("%s: %s" % item for item in attrs.items()))

    ################################################################################
    ## Check parameters
    ################################################################################
    def checkparameter(self, verbose: Optional[Union[bool,None]] = None):
        """Check the paramaters
        
        Args:

            verbose (bool or None, Optional): Verbose if `None`, use the verbose mode of the job [Default: `None`]

        Return

            `S1ROIparameter` class

        """ 

        if verbose == None:
            verbose = self.verbose
        if not isinstance(verbose,bool):
            raise ValueError(usermessage.errormsg(__name__,'checkparameter',__file__,constants.__copyright__,'Verbose must be True or False',self.log))
        
        usermessage.openingmsg(__name__,'checkparameter',__file__,constants.__copyright__,'Check the paramaters',self.log,verbose)

        if not (self.egmslevel == 'L2a' or self.egmslevel == 'L2b' or self.egmslevel == 'L3'):
            raise ValueError(usermessage.errormsg(__name__,'checkparameter',__file__,constants.__copyright__,'The level parameter is not correct',self.log))
        
        if not (self.egmsL3component == 'UD' or self.egmsL3component == 'EW'):
            raise ValueError(usermessage.errormsg(__name__,'checkparameter',__file__,constants.__copyright__,'The 3D-component parameter is not correct',self.log))
        
        if not (self.release == '2015_2021' or self.release == '2018_2022'):
            raise ValueError(usermessage.errormsg(__name__,'checkparameter',__file__,constants.__copyright__,'The release parameter is not correct',self.log))

        return self
    
    ################################################################################
    ## Function to create the ROI file
    ################################################################################
    def createROI(self, verbose: Optional[Union[bool,None]] = None):
        """Create the ROI file
        
        Args:

            verbose (bool or None, Optional): Verbose if `None`, use the verbose mode of the job [Default: `None`]

        Return

            `S1ROIparameter` class

        """ 
        if verbose == None:
            verbose = self.verbose
        if not isinstance(verbose,bool):
            raise ValueError(usermessage.errormsg(__name__,'createROI',__file__,constants.__copyright__,'Verbose must be True or False',self.log))
        
        self.checkparameter(verbose = False)

        usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Create the ROI files',self.log,verbose)

        if self.bbox == None:
            raise ValueError(usermessage.errormsg(__name__,'createROI',__file__,constants.__copyright__,'The bbox parameter is empty',self.log))

        for fi in ['bbox.cpg','bbox.cpg','bbox.dbf','bbox.prj','bbox.shp','bbox.shx']:
            if os.path.isfile(self.workdirectory+os.sep+fi): 
                os.remove(self.workdirectory+os.sep+fi)
         
        ## Create the polygons of the ROIs
        if isinstance(self.bbox, list):
            usermessage.egmstoolkitprint('Use the bbox given by the user',self.log,verbose)

            schema = {'geometry': 'MultiLineString','properties': {'FID': 'int'}}
            
            multi = loads("MULTILINESTRING ((%f %f, %f %f, %f %f, %f %f, %f %f))" % (
                self.bbox[0], self.bbox[1],
                self.bbox[2],self.bbox[1],
                self.bbox[2],self.bbox[3],
                self.bbox[0], self.bbox[3],
                self.bbox[0], self.bbox[1]))

            with fiona.open(self.workdirectory+os.sep+'bbox.shp', mode='w', driver='ESRI Shapefile',schema = schema, crs = "EPSG:4326")  as output:
                output.write({'geometry':mapping(multi),'properties': {'FID':1}})

        elif os.path.isfile(self.bbox):
            usermessage.egmstoolkitprint('Use the vector file giving by the user: %s' % (self.bbox),self.log,verbose)
            gdal.VectorTranslate(self.workdirectory+os.sep+'bbox.shp',self.bbox,options='-f "ESRI Shapefile" -t_srs "EPSG:4326"')
        
        elif isinstance(self.bbox, str): # ERROR
            usermessage.egmstoolkitprint('Use the country name given by the user',self.log,verbose)

            cmdi = 'gmt coast -JU6i -E%s -M > bbox.GMT' % (self.bbox)
            os.system(cmdi)
            gdal.VectorTranslate(self.workdirectory+os.sep+'bbox.shp','bbox.GMT',options='-f "ESRI Shapefile" -s_srs "EPSG:4326" -t_srs "EPSG:4326" -overwrite')

            os.remove('bbox.GMT')
            os.remove('gmt.history')

        else: 
            raise ValueError(usermessage.errormsg(__name__,'createROI',__file__,constants.__copyright__,'The format is not recognised.',self.log))
        
        self.ROIs = self.workdirectory+os.sep+'bbox.shp'

        return self

    ################################################################################
    ## Function to detect the data regarding the burst IDs
    ################################################################################
    def detectfromIDmap(self,infoburstID, 
        Track_user: Optional[str] = 'None',             
        Pass_user: Optional[str] = 'None', 
        verbose: Optional[Union[bool,None]] = None):
        """Detect the tiles from the user parameters
        
        Args:
            infoburstID: `S1burstIDmap` class
            Track_user (str or list or None, Optional): Satellite track number [Default: 'None']
            Pass_user (str or list or None, Optional): Satellite pass [Default: 'None']
            verbose (bool or None, Optional): Verbose if `None`, use the verbose mode of the job [Default: `None`]

        Return

            `S1ROIparameter` class

        """ 
     
        if verbose == None:
            verbose = self.verbose
        if not isinstance(verbose,bool):
            raise ValueError(usermessage.errormsg(__name__,'detectfromIDmap',__file__,constants.__copyright__,'Verbose must be True or False',self.log))
        
        self.checkparameter(verbose = False)

        usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Detect the data regarding the burst IDs',self.log,verbose)

        if not (isinstance(Track_user, list)):
            Track_user = [Track_user]
        if not isinstance(Pass_user, list):
            Pass_user = [Pass_user]

        for pii in Pass_user:
            if not (pii.upper() == 'ASCENDING' or pii.upper() == 'DESCENDING' or pii == 'None'): 
                raise ValueError(usermessage.errormsg(__name__,'createROI',__file__,constants.__copyright__,'Pass should be Ascending or Descending.',self.log))
            
        if (isinstance(Track_user, list) and isinstance(Pass_user, list) and len(Track_user) !=1 and len(Pass_user) !=1): 
            if not len(Track_user) == len(Pass_user):
                raise ValueError(usermessage.errormsg(__name__,'detectfromIDmap',__file__,constants.__copyright__,'The track and pass parameters do not have the same length.',self.log))
            
        usermessage.warningmsg(__name__,'checkfile',__file__,'The use of the S1 burst ID map is less accurate than the use of .xml S1 files.',self.log,True)
        
        ## Read the shapefile
        listROI = []
        listROIepsg3035 = []
        with fiona.open(self.ROIs) as shpfile:
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

        if self.egmslevel == 'L2a' or self.egmslevel == 'L2b':
            usermessage.egmstoolkitprint('For the L2a and L2b levels',self.log,verbose)

            ## Read the kml files to detect the burst ID
            filesqlite = glob.glob('%s%sIW%ssqlite%s*.sqlite3' % (infoburstID.pathIDmap,os.sep,os.sep,os.sep))[-1]
            
            fiona.supported_drivers["SQLite"] = "r"
            h = 1
            with fiona.open(filesqlite) as shpfile:
                with alive_bar(len(shpfile)) as bar: 
                    for feature in shpfile:
                        coordinates = []
                        polyburst = Polygon(feature['geometry']["coordinates"][0][0])

                        test_intersection = False
                        for ROi in listROI:
                            test_intersection = ROi.intersects(polyburst)
                            if test_intersection:
                                
                                relative_orbit_number = feature['properties']['relative_orbit_number']
                                subswath_name = feature['properties']['subswath_name']
                                orbit_pass = feature['properties']['orbit_pass']
                                esa_burst_id = feature['properties']['burst_id']
                                
                                anx_time = feature['properties']['time_from_anx_sec']
                                az_size = 750 # Changed value from 1500 (version 0.2.1)
                                dt_az = 0.0020555563
                                anx_mid = anx_time + az_size/2*dt_az
                                
                                egms_burst_id = esa2egmsburstID.get_egms_burst_cycle_id(relative_orbit_number, anx_mid)[-1]
                                
                                if (isinstance(Track_user,list) and isinstance(Pass_user,list) and len(Pass_user)==1):
                                    Pass_usertmp = np.tile(Pass_user[0], [len(Track_user),1])
                                    Pass_user = []
                                    for i1 in Pass_usertmp:
                                        Pass_user.append(i1[0])

                                for (tracki, passi) in zip(Track_user, Pass_user):
                                    
                                    if (tracki == relative_orbit_number or str(tracki) == 'None') and (passi.upper() == orbit_pass or passi == 'None'):
                                        if not "%s_%04d" % (orbit_pass,relative_orbit_number) in self.Data:
                                            self.Data["%s_%04d" % (orbit_pass,relative_orbit_number)] = {'IW1': [], 
                                                                                                            'IW2': [],
                                                                                                            'IW3': []}
                                            
                                        self.Data["%s_%04d" % (orbit_pass,relative_orbit_number)][subswath_name].append({'relative_orbit_number': relative_orbit_number, 
                                                                                                                    'subswath_name': subswath_name, 
                                                                                                                    'orbit_pass': orbit_pass, 
                                                                                                                    'esa_burst_id': esa_burst_id, 
                                                                                                                    'egms_burst_id': egms_burst_id,  
                                                                                                                    'polyburst': polyburst})
                        bar()
        elif self.egmslevel == 'L3':
            usermessage.egmstoolkitprint('For the L3 level: the input argument will be ignored.',self.log,verbose)

            self.DataL3['Tileinfo'] = []
            self.DataL3['polyL3'] = []
            self.DataL3['polyL3ll'] = []

            ## Bound of the EPSG:3035
            # xlimGRID = [1896628.62, 7104179.2]
            # ylimGRID = [1095703.18, 6882401.15]

            xlimGRID = [900000, 7400000]
            ylimGRID = [900000, 7400000]

            offset = 5
            xGRID = np.arange(np.floor(xlimGRID[0]/100000)-offset,np.floor(xlimGRID[1]/100000)+offset,1)
            yGRID = np.arange(np.floor(ylimGRID[0]/100000)-offset,np.floor(ylimGRID[1]/100000)+offset,1)

            for xi in xGRID:
                for yi in yGRID: 
                    xseg = [xi*100000, (xi+1)*100000, (xi+1)*100000, xi*100000, xi*100000]
                    yseg = [yi*100000, yi*100000, (yi+1)*100000, (yi+1)*100000, yi*100000]

                    lat, lon = meter_to_latlon.transform(xseg,yseg)
                    
                    polyL3 = Polygon(list(zip(xseg, yseg)))
                    polyL3ll = Polygon(list(zip(lon, lat)))

                    test_intersection = False
                    for ROi in listROI:
                        test_intersection = ROi.intersects(polyL3ll)
                        if test_intersection:
                            self.DataL3['Tileinfo'].append('Tile L3')
                            self.DataL3['polyL3'].append(polyL3)
                            self.DataL3['polyL3ll'].append(polyL3ll)

        return self
                    
    ################################################################################
    ## Save the results into a file
    ################################################################################
    def saveIDlistL2(self, 
        output: Optional[str] = 'egmslist.pkl', 
        verbose: Optional[Union[bool,None]] = None): 
        """Save the L2a/L2b search results into a file
        
        Args:
            output (str, Optional): File [Default: 'egmslist.pkl']
            verbose (bool or None, Optional): Verbose if `None`, use the verbose mode of the job [Default: `None`]

        Return

            `S1ROIparameter` class

        """ 
     
        if verbose == None:
            verbose = self.verbose
        if not isinstance(verbose,bool):
            raise ValueError(usermessage.errormsg(__name__,'saveIDlistL2',__file__,constants.__copyright__,'Verbose must be True or False',self.log))
        
        self.checkparameter(verbose = False)

        usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Save the L2a/L2b search results into a file',self.log,verbose)
        
        self.checkparameter(verbose=False)

        with open(output, 'wb') as fp:
            pickle.dump(self.Data, fp)

        usermessage.egmstoolkitprint('File %s created.' % (output),self.log,verbose)

        return self

    ################################################################################
    ## Load the results from a file
    ################################################################################
    def loadIDlistL2(self,
        input: Optional[str] = 'egmslist.pkl', 
        verbose: Optional[Union[bool,None]] = None): 
        """Load the L2a/L2b search results from a file
        
        Args:
            input (str, Optional): File [Default: 'egmslist.pkl']
            verbose (bool or None, Optional): Verbose if `None`, use the verbose mode of the job [Default: `None`]

        Return

            `S1ROIparameter` class

        """ 
    
        if verbose == None:
            verbose = self.verbose
        if not isinstance(verbose,bool):
            raise ValueError(usermessage.errormsg(__name__,'loadIDlistL2',__file__,constants.__copyright__,'Verbose must be True or False',self.log))
        
        usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Load the L2a/L2b search results from a file',self.log,verbose)
        
        self.checkparameter(verbose=False)

        with open(input, 'rb') as fp:
            self.Data = pickle.load(fp)
                
        usermessage.egmstoolkitprint('File %s loaded.' % (input),self.log,verbose)

        return self

    ################################################################################
    ## Create a map of the burst IDs
    ################################################################################
    def displaymap(self,
        output: Optional[Union[str,None]] = None, 
        verbose: Optional[Union[bool,None]] = None): 
        """Create a map of the burst IDs
        
        Args:
            output (str or None, Optional): File for the figure. If none, the figure will be displayed [Default: `None`]
            verbose (bool or None, Optional): Verbose if `None`, use the verbose mode of the job [Default: `None`]

        Return

            `S1ROIparameter` class

        """  
    
        if verbose == None:
            verbose = self.verbose
        if not isinstance(verbose,bool):
            raise ValueError(usermessage.errormsg(__name__,'displaymap',__file__,constants.__copyright__,'Verbose must be True or False',self.log))
        
        usermessage.openingmsg(__name__,__name__,__file__,constants.__copyright__,'Display a map of the selected burst IDs',self.log,verbose)
        
        self.checkparameter(verbose=False)

        if (not self.Data) and (not self.DataL3):
            raise ValueError(usermessage.errormsg(__name__,'displaymap',__file__,constants.__copyright__,'The search list(s) is/are empty',self.log))

        fig = go.Figure(go.Scattermapbox(
            mode = "lines"))

        lonall = []
        latall = []

        # Compute the color
        listtrack = []
        for tracki in self.Data:
            listtrack.append(tracki)

        listtrackunique = np.unique(listtrack)
        listcolor = []
        for li in listtrackunique:
            a = np.random.randint(255, size=3)
            listcolor.append('rgb(%d,%d,%d)' % (a[0],a[1],a[2]))
        
        # Plot the bursts
        if self.Data:
            for tracki in self.Data:
                
                ni = np.where(tracki == listtrackunique)[0][0]

                for idx in ['1','2','3']: 
                    for iwi in self.Data[tracki]['IW%s' %(idx)]:
                        lonall = lonall + iwi['polyburst'].exterior.coords.xy[0].tolist()
                        latall = latall + iwi['polyburst'].exterior.coords.xy[1].tolist()

                        fig.add_trace(go.Scattermapbox(
                            mode = "lines",
                            showlegend = False,
                            line=dict(color=listcolor[ni]), 
                            lon = iwi['polyburst'].exterior.coords.xy[0].tolist(),
                            lat = iwi['polyburst'].exterior.coords.xy[1].tolist(), 
                            hovertemplate='%s IW%s' % (tracki,idx), 
                            name='ID %d' % (iwi['egms_burst_id'])))
        
        try:
            for tilei in self.DataL3['polyL3ll']:
                
                lonall = lonall + tilei.exterior.coords.xy[0].tolist()
                latall = latall + tilei.exterior.coords.xy[1].tolist()

                fig.add_trace(go.Scattermapbox(
                    mode = "lines",
                    showlegend = False,
                    line=dict(color='red'), 
                    lon = tilei.exterior.coords.xy[0].tolist(),
                    lat = tilei.exterior.coords.xy[1].tolist(), 
                    hovertemplate='L3 UD/EW Grid', 
                    name='L3 UD/EW Grid'))
        except:
            a = 'dummy'
                    
        listROI = []            
        with fiona.open(self.ROIs) as shpfile:
            for feature in shpfile:
                coordinates = []
                line = shape(feature['geometry'])
                if isinstance(line, LineString):
                    for index, point in enumerate(line.coords):
                        if index == 0:
                            first_pt = point
                        coordinates.append(point)
                if len(coordinates) >= 3:
                    listROI.append(Polygon(coordinates))

        for polyi in listROI:
            fig.add_trace(go.Scattermapbox(
                        mode = "lines",
                        line=dict(color='rgb(0,0,0)'),
                        showlegend = False,
                        lon = polyi.exterior.coords.xy[0].tolist(),
                        lat = polyi.exterior.coords.xy[1].tolist(), 
                        hovertemplate='ROI', 
                        name='ROI'))
        
        max_bound = max(abs(np.min(lonall)-np.max(lonall)), abs(np.min(latall)-np.max(latall))) * 111
        zoom = 10 - np.log(max_bound)
        fig.update_layout(
            margin ={'l':0,'t':0,'b':0,'r':0},
            mapbox = {'style': "open-street-map",
                    'zoom': zoom,
                    'center': {'lon': np.mean(lonall), 'lat': np.mean(latall)}})
                
        if output == None: 
            fig.show()
        else: 
            fig.write_image(output)
            usermessage.egmstoolkitprint('Map saved in %s.' % (output),self.log,verbose)