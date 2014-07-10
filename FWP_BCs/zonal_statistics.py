# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# zonal_statistics.py
# Created on: 2014-06-23 15:01:32.00000
#   (generated by ArcGIS/ModelBuilder)
# Description: 
# ---------------------------------------------------------------------------

# Import arcpy module
import arcpy

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")


# Local variables:
nedraw10m_fwp = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\nedraw10m_fwp"
FWPvert_grid1000_UTMft_shp = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\FWPvert_grid1000_UTMft.shp"
FWPvert_nodes1000_UTMft_shp = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\FWPvert_nodes1000_UTMft.shp"
ZonalSt_shp1 = "C:\\Users\\pfjuckem\\Documents\\ArcGIS\\Default.gdb\\ZonalSt_shp1"

# Process: Zonal Statistics
arcpy.gp.ZonalStatistics_sa(FWPvert_grid1000_UTMft_shp, "FID", nedraw10m_fwp, ZonalSt_shp1, "MINIMUM", "DATA")

# Process: Extract Multi Values to Points
arcpy.gp.ExtractMultiValuesToPoints_sa(FWPvert_nodes1000_UTMft_shp, "C:\\Users\\pfjuckem\\Documents\\ArcGIS\\Default.gdb\\ZonalSt_shp1 NEDmin1kft", "NONE")

