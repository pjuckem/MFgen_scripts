import os
import numpy as np

CHD = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/MODFLOW/FWPvert.chd'
DRN_out = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/script_output/FWPvert.drn'
# conductance = 0.1 ft/d * 1000ft wide * 1000ft long / 1 ft thick
cond = (0.1 * 1000 * 1000 / 1)
skiplines = 3
face = 6


indat = []
infile_dat = open(CHD, 'r').readlines()
skp = 0
for line in infile_dat:
    if (skp >= skiplines):
        tmp = line.strip([:4]).split()
        indat.extend(tmp)
    skp += 1

print 'writing {}'.format(out_iuzfbnd)
# read BAS file; where IBOUND <= 0, turn off UZF (set IUZFBND to 0)
# To do: Read in list of other BC packages (eg: what if use DRN instead of CHD), then turn off UZF at those cells.
ibound = intarrayreader(bas, 5, nrows, ncols)
iuzfbnd = np.where(ibound >= 1, ibound, 0)
np.savetxt(out_iuzfbnd, iuzfbnd, fmt='%i', delimiter=' ')
