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
import GISio
import GISops

import pandas as pd

# NHDplus v2 waterbodies (no longer a list).  Note: formerly NHDPlus v2 catchment files (list)
waterbodies = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/NHDPlusV21FWP/NHDWaterbody_merge_FWPregion_UTMft.shp'
# input shapefile (should all be in same projection!)
MFdomain = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/FWPvert_domain_UTMft.shp'
MFgrid = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/FWPvert_grid1000_UTMft.shp'
SFR_shapefile = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/SFR_AndyFix/SFR_cellinfo_FWPvert1000ft.shp'
# temporary directories
workingdir = "D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/"
# output
out_IRUNBND = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/FWPvert_IRUNBND.dat'
out_IRUNBND_shp = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/FWPvert_IRUNBND.shp'

# initialize the arcpy environment
arcpy.env.workspace = os.getcwd()
arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False
arcpy.CheckOutExtension("spatial") # Check spatial analyst license

if arcpy.Exists(workingdir + 'SFR_watbodies.shp'):
    arcpy.Delete_management(workingdir + 'SFR_watbodies.shp')
if arcpy.Exists(workingdir + 'MFgrid_watbodies.shp'):
    arcpy.Delete_management(workingdir + 'MFgrid_watbodies.shp')

# preprocessing
'''
print 'merging NHDPlus catchemnt files:'
for f in catchments:
    print f
if len(catchments) > 1:
    arcpy.Merge_management(catchments, os.path.join(os.getcwd(), 'temp.shp'))
else:
    arcpy.CopyFeatures_management(catchments[0], os.path.join(os.getcwd(), 'temp.shp'))

print '\nreprojecting to {}.prj'.format(SFR_shapefile[:-4])
arcpy.Project_management(os.path.join(os.getcwd(), 'temp.shp'), os.path.join(os.getcwd(), 'temp2.shp'),
                         SFR_shapefile[:-4] + '.prj')

print 'clipping to {}'.format(MFdomain)
arcpy.Clip_analysis(os.path.join(os.getcwd(), 'temp2.shp'), MFdomain, os.path.join(os.getcwd(), 'catchments.shp'))
'''
print 'performing spatial join of waterbodies to SFR cells...'
arcpy.SpatialJoin_analysis(SFR_shapefile, waterbodies, workingdir + 'SFR_watbodies.shp')
print 'and to model grid (this may take awhile)...'
arcpy.SpatialJoin_analysis(MFgrid, waterbodies, workingdir + 'MFgrid_watbodies.shp')

# now figure out which SFR segment each waterbody should drain to
print 'reading {} into pandas dataframe...'.format(os.path.join(workingdir, 'SFR_watbodies.shp'))
SFRwatbods = GISio.shp2df(os.path.join(workingdir, 'SFR_watbodies.shp'))

print 'assigning an SFR segment to each waterbody... (this may take awhile)'
intersected_watbods = list(np.unique(SFRwatbods.FEATUREID))
segments_dict = {}
for wb in intersected_watbods:
    try:
        segment = SFRwatbods[SFRwatbods.FEATUREID == wb].segment.mode()[0]
    except: # pandas crashes if mode is called on df of length 1
        segment = SFRwatbods[SFRwatbods.FEATUREID == wb].segment[0]
    segments_dict[wb] = segment
    # can also use values_count() to get a frequency table for segments (reaches) in each catchment

print 'building UZF package IRUNBND array from {}'.format(MFgrid)
MFgrid_joined = GISio.shp2df(os.path.join(workingdir + 'MFgrid_watbodies.shp'), geometry=True)
MFgrid_joined.index = MFgrid_joined.node
nrows, ncols = np.max(MFgrid_joined.row), np.max(MFgrid_joined.column)

# make new column of SFR segment for each grid cell
MFgrid_joined['segment'] = MFgrid_joined.FEATUREID.apply(segments_dict.get).fillna(0)

print 'writing {}'.format(out_IRUNBND)
IRUNBND = np.reshape(MFgrid_joined['segment'].sort_index().values, (nrows, ncols))
np.savetxt(out_IRUNBND, IRUNBND, fmt='%i', delimiter=' ')

print 'writing {}'.format(out_IRUNBND_shp)
#df, shpname, geo_column, prj
GISio.df2shp(MFgrid_joined,
             os.path.join(workingdir + 'MFgrid_segments.shp'),
             'geometry',
             os.path.join(workingdir + 'MFgrid_watbodies.shp')[:-4]+'.prj')

MFgrid_joined_dissolved = GISops.dissolve_df(MFgrid_joined, 'segment')

GISio.df2shp(MFgrid_joined_dissolved,
             os.path.join(workingdir + 'MFgrid_segments_dissolved.shp'),
             'geometry',
             os.path.join(workingdir + 'MFgrid_watbodies.shp')[:-4]+'.prj')