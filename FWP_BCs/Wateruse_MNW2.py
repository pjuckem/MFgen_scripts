__author__ = 'Shope, Juckem'
#Program to use water use data throughout the FWP study area to create a Modflow *.MNW2 file

#Python code to collect water use data throughout the NAWQA Fox-Wolf-Peshtigo (FWP) study area in Wisconsin. The code
# uses water use data compiled by C. Buchwald and includes well ID, location, altitude, top and bot casing depth,
# aquifer, well class, and the water use. A single water use value is assumed that incorporates the entire period. The
# MODFLOW grid is also used to prescribe the row and col locations of each well on the grid for the *.MNW2 file.

# created/updated by C Shope - 23 July, 2014

#Import the well points from the water use *.csv data file (CB 18 June, 2014). Import the polygon grid for the FWP
# created in Modflow (PJF on 7 July, 2014). However, may not be necessary though since we can just find the files and
# then join them for a new file.

# Dependancies:
# arcpy, pandas, xlrd (imported with pandas, but installed separately), xml.etree, sys, os, geopandas, numpy)


import arcpy
import pandas as pd
import geopandas as gp
from shapely.geometry import Point, LineString, Polygon
import numpy as np
import matplotlib.pyplot as plt
import sys
import xml.etree.ElementTree as ET
import os
import shutil


def tf2flag(intxt):
    # converts text written in XML file to True or False flag
    if intxt.lower() == 'true':
        return True
    else:
        return False

# Read input from an XML file to facilitate collaboration and transportability
try:
    xmlname = sys.argv[1]
except:
    xmlname = 'FWPvert_mnw2_input_PFJ.xml'
inpardat = ET.parse(xmlname)
inpars = inpardat.getroot()

overwrite = tf2flag(inpardat.findall('.//overwrite')[0].text) # uses function above to convert str to boolean.
WU_data = inpardat.findall('.//WU_xls')[0].text
MFgrid = inpardat.findall('.//MFgrid_shp')[0].text
working_dir = inpardat.findall('.//working_dir')[0].text
MFoutdir = inpardat.findall('.//MFoutdir')[0].text
WU_points_name = inpardat.findall('.//WU_points_shp')[0].text
outfile = inpardat.findall('.//Out_File')[0].text
skin = float(inpardat.findall('.//skin')[0].text)
WU_points = os.path.join(working_dir + WU_points_name)

# initialize the arcpy environment
arcpy.env.workspace = working_dir
arcpy.env.overwriteOutput = overwrite
arcpy.env.qualifiedFieldNames = True
'''
# Local variables:
KMSFH_WU_sample_ = "D:\\USGS\\Shope_NAWQA\\Tomorrow_Waupaca\\Data\\Tables\\WaterUse\\sample.xlsx\\KMSFH_WU_sample$"
FWPvert_grid1000_UTMft = "FWPvert_grid1000_UTMft"
Sample_pts = "Sample_pts"
SamplePts_1000UTMft_shp = "D:\\USGS\\Shope_NAWQA\\Tomorrow_Waupaca\\Data\\Tables\\WaterUse\\SamplePts_1000UTMft.shp"
'''
# Read XLS file into dataframe and export a point shapefile with Geopandas, then intersect with grid to get row,col
# for each well.  Future versions will read DIS directly to gain info on layering.
# mfgridDF = gp.GeoDataFrame.from_file(MFgrid)
# read in the Excel Water Use file
WUdf = pd.read_excel(WU_data, 'KMSFH_WU_sample', na_values=['NA'])
# Oddly, we have to truncate the field names to fit with shapefile conventions, otherwise the values won't be written.
# Odd because the field names get truncated automatically, but if not dealt with directly, that auto fix vaporizes
# the values!
columns = []
for column in WUdf.columns:
    if len(column) > 10:
        newcol = column[:10]
    else:
        newcol = column
    WUdf.rename(columns={column:newcol}, inplace=True)

