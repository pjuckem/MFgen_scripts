# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Code to generate point shapefiles of model nodes for CHDs.  Designed for
# importing into GWVistas.  Future revisions should incorporate XML input
# file and use of Flopy to read DIS file directly to generate grid (talk w/
# BRC implementation in GlacKmaker.  Will also need to incorporate functionality
# for deciding upon layer assignment (Lake Michigan).
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

env.overwriteOutput = True  # overwrite existing output files?

# Local variables:
minelev_raster = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\nedmin1kft"
CHD_clip = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\FWPvert_CHD_clip.shp"
NHDFlowline = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\NHDPlusV21FWP\\NHDFlowline_FWPregion_editstraight_UTMft.shp"
NHDwaterbody = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\NHDPlusV21FWP\\NHDWaterbody_merge_FWPregion_UTMft.shp"
CHD_erase = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\FWPvert_CHD_erase.shp"
buff_dist = "500 Feet"  # use 1/2 cell size
nodes_shp = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\FWPvert_nodes1000_UTMft.shp"
grid_shp = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\FWPvert_grid1000_UTMft.shp" #output from ZonalStatistics; Input to later steps
SFR_cells = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\SFR_AndyFix\\SFR_cellinfo_FWPvert1000ft.shp"
NED = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\nedraw10m_fwp"
clipFL = "C:\\Users\\pfjuckem\\Documents\\ArcGIS\\Default.gdb\\NHDFlowline_FWPvert_CHDclip"
erasedFL = "C:\\Users\\pfjuckem\\Documents\\ArcGIS\\Default.gdb\\NHDFlowline_FWPvert_CHDlines"
buffFL = "C:\\Users\\pfjuckem\\Documents\\ArcGIS\\Default.gdb\\NHDFlowline_FWPvert_CHDbuff"
dissolv_buffFL = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\NHDFlowline_FWPvert_CHDbufdis.shp"
CHD_FL_clipnodes = "C:\\Users\\pfjuckem\\Documents\\ArcGIS\\Default.gdb\\NHDFlowline_FWPvert_CHDclipnodes"
CHD_FL_nodes = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\NHDFlowline_FWPvert_CHDnodes.shp"
clipWB = "C:\\Users\\pfjuckem\\Documents\\ArcGIS\\Default.gdb\\NHDwaterbody_FWPvert_CHDclip"
erasedWB = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\NHDwaterbody_FWPvert_CHD_UTMft.shp"
#buffWB = "C:\\Users\\pfjuckem\\Documents\\ArcGIS\\Default.gdb\\NHDwaterbody_FWPvert_CHDbuff"
#dissolv_buffWB = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\NHDwaterbody_FWPvert_CHDbufdis.shp"
CHD_WB_clipnodes = "C:\\Users\\pfjuckem\\Documents\\ArcGIS\\Default.gdb\\NHDwaterbody_FWPvert_CHDclipnodes"
CHD_WB_nodes = "D:\\PFJData2\\Projects\\NAQWA\\Cycle3\\FWP\\ARC\\NHDwaterbody_FWPvert_CHDnodes.shp"

# Process Zonal Statistics on grid cells to generate new NED raster to match model grid, with minimum elevations
# within the grid cell.  This takes a while, so comment it out if need to re-run the script.

#print "generating raster of minimum elevation per model grid cell. \n"
#arcpy.gp.ZonalStatistics_sa(grid_shp, "FID", NED, minelev_raster, "MINIMUM", "DATA")

# Process NHDflowlines to produce a shapefile of corresponding NODES for the model that will represent River CHD cells
print "Generating point shapefile of model nodes matching boundary rivers for CHD package."
print "Clipping to CHD lines."
arcpy.Clip_analysis(NHDFlowline, CHD_clip, clipFL, "")
arcpy.Erase_analysis(clipFL, CHD_erase, erasedFL, "")
print "Buffering CHD lines (1/2 cell width is a common entry value)."
arcpy.Buffer_analysis(erasedFL, buffFL, buff_dist, "FULL", "ROUND", "NONE", "")
print "Dissolving buffer."
arcpy.Dissolve_management(buffFL, dissolv_buffFL, "", "", "MULTI_PART", "DISSOLVE_LINES")
print "Clipping model nodes to CHD lines."
arcpy.Clip_analysis(nodes_shp, dissolv_buffFL, CHD_FL_clipnodes, "")  # clip nodes matching flowlines targeted for CHD
print "Remove flowline CHD nodes that overlap with SFR cells"
arcpy.Erase_analysis(CHD_FL_clipnodes, SFR_cells, CHD_FL_nodes, "")
print "Extracting raster values to CHD river nodes."
arcpy.gp.ExtractMultiValuesToPoints_sa(CHD_FL_nodes, [[minelev_raster, "NEDmin1K_m"]], "NONE")  # assign min elev to nodes
print "add field and calculate new value (m to ft). \n"
arcpy.AddField_management(CHD_FL_nodes, "NEDmin1Kft", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.CalculateField_management(CHD_FL_nodes, "NEDmin1Kft", '!NEDmin1K_m! * 3.28084', "PYTHON_9.3")

# Process NHDwaterbodies to produce a shapefile of corresponding NODES for the model that will represent lake and
# wetland CHD cells
print "Generating point shapefile of model nodes matching boundary water bodies for CHD package."
print "Clipping to CHD water bodies."
arcpy.Clip_analysis(NHDwaterbody, CHD_clip, clipWB, "")
arcpy.Erase_analysis(clipWB, CHD_erase, erasedWB, "")  # May need to manually edit after this step
print "Clipping model nodes to CHD water bodies."
arcpy.Clip_analysis(nodes_shp, erasedWB, CHD_WB_clipnodes, "")  # clip nodes matching flowlines targeted for CHD
print "Remove waterbody CHD nodes that overlap with SFR cells"
arcpy.Erase_analysis(CHD_WB_clipnodes, SFR_cells, CHD_WB_nodes, "")
print "Extracting raster values to CHD water body nodes."
arcpy.gp.ExtractMultiValuesToPoints_sa(CHD_WB_nodes, [[minelev_raster, "NEDmin1K_m"]], "NONE")  # assign min elev to nodes
print "add field and calculate new value (m to ft). \n"
arcpy.AddField_management(CHD_WB_nodes, "NEDmin1Kft", "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.CalculateField_management(CHD_WB_nodes, "NEDmin1Kft", '!NEDmin1K_m! * 3.28084', "PYTHON_9.3")

print "process completed! \n"
print "Check the output point shapefiles (FL & WB) and refine CHD_erase or buff_dist as necessary and re-run. "
print "Then, import CHD FL and WB nodes into GWV and use NEDmin1Kft as the input for stage elevation."

arcpy.CheckInExtension("spatial")

#  Next step: Inspect CHD_FL_nodes and CHD_WB_nodes for spurious nodes, and remove them or refine CHD_erase and re-run.
#  Then, import CHD_FL_nodes and CHD_WB_nodes into GWVistas as CHD boundary cells with "NEDmin1Kft" as elevation parameter.