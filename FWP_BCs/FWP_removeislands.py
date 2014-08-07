'''
Test script to feed into 'isolated_cell_check' module.
'''


import shutil
import os
import BCutils


namfile = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/MODFLOW/FWPvert.nam'
model_ws = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/MODFLOW'

bas_file = namfile[:-4] + '.bas'
rename_bas_file = namfile[:-4] + '_original.bas'
# see if the original file exists prior to making a copy (and potentially overwriting with a bad one created by
# a previous run of this script...)
try:
    test = open(rename_bas_file)
except:
    print '\n Saving a copy of the original *.bas file as *_original.bas \n'
    shutil.copyfile(bas_file, rename_bas_file)

model = BCutils.IsoCells(namfile)
newbas = model.fix_ibound(model.bas)

#newghb = BCutils.IsoCells.fix_GHB(model.ghb) # need to implement this...
#etc...
