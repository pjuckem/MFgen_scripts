__author__ = 'pfjuckem, aleaf'
'''
Route MODFLOW UZF Package groundwater discharge at waterbodies to SFR segments, using catchment info from NHDplus v2
inputs:
NHDPlus v2 waterbody files (e.g. NHDPlusV21_GL_04_NHDPlusCatchments_05.7z; available from http://www.horizon-systems.com/NHDPlus/NHDPlusV2_04.php)
shapefiles of model grid cells, model domain, and SFR cells (all in same projection)

requirements:
arcpy
GISio and GISops, from aleaf/GIS_utils on github
(these require the fiona, shapely, and pandas packages)

Could re-write for total arcpy depencancy, but FWP model was too large for some SFRmaker analysis apps that depended
upon arcpy.  The GIS_utils handled FWP better.
'''
import numpy as np
import arcpy
import os
import sys
GIS_utils_path = 'D:/PFJData2/Programs/GIS_utils'
if GIS_utils_path not in sys.path:
    sys.path.append(GIS_utils_path)
    #print sys.path
import GISio
import GISops

import pandas as pd

# NHDPlus v2 catchment files (list)
catchments = ['D:/ARC/Basemaps/National/Hydrography/NHDPlusV21/NHDPlusGL/NHDPlus04/NHDPlusV21_GL_04_NHDPlusCatchments_05/NHDPlusGL/NHDPlus04/NHDPlusCatchment/Catchment.shp',
              'D:/ARC/Basemaps/National/Hydrography/NHDPlusV21/NHDPlusMS/NHDPlus07/NHDPlusV21_MS_07_NHDPlusCatchment_01/NHDPlusMS/NHDPlus07/NHDPlusCatchment/Catchment.shp']
# NHDplus v2 waterbodies (no longer a list).  Note: formerly NHDPlus v2 catchment files (list)
waterbodies = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/NHDPlusV21FWP/NHDWaterbody_merge_FWPregion_UTMft.shp'
# input shapefile (should all be in same projection!)
MFdomain = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/FWPvert_domain_UTMft.shp'
MFgrid = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/FWPvert_grid1000_UTMft.shp'
MFnodes = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/FWPvert_nodes1000_UTMft.shp'
SFR_shapefile = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/SFR_AndyFix/SFR_cellinfo_FWPvert1000ft.shp'
# temporary directories
catchmentdir = 'D:/ARC/Basemaps/National/Hydrography/NHDPlusV21/'
workingdir = "D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/"

# output
out_IRUNBND = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/FWPvert_IRUNBND.dat'
out_IRUNBND_shp = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/FWPvert_IRUNBND.shp'

