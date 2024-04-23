#! /usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""
Wrapper of EGMS-toolkit 
    
    (From `EGMStoolkit` package)

Changelog:
    * 0.2.8: Fix regarding the force option for removerawdata, Apr. 2024, Alexis Hrysiewicz
    * 0.2.6: Bug fixes for Windows systems, Feb. 2024, Alexis Hrysiewicz
    * 0.2.0: Script structuring, Jan. 2024, Alexis Hrysiewicz
    * 0.1.0: Initial version, Nov. 2023

"""
###########################################################################
# Python packages
###########################################################################
import optparse
import sys
import os
import numpy as np

from EGMStoolkit.classes import EGMSS1burstIDapi
from EGMStoolkit.classes import EGMSS1ROIapi 
from EGMStoolkit.classes import EGMSdownloaderapi
from EGMStoolkit.functions import egmsdatatools

from EGMStoolkit import usermessage
from EGMStoolkit import constants

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

def main():
    """Main function"""
    ###########################################################################
    # Definition of user options 
    ###########################################################################
    if len(sys.argv) < 1:
        prog = os.path.basename(sys.argv[0])
        print("example (1): python3 %s -l L2a,L2b -r 2018_2022 -t XXXXXXXXXXXXXXXXXXXX -b -6.427059639290446,53.2606655698541,-6.0952332730202095,53.41811986118854 -o ./Output_directory --track 1 --pass Ascending --nomerging -noclipping --quiet --clean'" %
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
        parser.add_option("-o", "--outputdir", dest="outputdir", action="store", type="string", default='Output',
                        help="Output directory. Default: Output")
        
        parser.add_option("--track", dest="track", action="store", type="string", default='None',
                        help="Track numbers. The comma can be used for multiple selections. Track and Pass must have the same length. Default: None")
        parser.add_option("--pass", dest="passS1", action="store", type="string", default='None',
                        help="Passes. The comma can be used for multiple selections. Track and Pass must have the same length. Default: None")

        parser.add_option("--nodownload", dest="download", action="store_false", default=True,
                        help="Block downloading of files. Default: False")
        parser.add_option("--nounzip", dest="unzip", action="store_false", default=True,
                        help="Block unziping of files. Default: False")
        parser.add_option("--nozip", dest="nokeepzip", action="store_false", default=True,
                        help="We will remove .zip files. Default: False")
        parser.add_option("--nomerging", dest="merging", action="store_false", default=True,
                        help="Block merging of EGMS results. Default: False")
        parser.add_option("--noclipping", dest="clipping", action="store_false", default=True,
                        help="Block clipping/croppring of EGMS results. Default: False")
        
        parser.add_option("--clean", dest="clean", action="store_true", default=False,
                        help="Clean the raw-data files. Default: False")
        
        parser.add_option("-q","--quiet", dest="verbose", action="store_false", default=True,
                        help="Verbose. Default: True")
        
        parser.add_option("--nolog", dest="logmode", action="store_false", default=True,
                        help="Logging mode. Default: True")

        parser.add_option("--docs", dest="docmode", action="store_true", default=False,
                        help="Open the documentation. Default: False")
        
        (options, args) = parser.parse_args()

    if options.docmode == False: 
        usermessage.egmstoolkitprint("****************************************************************************************************************************",None,options.verbose)
        usermessage.egmstoolkitprint("EMGStoolkit.py: Toolkit to download the European Ground Motion (EGMS) InSAR-derived displacements",None,options.verbose)
        usermessage.egmstoolkitprint("****************************************************************************************************************************",None,options.verbose)

        usermessage.egmstoolkitprint('User options:',None,options.verbose)
        usermessage.egmstoolkitprint(options,None,options.verbose)

    
        ###########################################################################
        # Wrapper
        ###########################################################################

        if options.token == 'XXXXXXXXX':
            raise ValueError(usermessage.errormsg(__name__,__name__,__file__,constants.__copyright__,'The bbox parameter is not correct.',None))

        if options.logmode:
            log = 'egmstoolkit.log'
        else: 
            log = None

        usermessage.egmstoolkitprint("******************************************",log,options.verbose)
        usermessage.egmstoolkitprint('First level of parameters:',log,options.verbose)
        usermessage.egmstoolkitprint('\tLevel(s) of EGMS data (if L3, track and pass parameters will be ignored): %s' % (options.level),log,options.verbose)
        usermessage.egmstoolkitprint('\tRelease(s) of EGMS data: %s' % (options.release),log,options.verbose)
        usermessage.egmstoolkitprint('\tToken of user: %s' % (options.token),log,options.verbose)
        usermessage.egmstoolkitprint('\tBbox for searching: %s' % (options.bbox),log,options.verbose)
        usermessage.egmstoolkitprint('\tOutput Directory of EGMS data: %s' % (options.outputdir),log,options.verbose)

        if options.download: 
            usermessage.egmstoolkitprint('\tThe data files will be downloaded.',log,options.verbose)
        else: 
            usermessage.egmstoolkitprint('\tThe data files wil not be downloaded. The following user parameters will be ignored.',log,options.verbose)

        if options.unzip and options.download: 
            usermessage.egmstoolkitprint('\tThe data files will be unzipped.',log,options.verbose)
        else: 
            usermessage.egmstoolkitprint('\tThe data files will not be unzipped. The following user parameters will be ignored.',log,options.verbose)

        if options.nokeepzip: 
            usermessage.egmstoolkitprint('\t\tThe .zip files will be kept.',log,options.verbose)
        else: 
            usermessage.egmstoolkitprint('\t\tThe .zip files will not be kept.',log,options.verbose)

        if options.merging and options.unzip and options.download: 
            usermessage.egmstoolkitprint('\tThe data files will be merged (based on the files)',log,options.verbose)
        else:
            usermessage.egmstoolkitprint('\tThe data files will NOT be merged. The following user parameters will be ignored.',log,options.verbose)

        if options.clipping and options.merging and options.unzip and options.download: 
            usermessage.egmstoolkitprint('\tThe data files will be clipped/cropped (based on the files)',log,options.verbose)
        else:
            usermessage.egmstoolkitprint('\tThe data files will NOT be clipped/cropped. The following user parameters will be ignored.',log,options.verbose)

        if options.clean:
            usermessage.egmstoolkitprint('\tThe raw data files will be removed.',log,options.verbose)
        else:
            usermessage.egmstoolkitprint('\tThe raw data files will NOT be removed.',log,options.verbose)

        usermessage.egmstoolkitprint("******************************************",log,options.verbose)

        if options.bbox == 'None': 
            raise ValueError(usermessage.errormsg(__name__,__name__,__file__,constants.__copyright__,'The bbox parameter is not correct.',log))

        if not os.path.isdir(options.outputdir): 
            os.mkdir(options.outputdir)

        ###########################################################################
        # (1) Manage the S1 burst ID map 

        info = EGMSS1burstIDapi.S1burstIDmap(verbose=options.verbose,log=log)
        # Download the latest ID map
        print('dede')
        info.downloadfile()
        print('dede2')
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
                        raise ValueError(usermessage.errormsg(__name__,__name__,__file__,constants.__copyright__,'The bbox parameter is not correct.',log))
                else: 
                    bboxtmp.append(float(li))
            if not len(bboxtmp) == 0:
                if len(bboxtmp) == 4:
                    list_bbox.append(bboxtmp)
                    mode_3 = 1
                else: 
                    raise ValueError(usermessage.errormsg(__name__,__name__,__file__,constants.__copyright__,'The bbox parameter is not correct.',log))
            
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
            usermessage.warningmsg(__name__,__name__,__file__,'The multiple bbox parameters are not compabitible to the clipping mode. The clipping/cropping option will be fix to False. We recommend merging your ROIs inside the same shapefile.',log,True)

        if options.verbose: 
            usermessage.egmstoolkitprint('\tDetection of bbox parameters:',log,options.verbose)
            h = 1
            for i1 in list_bbox: 
                usermessage.egmstoolkitprint('\t\t(%d): %s' % (h,i1),log,options.verbose)
                h = h + 1
            
        h = 1
        downloadpara = EGMSdownloaderapi.egmsdownloader(verbose=options.verbose,log=log)

        check_dectection = False
        for bboxi in list_bbox:

            ROIpara = EGMSS1ROIapi.S1ROIparameter(verbose=options.verbose,log=log)

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

            ROIpara.displaymap(output='%s%sfig_search_%d.jpg' %(options.outputdir,os.sep,h))
            h = h + 1

        if options.verbose:
            downloadpara.printlist()

        ###########################################################################
        # (3) Download the EGMS data

        # Change the user token 
        downloadpara.token = options.token

        # Download (and unzip) the files
        if options.download: 
            downloadpara.download(outputdir=options.outputdir,unzipmode=False,cleanmode=False) 

        # Unzip the files
        if options.download and options.unzip:
            downloadpara.unzipfile(outputdir=options.outputdir,unzipmode=True,cleanmode=options.nokeepzip) 

        ###########################################################################
        # (4) Post-process of the files (all these steps are optional)

        # Merge the .csv files 
        if options.download and options.unzip and options.merging:
            egmsdatatools.datamergingcsv(infoEGMSdownloader=downloadpara,inputdir=options.outputdir,outputdir=options.outputdir,mode='onfiles',verbose=options.verbose,paratosave='all',log=log) 
            egmsdatatools.datamergingtiff(infoEGMSdownloader=downloadpara,inputdir=options.outputdir,outputdir=options.outputdir,mode='onfiles',verbose=options.verbose,log=log)

        # Clip/crop the data
        if options.download and options.unzip and options.merging and options.clipping:
            egmsdatatools.dataclipping(inputdir=options.outputdir,outputdir=options.outputdir,namefile='all',shapefile='bbox.shp',verbose=options.verbose,log=log)

        # Clean the raw data
        if options.clean: 
            egmsdatatools.removerawdata(inputdir=options.outputdir,verbose=options.verbose,forcemode=True,log=log)
    
    else: 
        ## Open the documentation
        import webbrowser
        import requests


        usermessage.openingmsg(__name__,main.__name__,__file__,constants.__copyright__,'Run the EGMStoolkit documentation via the default web browser',None,True)
        urlfile = 'file:'+__file__.replace('EGMStoolkitapp.py','')+'..'+os.sep+'..'+os.sep+'docs'+os.sep+'build'+os.sep+'html'+os.sep+'index.html'
        urlonline = 'https://alexisinsar.github.io/EGMStoolkit/'
        
        try:
            response = requests.head(urlonline)
        except Exception as e:
            a = 'dummy'
        
        if response.status_code == 200:
            url = urlonline 
        else:
            url = urlfile
    
        webbrowser.open_new(url)

##############################################
## Run
##############################################
if __name__=='__main__':
    main()