import os
import numpy as np

mfdir = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/MODFLOW/'
mfname = 'FWPvert'
bas = os.path.join(mfdir + mfname + '.bas')
out_iuzfbnd = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/temp/FWPvert_IUZFBND.dat'
nrows = 930
ncols = 650

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

print 'writing {}'.format(out_iuzfbnd)
# read BAS file; where IBOUND <= 0, turn off UZF (set IUZFBND to 0)
# To do: Read in list of other BC packages (eg: what if use DRN instead of CHD), then turn off UZF at those cells.
ibound = intarrayreader(bas, 5, nrows, ncols)
iuzfbnd = np.where(ibound >= 1, ibound, 0)
np.savetxt(out_iuzfbnd, iuzfbnd, fmt='%i', delimiter=' ')
