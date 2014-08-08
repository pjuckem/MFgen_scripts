__author__ = 'pfjuckem, aleaf'
'''
Program to write the 3 primary arrays for UZF (IUZFBND, IRUNBND, FINF) in order to run UZF and route discharge
from waterbodies to SFR segments.
Inputs:
1. NHDPlus v2 waterbody and catchment files:
(e.g. NHDPlusV21_GL_04_NHDPlusCatchments_05.7z; available from http://www.horizon-systems.com/NHDPlus/NHDPlusV2_04.php)
Catchments are needed because water bodies (wetlands) can span several catchments, complicating decisions as to which
SFR segments to route into.
2. NHDPlus v
3. An XML file pointing to shapefiles of model grid nodess, model domain, and SFR cells (all in same projection)

Dependencies:
arcpy, numpy
GISio and GISops, from aleaf/GIS_utils on github
(these require the fiona, shapely, and pandas packages)

Limitations & assumptions: This method assumes that the entire area of any waterbody that overlaps with an SFR cell is
able to route water to that SFR segment (isolated waterbodies are not routed, thus assumed that GW discharge to these
waterbodies is transpired away). It also assumes that the potential recharge (FINF) within 'SwampMarsh' waterbodies
(wetlands) is the same as that for land.  That is, without apriori information on the degree of saturation or
transpiration, there is little to justify deviation from a standard recharge array (unsat flow is turned off, so FINF
is essentially recharge if no GW discharge occurs in a cell). Application of the Soil Water Balance (SWB) code should
ameliorate this limitation for recharge.  Recharge to waterbodies noted as 'Lake/Pond' and 'Reservoir' are assigned
potential recharge rates (FINF) of precip minus evap. Currently a single value is used for recharge (FINF), precip and
evap. The code may be edited in the future to incorporate spatially distributed P and E.

Future plans:
1. Auto-generate the entire UZF file instead of just the 3 primary arrays.
2.
3. Read other BC files to avoid overlapping UZF with other BCs
4. Re-write to utilize Geopandas instead of GISio.
5. Read directly from DIS using flopy instead of requiring shapefile representation of domain and nodes.
'''
import numpy as np
import arcpy
import os
import pandas as pd
import geopandas as gpd
import sys
import xml.etree.ElementTree as ET
import scipy
import flopy.modflow as fpmf

GIS_utils_path = 'D:/PFJData2/Programs/GIS_utils'
if GIS_utils_path not in sys.path:
    sys.path.append(GIS_utils_path)
#    #print sys.path
import GISio

def tf2flag(intxt):
    # converts text written in XML file to True or False flag
    if intxt.lower() == 'true':
        return True
    else:
        return False

try:
    xmlname = sys.argv[1]
except:
    xmlname = 'FWPvert_uzfGEN_input_080614.xml'
inpardat = ET.parse(xmlname)
inpars = inpardat.getroot()

preproc = tf2flag(inpardat.findall('.//preproc')[0].text)
overwrite = tf2flag(inpardat.findall('.//overwrite')[0].text)
bas = inpardat.findall('.//BASname')[0].text
basskip = int(inpardat.findall('.//BASskiplines')[0].text)
mfdomain_shp = inpardat.findall('.//MFdomain_shp')[0].text
mfnode_shp = inpardat.findall('.//MFnodes_shp')[0].text
sfr_shp = inpardat.findall('.//SFR_shapefile')[0].text
catchments = inpardat.findall('.//catchments')[0].text
waterbodies = inpardat.findall('.//waterbodies')[0].text
recharge = float(inpardat.findall('.//infiltration')[0].text)
precip = float(inpardat.findall('.//precip')[0].text)
evap = float(inpardat.findall('.//evap')[0].text)
out_IUZFBND = inpardat.findall('.//out_IUZFBND')[0].text
out_FINF = inpardat.findall('.//out_FINF')[0].text
out_IRUNBND = inpardat.findall('.//out_IRUNBND')[0].text
junkGDB = inpardat.findall('.//junkGDB')[0].text
modelcatchments = inpardat.findall('.//modelcatchments')[0].text
modelwaterbodies = inpardat.findall('.//modelwaterbodies')[0].text
uniqueWB = inpardat.findall('.//uniqueWB')[0].text
sfr_WB = inpardat.findall('.//SFR_WB')[0].text
nodes_WB = inpardat.findall('.//nodes_WB')[0].text
catchment_dir = inpardat.findall('.//catchmentdir')[0].text
working_dir = inpardat.findall('.//working_dir')[0].text
MFoutdir = inpardat.findall('.//MFoutdir')[0].text

