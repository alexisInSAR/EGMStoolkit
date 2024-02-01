#! /usr/bin/env python3
# -*- coding: iso-8859-1 -*-
"""
Module to get the EGMS-burst IDs**

The module contains some functions to get the EGMS-burst IDs , required by to run `EGMStoolkit`.

    (From `EGMStoolkit` package)

    The code is from `HERE <https://land.copernicus.eu/en/technical-library/egms-product-description-document/@@download/file>`_.  

Changelog:
    * 0.2.0: Script structuring, Jan. 2024, Alexis Hrysiewicz
    * 0.1.0: Initial version, Nov. 2023

"""

import math

## S1 IW timing parameters (NB! Must be 64-bit precision or higher!)
TPRE  = 2.298687
TBEAM = 2.758273
TORB  = 12*86400/175

def get_egms_burst_id(r, bc, swath, polarization):
        return "{:03d}-{:04d}-{:s}-{:s}".format(r, bc, swath, polarization)
def get_esa_burst_cycle_id(delta_tb):
    return math.floor((delta_tb - TPRE)/TBEAM) + 1

def get_egms_burst_cycle_id(r, anx_time):
    # ESA burst cycle ID of first complete burst cycle in relative orbit "r".
    # NB! This calculation assumes that (r-1)*TORB is not an exact multiple
    # of TBEAM, which is true for all 175 S1 relative orbits.
    
    id_esa_first = get_esa_burst_cycle_id((r-1)*TORB) + 1
    # ESA burst cycle ID for "anx_time" seconds into relative orbit "r".
    # Note that "anx_time" is sensing time of middle of a burst.has to be
    id_esa = get_esa_burst_cycle_id((r-1)*TORB + anx_time)
    # EGMS burst ID is decomposed into (relative orbit, burst cycle within orbit).
    return (r, id_esa - id_esa_first + 1)

if __name__ == "__main__":
    ## Example: burst covering Mulhouse in the EGMS ORR ascending data.
    ## Product: S1B_IW_SLC__1SDV_20180902T172257_20180902T172324_012539_01721C_6F69.SAFE
    ## Annotation XML file in <Product>/annotation/:
    ## s1b-iw2-slc-vv-20180902t172258-20180902t172323-012539-01721c-005.xml

    # Relative orbit can be found, e.g., in <product>/manifest.safe.
    r = 88
    # The following timing for first line of burst can be found in XML as
    # <swathTiming/burstList/burst> (item #7)
    anx_time = 775.1918283259
    # We need to adjust this to middle of burst for this calculation.
    # Burst size is found in XML as
    #   <swathTiming/linesPerBurst>
    az_size = 1508
    # Azimuth sampling interval is found in XML as
    #   <imageAnnotation/imageInformation/azimuthTimeInterval>
    dt_az = 0.0020555563
    # Adjust timing reference to middle of burst, where
    # zero doppler time is almost equal to sensing time.
    # Note: it is sufficient that this calculation is accurate to within
    # about 0.1 sec, so any line near middle of burst is fine.
    anx_mid = anx_time + az_size/2*dt_az
    # ESA burst ID calculation
    #   Should be equal to the following field, that will be present
    #   in S1 IW SLC products from IPF v3.40.
    #     <swathTiming/burstList/burst/burstID>
    bc_id_esa = get_esa_burst_cycle_id((r-1)*TORB + anx_mid)
    assert bc_id_esa == 187151
    # EGMS burst cycle ID
    bc_id_egms = get_egms_burst_cycle_id(r, anx_mid)
    assert bc_id_egms == (88, 282)
    # EGMS unique burst ID
    uid_egms = get_egms_burst_id(*bc_id_egms, "IW2", "VV")
    assert uid_egms == "088-0282-IW2-VV"