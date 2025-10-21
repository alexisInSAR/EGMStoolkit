#! /usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""
Module to add some functions to **`EGMStoolkit`**

The module adds some functions, required by to run `EGMStoolkit`.

    (From `EGMStoolkit` package)

Changelog:
    * 0.3.0: Add the downloading function, Oct. 2025, Alexis Hrysiewicz
    * 0.2.12: Add the support of the 2019_2023 release, Nov. 2024, Alexis Hrysiewicz
    * 0.2.1: Remove the duplicate points for L2 datasets, Feb. 2024, Alexis Hrysiewicz
    * 0.2.0: Script structuring, Jan. 2024, Alexis Hrysiewicz
    * 0.1.0: Initial version, Nov. 2023

"""

from EGMStoolkit import usermessage
from EGMStoolkit import constants
import os 
from urllib.parse import urlsplit
import requests
import time 
from tqdm import tqdm

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
    elif inputrelease == '2019_2023':
        ext_release = '_2019_2023_1'
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
    elif '_2019_2023_1' in ni[-1]: 
        inputrelease = '2019_2023'
        ext_release = '_2019_2023_1'
    else: 
        inputrelease = '2015_2021'
        ext_release = ''
    
    release_para = [inputrelease, ext_release]

    return release_para

################################################################################
## Function to download a file
################################################################################
def download_file(url, 
    username = None,
    password = None,
    output_file=None,
    retries=10,
    bypass502=False,
    verbose=True,
    log=None):
    """Download function
    """

    if output_file == None:
        filename = os.path.basename(urlsplit(url).path)
        if not filename:
            raise ValueError('Cannot determine filename from URL. Please provide output_file.',log)    
    else:
            filename = output_file

    existing_size = 0
    if os.path.exists(filename):
        existing_size = os.path.getsize(filename)

    headers = {
            'Range': f'bytes={existing_size}-'
    }

    attempt = 0
    while attempt < retries:
        try:
            usermessage.egmstoolkitprint('EGMS-Toolkit - Downloader - Starting download from: %s' % (url),log,verbose)

            if password == None:
                response = requests.get(url, headers=headers, stream=True, allow_redirects=True, timeout= (5, 5))
            else:
                response = requests.get(url, headers=headers, auth=(username, password), stream=True, allow_redirects=True, timeout= (5, 5))

            if response.status_code == 416:
                usermessage.egmstoolkitprint('EGMS-Toolkit - Downloader - Download already done.',log,verbose)

            if (response.status_code == 502) and (bypass502 == True):
                usermessage.egmstoolkitprint('The EGMS file does not exist.',log,verbose)
                time.sleep(2)
                return 

            response.raise_for_status() 

            content_range = response.headers.get('Content-Range')
            if content_range:
                total_size = int(content_range.split('/')[-1])
            else:
                content_length = response.headers.get('Content-Length')
                total_size = int(content_length) + existing_size if content_length else None

            mode = 'ab' if existing_size > 0 else 'wb'

            with open(filename, mode) as f:
                if verbose:
                    with tqdm(
                        total=total_size,
                        unit='B',
                        unit_scale=True,
                        unit_divisor=1024,
                        desc=filename,
                        initial=existing_size,
                        ascii=True,
                        dynamic_ncols=True,
                        mininterval=0.1,
                        disable=total_size is None,
                        ) as progress_bar:
                            for chunk in response.iter_content(chunk_size=constants.__chunksize__):
                                if chunk:
                                    f.write(chunk)
                                    progress_bar.update(len(chunk)) 
                else:
                    with open(filename, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=constants.__chunksize__):
                            if chunk:
                                f.write(chunk)

            usermessage.egmstoolkitprint('EGMS-toolkit - Downloader - Download complete',log,verbose)
            return
        
        except requests.exceptions.ReadTimeout as errt:
            attempt += 1
            usermessage.egmstoolkitprint(f"Read timeout on attempt {attempt}/{retries}. Retrying...",log,verbose)
            time.sleep(1)
        except requests.exceptions.HTTPError as errh:
            raise ValueError('EGMS-toolkit - Downloader - HTTP Error: %s' % (errh),log)
        except requests.exceptions.ConnectionError as errc:
            attempt += 1
            usermessage.egmstoolkitprint(f"Read timeout on attempt {attempt}/{retries}. Retrying...",log,verbose)
            time.sleep(1)
        except requests.exceptions.Timeout as errt:
            raise ValueError('EGMS-toolkit - Downloader - Timeout Error: %s' % (errt),log)
        except requests.exceptions.RequestException as err:
            raise ValueError('EGMS-toolkit - Downloader - Other Error: %s' % (err),log)