#! /usr/bin/env python3
# -*- coding: iso-8859-1 -*-

# ##########################################################################
# Header information 
# ##########################################################################

"""EMGStoolkit.py: Toolkit to download the European Ground Motion (EGMS) InSAR-derived displacements"""

__author__ = "Alexis Hrysiewicz"
__copyright__ = "Copyright 2023"
__credits__ = ["Alexis Hrysiewicz"]
__license__ = "GPL"
__version__ = "1.0.0 Beta"
__maintainer__ = "Alexis Hrysiewicz"
__email__ = "alexis.hrysiewicz@ucd.ie"
__status__ = "Production"
__date__ = "Nov. 2022"

###########################################################################
# Track Changes
###########################################################################


###########################################################################
# Python packages
###########################################################################
import optparse
import sys
import os
import warnings
import numpy as np

###########################################################################
# Class definition for the user options 
###########################################################################
class OptionParser (optparse.OptionParser):
    def check_required(self, opt):
        option = self.get_option(opt)
        if getattr(self.values, option.dest) is None:
            self.error("%s option not supplied" % option)

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1','True'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0','False'):
        return False

###########################################################################
# Definition of user options 
###########################################################################
if len(sys.argv) < 1:
    prog = os.path.basename(sys.argv[0])
    print("example (1): python3 %s -t XXXXXXXXXXXXXXXXXXXX'" %
          sys.argv[0])
    print("example (2): python3 %s -l L2a,L2b -r 2018_2022 -t XXXXXXXXXXXXXXXXXXXX -b -6.427059639290446,53.2606655698541,-6.0952332730202095,53.41811986118854 -o ./Output_directory --track 1 --pass Ascending --nomerging -noclipping --quiet --clean'" %
          sys.argv[0])
    print("example (3): python3 %s -e'" %
          sys.argv[0])
    sys.exit(-1)
else:
    usage = "usage: %prog [options] "
    parser = optparse.OptionParser()

    parser.add_option("-l", "--level", dest="level", action="store", type="string", default='L2a,L2b',
                      help="Selected levels of EGMS data: [L2a,L2b,L3UD,L3EW]. Default: [L2a,L2b]. The comma can be used for multiple selections.")                
    parser.add_option("-r", "--release", dest="release", action="store", type="string", default='2018_2022',
                      help="Selected releases of EGMS data: [2015_2021,2018_2022]. Default: [2018_2022]. The comma can be used for multiple selections.")  
    parser.add_option("-t", "--token", dest="token", action="store", type="string", default='XXXXXXXXX',
                      help="User token given by EGMS website.")
    parser.add_option("-b", "--bbox", dest="bbox", action="store", type="string", default='None',
                      help="BBOX [WSEN] or country indices or shapefile in EPGS:4326.")
    parser.add_option("-o", "--outputdir", dest="outputdir", action="store", type="string", default='./Output',
                      help="Output directory. Default: ./Output")
    
    parser.add_option("--track", dest="track", action="store", type="string", default='None',
                      help="Track numbers. The comma can be used for multiple selections. Track and Pass must be the same length. Default: None")
    parser.add_option("--pass", dest="passS1", action="store", type="string", default='None',
                      help="Passes. The comma can be used for multiple selections. Track and Pass must be the same length. Default: None")

    parser.add_option("--nodownload", dest="download", action="store_false", default=True,
                      help="Block the downloading of the files. Default: False")
    parser.add_option("--nounzip", dest="unzip", action="store_false", default=True,
                      help="Block the unziping of the files. Default: False")
    parser.add_option("--nozip", dest="nokeepzip", action="store_false", default=True,
                      help="We will remove the .zip files. Default: False")
    parser.add_option("--nomerging", dest="merging", action="store_false", default=True,
                      help="Block the merging of the EGMS results. Default: False")
    parser.add_option("--noclipping", dest="clipping", action="store_false", default=True,
                      help="Block the clipping/croppring of the EGMS results. Default: False")
    
    parser.add_option("--clean", dest="clean", action="store_true", default=False,
                      help="Clean the raw-data files. Default: False")
    
    parser.add_option("-q","--quiet", dest="verbose", action="store_false", default=True,
                      help="Verbose. Default: True")
    
    parser.add_option("--example", action="store_true", dest="example", default=False,
                      help="Print an example. Default: False")
    
    (options, args) = parser.parse_args()

    if options.verbose: 
        print("****************************************************************************************************************************")
        print("EMGStoolkit.py: Toolkit to download the European Ground Motion (EGMS) InSAR-derived displacements")
        print("****************************************************************************************************************************")

        print('User options:')
        print(options)

