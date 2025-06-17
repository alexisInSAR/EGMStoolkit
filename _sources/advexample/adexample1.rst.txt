Gridding of L2a and L2b EGMS data to minimise the overlap artefacts
###################################################################

*By Alexis Hrysiewicz, Jan. 2025*

.. admonition:: For your information
    :class: danger

    This documentation is an early version. 

This example offers the way in order to download EGMS data in L2a (or L2b) level and to use interpolations for minimising of burst-overlap artefacts. This example therefore proposes an advanced use of **EGMS toolkit**. 

First, we import the **EGMS toolkit** package and the required packages. 

.. code:: python 

    from EGMStoolkit.classes import EGMSS1burstIDapi
    from EGMStoolkit.classes import EGMSS1ROIapi
    from EGMStoolkit.classes import EGMSdownloaderapi
    from EGMStoolkit.functions import egmsdatatools
    import fiona, os 
    from shapely.geometry import Polygon, mapping, shape, LineString, Point
    import pyproj
    import numpy as np 
    import pandas as pd
    from osgeo import gdal, osr
    import glob 

Then we detect the available data based on the following parameters: 
* L2a level; 
* Region of Interest over Dublin, Ireland 
* 2018-2020 release 
* Track number 1
* Ascending data

.. code:: python 

    info = EGMSS1burstIDapi.S1burstIDmap(verbose=True,log=None)
    info.downloadfile(verbose=True)

    ROIpara = EGMSS1ROIapi.S1ROIparameter(verbose=False)

    ROIpara.egmslevel = 'L2a'
    ROIpara.bbox = [-6.427059639290446,53.2606655698541,-6.0952332730202095,53.41811986118854]
    ROIpara.release = '2018_2022'

    ROIpara.createROI(verbose=True)
    ROIpara.detectfromIDmap(info,Track_user=1,Pass_user='Ascending',verbose=True)

    ROIpara.displaymap(output='fig_search_adexample1.jpg')

The search parameters are now ready. We can send the request to retreive the files. 

.. code:: python 

    downloadpara = EGMSdownloaderapi.egmsdownloader(verbose=False)
    downloadpara.updatelist(infoS1ROIparameter=ROIpara)
    downloadpara.printlist(verbose=True)

So there are 4 files to be downloaded. 

.. code:: python 

    downloadpara.token = 'xxxxxxxxxxxxxxxxxxxx'
    downloadpara.download(outputdir='./Output')
    downloadpara.unzipfile(outputdir='./Output')

The files therefore are downloaded and unzipped. For this example, only two parameters will be manipulated: (1) *mean_velocity*, (2) 
*mean_velocity_std*.

.. note:: 

    If all parameters need to be stored, a parameter variable can be generated from any file header of EGMS dataset. For example, 

    .. code:: python

        with open('Output/L2a/2018_2022/EGMS_L2a_001_0314_IW2_VV_2018_2022_1/EGMS_L2a_001_0314_IW2_VV_2018_2022_1.csv','r') as fi: 
            first_line = fi.readline() 
        paralist = first_line.split()[0].split(',')

    Here, all parameters (i.e., *mean_velocity*) and displacement for each date will be manipulated and stored. There are 294 parameters, including 269 observation dates. 

The following lines will run the merging. The duplicated-point removal must be deactived as the interpolation will be average the observation points. 

.. code:: python 

    paralist = ['mean_velocity','mean_velocity_std']

    egmsdatatools.datamergingcsv(infoEGMSdownloader=downloadpara,inputdir='./Output',outputdir='./Output',mode='onlist',verbose=True,paratosave=paralist,__removeduplicate__=False)

Now, we therefore have a .csv file with the EGMS observations. The idea is to grid these observations into the regular grid (no clip or cropped will be required). Based on our Region of Interest shapefile, we can extract the final image extent. 

.. code:: python 

    schema = {
        'geometry': 'Polygon',
        'properties' : {'id':'int'}
        }

    latlon_to_meter = pyproj.Transformer.from_crs('epsg:4326', 'epsg:3035')

    with fiona.open('bbox.shp','r','ESRI Shapefile', schema) as shpfile:
        coordinates = []
        Xcoord = []
        Ycoord = []
        for feature in shpfile:
            line = shape(feature['geometry'])
            if isinstance(line, LineString):
                for index, point in enumerate(line.coords):
                    if index == 0:
                        first_pt = point
                    a, b = latlon_to_meter.transform(point[1],point[0])
                    Xcoord.append(b)
                    Ycoord.append(a)

