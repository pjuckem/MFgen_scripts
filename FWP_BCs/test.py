import numpy as np
import flopy as fp
'''
Method to identify isolated activated cells, which MF-NWT will inactivate at run-time.  This can be problematic for 
cells with boundary condition packages, except the CHD package (when ibound is specified as -1).

Before implement this, how should we deal with -1 values in ibound?  Need to temporarily set them as active, but how 
set them back to -1 if the user would like to retain that?  Or, do we just throw a warning because there's no need to 
run this program for isolated -1 cells.  That is, why fix a problem that doesn't exist?
'''
m = fp.modflow.Modflow.load(namfile,)
bas = m.get_package('BAS6')
ibound = bas.getibound()  # np 3d array (nlay, nrow, ncol)
ibound = np.absolute(ibound)  # should add a flag for user to choose to remove -1 from ibound.


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

mask = np.ma.masked_equal(ibound, 0)  # mask out inactive cells.
# For an unmasked cell (active, or 1 in mask), if adding U,D,L,R, to the mask array sums to 1, it's surrounded by
# inactive cells.
tot = np.add(mask, up)
tot = np.add(tot, down)
tot = np.add(tot, left)
tot = np.add(tot, right)
tot = np.where(tot > 1, 1, 0)  # add them all.  Where tot > 1, not isolated; else, isolated and set to zero
newibnd = np.ma.filled(tot, fill_value=0)  # keep tot as it is, but convert masked cells back to zero.
print 'Updating the BAS file with the new IBOUND array.\n'
fp.modflow.ModflowBas.setibound(bas, ibound=newibnd)
fp.modflow.ModflowBas.write_file(bas)  