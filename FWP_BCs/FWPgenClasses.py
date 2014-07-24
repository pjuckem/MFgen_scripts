'''
Classes to assist with generating MF arrays to generate the FWP MF model with Flopy
'''
__authors__ = 'Paul Juckem, Brian Clark'
__title__ = 'FWPgenClasses'

import os, arcpy, csv, cmath, math
import flopy as fp
import numpy as np
import subprocess as sp
#from arcpy.sa import *
import sys
import xml.etree.ElementTree as ET


try:
    xmlname=sys.argv[1]
except:
    xmlname='FWPinput.xml'
inpardat = ET.parse(xmlname)
inpars = inpardat.getroot()

overWrite=inpardat.findall('.//overwrite')[0].text
namfile=inpardat.findall('.//namfile')[0].text
#origin=inpardat.findall('.//origin')[0].text
#lwrRight=inpardat.findall('.//lwrRight')[0].text
#e00proj=inpardat.findall('.//e00proj')[0].text
modelproj=inpardat.findall('.//modelproj')[0].text
#e00file=inpardat.findall('.//e00file')[0].text
#gdb=inpardat.findall('.//gdb')[0].text
#lithFile=inpardat.findall('.//lithFile')[0].text
#e00fc=inpardat.findall('.//e00fc')[0].text
model_ws=inpardat.findall('.//moddir')[0].text
#modelfc=inpardat.findall('.//modfc')[0].text
modelgridshp=inpardat.findall('.//modexistgridshp')[0].text
modelnodeshp=inpardat.findall('.//modexistnodesshp')[0].text
#logfc=inpardat.findall('.//logfc')[0].text
#rastpath=inpardat.findall('.//rastpath')[0].text
#type=inpardat.findall('.//type')[0].text

class CreateModelGrid():
    '''Use flopy to access DIS file, get world coordinates for model grid corner
    and rotation, and create fishnet of modelgrid.
    need to get correct units/conversion for cell dimensions'''

    def __init__(self,namfile,modelfc,model_ws,origin,sr,yax,rastpath):
        arcpy.env.overwriteOutput=True
        m=fp.modflow.Modflow.load(namfile,model_ws=model_ws)
        dis=m.get_package('DIS')
        # t=dis.gettop()
        # b=dis.getbotm()
        # thk=t-b[0,:,:]
        # o=origin.split(' ')
        # y=yax.split(' ')
        # dY = float(y[1]) - float(o[1])
        # dX = float(y[0]) - float(o[0])
        # pol= cmath.polar(complex(dX,dY))
        # angle=math.degrees(pol[1])-90
        # print angle
        # pt=arcpy.Point(o[0],o[1])
        # rast=arcpy.NumPyArrayToRaster(thk,pt,dis.delc[0]*0.3048,dis.delr[0]*0.3048)
        # r=os.path.join(rastpath,'thkhoriz')
        # rrotate=os.path.join(rastpath,'thk')
        # rast.save(r)
        # arcpy.Rotate_management(r,rrotate,angle*-1)
        # exit()

        arcpy.AddMessage('creating model grid...')
        arcpy.CreateFishnet_management(modelfc,origin,yax,dis.delc[0]*0.3048,dis.delr[0]*0.3048,dis.nrow,dis.ncol,'','','','POLYGON')
        arcpy.DefineProjection_management(modelfc, sr)
        arcpy.AddMessage('add row col fields...')
        arcpy.AddField_management(modelfc, "row", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(modelfc, "col", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(modelfc, "rc", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddMessage('calc rc')
        arcpy.CalculateField_management(modelfc, "row", "int(("+str(dis.nrow*dis.ncol)+"-[OID])/int("+str(dis.ncol)+"))+1", "VB", "")
        arcpy.CalculateField_management(modelfc, "col", "[OID]-(("+str(dis.nrow)+"-[row])*"+str(dis.ncol)+")", "VB", "")
        arcpy.CalculateField_management(modelfc, "rc", "[row]*1000+[col]", "VB", "")

        # with arcpy.ds.updateCursor(modelfc,['laythk1','OID']) as uCursor:
            # for row in uCursor:

        # for i in range(dis.nlay):
            # arcpy.AddField_management(modelfc, "laythk"+str(i), "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            # t=dis.getbotm(i)
            # with arcpy.ds.updateCursor(modelfc,'laythk'+str(i)) as uCursor:
                # for row in uCursor:

        #same for cell centers
        arcpy.DefineProjection_management(modelfc+'_label', sr)
        arcpy.AddMessage('add row col fields...')
        arcpy.AddField_management(modelfc+'_label', "row", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(modelfc+'_label', "col", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(modelfc+'_label', "rc", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddMessage('calc rc')
        arcpy.CalculateField_management(modelfc+'_label', "row", "int(("+str(dis.nrow*dis.ncol)+"-[OID])/int("+str(dis.ncol)+"))+1", "VB", "")
        arcpy.CalculateField_management(modelfc+'_label', "col", "[OID]-(("+str(dis.nrow)+"-[row])*"+str(dis.ncol)+")", "VB", "")
        arcpy.CalculateField_management(modelfc+'_label', "rc", "[row]*1000+[col]", "VB", "")