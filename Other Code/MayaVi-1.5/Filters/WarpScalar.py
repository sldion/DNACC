"""

This wraps the vtkWarpScalar filter.  vtkWarpScalar is a filter that
modifies point coordinates by moving points along point normals by the
scalar amount times the scale factor.  Useful for creating carpet or
x-y-z plots.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.4 $"
__date__ = "$Date: 2005/08/02 18:26:25 $"

import PolyDataNormals
import Common
import vtk

debug = Common.debug

# derived from PolyDataNormals since it implements exactly what we need.
class WarpScalar (PolyDataNormals.PolyDataNormals):

    """ This wraps the vtkWarpScalar filter.  vtkWarpScalar is a
    filter that modifies point coordinates by moving points along
    point normals by the scalar amount times the scale factor.  Useful
    for creating carpet or x-y-z plots.  """

    def initialize (self):
        debug ("In WarpScalar::initialize ()")
        self.fil = vtk.vtkWarpScalar ()
        self._set_input ()
        self.fil.Update ()
