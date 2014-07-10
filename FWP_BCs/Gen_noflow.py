# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Code to generate polygon shapefiles of inactive area of model.  Designed for
# importing into GWVistas.  Future revisions should incorporate XML input
# file and use Flopy to read DIS file directly to generate grid (talk w/ BRC RE implementation
# in GlacKmaker.  May also need to incorporate functionality
# for adjusting by layer (dipping beds).
# Would also be good to add a script to adjust the bottom elevation, and should
# follow-up with Andy on how they did that in SFRmaker. Workaround for now is GWV.
# ---------------------------------------------------------------------------

import os
try:
    import arcpy
    from arcpy import env
except:
    print ('\n'
           'ERROR: Unable to import the "ARCPY" module. \n\n'
           'The program will not work without this module. \n'
           'Please ensure that ARC9.3 or newer is installed and \n'
           'the python path includes a path to ARCPY. \n\n')

env.overwriteOutput = True  # overwrite existing output files?
write_shapefiles = True

# Local variables:
outGDB = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\GenFWPvert.gdb"
junkGDB = "C:\\Users\\pfjuckem\\Documents\\ArcGIS\\Default.gdb"
CHD_FL_nodes = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\NHDFlowline_FWPvert_CHDnodes.shp"
CHD_WB_nodes = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\NHDwaterbody_FWPvert_CHDnodes.shp"
domain = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\FWPvert_domain_UTMft.shp"
grid_shp = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\FWPvert_grid1000_UTMft.shp" #output from ZonalStatistics; Input to later steps
SFR_cells = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\SFR_AndyFix\\SFR_cellinfo_FWPvert1000ft.shp"
select_cells = junkGDB + "\\select_cells"
CHD_dissolved_poly = junkGDB + "\\CHD_dispoly"
erased_domain = junkGDB + "\\erased_domain"
erased_singles = junkGDB + "\\erased_singles"
CHD_WB_clipnodes = junkGDB + "\\NHDwaterbody_FWPvert_CHDclipnodes"
NF_area = "\\FWPvert_NF_area"
#NF_area = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\FWPvert_NF_area.shp"

# Check if files exist, and create/delete them as appropriate
if arcpy.Exists(os.path.dirname(outGDB) + NF_area + ".shp"):  # os.path.dirname removes the GDB designation
    arcpy.Delete_management(os.path.dirname(outGDB) + NF_area + ".shp")
try:
    arcpy.Exists(outGDB)
    if arcpy.Exists(outGDB + NF_area):
        arcpy.Delete_management(outGDB + NF_area)
except:
    arcpy.CreateFileGDB_management(outGDB)
try:
    arcpy.Exists(junkGDB)
    if arcpy.Exists(select_cells):
        arcpy.Delete_management(select_cells)
    if arcpy.Exists(CHD_dissolved_poly):
        arcpy.Delete_management(CHD_dissolved_poly)
    if arcpy.Exists(erased_domain):
        arcpy.Delete_management(erased_domain)
    if arcpy.Exists(erased_singles):
        arcpy.Delete_management(erased_singles)
    if arcpy.Exists(CHD_WB_clipnodes):
        arcpy.Delete_management(CHD_WB_clipnodes)
except:
    arcpy.CreateFileGDB_management(junkGDB)

# Process previously generated shapefiles to produce a shapefile of the inactive area of the model
print "Selecting SFR cells near CHD boundaries"
arcpy.MakeFeatureLayer_management(SFR_cells, "SFR_cells_lyr")
arcpy.SelectLayerByLocation_management("SFR_cells_lyr", "WITHIN_A_DISTANCE", CHD_FL_nodes, "2000", "ADD_TO_SELECTION")
arcpy.SelectLayerByLocation_management("SFR_cells_lyr", "WITHIN_A_DISTANCE", CHD_WB_nodes, "2000", "ADD_TO_SELECTION")
print "Matching CHD nodes to grid cells."
arcpy.MakeFeatureLayer_management(grid_shp, "grid_lyr")
arcpy.SelectLayerByLocation_management("grid_lyr", "INTERSECT", CHD_FL_nodes)
arcpy.SelectLayerByLocation_management("grid_lyr", "INTERSECT", CHD_WB_nodes, "", "ADD_TO_SELECTION")
print "Merging CHD and SFR cells and dissolving to create a polygon of the selected cells."
arcpy.Merge_management(["SFR_cells_lyr", "grid_lyr"], select_cells)
arcpy.MakeFeatureLayer_management(select_cells, "select_cells_lyr")
arcpy.Dissolve_management("select_cells_lyr", CHD_dissolved_poly, "", "", "MULTI_PART", "DISSOLVE_LINES")
print "Removing (erase) the CHD polygon from the model domain to split the domain"
arcpy.Erase_analysis(domain, CHD_dissolved_poly, erased_domain, "")
arcpy.MultipartToSinglepart_management(erased_domain, erased_singles)
print "Selecting the parts of the domain west of the CHD boundaries to create a polygon of the desired NF area"
arcpy.MakeFeatureLayer_management(erased_singles, "erased_lyr")
arcpy.SelectLayerByLocation_management("erased_lyr", "INTERSECT", arcpy.PointGeometry(arcpy.Point(906880, 16342466)))
arcpy.SelectLayerByLocation_management("erased_lyr", "INTERSECT", arcpy.PointGeometry(arcpy.Point(868835, 15853314)), "", "ADD_TO_SELECTION")
arcpy.CopyFeatures_management("erased_lyr", outGDB + NF_area)
if write_shapefiles:
    print "writing output to shapefiles"
    if arcpy.Exists(os.path.dirname(outGDB) + NF_area + ".shp"):
        arcpy.Delete_management(os.path.dirname(outGDB) + NF_area + ".shp")
    arcpy.FeatureClassToShapefile_conversion(outGDB + NF_area, os.path.dirname(outGDB))
print "process completed! \n"

#  Next step: Import NF_area into GWVistas as NF boundary cells.