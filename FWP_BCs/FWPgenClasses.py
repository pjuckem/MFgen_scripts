'''
Classes to assist with generating MF arrays to generate the FWP MF model with Flopy

I started on this by selecting from SFRmaker, but bailed -- perhaps in the future....
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

'''
try:
    xmlname=sys.argv[1]
except:
    xmlname='FWPinput.xml'
inpardat = ET.parse(xmlname)
inpars = inpardat.getroot()
'''

class UZFInput:
    """
    the SFRInput class holds all data from the XML-based input file
    """
    def __init__(self, infile):
        try:
            inpardat = ET.parse(infile)
        except:
            raise(InputFileMissing(infile))

        inpars = inpardat.getroot()

        try:
            self.working_dir = inpars.findall('.//working_dir')[0].text
            os.path.isdir(self.working_dir)
        except:
            self.working_dir = os.getcwd()

        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)
        os.chdir(self.working_dir)

        self.preproc = self.tf2flag(inpars.findall('.//preproc')[0].text)
        if not self.preproc:
            print "Running without pre-processing the shapefiles; \n" \
                  "processing UZF arrays directly from previously made shapefiles.\n"
        self.overwrite = self.tf2flag(inpardat.findall('.//overwrite')[0].text)
        bas = inpardat.findall('.//BASname')[0].text
        basskip = inpardat.findall('.//BASskiplines')[0].text
        mfdomain_shp = inpardat.findall('.//MFdomain_shp')[0].text
        mfnode_shp = inpardat.findall('.//MFnodes_shp')[0].text
        sfr_shp = inpardat.findall('.//SFR_shapefile')[0].text
        cathments = inpardat.findall('.//cathments')[0].text
        waterbodies = inpardat.findall('.//waterbodies')[0].text
        infiltration = inpardat.findall('.//infiltration')[0].text
        precip = inpardat.findall('.//precip')[0].text
        evap = inpardat.findall('.//evap')[0].text
        out_IUZFBND = inpardat.findall('.//out_IUZFBND')[0].text
        out_FINF = inpardat.findall('.//out_FINF')[0].text
        out_IRUNBND = inpardat.findall('.//out_IRUNBND')[0].text
        junkGDB = inpardat.findall('.//junkGDB')[0].text
        modelcatchments = inpardat.findall('.//modelcatchments')[0].text
        modelwaterbodies = inpardat.findall('.//modelwaterbodies')[0].text
        uniqueWB = inpardat.findall('.//uniqueWB')[0].text
        SFR_WB = inpardat.findall('.//SFR_WB')[0].text
        nodes_WB = inpardat.findall('.//nodes_WB')[0].text
        catchmentdir = inpardat.findall('.//catchmentdir')[0].text
        working_dir = inpardat.findall('.//working_dir')[0].text
        MFoutdir = inpardat.findall('.//MFoutdir')[0].text

        self.reach_cutoff = float(inpars.findall('.//reach_cutoff')[0].text)
        self.rfact = float(inpars.findall('.//rfact')[0].text)
        self.Lowerbot = self.tf2flag(inpars.findall('.//Lowerbot')[0].text)
        self.buff = float(inpars.findall('.//buff')[0].text)
        self.minimum_slope = float(inpars.findall('.//minimum_slope')[0].text)
        self.tpl = self.tf2flag(inpars.findall('.//tpl')[0].text)
        self.MFgrid = inpars.findall('.//MFgrid')[0].text
        self.MFdomain = inpars.findall('.//MFdomain')[0].text
        self.MFdis = inpars.findall('.//MFdis')[0].text
        self.DEM = inpars.findall('.//DEM')[0].text
        self.intersect = self.add_path(inpars.findall('.//intersect')[0].text)
        self.intersect_points = self.add_path(inpars.findall('.//intersect_points')[0].text)
        self.rivers_table = inpars.findall('.//rivers_table')[0].text
        self.PlusflowVAA = inpars.findall('.//PlusflowVAA')[0].text
        self.Elevslope = inpars.findall('.//Elevslope')[0].text
        self.Flowlines_unclipped = inpars.findall('.//Flowlines_unclipped')[0].text
        self.arcpy_path = inpars.findall('.//arcpy_path')[0].text
        self.FLOW = inpars.findall('.//FLOW')[0].text
        self.FTab = inpars.findall('.//FTab')[0].text
        self.Flowlines = self.add_path(inpars.findall('.//Flowlines')[0].text)
        self.ELEV = self.add_path(inpars.findall('.//ELEV')[0].text)
        self.CELLS = self.add_path(inpars.findall('.//CELLS')[0].text)
        self.CELLS_DISS = self.add_path(inpars.findall('.//CELLS_DISS')[0].text)
        self.NHD = self.add_path(inpars.findall('.//NHD')[0].text)
        self.OUT = self.add_path(inpars.findall('.//OUT')[0].text)
        self.MAT1 = self.add_path(inpars.findall('.//MAT1')[0].text)
        self.MAT2 = self.add_path(inpars.findall('.//MAT2')[0].text)
        self.WIDTH = self.add_path(inpars.findall('.//WIDTH')[0].text)
        self.MULT = self.add_path(inpars.findall('.//MULT')[0].text)
        self.ELEVcontours = inpars.findall('.//ELEVcontours')[0].text
        self.Routes = self.add_path(inpars.findall('.//Routes')[0].text)
        self.Contours_intersect = self.add_path(inpars.findall('.//Contours_intersect')[0].text)
        self.Contours_intersect_distances = self.add_path(inpars.findall('.//Contours_intersect_distances')[0].text)
        self.RCH = self.add_path(inpars.findall('.//RCH')[0].text)
        self.nsfrpar = int(inpars.findall('.//nsfrpar')[0].text)
        self.nparseg = int(inpars.findall('.//nparseg')[0].text)
        self.const = float(inpars.findall('.//const')[0].text)
        self.dleak = float(inpars.findall('.//dleak')[0].text)
        self.nstrail = int(inpars.findall('.//nstrail')[0].text)
        self.isuzn = int(inpars.findall('.//isuzn')[0].text)
        self.nsfrsets = int(inpars.findall('.//nsfrsets')[0].text)
        self.istcb1 = int(inpars.findall('.//istcb1')[0].text)
        self.istcb2 = int(inpars.findall('.//istcb2')[0].text)
        self.isfropt = int(inpars.findall('.//isfropt')[0].text)
        self.bedK = float(inpars.findall('.//bedK')[0].text)
        self.bedKmin = float(inpars.findall('.//bedKmin')[0].text)
        self.bedthick = float(inpars.findall('.//bedthick')[0].text)
        self.icalc = int(inpars.findall('.//icalc')[0].text)
        self.nstrpts = int(inpars.findall('.//nstrpts')[0].text)
        self.iprior = int(inpars.findall('.//iprior')[0].text)
        self.flow = float(inpars.findall('.//flow')[0].text)
        self.runoff = float(inpars.findall('.//runoff')[0].text)
        self.etsw = float(inpars.findall('.//etsw')[0].text)
        self.pptsw = float(inpars.findall('.//pptsw')[0].text)
        self.roughch = float(inpars.findall('.//roughch')[0].text)
        self.roughbk = float(inpars.findall('.//roughbk')[0].text)
        self.cdepth = float(inpars.findall('.//cdepth')[0].text)
        self.fdepth = float(inpars.findall('.//fdepth')[0].text)
        self.awdth = float(inpars.findall('.//awdth')[0].text)
        self.bwdth = float(inpars.findall('.//bwdth')[0].text)
        self.thickm1 = float(inpars.findall('.//thickm1')[0].text)
        self.thickm2 = float(inpars.findall('.//thickm2')[0].text)
        self.Hc1fact = float(inpars.findall('.//Hc1fact')[0].text)
        self.Hc2fact = float(inpars.findall('.//Hc2fact')[0].text)
        self.stream_depth = float(inpars.findall('.//stream_depth')[0].text)
        self.GISSHP = self.add_path(inpars.findall('.//GISSHP')[0].text)
        self.elevflag = inpars.findall('.//elevflag')[0].text


        self.calculated_DEM_elevs = False
        self.calculated_contour_elevs = False

        # initialize the arcpy environment
        #arcpy.env.workspace = os.getcwd()
        arcpy.env.workspace = self.working_dir
        arcpy.env.overwriteOutput = True
        arcpy.env.qualifiedFieldNames = False
        # Check out any necessary arcpy licenses
        arcpy.CheckOutExtension("spatial")

        # read in model information
        self.DX, self.DY, self.NLAY, self.NROW, self.NCOL, i = disutil.read_meta_data(self.MFdis)
        # make backup copy of MAT 1, if it exists
        MAT1backup = "{0}_backup".format(self.MAT1)
        if os.path.isfile(self.MAT1):
            try:
                shutil.copyfile(self.MAT1, MAT1backup)
            except IOError:
                print "Tried to make a backup copy of {0} but got an error.".format(self.MAT1)
        try:
            self.plotflag = self.tf2flag(inpars.findall('.//plotflag')[0].text)
        except:
            self.plotflag = True
        try:
            self.eps = float(inpars.findall('.//eps')[0].text)
        except:
            self.eps = 1.0000001e-02  # default value used if not in the input file
        try:
            self.min_elev = float(inpars.findall('.//minimum_elevation')[0].text)
        except:
            self.min_elev = -999999.0  # default value used if not in the input file

        # conversion for vertical length units between NHDPlus v2. (usually cm) and model
        try:
            self.z_conversion = float(inpars.findall('.//z_conversion')[0].text)
        except:
            self.z_conversion = 1.0/(2.54 *12)  # default value used if not in the input file

        # conversion for vertical length units between DEM and model
        try:
            self.DEM_z_conversion = float(inpars.findall('.//DEM_z_conversion')[0].text)
        except:
            self.DEM_z_conversion = 1.0  # default value used if not in the input file

        #cutoff to check stream length in cell against fraction of cell dimension
        #if the stream length is less than cutoff*side length, the piece of stream is dropped
        try:
            self.cutoff = float(inpars.findall('.//cutoff')[0].text)
        except:
            self.cutoff = 0.0

        try:
            self.distanceTol = float(inpars.findall('.//distanceTol')[0].text)
        except:
            self.distanceTol = 10*np.min(self.DX[1:] - self.DX[:-1]) # get spacings, then take the minimum

        try:
            self.profile_plot_interval = int(inpars.findall('.//profile_plot_interval')[0].text)
        except:
            self.profile_plot_interval = 20

        try:
            self.elev_comp = self.tf2flag(inpars.findall('.//compare_elevation_methods')[0].text)

        except:
            self.elev_comp = False

        # PFJ: The exception assignment to a string when no field is present in the input XML file is problematic because
        # it causes the code to skip the checking analysis near line 1265, where 'cellnum' had previously been generated.
        # I've added a boolean assigment here, and added a "self.node_attribute = 'cellnum' " assigment around line 1295.
        # Of course, now I had to add a check for a newly generated cellnum field in the shapefile (following try/except)

        # if no node attribute is specified, will default to "old way," where it looks for a "cellnum" column,
        # tests if it has unique values, otherwise attempts to make one from row and column columns
        try:
            self.node_attribute = inpars.findall('.//node_attribute')[0].text
        except:
            self.node_attribute = False
            # PFJ: now need to add a test to see if 'cellnum' has been added to self.MFgrid from a prior run with preproc
            fields = arcpy.ListFields(self.MFgrid)
            for field in fields:
                if str(field.name) == "cellnum":
                    self.node_attribute = 'cellnum'


        #read the Fcode-Fstring table and save it into a dictionary, Fstring
        descrips = arcpy.SearchCursor(self.FTab)
        self.Fstring = dict()
        for description in descrips:
            Fcodevalue = int(description.FCode)
            if not Fcodevalue in self.Fstring:
                self.Fstring[Fcodevalue]=description.Descriptio
        del descrips

    def tf2flag(self, intxt):
        # converts text written in XML file to True or False flag
        if intxt.lower() == 'true':
            return True
        else:
            return False

    def add_path(self, infile):

        # if there is no path in front of the input file, add one
        if len(os.path.split(infile)[0]) == 0:
            fullpath = os.path.join(self.working_dir, infile)

        # otherwise, leave the path as is
        else:
            fullpath = infile
        return fullpath


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