if options.example == False:
    ###########################################################################
    # Wrapper
    ###########################################################################

    if options.token == 'XXXXXXXXX':
        sys.exit('Error: please give a correct use token.')

    if options.verbose:
        print("******************************************")
        print('First level of parameters:')
        print('\tLevel(s) of EGMS data (if L3, track and pass parameters will be ignored): %s' % (options.level) )
        print('\tRelease(s) of EGMS data: %s' % (options.release) )
        print('\tToken of user: %s' % (options.token) )
        print('\tBbox for searching: %s' % (options.bbox) )
        print('\tOutput Directory of EGMS data: %s' % (options.outputdir))

        if options.download: 
            print('\tThe data files will be downloaded.')
        else: 
            print('\tThe data files wil not be downloaded. The following user parameters will be ignored.')

        if options.unzip and options.download: 
            print('\tThe data files will be unzipped.')
        else: 
            print('\tThe data files wil not be unzipped. The following user parameters will be ignored.')

        if options.nokeepzip: 
            print('\t\tThe .zip files will be kept.')
        else: 
            print('\t\tThe .zip files wil not be kept.')

        if options.merging and options.unzip and options.download: 
            print('\tThe data files will be merged (based on the files)')
        else:
            print('\tThe data files will NOT be merged. The following user parameters will be ignored.')

        if options.clipping and options.merging and options.unzip and options.download: 
            print('\tThe data files will be clipped/cropped (based on the files)')
        else:
            print('\tThe data files will NOT be clipped/cropped. The following user parameters will be ignored.')

        if options.clean:
            print('\tThe raw data files will be removed.')
        else:
            print('\tThe raw data files will NOT be removed.')

        print("******************************************")

        if options.bbox == 'None': 
            sys.exit('Error: The bbox is a mandatory parameter.')

    ###########################################################################
    # (0) Import the Python packages
    from classes import EGMSS1burstIDapi
    from classes import EGMSS1ROIapi 
    from classes import EGMSdownloaderapi
    
    from functions import egmsdatatools
    
    ###########################################################################
    # (1) Manage the S1 burst ID map 
    
    info = EGMSS1burstIDapi.S1burstIDmap()
    # Download the latest ID map
    info.verbose = options.verbose
    info.downloadfile()
    
    ###########################################################################
    # (2) Check the tile/bursts available according the user imputs

    # Generate the lists regarding the user input

    # For the bbox
    mode_1 = 0
    mode_2 = 0
    mode_3 = 0
    if not options.bbox == 'None':
        list_tmp = options.bbox.split(',')

        bboxtmp = []
        list_bbox = []
        for li in list_tmp: 
            it_nb = False
            try:
                int(li)
                it_is = True
            except ValueError:
                it_is = False
            try:
                float(li)
                it_nb = True
            except ValueError:
                it_nb = False

            if not it_nb: 
                if len(li) == 2:
                    list_bbox.append(li)
                    mode_1 = 1
                elif os.path.isfile(li) == 1: 
                    list_bbox.append(li)
                    mode_2 = 1
                else: 
                    sys.exit('Error: The bbox parameter is not correct.')
            else: 
                bboxtmp.append(float(li))
        if not len(bboxtmp) == 0:
            if len(bboxtmp) == 4:
                list_bbox.append(bboxtmp)
                mode_3 = 1
            else: 
                sys.exit('Error: The bbox parameter is not correct.')
        
    listtmp1 = []
    listtmp2 = []
    listtmp3 = []
    for i1 in list_bbox: 
        if len(i1) == 2:
            listtmp1.append(i1)
        elif i1 and (isinstance(i1[0],float) or isinstance(i1[0],int)):
            listtmp2.append([i1])
        elif os.path.isfile(i1):
            listtmp3.append(i1)
    
    if listtmp1:
        list_bbox = [','.join(listtmp1)]
    else: 
        list_bbox = []
    if listtmp2:
        list_bbox.append(listtmp2[0][0])
    if listtmp2:
        for i1 in listtmp3:
            list_bbox.append(i1)

    if not mode_1 + mode_2 + mode_3 == 1 or len(listtmp3)>1: 
        warnings.warn('The multiple bbox parameters are not compabitible to the clipping mode. The clipping/cropping option will be fix to False. We recommend merging your ROIs inside the same shapefile.')

    if options.verbose: 
        print('\tDetection of bbox parameters:')
        h = 1
        for i1 in list_bbox: 
            print('\t\t(%d): %s' % (h,i1))
            h = h + 1
        

    h = 1
    downloadpara = EGMSdownloaderapi.egmsdownloader()
    downloadpara.verbose = options.verbose 

    check_dectection = False
    for bboxi in list_bbox:

        ROIpara = EGMSS1ROIapi.S1ROIparameter()
        ROIpara.verbose = options.verbose

        ROIpara.bbox = bboxi
        ROIpara.createROI()

        levellist = np.unique(options.level.split(','))

        for leveli in options.level.split(','):
            if 'UD' in leveli: 
                ROIpara.egmslevel = 'L3'
                ROIpara.egmsL3component = 'UD'
            elif 'EW' in leveli: 
                ROIpara.egmslevel = 'L3'
                ROIpara.egmsL3component = 'EW'
            else:
                ROIpara.egmslevel = leveli

            if check_dectection == False or ROIpara.egmslevel != 'L3': 
                tracklist = options.track.split(',')
                passlist = options.passS1.split(',')
               
                if not check_dectection:
                    if 'None' in tracklist  and 'None' in passlist:
                        ROIpara.detectfromIDmap(infoburstID=info)
                        check_dectection = True
                    else:
                        ROIpara.detectfromIDmap(infoburstID=info,Track=[eval(tii) for tii in tracklist],Pass=passlist)
                        check_dectection = True

            else:
                ROIpara.detectfromIDmap(infoburstID=info)
                check_dectection = True
            
            for releasei in options.release.split(','):
                ROIpara.release = releasei
                downloadpara.updatelist(infoS1ROIparameter=ROIpara)

        ROIpara.displaymap(output='fig_search_%d.jpg' %(h))
        h = h + 1

    if options.verbose:
        downloadpara.printlist()        
    
    ###########################################################################
    # (3) Download the EGMS data

    # Change the user token 
    downloadpara.token = options.token
    
    # Download (and unzip) the files
    if options.download: 
        downloadpara.download(outputdir=options.outputdir,unzip=False,clean=False) 

    # Unzip the files
    if options.download and options.unzip:
        downloadpara.unzipfile(outputdir=options.outputdir,unzip=True,clean=options.nokeepzip) 
  
    ###########################################################################
    # (4) Post-process of the files (all these steps are optional)
    
    # Merge the .csv files 
    if options.download and options.unzip and options.merging:
        egmsdatatools.datamergingcsv(infoEGMSdownloader=downloadpara,inputdir=options.outputdir,outputdir=options.outputdir,mode='onfiles',verbose=options.verbose,paratosave='all') 
        egmsdatatools.datamergingtiff(infoEGMSdownloader=downloadpara,inputdir=options.outputdir,outputdir=options.outputdir,mode='onfiles',verbose=options.verbose)
    
    # Clip/crop the data
    if options.download and options.unzip and options.merging and options.clipping:
        egmsdatatools.dataclipping(inputdir=options.outputdir,outputdir=options.outputdir,file='all',shapefile='bbox.shp',verbose=options.verbose)

    # Clean the raw data
    if options.clean: 
        egmsdatatools.removerawdata(inputdir=options.outputdir,verbose=options.verbose,force=True)
    
