#! /usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""
Module to generate the EGMS-toolkit message

The module allows to generate the different user messages
(e.g., error, warning, verbose). 
    
    (From `EGMStoolkit` package)

Changelog:
        * 0.2.0: Initial version, Jan. 2024

"""
################################################################################
## Python packages
################################################################################
import logging

from EGMStoolkit import constants
__copyright__ = constants.__copyright__

################################################################################
def openingmsg(namescript,defname,filescript,copyright,msg,log,verbose):
    """Display an opening message 

    The function creates an opening message for the verbose and the log.  

    Args:
        namescript (str): Name of the `EGMStoolkit` module 
        defname (str): Name of the function
        filescript (str): Full path of the `EGMStoolkit` module 
        copyright (str): Copyright
        msg (str): Message
        log (str or None): log value 
        verbose (bool): verbose value 
    
    """

    egmstoolkitprint('%s\n%s %s\n\n%s\n%s.%s:\n\t%s\n\n\tScript: %s\n\t\t%s\n%s\n' % (constants.__displayline1__,
        constants.__name__,constants.__version__,constants.__displayline2__,
        namescript,defname,msg,filescript,copyright,constants.__displayline1__)
        ,log,verbose)   

################################################################################

def warningmsg(namescript,defname,filescript,msg1,log,verbose): 
    """Create a warning message 

    The function creates a warning message.  

    Args:
        namescript (str): Name of the `EGMStoolkit` module 
        defname (str): Name of the function
        filescript (str): Full path of the `EGMStoolkit` module 
        msg1 (str): Message
        log (str or None): log value 
        verbose (bool): verbose value 

    Returns:
        str: Output message if verbose is ``True``
    
    """

    msgsentence = ('%s in %s.%s\n\t%s\n\t\t--> %s'
                    % (constants.__warning__,namescript,defname,filescript,msg1))
    
    if not log == None: 
        logging.basicConfig(filename=log, filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger=logging.getLogger() 
        logger.setLevel(definelevel(constants.__loggingmode__)) 
        logger.warning(msgsentence.replace('\n',' '))

    if verbose == True: 
        print(msgsentence)

################################################################################
def errormsg(namescript,defname,filescript,copyright,msg1,log): 
    """Create an error message 

    The function creates an error message.  

    Args:
        namescript (str): Name of the `EGMStoolkit` module 
        defname (str): Name of the function
        filescript (str): Full path of the `EGMStoolkit` module 
        copyright (str): Copyright
        msg1 (str): Message
        log (str or None): log value 

    Returns:
        str: Output message
    
    """

    msgsentence = ('%s\n\tin %s.%s\n\t\t%s\n\t\t%s'
                    % (constants.__error__,namescript,defname,filescript,msg1))
    
    if not log == None: 
        logging.basicConfig(filename=log, filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger=logging.getLogger() 
        logger.setLevel(definelevel(constants.__loggingmode__)) 
        logger.error(msgsentence.replace('\n',' '))

    return msgsentence

################################################################################
def egmstoolkitprint(msg,log,verbose):
    """Print a message 

    The function print an message for the verbose and the log.  

    Args:
        msg (str): Message
        log (str or None): log value 
        verbose (bool): verbose value 

    """

    if verbose == True:
        print(msg)

    if not log == None: 
        logging.basicConfig(filename=log, filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger=logging.getLogger() 
        logger.setLevel(definelevel(constants.__loggingmode__)) 
        logger.info(msg.replace('\n',' '))

################################################################################
def definelevel(level):
    """Define the logging level

    The function defines the logging level. 

    Args:
        level (str): Level of logging. Can be ``NOTSET``, ``DEBUG``, ``INFO``, ``WARN``, ``ERROR``, ``CRITICAL``.

    Returns:
        str: level of logging

    """

    if level == 'NOTSET': 
        out = logging.NOTSET
    elif level == 'DEBUG': 
        out = logging.DEBUG
    elif level == 'INFO': 
        out = logging.INFO
    elif level == 'WARN': 
        out = logging.WARN
    elif level == 'ERROR': 
        out = logging.ERROR
    elif level == 'CRITICAL': 
        out = logging.CRITICAL
    else: 
        out = logging.NOTSET
    
    return out
