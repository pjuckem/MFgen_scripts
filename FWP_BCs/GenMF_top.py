# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# GenMF_top.py
# Created on: 2014-05-23 13:30:25.00000
#   (generated by ArcGIS/ModelBuilder)
# Description: 
# ---------------------------------------------------------------------------

try:
    import arcpy
    from arcpy import env
except:
    print ('\n'
           'ERROR: Unable to import the "ARCPY" module. \n\n'
           'The program will not work without this module. \n'
           'Please ensure that ARC9.3 or newer is installed and \n'
           'the python path includes a path to ARCPY. \n\n')

# Check out any necessary licenses
if arcpy.CheckExtension("spatial") == "Available":
    arcpy.CheckOutExtension("spatial")
else:
    print ('ERROR: Spatial Analyst is required for this tool, but \n'
           'the license is unavailable. Please work with your IT \n'
           'staff to ensure that your installation of ARC includes \n'
           'a license for Spatial Analyst. \n')

env.overwriteOutput = True

# Compute mean zonal statistic for model cell from 10m NED
# Local variables:
model_grid_shapefile = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\FWPvert_grid1000_UTMft.shp"
Zone_field = "FID"
input_raster = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\nedraw10m_fwp"
Statistics_type = "MEAN"
Zone_stat_out_raster = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\nedAVE1Kvert"

# Process: Zonal Statistics
print "process zonal statistics"
arcpy.gp.ZonalStatistics_sa(model_grid_shapefile, Zone_field, input_raster, Zone_stat_out_raster, Statistics_type, "DATA")


model_node_shapefile = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\FWPvert_nodes1000_UTMft.shp"
Bilinear_interpolation = "false"

# Process: Extract Multi Values to Points
print "extract multivalues to points"
arcpy.gp.ExtractMultiValuesToPoints_sa(model_node_shapefile, Zone_stat_out_raster, Bilinear_interpolation)

# Process: Add Field
print "add field and calculate new value (m to ft)"
arcpy.AddField_management(model_node_shapefile, "nedAVE_ft", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.CalculateField_management(model_node_shapefile, "nedAVE_ft", '!nedave1kve! * 3.28084', "PYTHON_9.3")
# nedave1kve is the 10-digit abbreviation for the input_raster name
arcpy.CheckInExtension("spatial")

# Next Steps:  Import into GWvistas as top property.