else:
    ###########################################################################
    # Example 
    ###########################################################################

    print(" ###########################################################################\n",
    "# Example of EGMS toolkit in Python environment\n",
    "###########################################################################\n",
    "\n",
    "###########################################################################\n",
    "# (0) Import the Python packages\n",
    "from classes import EGMSS1burstIDapi\n", 
    "from classes import EGMSS1ROIapi \n",
    "from classes import EGMSdownloaderapi\n", 
    "\n",
    "from functions import egmsdatatools\n",
    "\n",
    "###########################################################################\n",
    "# (1) Manage the S1 burst ID map \n",
    "\n",
    "# Create the python variable \n",
    "info = EGMSS1burstIDapi.S1burstIDmap()\n",
    "\n",
    "# Print the variable\n",
    "# info.print()\n",
    "\n",
    "# Active/Deactive the verbose\n",
    "info.verbose = False # or False\n",
    "\n",
    "# Download the latest ID map\n",
    "info.downloadfile()\n",
    "\n",
    "###########################################################################\n",
    "# (2) Check the tile/bursts available according the user imputs\n",
    "\n",
    "# Create the python variable \n",
    "ROIpara = EGMSS1ROIapi.S1ROIparameter()\n",
    "\n",
    "# Print the variable\n",
    "ROIpara.print()\n",
    "\n",
    "# Active/Deactive the verbose\n",
    "ROIpara.verbose = False # or False\n",
    "\n",
    "# Define the user parameter\n",
    "ROIpara.egmslevel = 'L2b' # Level of EGMS data\n",
    "ROIpara.bbox = [-6.427059639290446,53.2606655698541,-6.0952332730202095,53.41811986118854] # Bbox for searching. The European country names can be used (i.e., IE, FR) or a shapefile in EPSG:4326.\n",
    "ROIpara.release = '2018_2022' # Release of EGMS data\n",
    "\n",
    "# Create the ROI file\n",
    "ROIpara.createROI()\n",
    "\n",
    "# Detect the burst ID\n",
    "ROIpara.detectfromIDmap(infoburstID=info,Track=1,Pass='Ascending')\n",
    "    # Track: track number or list of number\n",
    "    # Pass: [Ascending or Descending] or list of string\n",
    "\n",
    "# Save the burst ID list\n",
    "ROIpara.saveIDlistL2() # Or ROIpara.saveIDlistL2(input=saveseach.pkl)\n",
    "\n",
    "# Load the burst ID list\n",
    "ROIpara.loadIDlistL2() # Or ROIpara.loadIDlistL2(input=saveseach.pkl)\n",
    "\n",
    "# Display a map in the internet browser\n",
    "ROIpara.displaymap() # Or ROIpara.displaymap(output='fig_search.jog')\n",
    "\n",
    "###########################################################################\n",
    "# (3) Download the EGMS data\n",
    "\n",
    "# Create the python variable \n",
    "downloadpara = EGMSdownloaderapi.egmsdownloader()\n",
    "\n",
    "# Print the variable\n",
    "# downloadpara.print()\n",
    "\n",
    "# Active/Deactive the verbose\n",
    "downloadpara.verbose = True # or False\n",
    "\n",
    "# Create the list of files\n",
    "downloadpara.updatelist(infoS1ROIparameter=ROIpara)\n",
    "\n",
    "# Print the list of files\n",
    "downloadpara.printlist()\n",
    "\n",
    "# Possibility to concatenante other research\n",
    "ROIpara.egmslevel = 'L3'\n",
    "ROIpara.egmsL3component = 'UD'\n",
    "ROIpara.release = '2015_2021'\n",
    "ROIpara.detectfromIDmap(infoburstID=info)\n",
    "# ROIpara.print()\n",
    "downloadpara.updatelist(infoS1ROIparameter=ROIpara)\n",
    "# ROIpara.displaymap()\n",
    "\n",
    "# Print the final list of files\n",
    "downloadpara.printlist()\n",
    "\n",
    "# Change the user token \n",
    "downloadpara.token = 'xxxx'\n",
    "\n",
    "# Download (and unzip) the files\n",
    "downloadpara.download() # or downloadpara.download(outputdir='./Output',unzip=True,clean=True) \n",
    "    # outputdir: output directory [./Output]\n",
    "    # unzip: unzipping of the downloaded files [True or False]\n",
    "    # clean: remove the .zip files [True or False]\n",
    "\n",
    "# Unzip the files\n",
    "downloadpara.unzipfile() # or downloadpara.download(outputdir='./Output',unzip=True,clean=True) \n",
    "    # outputdir: output directory [./Output]\n",
    "    # unzip: unzipping of the downloaded files [True or False]\n",
    "    # clean: remove the .zip files [True or False]\n",

    "# Clean the used files, remove the files that are not in the lists\n",
    "# downloadpara.clean() # or downloadpara.clean(outputdir='./Output) \n",
    "\n",
    "###########################################################################\n",
    "# (4) Post-process of the files (all these steps are optional)\n",
    "\n",
    "# Merge the .csv files \n",
    "egmsdatatools.datamergingcsv(infoEGMSdownloader=downloadpara,inputdir='./Output',outputdir='./Output',mode='onlist',verbose=True,paratosave='all') # or egmsdatatools.datamergingcsv()\n",
    "    # infoEGMSdownloader: output of EGMSdownloaderapi, required with the 'onlist' mode\n",
    "    # outputdir: output directory [./Output]\n",
    "    # inputdir: inputdir directory [./Output]\n",
    "    # mode: merge the files regarding the files available (onfiles) or on the list [onlist or onfiles]\n",
    "    # verbose [True or False]\n",
    "    # paratosave: extraction of parameter regarding the EGMS names ['all' or string value]. ['latitude', 'longitude', 'easting', 'northing', 'height', 'height_wgs84'] will always be saved.\n",
    "\n",
    "# Merge the .tiff files (only for the L3 levels)\n",
    "egmsdatatools.datamergingtiff(infoEGMSdownloader=downloadpara,inputdir='./Output',outputdir='./Output',mode='onlist',verbose=True) # or egmsdatatools.datamergingtiff()\n",
    "    # infoEGMSdownloader: output of EGMSdownloaderapi, required with the 'onlist' mode\n",
    "    # outputdir: output directory [./Output]\n",
    "    # inputdir: inputdir directory [./Output]\n",
    "    # mode: merge the files regarding the files available (onfiles) or on the list [onlist or onfiles]\n",
    "    # verbose [True or False]\n",
    "\n",
    "# Clip/crop the data\n",
    "egmsdatatools.dataclipping(inputdir='./Output',outputdir='./Output',file='all',shapefile='bbox.shp',verbose=True)\n",
    "    # outputdir: output directory [./Output]\n",
    "    # inputdir: inputdir directory [./Output]\n",
    "    # file: list of files for clipping or cropping, they must not to have the '_cropped' or '_clipped' in their names, not in the paths [all] \n",
    "    # shapefile: EPGS:4326 shapefile with the ROI [bbox or name files]\n",
    "    # verbose [True or False]", 
    "\n",
    "# Delete the raw-data directorie\n",
    "egmsdatatools.removerawdata(inputdir='./Output',verbose=True)\n",
    "    # inputdir: inputdir directory [./Output]\n",
    "    # verbose [True or False])\n",
    "\n",
    "###########################################################################\n",
    "# (5) Post-process of the file for ADVANCED USERS\n",
    "\n",
    "# Interpolation of point data into a .tif raster file (can be done before the cropping/clipping step)\n",
    "# Creation of the dict. for the gridding parameters\n",
    "paragrid = dict()\n",
    "paragrid['Xmin'] = 2896000 # Minimal X coordinate in EPGS:3035\n",
    "paragrid['Ymin'] = 3317250 # Minimal Y coordinate in EPGS:3035\n",
    "paragrid['Xmax'] = 3359000 # Maximal X coordinate in EPGS:3035\n",
    "paragrid['Ymax'] = 3745500 # Maximal Y coordinate in EPGS:3035\n",
    "paragrid['xres'] = 500 # X spatial resolution in EPGS:3035\n",
    "paragrid['yres'] = 500 # Y spatial resolution in EPGS:3035\n",
    "paragrid['algo'] = 'average:radius1=500:radius2=500:angle=0.0:nodata=-9999' # Alfgorithm used and options\n",
    "paragrid['variable'] = 'mean_velocity,mean_velocity_std,acceleration,acceleration_std,seasonality,seasonality_std'\n",
    "# paragrid['algo'] = 'invdist:power=2.0:smoothing=0.0:radius1=0.0:radius2=0.0:angle=0.0:max_points=0:min_points=0:nodata=0.0'\n",
    "# paragrid['algo'] = 'invdistnn:power=2.0:radius=1.0:max_points=12:min_points=0:nodata=0'\n",
    "# paragrid['algo'] = 'average:radius1=0.0:radius2=0.0:angle=0.0:min_points=0:nodata=0.0'\n",
    "# paragrid['algo'] = 'nearest:radius1=0.0:radius2=0.0:angle=0.0:nodata=0.0'\n",
    "# paragrid['algo'] = 'linear:radius=-1.0:nodata=0.0'\n",
    "\n",
    "egmsdatatools.datagridding(inputdir='./Output',outputdir='./Output',file='all',verbose=True,paragrid=paragrid)")

    # Conversion of the data (for later)


