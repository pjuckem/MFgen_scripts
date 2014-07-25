__author__ = 'pfjuckem, aleaf'
'''
Program to write the 3 primary arrays for UZF (IUZFBND, FINF, IRUNBND) in order to run UZF and route discharge
from waterbodies to SFR segments.
Inputs:
1. NHDPlus v2 waterbody and catchment files:
(e.g. NHDPlusV21_GL_04_NHDPlusCatchments_05.7z; available from http://www.horizon-systems.com/NHDPlus/NHDPlusV2_04.php)
Catchments are needed because water bodies (wetlands) can span several catchments, complicating decisions as to which
SFR segments to route into.
2. NHDPlus v
2. shapefiles of model grid nodess, model domain, and SFR cells (all in same projection)

Dependancies:
arcpy, numpy
GISio and GISops, from aleaf/GIS_utils on github
(these require the fiona, shapely, and pandas packages)

Limitations: This method assumes that the entire area of any waterbody that overlaps with an SFR cell is able to route
water to that SFR segment (isolated waterbodies are not routed). It also assumes that the potential recharge (FINF)
within 'SwampMarsh' waterbodies (wetlands) is the same as that for land.  That is, without information on the degree of
saturation or transpiration, there is little to justify deviation from a standard recharge array. Application of the
Soil Water Balance (SWB) code will ameliorate this limitation.  Recharge to waterbodies noted as 'Lake/Pond' and
'Reservoir' are assigned potential recharge rates (FINF) of precip minus evap.

Future plans:
1. Auto-generate the entire UZF file instead of just the 3 primary arrays.
2. Read-in input from XML
3. Re-write to utilize Geopandas instead of GISio.
4. Read directly from DIS using flopy instead of requiring shapefile representation of domain and nodes. Not sure reading
   SFR from the SFR package will be realistic at this time.
'''
import numpy as np
import arcpy
import os
import sys
import flopy.modflow as fpmf
import flopy.utils as fputl
from geopandas import GeoDataFrame
GIS_utils_path = 'D:/PFJData2/Programs/GIS_utils'
if GIS_utils_path not in sys.path:
    sys.path.append(GIS_utils_path)
    #print sys.path
import GISio
import GISops
import pandas as pd
import sys
import xml.etree.ElementTree as ET

try:
    xmlname=sys.argv[1]
except:
    xmlname='FWPinput.xml'
inpardat = ET.parse(xmlname)
inpars = inpardat.getroot()

overwrite=inpardat.findall('.//overwrite')[0].text
modeldomainshp=inpardat.findall('.//modexistgridshp')[0].text
modelnodeshp=inpardat.findall('.//modexistnodesshp')[0].text


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
recharge = 0.002 # nice round number; 8.77 in/yr, which seems OK for this area.
precip = 0.007301 # 32 in/yr; common # used for WI
evaporation = 0.006845 # 30 in/yr ; rough average from Farnsworth, 1970s

# temporary directories
catchmentdir = 'D:/ARC/Basemaps/National/Hydrography/NHDPlusV21/'
workingdir = "D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/"
mfdir = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/MODFLOW/'
mfname = 'FWPvert'
bas = os.path.join(mfdir + mfname + '.bas')

# output
out_IRUNBND = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/FWPvert_IRUNBND.dat'
out_IRUNBND_shp = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/ARC/FWPvert_IRUNBND.shp'
out_FINF = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/temp/FWPvert_FINF.dat'
out_iuzfbnd = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/temp/FWPvert_IUZFBND.dat'

# initialize the arcpy environment
arcpy.env.workspace = os.getcwd()
arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False
#arcpy.CheckOutExtension("spatial") # Check spatial analyst license

#def get_cellnum(r, c, nrows=nrows, ncols=ncols):
#    cellnum = (r-1) * ncols + c
#    return cellnum

def intarrayreader(infile, skiplines, NROWS, NCOLS):
    indat = []
    infile_dat = open(infile, 'r').readlines()
    skp = 0
    for line in infile_dat:
        if (skp >= skiplines and len(indat) < (ncols * nrows)):
            tmp = line.strip().split()
            indat.extend(tmp)
        skp += 1
    indat = np.array(indat).astype(int)
    indat = indat.reshape(NROWS, NCOLS)
    return indat
