import os
import numpy as np

CHD = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/MODFLOW/FWPvert.chd'
DRN_out = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/script_output/FWPvert.drn'
# conductance = 0.1 ft/d * 1000ft wide * 1000ft long / 1 ft thick
cond = (0.1 * 1000 * 1000 / 1)
IDRNCB = 50
chd_skiplines = 3
face = 6
add = [cond, face]

indat = []
chdfile = open(CHD, 'r').readlines()
drnfile = open(DRN_out, 'w')
skp = 0

def linereader(infile, skiplines):
    indat = []
    skp = 0
    for line in infile:
        if (skp >= skiplines):
            tmp = line.strip().split()
            indat.append(tmp)
        skp += 1
    return indat
##########
### MAIN #
##########

chdlist = linereader(chdfile, chd_skiplines)
drnfile.write('# MODFLOW-NWT Drain Package \n'
            '     ' + str(len(chdlist)) + '        ' + str(IDRNCB) + '  ' + 'AUX IFACE \n'
            '     ' + str(len(chdlist)) + '         0' + '              Stress Period 1 \n')
for line in chdlist:
    use = line[:4]
    use.extend(add)
    #outfile.write('%10d, %10d, %10d, %10.3f, %10.3f, $10d' % (int(use[0]), int(use[1]), int(use[2]), float(use[3]), use[4], use[5]))
    drnfile.write('{0:10d} {1:9d} {2:9d} {3:9.2f} {4:9.1f} {5:9d}\n'.format(int(use[0]), int(use[1]), int(use[2]), float(use[3]), use[4], use[5]))
drnfile.close()

# use a text editor to replace -1 with 1 in IBOUND