# initialize the arcpy environment
arcpy.env.workspace = working_dir
arcpy.env.overwriteOutput = overwrite
arcpy.env.qualifiedFieldNames = False

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

# preprocessing
if preproc:
    print 'merging NHDPlus catchment files:'
    for f in catchments:
        print f
    if len(catchments) > 1:
        arcpy.Merge_management(catchments, catchment_dir + 'catchment_merge.shp')
    else:
        arcpy.CopyFeatures_management(catchments[0], catchment_dir + 'catchment_merge.shp')
    print '\nreprojecting catchments to {}.prj'.format(sfr_shp[:-4])
    arcpy.Project_management(catchment_dir + 'catchment_merge.shp', catchment_dir + 'catchment_merge_projected.shp', sfr_shp[:-4] + '.prj')

    print 'merging NHDPlus waterbody files:'
    for f in waterbodies:
        print f
    if len(waterbodies) > 1:
        arcpy.Merge_management(waterbodies, catchment_dir + 'waterbodies_merge.shp')
    else:
        arcpy.CopyFeatures_management(waterbodies[0], catchment_dir + 'waterbodies_merge.shp')
    print '\nreprojecting waterbodies to {}.prj'.format(sfr_shp[:-4])
    arcpy.Project_management(catchment_dir + 'waterbodies_merge.shp', catchment_dir + 'waterbodies_merge_projected.shp', sfr_shp[:-4] + '.prj')

    print 'clipping catchments and waterbodies to {}'.format(mfdomain_shp)
    arcpy.Clip_analysis(catchment_dir + 'catchment_merge_projected.shp', mfdomain_shp, working_dir + modelcatchments)
    arcpy.Clip_analysis(catchment_dir + 'waterbodies_merge_projected.shp', mfdomain_shp, working_dir + modelwaterbodies)

    # Now isolate individual waterbodies within each catchment
    print 'clipping waterbodies by catchments'
    arcpy.Intersect_analysis([working_dir + modelwaterbodies, working_dir + modelcatchments], working_dir + uniqueWB)
    # Note: clipping only clipped to the perimeter, not interior catchments -- odd.

    # Need to generate a unique ID that can be maintained during the spatial join b/c COMID overlaps watersheds
    print 'Creating Unique IDs'
    arcpy.AddField_management(working_dir + uniqueWB, 'WBID', "LONG", "", "", "", "", "NULLABLE", "REQUIRED", "")
    arcpy.CalculateField_management(working_dir + uniqueWB, 'WBID', '!FID! + 1', "PYTHON_9.3")

    print 'performing intersect of waterbodies and SFR cells...'
    # Intersect is equivalent to a Spatial Join that uses Join_one_to_many and Keep_Common....but Intersect is much faster
    arcpy.Intersect_analysis([sfr_shp, working_dir + uniqueWB], working_dir + sfr_WB)

    print 'Intersecting model nodes with waterbodies'
    arcpy.Intersect_analysis([mfnode_shp, working_dir + uniqueWB], working_dir + nodes_WB)
    # Note: Intersecting nodes instead of grid prevents the artificial growth of waterbodies in MF. Attempts were made
    # to intersect the grid and then evaluate whether the intersected cell area was >X% (eg, 50%) of the cell area.
    # This seemed better in some cases (narrow "meanders"), but lead to some holes in major lakes, such as Winnebago,
    # due to how the catchments intersected the waterbodies. In the end, intersecting nodes seemed most robust.
    # FYI: SpatialJoin was taking >48 hrs for FWP model grid.  Intersecting is much quicker.

# now figure out which SFR segment each waterbody should drain to
print 'reading {} into geopandas dataframe...'.format(os.path.join(working_dir, sfr_WB))
#SFRwatbods = GISio.shp2df(os.path.join(working_dir, sfr_WB))
SFRwatbods_gdf = gpd.read_file(os.path.join(working_dir, sfr_WB))
SFRwatbods = pd.DataFrame(SFRwatbods_gdf)