'''
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

print 'clipping catchments and waterbodies to {}'.format(MFdomain)
arcpy.Clip_analysis(catchmentdir + 'catchment_mergeUTMft.shp', MFdomain, workingdir + 'catchment_FWP.shp')
arcpy.Clip_analysis(waterbodies, MFdomain, workingdir + 'waterbodies_FWP.shp')

# Now isolate individual waterbodies within each catchment
print 'clipping waterbodies by catchments'
arcpy.Intersect_analysis([workingdir + 'waterbodies_FWP.shp', workingdir + 'catchment_FWP.shp'], workingdir + 'WB_cmt_clip.shp')
# Note: arcpy.Clip_analysis(workingdir + 'waterbodies_FWP.shp', workingdir + 'catchment_FWP.shp', workingdir +
# 'WB_cmt_clip.shp') only clips perimeter, not interior catchments -- odd.

# Need to generate a unique ID that can be maintained during the spatial join b/c COMID overlaps watersheds
print 'Creating Unique IDs'
arcpy.AddField_management(workingdir + 'WB_cmt_clip.shp', 'WBID', "LONG", "", "", "", "", "NULLABLE", "REQUIRED", "")
arcpy.CalculateField_management(workingdir + 'WB_cmt_clip.shp', 'WBID', '!FID! + 1', "PYTHON_9.3")

print 'performing intersect of waterbodies and SFR cells...'
# Intersect is equivalent to a Spatial Join that uses Join_one_to_many and Keep_Common....but Intersect is much faster
arcpy.Intersect_analysis([SFR_shapefile, workingdir + 'WB_cmt_clip.shp'], workingdir + 'SFR_watbodies.shp')

print 'Intersecting model nodes with waterbodies'
arcpy.Intersect_analysis([MFnodes, workingdir + 'WB_cmt_clip.shp'], workingdir + 'MFnodes_watbodies.shp')
# Note: Intersecting nodes instead of grid prevents the artificial growth of waterbodies in MF. Attempts were made to
# intersect the grid and then evaluate whether the intersected cell area was >X% (eg, 50%) of the cell area.
# This seemed better in some cases (narrow "meanders"), but then lead to some holes in major lakes, such as Winnebago,
# due to how the catchments intersected the waterbodies. In the end , intersecting nodes seemed most robust.
# SpatialJoin was taking >48 hrs for FWP model grid.  Intersecting is much quicker.
'''
#  ########
# all intermediate shapefiles are now created, so can comment out the above code if simply need to re-process the
# shapefiles for output.
# #########

# now figure out which SFR segment each waterbody should drain to
print 'reading {} into pandas dataframe...'.format(os.path.join(workingdir, 'SFR_watbodies.shp'))
SFRwatbods = GISio.shp2df(os.path.join(workingdir, 'SFR_watbodies.shp'))

print 'assigning an SFR segment to each waterbody... (this may take awhile)'
intersected_watbods = list(np.unique(SFRwatbods.WBID))
segments_dict = {}
for wb in intersected_watbods:
    try:
        # if one waterbody intersected multiple segment reaches, select the most common (mode) segment
        segment = SFRwatbods[SFRwatbods.WBID == wb].segment.mode()[0]
    except: # pandas crashes if mode is called on df of length 1 or 2
        segment = SFRwatbods[SFRwatbods.WBID == wb].segment[0]
    segments_dict[wb] = segment

print 'Dimensioning arrays to match {}'.format(MFnodes)
# get dimensions of grid and compute unique cell ID
MFnodesDF = GISio.shp2df(MFnodes, geometry=True)
nrows, ncols = np.max(MFnodesDF.row), np.max(MFnodesDF.column)
MFnodesDF['cellnum'] = (MFnodesDF.row-1)*ncols + MFnodesDF.column  # as per SFRmaker algorithm line 297 of SFR_plots.py

print 'Linking the rest of each water body that did not directly overlap an SFR cell to the appropriate SFR segment'
MFnodes_watbod = GISio.shp2df(os.path.join(workingdir + 'MFnodes_watbodies.shp'), geometry=True)
MFnodes_watbod['cellnum'] = (MFnodes_watbod.row-1)*ncols + MFnodes_watbod.column

# Make new column of SFR segment for each waterbody.
# Uses the WBID-to-segments dictionary from SFRwaterbods and applies it to MFnodes_watbodies.shp.
# That is, it assigns segments to the rest of the water body area (all model nodes that intersected the waterbody).
MFnodes_watbod['segment'] = MFnodes_watbod.WBID.apply(segments_dict.get).fillna(0)

print 'Distinguishing between lakes and wetlands, and assigning and SFR segment to each node of the model... ' \
      '(this may take awhile)'
cellnumbers = list(np.unique(MFnodes_watbod.cellnum))
cellnum_dict = {}
WBtype_dict = {}
for cn in cellnumbers:
    try:
        # if multiple segments per cellnum, select the most common (mode)
        segment = MFnodes_watbod[MFnodes_watbod.cellnum == cn].segment.mode()[0]
        segment = int(segment)
    except:  # pandas crashes if mode is called on df of length 1 or 2
        segment = MFnodes_watbod[MFnodes_watbod.cellnum == cn].segment[0]
        segment = int(segment.max()) # when cellnums have 2 segments. This selects the most downstream Seg and converts to int.
    cellnum_dict[cn] = segment
    # setup the recharge array (FINF)
    WBtype = MFnodes_watbod[MFnodes_watbod.cellnum == cn].FTYPE[0]
    WBtype_dict[cn] = WBtype


