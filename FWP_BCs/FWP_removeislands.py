'''
Test script to feed into 'isolated_cell_check' module.
'''

import flopy as fp
import shutil
import os
import BCutils


namfile = 'D:/PFJData/Models/fwp/test/FWPvert.nam'
model_ws = 'D:/PFJData/Models/fwp/test'

bas_file = namfile[:-4] + '.bas'
rename_bas_file = namfile[:-4] + '_original.bas'
# see if the original file exists prior to making a copy (and potentially overwriting with a bad one created by
# a previous run of this script...)
try:
    os.path.isfile(rename_bas_file)
except:
    print '\n Saving a copy of the original *.bas file as *_original.bas \n'
    shutil.copyfile(bas_file, rename_bas_file)

newibound = BCutils.IsoCells.find_islands(namfile)
BCutils.IsoCells.fix_bas(newibound)

BCutils.IsoCells.fix_GHB(ghbfilename)
'''etc...