print 'assigning an SFR segment to each waterbody... (this may take awhile)'
intersected_watbods = list(np.unique(SFRwatbods.WBID))
#segments_dict = {}
outseg_dict = {}
for wb in intersected_watbods:
    try:
        # if one waterbody intersected multiple segment reaches, select the most common (mode) segment
        #segment = SFRwatbods[SFRwatbods.WBID == wb].segment.mode()[0]
        outseg = SFRwatbods[SFRwatbods.WBID == wb].outseg.mode()[0]
        print 'mode worked!!'
    except: # pandas crashes if mode is called on df of length 1 or 2
        #segment = SFRwatbods[SFRwatbods.WBID == wb].segment[0]
        outseg = SFRwatbods[SFRwatbods.WBID == wb].outseg[0]
    #segments_dict[wb] = segment
    outseg_dict[wb] = outseg

print 'Dimensioning arrays to match {}'.format(mfnode_shp)
# get dimensions of grid and compute unique cell ID
#MFnodesDF = GISio.shp2df(mfnode_shp, geometry=True)
MFnodesDF = gpd.read_file(mfnode_shp)
nrows, ncols = np.max(MFnodesDF.row), np.max(MFnodesDF.column)
MFnodesDF['cellnum'] = (MFnodesDF.row-1)*ncols + MFnodesDF.column  # as per SFRmaker algorithm line 297 of SFR_plots.py

print 'Linking the rest of each water body that did not directly overlap an SFR cell to the appropriate SFR segment'
#MFnodes_watbod = GISio.shp2df(os.path.join(working_dir + nodes_WB), geometry=True)
MFnodes_watbod = gpd.read_file(os.path.join(working_dir + nodes_WB))
MFnodes_watbod['cellnum'] = (MFnodes_watbod.row-1)*ncols + MFnodes_watbod.column

# Make new column of SFR segment for each waterbody.
# Uses the WBID-to-segments dictionary from SFRwaterbods and applies it to MFnodes_watbodies.shp.
# That is, it assigns segments to the rest of the water body area (all model nodes that intersected the waterbody).
#MFnodes_watbod['segment'] = MFnodes_watbod.WBID.apply(segments_dict.get).fillna(0)
MFnodes_watbod['outseg'] = MFnodes_watbod.WBID.apply(outseg_dict.get).fillna(0)

print 'Distinguishing between lakes and wetlands, and assigning and SFR segment to each node of the model... ' \
      '(this may take awhile)'
cellnumbers = list(np.unique(MFnodes_watbod.cellnum))
cellnum_dict = {}
WBtype_dict = {}
for cn in cellnumbers:
    try:
        # if multiple segments per cellnum, select the most common (mode)
        #segment = MFnodes_watbod[MFnodes_watbod.cellnum == cn].segment.mode()[0]
        #segment = int(segment)
        outseg = MFnodes_watbod[MFnodes_watbod.cellnum == cn].outseg.mode()[0]
        outseg = int(outseg)
    except:  # pandas crashes if mode is called on df of length 1 or 2
        #segment = MFnodes_watbod[MFnodes_watbod.cellnum == cn].segment[0]
        #segment = int(segment.max()) # when cellnums have 2 segments. This selects the most downstream Seg and converts to int.
        outseg = MFnodes_watbod[MFnodes_watbod.cellnum == cn].outseg[0]
        outseg = int(outseg.max())
    #cellnum_dict[cn] = segment
    cellnum_dict[cn] = outseg
    # setup the recharge array (FINF)
    WBtype = MFnodes_watbod[MFnodes_watbod.cellnum == cn].FTYPE[0]
    WBtype_dict[cn] = WBtype


# Make new column of SFR segment for each grid node.
# Uses the cellnum-to-segments dictionary from MFnodes_watbodies.shp and applies it to MFnodes (array of every node for the model).
# That is, it assigns segments to all model nodes that were connected previously and fills with zero if no match found.
#MFnodesDF['segment'] = MFnodesDF.cellnum.apply(cellnum_dict.get).fillna(0)
MFnodesDF['outseg'] = MFnodesDF.cellnum.apply(cellnum_dict.get).fillna(0)
MFnodesDF['WBtype'] = MFnodesDF.cellnum.apply(WBtype_dict.get).fillna('Land')

