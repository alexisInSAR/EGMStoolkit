EGMS toolkit
############

**EGMS toolkit** is a set of python scripts to download and manage the InSAR data from `European Ground Motion Service <https://egms.land.copernicus.eu>`_. The toolkit allows:


* to download the data automatically; 
* to merge the files; 
* to clip/crop the datasets.  

**UNDER DEVELOPMENT**

**Release info**: Version 0.2.2 Beta, Feb., 2024

The online documentation can be found `here <https://alexisinsar.github.io/EGMStoolkit/>`_.

Dependencies and installation 
=============================

The requirements are:

* Python 3
* GDAL
* GMT (with GSHHG)

To install the **EGMS toolkit**, 

.. code-block:: bash

    git clone https://github.com/alexisInSAR/EGMStoolkit.git
    pip3 install -e EGMStoolkit

.. note::

    For an installation in protected directories, the path of the Sentinel-Burst-ID map could be modified.

Run the toolkit
===============

There are two ways to use the toolkit (in shell or in Python). 

**The user needs to use the temporary token from the EGMS website. It can be found at the end of download links (see image below). Any download links can be used, the user can use a random download link.**

.. image:: private/example_token.png
    :width: 750px
    :alt: EGMS Token

**Please find an example of the script use in your shell terminal.**

.. code-block:: bash

    EGMStoolkit -l L2a,L2b -r 2018_2022 -t XXXXXXXXXXXXXXXXXXXX -b -6.427059639290446,53.2606655698541,-6.0952332730202095,53.41811986118854 -o ./Output_directory --track 1 --pass Ascending --nomerging -noclipping --quiet --clean

.. note:: 

    The -h option is useful to get a help, i.e., 
    
    .. code-block:: bash
        
        EGMStoolkit -h 

    The --docs option is useful to get the documentation of EGMS-toolkit: i.e., 

    .. code-block:: bash
        
        EGMStoolkit --docs     

**In addition, EGMStoolkit can be used in a Python environment: see the example in the EGMStoolkit documentation.**

Merging the L2 datasets
=======================

Due to the Sentinel-1 acquisition mode, EGMStoolkit offers two different methods of merging: 

* Without deleting of duplicate of measurement points in burst/swath overlaps; 
* With deleting of duplicate of measurement points in burst/swath overlaps based on the convace-hull algorithm.

The method can be selected by modifing (True or False) the variable *__removeduplicate__* in the *constant.py* script. The *__length_threshold__* can be modified in the same script (1000 by default). 

Authors
=======

Alexis Hrysiewicz University College Dublin / iCRAG

Partners
========

.. list-table::
   :widths: 75 75
   :header-rows: 1

   * - University College Dublin 
     - iCRAG
   * - .. image:: private/UCDlogo.png
            :height: 75px
            :alt: UCD Logo
     - .. image:: private/icrag-logo.png
            :height: 75px
            :alt: iCRAG Logo