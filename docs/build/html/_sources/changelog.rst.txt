Change log
##########

The different versions are as follows:

* 0.2.12: Add the support of the 2019_2013 release, Nov. 2024, Alexis Hrysiewicz
* 0.2.11: Fix regarding the input and output directory for data gridding, Aug. 2024, Alexis Hrysiewicz
* 0.2.10: Some fixes on the MATLAB script, Apr. 2024, Alexis Hrysiewicz
   * Add the cluster_label parameters into the no-saved parameters
   * Fix the colorscale from -10 to 10 mm/yr (plot methods)
* 0.2.9: Some fixes, Apr. 2024, Alexis Hrysiewicz
   * Fix regarding the cropping mode and L3 data in the wrapper
   * Fix regarding the Track_user and Pass_user options (wrong typo.) in the wrapper
* 0.2.8: Fix regarding the application: forcemode option (wrong typo.) in the wrapper, Apr. 2024, Alexis Hrysiewicz
* 0.2.7: Some changes, Apr. 2024, Alexis Hrysiewicz
   * Add a MATLAB function to import the EGMS data in .csv format (see contrib directory)
   * Add the Folium package to create the map (see EGMSS1ROIapi class)
   * Folium, selenium and pillow Python packages have been added to the requirements
* 0.2.6: Bug fixes regarding the windows system + min. version of GDAL 3.8 + message update, Feb. 2024, Alexis Hrysiewicz
* 0.2.5: Add the interpolation processing for the .vrt file + optional function arguments for "duplicate" point and vrt files, Feb. 2024, Alexis Hrysiewicz
* 0.2.4: Add the possibility to merge the L3 .csv file into a .vrt file and fix the problem with the L2 datasets, Feb. 2024, Alexis Hrysiewicz
* 0.2.3: Add the possibility to merge the L2 .csv file into a .vrt file (but can fail), Feb. 2024, Alexis Hrysiewicz
* 0.2.2: Optimisation of clipping based on ogr2ogr, Feb. 2024, Alexis Hrysiewicz
* 0.2.1: Fix regarding the ID burst selection, Feb. 2024, Alexis Hrysiewicz
   * The value of burst size has been changed to 750 (indead of 1500)
   * Remove the duplicate points for L2 datasets
* 0.2.0: Script structuring and documentation, Jan. 2024, Alexis Hrysiewicz
* 0.1.0: Initial version, Nov. 2023