# Construct FINF array. Assign recharge ('FINF') based on water body type (open water = P-E).  Stick with estimated
# recharge for wetlands because with out additional information, it is not possible to know whether they are GW
# discharge or GW recharge areas. Would be good to have estimated RO into lakes, but no idea where that would come from,
# so assume no RO.
MFnodesDF['Recharge'] = MFnodesDF.WBtype.replace(['LakePond', 'Reservoir', 'Land', 'SwampMarsh'],
                                                 [(precip - evap), (precip - evap), recharge, recharge])

print 'writing {}'.format(out_IRUNBND)
MFnodesDF.sort(columns='cellnum', inplace=True)  # Sort by cellnum so that in correct order for saving ascii file.
#IRUNBND = np.reshape(MFnodesDF['segment'].values, (nrows, ncols))  # Reshape to grid dimensions
IRUNBND = np.reshape(MFnodesDF['outseg'].values, (nrows, ncols))  # Reshape to grid dimensions
np.savetxt(MFoutdir + out_IRUNBND, IRUNBND, fmt='%i', delimiter=' ')
'''  No need to re-generate these arrays.
print 'writing {}'.format(out_FINF)
FINF = np.reshape(MFnodesDF['Recharge'].values, (nrows, ncols))
np.savetxt(MFoutdir + out_FINF, FINF, fmt='%8.6f', delimiter=' ')
print 'writing {}'.format(out_IUZFBND)
# read BAS file; where IBOUND <= 0, turn off UZF (set IUZFBND to 0)
# To do: Read in list of other BC packages (eg: what if use DRN instead of CHD), then turn off UZF at those cells.
ibound = intarrayreader(bas, 5, nrows, ncols)
iuzfbnd = np.where(ibound >= 1, ibound, 0)
np.savetxt(MFoutdir + out_IUZFBND, iuzfbnd, fmt='%i', delimiter=' ')
'''
'''
iuzfbnd = np.ones_like(IRUNBND, int)
if bas:
    ibound = arrayreader(bas, 5, int, nrows, ncols)
    iuzfbnd = np.where(ibound >= 1, ibound, 0)
if drn:
    drncells = arrayreader(drn, 5, float, nrows, ncols)
    iuzfbnd = np.where(drncells > 0, 0, iuzfbnd)
np.savetxt(out_iuzfbnd, iuzfbnd, fmt='%i', delimiter=' ')
'''

#df, shpname, geo_column, prj
#GISio.df2shp(MFnodesDF, os.path.join(MFoutdir + (out_IRUNBND + '.shp')), 'geometry',
#             os.path.join(working_dir + nodes_WB)[:-4]+'.prj')
# this one only prints out the points where waterbodies occur
#GISio.df2shp(MFnodes_watbod, os.path.join(working_dir + 'UZF_segments.shp'), 'geometry',
#             os.path.join(working_dir + nodes_WB)[:-4]+'.prj')
GISio.df2shp(MFnodesDF, os.path.join(MFoutdir + (out_IRUNBND[:-4] + '_outseg.shp')), 'geometry',
             os.path.join(working_dir + nodes_WB)[:-4]+'.prj')
# this one only prints out the points where waterbodies occur
GISio.df2shp(MFnodes_watbod, os.path.join(working_dir + 'UZF_outseg_segments.shp'), 'geometry',
             os.path.join(working_dir + nodes_WB)[:-4]+'.prj')

'''
Additional thoughts and notes:

1. Do we need to remove UZF cells that overlap SFR cells?  No, removing these cells would reduce the amount of
'potential recharge' applied to the model apriori.  Even if all the recharge is re-discharged within a cell with SFR,
it should be applied b/c most streams don't cover 1000ft.  Plus, it doesn't matter if water is discharged to a SFR or
UZF cell as they're routed together. Besides, SFR cells should have lower STOPs then the land surface used for UZF b/c
SFR drills deeper to enforce down-stream slopes, and b/c the top of the model, which UZF relies upon, was generated as
the mean of the DEM, which seems appropriate for minimizing bias for UZF.

2. Considered

To Do:
#
#
#
3. Auto-generate a UZF file that reads in each of the arrays by name.
4. Read directly from DIS file rather than from shapefiles of grid or nodes.  Read in IBOUND and BC arrays/packages to
directly with flopy
5.
6. Switch to using GeoPandas instead of Andy's GISio because more standardized and available.
7. Convert to a Class for future implementation as part of a larger MF model generation process?
8. Consider option flags for plotting some of the arrays rather than writing shapefiles. For example, the original
problem with the IRUNBND array would have been detected earlier had it been plotted with matplotlib.
'''