x, y = WUdf['UTM16FT_X'], WUdf['UTM16FT_Y']
xy = zip(x, y)
wellpoints = gp.GeoSeries([Point(x, y) for x, y in xy])
WUdf['geometry'] = wellpoints
#UTM83Z16_ft = '+proj=utm +zone=16 +ellps=GRS80 +datum=NAD83 +units=ft +no_defs' #UTM83 zone 16 feet, manually defined
#WUgdf = gp.GeoDataFrame(WUdf, crs=UTM83Z16_ft)
WUgdf = gp.GeoDataFrame(WUdf)
WUgdf.to_file(WU_points)
# hard coding the projection for now
shutil.copyfile(MFgrid[:-4]+'.prj', WU_points[:-4]+'.prj')
WU_ptjoin = WU_points[:-4] + 'IntGrd.shp'
arcpy.SpatialJoin_analysis(WU_points, MFgrid, WU_ptjoin)

# For some unknown reason, I can't get the spatial join above to work.  It seems projection related, but I'm copying
# the *.prj file for pete's sake!  Did in manually in ARC, so reading that one in now.  Need to fix this, but at a loss
# for the moment...
'''
manuallyjoined = os.path.join(working_dir + WU_points[:-4] + 'IntGrd2.shp' )
joined_gdf = pd.GeoDataFrame.from_file(manuallyjoined)
MNWMAX = joined_gdf.count

ofp = open(outfile, 'w')
ofp.write('# MODFLOW-NWT MNW2 Package \n')
{0:10d} {1:9d} {2:9d} {3:9.2f} {4:9.1f} {5:9d}\n'.format(int(use[0]), int(use[1]), int(use[2]), float(use[3]), use[4], us

# Get the highest water use by sorting the dataframe and selecting the top row, also gives the row info for that site ID
Sorted = df.sort(['Q2011-15_CFD'], ascending=[0])
Sorted.head(1)
# Get highest water use just by getting the maximum value
df['Q2011-15_CFD'].max()

 # PFJ: you shouldn't need to vectorize as in Matlab.

#read the Excel data from the water use dataset and vectorize
[WellID,WellIDtxt] = xlsread('sample.xlsx','KMSFH_WU_sample','A2:a131')
UTMX = xlsread('sample.xlsx','KMSFH_WU_sample','b2:b131')
UTMY = xlsread('sample.xlsx','KMSFH_WU_sample','c2:c131')
Alt = xlsread('sample.xlsx','KMSFH_WU_sample','d2:d131')
Top = xlsread('sample.xlsx','KMSFH_WU_sample','e2:e131')
Bot = xlsread('sample.xlsx','KMSFH_WU_sample','f2:f131')
[Aquif,Aquiftxt] = xlsread('sample.xlsx','KMSFH_WU_sample','g2:g131')
[WUClass,WUClasstxt] = xlsread('sample.xlsx','KMSFH_WU_sample','h2:h131')
Q2011_15 = xlsread('sample.xlsx','KMSFH_WU_sample','i2:i131')

No_Sites = length(UTMX)
CurrentDt = date

# CALCULATE CASED INTERVAL ELEVATIONS, PUMPING LIMITS, AND CONVERT PUMPING RATE TO WITHDRAW
for i = 1:No_Sites
    ZTop = Alt - Top
    ZBot = Alt - Bot
    HLim = ZTop + 5
    Q2011_15out = Q2011_15 * -1
end

#VARIABLES for *.MNW2 file
#MNWMAX=No_Sites; # 1-max number of multi-node wells to simulate. Total num of wells.
#IMNWCB=-90; # 1-flag and unit number. If >0, unit # to record cell by cell flow terms for budget data written to a
# file. if =0, MNW cell by cell flowterms not printed, if <0, well inject/withdraw rates and water levels inwell and
# cells printed.
#MNWPRNT=2; # 1-flag for level of detail written. if =0, only basin info, if =2 maximum level of detail.
#WELLID='WellIDtxt{i}'; # 2a-Name of the well as a text string.
#NNODES=-1; # 2a-# of cells/nodes associated with well. Normally>0. Setting <0,allows specification of top and bot of
# screen/open. The # is number of screens/open intervals.
#LOSSTYPE='SKIN'; # 2b-charact flag for well loss model. This gives correction for skin and formation damage.
# Alternatives are NONE, THIEM, GENERAL, SPECIFYcwc.
#PUMPLOC=0; # 2b-integer flag for pump intake location.  if =0, no pump or intake and discharge above first active node.
# If >0, intake cell specified in 2e as LAY-ROW-COL. If <0, define intake in 2e for ROW-COL.
#QLIMIT=1; # 2b-integer flag for WL head to constrain pump rate. If =0, there are no constraints. If >0, limited by
# water level in well defined by 2f. If <0, limited by water level in well and vary with time by 4b.
#PPFLAG=0; # 2b-integer flag for head corrected for partial penetration. If =0, head adjusted for partial penetration.
# If >0, head adjusted if vertical. This is based on NNODES in 2d.
#PUMPCAP=0; # 2b-integer flag and value for discharge adjust by changes in # head with time. If =0, not adjusted. If
# >0, adjusted by lift. If not=0, # then 1-25.
#Rw=0.1333; # 2c-radius of the well [DEFAULT].
#Rskin=1.79471628; % 2c-radius of outer limit of skin [DEFAULT].
#Kskin=12.5; # 2c-skin hydraulic conductivity [DEFAULT]. May need to adjust based on aquifer conductivity.
#ztop=ZTop(i); # 2d-top elevation of open interval.
#zbotm=ZBot(i); # 2d-bottom elevation of open interval.
#row=?; # 2d-Calculate with ArcPy.
#col=?; # 2d-Calculate with ArcPy.
#hlim=HLim(i); # 2f-limiting water level in well.
#QCUT=-1; # 2f-Integer flag  how pumping limits next 2 variables. If >0, pump limits are a rate. If <0, rates are
# fraction of Qdes. If =0, no min pumping rate.
#Qfrcmn=-1.0; # 2f-min pumping rate to remain active for stress period.
#Qfrcmx=-10; # 2f-min pumping rate exceed to reactivate well that was shut off.
#ITMP=No_Sites; # 3-integer value for reading multi-node data, changes each stress period. Must be >=0 for first SP. If
# >0, total # wells during SP from 4a. If=0, no wells active for SP. If<0, same # of wells and info reused from prev SP.
#Qdes=Q2011_15out(i); # 4-actual volumetric pumpin at well (L3/T)

#Print the *.MNW2 output file
fid = fopen('WaterUse_Sample.mnw2','w')
fprintf(fid,'%s %s\n','# File generated on ',date)
fprintf(fid,'%s\n','# ***Any additional text can be written here over multiple lines')
fprintf(fid,'%s %i %s\n',' ',No_Sites,' -90 2                       ; 1.    MNWMAX,IMNWCB,MNWPRNT')
for i = 1:No_Sites;
    fprintf(fid,'%s %s\n',WellIDtxt{i},' -1                  ; 2a.   WELLID,NNODES')

    # if additional screens/open intervals are required, this has to be
    # iteratively determined and placed here in a loop.

    fprintf(fid,'%s\n','SKIN 0 1 0 0                       ; 2b.   LOSSTYPE,PUMPLOC,QLIMIT,PPFLAG,PUMPCAP')
    fprintf(fid,'%s\n',' 0.1333 1.79471628 12.5            ; 2c.   Rw,Rskin,Kskin')
    fprintf(fid,'%i %s %i %s\n',ZTop(i),' ',ZBot(i),' 'Num(i)' 'Col(i)')                    ; 2d.   ztop,zbotm,row,col')
    fprintf(fid,'%i %s\n',HLim(i),' -1 -1.0 -10                    ; 2f.   hlim,QCUT,Qfrcmn,Qfrcmx')
end
fprintf(fid,'%i %s\n',No_Sites,'                               ; 3.    ITMP (Stress Period 1)')

# if additional stress periods to investigate, will have to add code to
# iteratively do all stress period WELLID, Qdes and then move to next

for i = 1:No_Sites
    fprintf(fid,'%16s %s %9.2f %s\n',WellIDtxt{i},' ',Q2011_15out(i),'         ; 4.    WELLID,QDes')
end
fclose(fid)
'''