# Make new column of SFR segment for each grid node.
# Uses the cellnum-to-segments dictionary from MFnodes_watbodies.shp and applies it to MFnodes (array of every node for the model).
# That is, it assigns segments to all model nodes that were connected previously and fills with zero if no match found.
MFnodesDF['segment'] = MFnodesDF.cellnum.apply(cellnum_dict.get).fillna(0)
MFnodesDF['WBtype'] = MFnodesDF.cellnum.apply(WBtype_dict.get).fillna('Land')
# Construct FINF array. Assign recharge ('FINF') based on water body type (open water = P-E).  Stick with estimated
# recharge for wetlands because with out additional information, it is not possible to know whether they are GW
# discharge or GW recharge areas. Would be good to have estimated RO into lakes, but no idea where that would come from,
# so assume no RO.
MFnodesDF['Recharge'] = MFnodesDF.WBtype.replace(['LakePond', 'Reservoir', 'Land', 'SwampMarsh'],
                                                 [(precip - evaporation), (precip - evaporation), recharge, recharge])

print 'writing {}'.format(out_IRUNBND)
MFnodesDF.sort(columns = 'cellnum', inplace = True)  # Sort by cellnum so that in correct order for saving ascii file.
IRUNBND = np.reshape(MFnodesDF['segment'].values, (nrows, ncols))  # Reshape to grid dimensions
np.savetxt(out_IRUNBND, IRUNBND, fmt='%i', delimiter=' ')
print 'writing {}'.format(out_FINF)
FINF = np.reshape(MFnodesDF['Recharge'].values, (nrows, ncols))
np.savetxt(out_FINF, FINF, fmt='%8.6f', delimiter=' ')
print 'writing {}'.format(out_iuzfbnd)
# read BAS file; where IBOUND <= 0, turn off UZF (set IUZFBND to 0)
# To do: Read in list of other BC packages (eg: what if use DRN instead of CHD), then turn off UZF at those cells.
ibound = intarrayreader(bas, 5, nrows, ncols)
iuzfbnd = np.where(ibound >= 1, ibound, 0)
np.savetxt(out_iuzfbnd, iuzfbnd, fmt='%i', delimiter=' ')

#df, shpname, geo_column, prj
GISio.df2shp(MFnodesDF, out_IRUNBND_shp, 'geometry',
             os.path.join(workingdir + 'MFnodes_watbodies.shp')[:-4]+'.prj')
# this one only prints out the points where waterbodies occur
GISio.df2shp(MFnodes_watbod, os.path.join(workingdir + 'UZF_segments.shp'), 'geometry',
             os.path.join(workingdir + 'MFnodes_watbodies.shp')[:-4]+'.prj')

# Notes:
# Do we need to remove UZF cells that overlap SFR cells?  No, removing these cells would reduce the amount of
# 'potential recharge' applied to the model apriori.  Even if all the recharge is re-discharged within the cell, it
# should be applied b/c most streams don't cover 1000ft.  Plus, it doesn't matter if water is discharged to a SFR or
# UZF cell as they're routed together.  Only remove UZF cells from SFR cells if causes instability.  It shouldn't,
# as SFR cells should have lower STOPs then the land surface used for UZF b/c SFR drills deeper to enforce down-stream
# slopes, and b/c the top of the model, which UZF relies upon, was generated as the mean of the DEM, which seems
# appropriate for minimizing bias.

# To Do:
#
#
#
# 3. Auto-generate a UZF file that reads in each of the arrays by name.
# 4. Read directly from DIS file rather than from shapefiles of grid or nodes.  Read in IBOUND and BC arrays/packages to
# directly with flopy
# 5. Switch to using XML input files.
# 6. Switch to using GeoPandas instead of Andy's GISio because more standardized and available.
# 7. Convert to a Class for future implementation as part of a larger MF model generation process?
# 8. Consider option flags for plotting some of the arrays rather than writing shapefiles. For example, the original
# problem with the IRUNBND array would have been detected earlier had it been plotted with matplotlib.
#


# unused code:
#arcpy.Intersect_analysis([MFgrid, workingdir + 'WB_cmt_clip.shp'], workingdir + 'MFgrid_watbodies.shp')
#arcpy.CalculateAreas_stats(workingdir + 'MFgrid_watbodies.shp', workingdir + 'MFnodes_watbodies.shp')
#cellarea = np.max(MFnodes_watbod.F_AREA)
#keep = MFnodes_watbod['F_AREA'] > (cellarea * 0.5)
#MFnodes_watbod = MFnodes_watbod[keep]