# initialize the arcpy environment
arcpy.env.workspace = os.getcwd()
arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False
#arcpy.CheckOutExtension("spatial") # Check spatial analyst license
'''
print 'removing old temporary and results files'
if arcpy.Exists(catchmentdir + 'catchment_merge.shp'):
    arcpy.Delete_management(catchmentdir + 'catchment_merge.shp')
if arcpy.Exists(catchmentdir + 'catchment_mergeUTMft.shp'):
    arcpy.Delete_management(catchmentdir + 'catchment_mergeUTMft.shp')
if arcpy.Exists(workingdir + 'catchment_FWP.shp'):
    arcpy.Delete_management(workingdir + 'catchment_FWP.shp')
if arcpy.Exists(workingdir + 'waterbodies_FWP.shp'):
    arcpy.Delete_management(workingdir + 'waterbodies_FWP.shp')
if arcpy.Exists(workingdir + 'catchment_WBclip.shp'):
    arcpy.Delete_management(workingdir + 'catchment_WBclip.shp')
if arcpy.Exists(workingdir + 'SFR_watbodies.shp'):
    arcpy.Delete_management(workingdir + 'SFR_watbodies.shp')
if arcpy.Exists(workingdir + 'MFgrid_watbodies.shp'):
    arcpy.Delete_management(workingdir + 'MFgrid_watbodies.shp')

# preprocessing
print 'merging NHDPlus catchment files:'
for f in catchments:
    print f
if len(catchments) > 1:
    arcpy.Merge_management(catchments, catchmentdir + 'catchment_merge.shp')
else:
    arcpy.CopyFeatures_management(catchments[0], catchmentdir + 'catchment_merge.shp')

print '\nreprojecting to {}.prj'.format(SFR_shapefile[:-4])
arcpy.Project_management(catchmentdir + 'catchment_merge.shp', catchmentdir + 'catchment_mergeUTMft.shp', SFR_shapefile[:-4] + '.prj')
'''
print 'clipping catchments and waterbodies to {}'.format(MFdomain)
arcpy.Clip_analysis(catchmentdir + 'catchment_mergeUTMft.shp', MFdomain, workingdir + 'catchment_FWP.shp')
arcpy.Clip_analysis(waterbodies, MFdomain, workingdir + 'waterbodies_FWP.shp')
# Clipping is not enough.  Need to isolate individual waterbodies within each catchment
print 'clipping waterbodies by catchments'
arcpy.Intersect_analysis([workingdir + 'waterbodies_FWP.shp', workingdir + 'catchment_FWP.shp'], workingdir + 'WB_cmt_clip.shp')
# arcpy.Clip_analysis(workingdir + 'waterbodies_FWP.shp', workingdir + 'catchment_FWP.shp', workingdir + 'WB_cmt_clip.shp') Only clips perimeter, not interior catchments -- odd.

# Need to generate a unique ID that can be maintained during the spatial join b/c COMID overlaps watersheds
print 'Creating Unique IDs'
arcpy.AddField_management(workingdir + 'WB_cmt_clip.shp', 'WBID', "LONG", "", "", "", "", "NULLABLE", "REQUIRED", "")
arcpy.CalculateField_management(workingdir + 'WB_cmt_clip.shp', 'WBID', '!FID! + 1', "PYTHON_9.3")

print 'performing spatial join of waterbodies to SFR cells...'
arcpy.SpatialJoin_analysis(SFR_shapefile, workingdir + 'WB_cmt_clip.shp', workingdir + 'SFR_watbodies.shp')
# Note: Spatial join is set as one-to-one, so some water bodies are being left behind and not routing to SFR segments.
# Need to change this to a one-to-many join (or an intersect), but then have to figure out how to handle this below.

#print 'and to model grid (this may take awhile)...'
#arcpy.SpatialJoin_analysis(MFgrid, workingdir + 'WB_cmt_clip.shp', workingdir + 'MFgrid_watbodies.shp')
# Currently taking 48 hrs.
# Might try an intersection instead, as intersection takes advantage of tiling (splitting into smaller subsets)
# Intersecting will retain all attributes, but it will discard cells that don't overlap with waterbodies, which seems OK
print 'Intersecting model nodes with waterbodies'
arcpy.Intersect_analysis([MFnodes, workingdir + 'WB_cmt_clip.shp'], workingdir + 'MFnodes_watbodies.shp')


# now figure out which SFR segment each waterbody should drain to
print 'reading {} into pandas dataframe...'.format(os.path.join(workingdir, 'SFR_watbodies.shp'))
SFRwatbods = GISio.shp2df(os.path.join(workingdir, 'SFR_watbodies.shp'))

print 'assigning an SFR segment to each waterbody... (this may take awhile)'
intersected_watbods = list(np.unique(SFRwatbods.WBID))
segments_dict = {}
for wb in intersected_watbods:
    try:
        # if one waterbody intersected multiple segments, select the most common (mode) segment
        segment = SFRwatbods[SFRwatbods.WBID == wb].segment.mode()[0]
    except: # pandas crashes if mode is called on df of length 1 or 2
        segment = SFRwatbods[SFRwatbods.WBID == wb].segment[0]
    segments_dict[wb] = segment
    # can also use values_count() to get a frequency table for segments (reaches) in each catchment