And we can create the interpolation parameters. The grid is aligned to the coordinates used by EGMS for L3 datasets.  

.. code:: python 

    paragrid = dict()
    paragrid['Xmin'] = np.fix(np.min(Xcoord)/100)*100
    paragrid['Ymin'] = np.fix(np.min(Ycoord)/100)*100
    paragrid['Xmax'] = np.fix((np.max(Xcoord)/100)+1)*100
    paragrid['Ymax'] = np.fix((np.max(Ycoord)/100)+1)*100
    paragrid['xres'] = 100 
    paragrid['yres'] = 100 
    paragrid['algo'] = 'average:radius1=100:radius2=100:angle=0.0:nodata=-9999' # Alfgorithm used and options
    paragrid['variable'] = ','.join(paralist)

Finally, we can run the interpolation via the **EGMS toolkit** tool. 

.. code:: python
    
    egmsdatatools.datagridding(inputdir='./Output',outputdir='./Geotiff',namefile='all',verbose=True,paragrid=paragrid,AREA_OR_POINT='Area')

----

**This following sections are optional but improve the result quality.**

Even if the rasters are correct, the GDAL-based interpolation uses a circular kernel. It means that we extrapolated some points. However the goal is to avoid any extrapolation, and to ideally interpolate only pixels with EGMS measurement points. The solution is to create a mask by counting numbers of measurement points. 

.. code:: python 

    data = pd.read_csv('Output/EGMS_L2a_001_VV_2018_2022_1.csv',delimiter=';')

    centersX=np.arange(paragrid['Xmin'],paragrid['Xmax']+paragrid['xres'],paragrid['xres']) + paragrid['xres']/2
    centersY=np.arange(paragrid['Ymin'],paragrid['Ymax']+paragrid['yres'],paragrid['yres']) - paragrid['yres']/2

    H, *_ = np.histogram2d(data['easting'],data['northing'],bins=[centersX, centersY])
    H = np.flipud(H.T)

The variable *H* contains the numbers of measurement points for each pixel. 

To be more conservative, we can define a threshold to keep pixels containing at least *x* points. Here only the pixels with at least 1 measurement points will be kept. 

.. code:: python

    H[H<1] = 0

Then we save a GTiff image of this mask using GDAL: 

.. code:: python 

    image_size = H.shape
    nx = image_size[0]
    ny = image_size[1]

    dst_ds = gdal.GetDriverByName('GTiff').Create('Geotiff/mask.tif', ny, nx, 1)
    geotransform = (paragrid['Xmin'], paragrid['xres'], 0, paragrid['Ymax'], 0, -paragrid['yres'])

    dst_ds.SetGeoTransform(geotransform)                           
    srs = osr.SpatialReference()                                     
    srs.ImportFromEPSG(3035)
    dst_ds.SetProjection(srs.ExportToWkt())                         
    dst_ds.GetRasterBand(1).WriteArray(H)                   
    dst_ds.GetRasterBand(1).SetNoDataValue(np.nan)                  
    dst_ds.FlushCache()                                             
    dst_ds = None 

The last code section is for the application of the computed mask. 

.. code:: python 

    # Read the mask
    src_ds = gdal.Open('Geotiff/mask.tif')
    mask = src_ds.GetRasterBand(1).ReadAsArray()
    src_ds = None

    # Loop for each file
    for fi in glob.glob('Geotiff/EGMS_*.tif'): 

        src_ds = gdal.Open(fi)
        band = src_ds.GetRasterBand(1).ReadAsArray()
        band[mask==0] = -9999
    
        dst_ds = gdal.GetDriverByName("GTiff").Create(fi.replace('.tif','_masked.tif'), src_ds.RasterXSize, src_ds.RasterYSize, 1, gdal.GDT_Float64)
        dst_ds.SetGeoTransform(src_ds.GetGeoTransform()) 
        dst_ds.SetProjection(src_ds.GetProjection())
        dst_ds.GetRasterBand(1).WriteArray(band)   
        dst_ds.GetRasterBand(1).SetNoDataValue(-9999)
        dst_ds.FlushCache()

        src_ds = None 
        dst_ds = None 

Each file ending by *_masked.tif* - stored in the *Geotiff* directory - will be the EGMS rasterised datasets. 