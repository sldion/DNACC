"""

This class produces PointData given an input that contains CellData.
This is useful because many of VTK's algorithms work best with
PointData.  The filter basically wraps the vtkCellDataToPointData
class.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.4 $"
__date__ = "$Date: 2005/08/02 18:26:24 $"

import Base.Objects, Common
import vtk
import vtkPipeline.ConfigVtkObj

debug = Common.debug

class CellToPointData (Base.Objects.Filter):

    """ This class produces PointData given an input that contains
    CellData.  This is useful because many of VTK's algorithms work
    best with PointData.  The filter basically wraps the
    vtkCellDataToPointData class. """

    def initialize (self):
        debug ("In CellToPointData::initialize ()")
        self.prev_data_type = ""
        self.fil = vtk.vtkCellDataToPointData ()
        self.fil.SetInput (self.prev_fil.GetOutput ())
        self._find_input_data_type()
        self.fil.Update ()

    def _find_input_data_type(self):        
        """Determines the input data type and uses it later to get the
        appropriate output."""        
        debug ("In CellToPointData::_find_input_data_type ()")
        out = self.prev_fil.GetOutput ()
        types = ['vtkStructuredGrid', 'vtkRectilinearGrid',
                 'vtkStructuredPoints', 'vtkUnstructuredGrid',
                 'vtkPolyData', 'vtkImageData']
        for type in types:
            if out.IsA (type):
                self.prev_data_type = type
                break
        
    def set_input_source (self, source):
        debug ("In CellToPointData::set_input_source ()")
        Common.state.busy ()
        self.fil.SetInput (source.GetOutput ())
        self.prev_filter = source
        self._find_input_data_type()
        # The following is necessary for things to work properly.
        self.mod_m.update_modules ()
        Common.state.idle ()

    def GetOutput (self):
        """Returns an appropriate output depending on the input."""
        debug ("In CellToPointData::GetOutput ()")
        return eval ('self.fil.Get%sOutput()'%self.prev_data_type[3:])

    def configure (self, master=None):
        debug ("In CellToPointData::configure ()")
        c = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        c.set_update_method (self.mod_m.Update)
        c.configure (self.root, self.fil)
        c.root.transient (master)