print 'building UZF package IRUNBND array from {}'.format(MFnodes)
# get dimensions of grid and compute unique cell ID
MFnodesDF = GISio.shp2df(MFnodes)
nrows, ncols = np.max(MFnodesDF.row), np.max(MFnodesDF.column)
MFnodesDF['cellnum'] = (MFnodesDF.row-1)*ncols + MFnodesDF.column  # as per SFRmaker algorithm line 297 of SFR_plots.py

MFnodes_watbod = GISio.shp2df(os.path.join(workingdir + 'MFnodes_watbodies.shp'), geometry=True)
MFnodes_watbod['cellnum'] = (MFnodes_watbod.row-1)*ncols + MFnodes_watbod.column
MFnodes_watbod.index = MFnodes_watbod.node
# nrows, ncols = np.max(MFnodes_watbod.row), np.max(MFnodes_watbod.column)
# nrows, ncols = np.max(MFnodes.row), np.max(MFnodes.column)

# make new column of SFR segment for each waterbody
# Uses the WBID-to-Segments dictionary from SFRwaterbods and applies it to MFnodes_watbodies.shp
# That is, it assigns segments to the rest of the water body area (all nodes that intersected the waterbody)
MFnodes_watbod['segment'] = MFnodes_watbod.WBID.apply(segments_dict.get).fillna(0)

print 'assigning an SFR segment to each node of the model... (this may take awhile)'
cellnumbers = list(np.unique(MFnodes_watbod.cellnum))
cellnum_dict = {}
for cn in cellnumbers:
    try:
        # if multiple segments per cellnum, select the most common (mode)
        segment = MFnodes_watbod[MFnodes_watbod.cellnum == cn].segment.mode()[0]
        segment = int(segment)
    except:  # pandas crashes if mode is called on df of length 1 or 2
        segment = MFnodes_watbod[MFnodes_watbod.cellnum == cn].segment[0]
        segment = int(segment.max()) # when cellnums have 2 segments. This selects the most downstream Seg and converts to int
    cellnum_dict[cn] = segment

# make new column of SFR segment for each grid cell
# Uses the cellnum-to-Segments dictionary from MFnodes_watbodies.shp and applies it to MFnodes (array of every node for the model)
# That is, it assigns segments to all model nodes that were connected previously
# fills with zero if no match found
MFnodesDF['segment'] = MFnodesDF.cellnum.apply(cellnum_dict.get).fillna(0)

print 'writing {}'.format(out_IRUNBND)
#IRUNBND = np.zeros_like(MFnodes)
# need some way to change zeros to segment values.
IRUNBND = np.reshape(MFnodesDF['segment'].sort_index().values, (nrows, ncols))
# IRUNBND mus not be a uniform array...
#IRUNBND = IRUNBND.astype(np.int, copy=False)
np.savetxt(out_IRUNBND, IRUNBND, fmt='%i', delimiter=' ')

print 'writing {}'.format(out_IRUNBND_shp)
#df, shpname, geo_column, prj
GISio.df2shp(MFnodes_watbod,
             os.path.join(workingdir + 'UZF_segments.shp'),
             'geometry',
             os.path.join(workingdir + 'MFnodes_watbodies.shp')[:-4]+'.prj')

#MFnodes_watbod_dissolved = GISops.dissolve_df(MFnodes_watbod, 'segment')
# crashing here -- need to figure out why ('geometry' = key_error)
#GISio.df2shp(MFnodes_watbod_dissolved,
#             os.path.join(workingdir + 'UZF_segments_dissolved.shp'),
#             'geometry',
#             os.path.join(workingdir + 'MFnodes_watbodies.shp')[:-4]+'.prj')
#GISio.df2shp(MFnodes_watbod_dissolved,
#             os.path.join(workingdir + 'UZF_segments_dissolved.shp'),
#             'shape',
#             os.path.join(workingdir + 'MFnodes_watbodies.shp')[:-4]+'.prj')