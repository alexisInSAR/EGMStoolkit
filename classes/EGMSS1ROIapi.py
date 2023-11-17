#! /usr/bin/env python3
# -*- coding: iso-8859-1 -*-

# Part of EMGStoolkit.py:

import os 
import sys
import warnings
from shapely.geometry import Polygon, mapping, shape, LineString
from osgeo import gdal
from osgeo import ogr
import fiona
import numpy as np
from shapely.wkt import loads
import glob
from alive_progress import alive_bar
import warnings
import pickle
import pyproj
import plotly.graph_objects as go
from numpy.matlib import repmat

from functions import esa2egmsburstID

source_crs = 'epsg:4326'
target_crs = 'epsg:3035'

latlon_to_meter = pyproj.Transformer.from_crs(source_crs, target_crs)
meter_to_latlon = pyproj.Transformer.from_crs(target_crs,source_crs)

################################################################################
## Creation of a class to manage the Sentinel-1 burst ID map
################################################################################
class S1ROIparameter:

    ################################################################################
    ## Initialistion of the class
    ################################################################################
    def __init__(self):
        self.bbox = 'None'
        self.ROIs = []
        self.egmslevel = 'L2a'
        self.egmsL3component = 'UD'
        self.release = '2018_2022'
        self.Data = dict()
        self.DataL3 = dict()
        self.workdirectoy = ''
       
        self.verbose = True

        self.checkparameter()

    ################################################################################
    ## Function to print the attributes
    ################################################################################
    def print(self):

        self.checkparameter()

        attrs = vars(self)
        print(', '.join("%s: %s" % item for item in attrs.items()))

    ################################################################################
    ## Check parameters
    ################################################################################
    def checkparameter(self):
        if not (self.egmslevel == 'L2a' or self.egmslevel == 'L2b' or self.egmslevel == 'L3'):
            print('Error: The level parameter is not correct (in EGMSROIapi.py)')
        if not (self.egmsL3component == 'UD' or self.egmsL3component == 'EW'):
            print('Error: The 3D-component parameter is not correct (in EGMSROIapi.py)')
        if not (self.release == '2015_2021' or self.release == '2018_2022'):
            print('Error: The release parameter is not correct (in EGMSROIapi.py)')
        if not (self.verbose == True or self.verbose == False):
            print('Error: The verbose parameter is not correct (in EGMSROIapi.py)')

    ################################################################################
    ## Function to create the ROI file
    ################################################################################
    def createROI(self): 
    
        self.checkparameter()

        if self.verbose:
            print('EMGStoolkit.py => EGMSS1ROIapi: create the ROI file for searching')

        if self.bbox == 'None':
            sys.exit('ERROR: the bbox is empty.')

        if os.path.isfile('bbox.cpg'): 
            os.remove('bbox.cpg')
        if os.path.isfile('bbox.dbf'): 
            os.remove('bbox.dbf')
        if os.path.isfile('bbox.prj'): 
            os.remove('bbox.prj')
        if os.path.isfile('bbox.shp'): 
            os.remove('bbox.shp')
        if os.path.isfile('bbox.shx'): 
            os.remove('bbox.shx')

        ## Create the polygons of the ROIs
        if isinstance(self.bbox, list):
            if self.verbose:
                print('\tUse the bbox given by the user')

            schema = {'geometry': 'MultiLineString','properties': {'FID': 'int'}}
            
            multi = loads("MULTILINESTRING ((%f %f, %f %f, %f %f, %f %f, %f %f))" % (
                self.bbox[0], self.bbox[1],
                self.bbox[2],self.bbox[1],
                self.bbox[2],self.bbox[3],
                self.bbox[0], self.bbox[3],
                self.bbox[0], self.bbox[1]))

            with fiona.open('bbox.shp', mode='w', driver='ESRI Shapefile',schema = schema, crs = "EPSG:4326")  as output:
                output.write({'geometry':mapping(multi),'properties': {'FID':1}})

        elif os.path.isfile(self.bbox):
            if self.verbose:
                print('\tUse the vector file giving by the user: %s' % (self.bbox))
            gdal.VectorTranslate('bbox.shp',self.bbox,options='-f "ESRI Shapefile" -t_srs "EPSG:4326"')
        
        elif isinstance(self.bbox, str): # ERROR
            if self.verbose:
                print('\tUse the country name given by the user')

            cmd = 'gmt coast -JU6i -E%s -M > bbox.GMT' % (self.bbox)
            os.system(cmd)
            gdal.VectorTranslate('bbox.shp','bbox.GMT',options='-f "ESRI Shapefile" -s_srs "EPSG:4326" -t_srs "EPSG:4326" -overwrite')

            os.remove('bbox.GMT')
            os.remove('gmt.history')

        else: 
            sys.exit('ERROR: the format is not recognised (in EGMSS1ROIapi: create the ROI file for searching).')
        
        self.ROIs = 'bbox.shp'

    ################################################################################
    ## Function to detect the data regarding the burst IDs
    ################################################################################
    def detectfromIDmap(self,**kwargs):
     
        self.checkparameter()

        if self.verbose:
            print('EMGStoolkit.py => EGMSS1ROIapi: detect the data regarding the burst IDs')

        infoburstID = kwargs['infoburstID']

        if not "Track" in kwargs:
            Track_user = 'None'
        else: 
            Track_user = kwargs['Track']
        if not "Pass" in kwargs:
            Pass_user = 'None'
        else:
            Pass_user = kwargs['Pass']
            for pii in Pass_user:
                if not (pii.upper() == 'ASCENDING' or pii.upper() == 'DESCENDING' or pii == 'None'): 
                    sys.exit('Error: pass should be Ascending or Descending.')

        if (isinstance(Track_user, list) and isinstance(Pass_user, list) and len(Track_user) !=1 and len(Pass_user) !=1): 
            if not len(Track_user) == len(Pass_user):
                sys.exit('Error: The track and pass parameters do not have the same length.')

        warnings.warn('The use of the S1 burst ID map is less accurate than the use of .xml S1 files.')
        
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
            if self.verbose:
                print('\tFor the L2a and L2b levels')

            ## Read the kml files to detect the burst ID
            filesqlite = glob.glob('%s/IW/sqlite/*.sqlite3' % (infoburstID.pathIDmap))[-1]
            
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
                                az_size = 1508
                                dt_az = 0.0020555563
                                anx_mid = anx_time + az_size/2*dt_az

                                egms_burst_id = esa2egmsburstID.get_egms_burst_cycle_id(relative_orbit_number, anx_mid)[-1]
                                
                                if not (isinstance(Track_user, list)):
                                    Track_user = [Track_user]
                                if not isinstance(Pass_user, list):
                                    Pass_user = [Pass_user]

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
            if self.verbose:
                print('\tFor the L3 level: the input argument will be ignored.')

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
                    
    ################################################################################
    ## Save the results into a file
    ################################################################################
    def saveIDlistL2(self,**kwargs): 
        
        self.checkparameter()

        if self.verbose:
            print('EMGStoolkit.py => EGMSS1ROIapi: save the L2a/L2b search results into a file')

        if not "output" in kwargs:
            output = 'egmslist.pkl'
        else: 
            output = kwargs['output']
        with open(output, 'wb') as fp:
            pickle.dump(self.Data, fp)

        if self.verbose:
            print('\tFile %s created.' % (output))

    ################################################################################
    ## Load the results from a file
    ################################################################################
    def loadIDlistL2(self,**kwargs): 
    
        self.checkparameter()

        if self.verbose:
            print('EMGStoolkit.py => EGMSS1ROIapi: load the L2a/L2b search results from a file')

        if not "input" in kwargs:
            input = 'egmslist.pkl'
        else: 
            input = kwargs['input']
        with open(input, 'rb') as fp:
            self.Data = pickle.load(fp)
        
        if self.verbose:
            print('\tFile %s loaded.' % (input))

    ################################################################################
    ## Create a map of the burst IDs
    ################################################################################
    def displaymap(self,**kwargs):  
    
        self.checkparameter()

        if self.verbose:
            print('EMGStoolkit.py => EGMSS1ROIapi: display a map of the selected burst IDs')

        if not "output" in kwargs:
            output = 'None'
        else: 
            output = kwargs['output']    

        if (not self.Data) and (not self.DataL3):
            sys.exit('ERROR: the search list(s) is/are empty (in EGMSS1ROIapi: display a map of the selected burst IDs)')

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
                
        if output == 'None': 
            fig.show()
        else: 
            fig.write_image(output)
            if self.verbose:
                print('\tMap saved in %s.' % (output))