import os
import numpy as np
import flopy as fp
import shutil

namfile = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/MODFLOW/test/FWPvert.nam'
model_ws = 'D:/PFJData2/Projects/NAQWA/Cycle3/FWP/MODFLOW/test'
print 'Saving a copy of the original *.bas file as *_original.bas \n'
bas_file = namfile[:-4] + '.bas'
rename_bas_file = namfile[:-4] + '_original.bas'
shutil.copyfile(bas_file,rename_bas_file)

# List of isolated cells.  This can be identified in the MF LIST file when using MF-NWT with xmd solver.
isolated = [[43,80],[433,61],[470,73],[471,71],[626,21],[626,24]]

m = fp.modflow.Modflow.load(namfile,)
bas = m.get_package('BAS6')
ibound = bas.getibound() #np 3d array (nlay, nrow, ncol)
ibound = np.absolute(ibound) # should add a flag for user to choose to remove -1 from ibound.
print '\n Converting isolated active cells to inactive. \n'
for cells in isolated:
    rindex = cells[0]-1
    cindex = cells[1]-1
    ibound[0][rindex][cindex] = 0  # set isolated active cells to inactive
print 'Updating the BAS file with the new IBOUND array.\n'
fp.modflow.ModflowBas.setibound(bas, ibound=ibound)
fp.modflow.ModflowBas.write_file(bas)  # overwrite the bas file

###########################
# Fix the DRN package too #
###########################
print 'Saving a copy of the original *.drn file as *_original.drn\n'
drn_file = namfile[:-4] + '.drn'
#drnfile = open(drn_file, 'w')
rename_drn_file = namfile[:-4] + '_original.drn'
shutil.copyfile(drn_file, rename_drn_file)  # save a copy of the original

IDRNCB = 50
face = 6

drn = m.get_package('DRN')
rows = drn.layer_row_column_elevation_cond[0]
print 'Removing DRN cells where isolated active cells were converted to inactive.\n'
header=('# MODFLOW-NWT Drain Package \n'
            '     ' + str(int(rows.shape[0]) - len(isolated)) + '        ' + str(IDRNCB) + '  ' + 'AUX IFACE \n'
            '     ' + str(int(rows.shape[0]) - len(isolated)) + '         0' + '              Stress Period 1')
i = 1
newrows = []
remove = []
for i, line in enumerate(rows):
    lay = int(line[0])
    row = int(line[1])
    col = int(line[2])
    elev = float(line[3])
    cond = float(line[4])
    for cells in isolated:
        rindex = cells[0]
        cindex = cells[1]
        if (row == rindex and col == cindex):
            remove.append(i)
    newrows.append([lay, row, col, elev, cond, face])
    #drnfile.write('{0:10d} {1:9d} {2:9d} {3:9.2f} {4:9.1f} {5:9d}\n'
    #                      .format(lay, row, col, elev, cond, face))
newrows = np.array(newrows)
remove = np.array(remove)
keeprows = np.delete(newrows, remove, 0)
print 'Updateing the DRN file with the new list of DRN cells.'
np.savetxt(drn_file, keeprows, fmt='%10d %9d %9d %9.2f %9.1f %9d',
           header=header, comments='', delimiter='')
#fp.modflow.ModflowDrn.assign_layer_row_column_data(drn, newrows, int(rows.shape[1]))
#fp.modflow.ModflowDrn.write_file(drn)
'''
Have to abandon effort to identify isolated active cells automatically...
l, r, c = ibound.shape
r_zeros = np.zeros(c, dtype=int)
c_zeros = np.zeros(r, dtype=int)
c_zeros = c_zeros.reshape(int(c_zeros.shape[0]), 1)  # Reshape to make array a 'column'
# Generate 4 arrays that shift Ibound down, up, right, and left. Will use these to compare
# against original ibound to identify isolated active cells.
down = np.vstack((r_zeros, ibound[0]))  # add a row of zeros at the top of the grid (shift the grid down)
down = down[:-1]  # remove the rows along the bottom of the grid to return to r, c dimensions
up = np.vstack((ibound[0], r_zeros))  # add a row of zeros at bottom of grid (shift up)
up = up[1:]  # remove rows along top
right = np.hstack((c_zeros, ibound[0]))  # add column along left side of grid (move right)
right = np.hsplit(right, np.array([int(c)]))[0]  # remove column along right side of grid
left = np.hstack((ibound[0], c_zeros))  # add column along right
left = np.hsplit(left, np.array([1]))[1]  # remove column along left
isum = []
for i, j in enumerate(ibound[0]):
    sum = np.sum((up, down, left, right))
    isum = np.append(sum)
isumarray = isum.reshape(int(r), int(c))
'''




