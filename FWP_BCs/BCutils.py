'''
A method to identify isolated activated cells, which MF-NWT will inactivate at run-time.  This can be problematic for
cells with boundary condition packages, except the CHD package (when ibound is specified as -1).

For this implementation, values of -1 in ibound are converted to 1.  It is assumed that the user is calling this method
because islands in the IBOUND array are being automatically turned off, resulting in problems with boundary condition
packages.  Using constant heads with the -1 flag in IBOUND does not suffer from problems with isolated cells, thus, there
is no value to running this code.  Nonetheless, a warning will be printed to the screen when a -1 value is detected in
an input IBOUND array so the user is informed.

Parameters:
-----------
model: model object from which the BAS file and IBOUND array will be obtained.  Pulling the entire model will facilitate
    future enhancements whereby boundary packages (DRN, CHD, GHB, etc) can be edited to remove input where isolated cells
    have been removed.

'''

import numpy as np
import flopy.modflow as fpmf

class IsoCells:
    """
    A class to handle isolated cells (active cells surrounded by inactive cells), and fix associated MODFLOW packages.
    """

    def __init__(self, namfilename):
        """
        Read in the model
        :param namfilename:
        """
        self.namfilename = namfilename
        m = fpmf.Modflow.load(namfilename)
        self.bas = m.get_package('BAS6')

    def negatives(self, ibound): # test to see if negatives in ibound array
        """
        Warn user that negative values in IBOUND will not be retained
        """
        minimum = np.amin(ibound)
        if minimum < 0:
            print "Negative values were found in the IBOUND array. \n" \
                  "The absolute value will be written to the new IBOUND array"

    def fix_islands(self, ibound):
        """
        Find isolated cells in a 2d-array (IBOUND) and return a new 2d IBOUND array with isolated 1s replaced by zeros.
        :param: arr, a 2d array
        :return: newibnd
        """

        self.negatives(ibound) # check for negative values and print warning prior to creating new IBOUND
        ibound = np.absolute(ibound)

        l, r, c = ibound.shape
        r_zeros = np.zeros(c, dtype=int)
        c_zeros = np.zeros(r, dtype=int)
        c_zeros = c_zeros.reshape(int(c_zeros.shape[0]), 1)  # Reshape to make array a 'column'

        # Generate 4 arrays that shift Ibound up, down, left, and right.
        down = np.vstack((r_zeros, ibound[0]))  # add a row of zeros at the top of the grid (shift the grid down)
        down = down[:-1]  # remove the rows along the bottom of the grid to return to r, c dimensions
        up = np.vstack((ibound[0], r_zeros))  # add a row of zeros at bottom of grid (shift up)
        up = up[1:]  # remove rows along top
        right = np.hstack((c_zeros, ibound[0]))  # add column along left side of grid (move right)
        right = np.hsplit(right, np.array([int(c)]))[0]  # remove column along right side of grid
        left = np.hstack((ibound[0], c_zeros))  # add column along right
        left = np.hsplit(left, np.array([1]))[1]  # remove column along left

        mask = np.ma.masked_equal(ibound, 0)  # mask out inactive cells. (IBOUND = zero is TRUE in the mask)
        # For an unmasked cell (active cells), if adding U,D,L,R, to the mask array sums to 1, it's surrounded by
        # inactive cells (only the unmasked cell itself is active, thus summing to 1).
        tot = np.add(mask, up)
        tot = np.add(tot, down)
        tot = np.add(tot, left)
        tot = np.add(tot, right)
        tot = np.where(tot > 1, 1, 0)  # add them all.  Where tot > 1, not isolated; else, isolated and set to zero
        newibnd = np.ma.filled(tot, fill_value=0)  # keep tot as it is, but convert masked cells back to zero.
        return newibnd

    def fix_ibound(self, bas):
        """
        Write the new IBOUND array to the BAS file and write the BAS file
        :param bas:
        :param newibnd:
        """
        ibound = bas.getibound()  # np 3d array (nlay, nrow, ncol)
        newibound = self.fix_islands(ibound)
        print 'Updating the BAS file with the new IBOUND array.\n'
        fpmf.ModflowBas.setibound(bas, ibound=newibound)
        fpmf.ModflowBas.write_file(bas)