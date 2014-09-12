"""

This wraps the vtkPolyDataNormals filter.  vtkPolyDataNormals is a
filter that computes point normals for a polygonal mesh.  This filter
tries its best to massage the input data to a suitable form.  Its
output is a vtkPolyData object.  Computing the normals is very useful
when one wants a smoother looking surface.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/08/02 18:26:25 $"

import Base.Objects, Common
import vtk
import vtkPipeline.vtkMethodParser, vtkPipeline.ConfigVtkObj

debug = Common.debug

class PolyDataNormals (Base.Objects.Filter):

    """ This wraps the vtkPolyDataNormals filter.  vtkPolyDataNormals
    is a filter that computes point normals for a polygonal mesh.
    This filter tries its best to massage the input data to a suitable
    form.  Its output is a vtkPolyData object.  Computing the normals
    is very useful when one wants a smoother looking surface.  """

    def initialize (self):
        debug ("In PolyDataNormals::initialize ()")
        self.fil = vtk.vtkPolyDataNormals ()
        self._set_input ()
        self.fil.Update ()

    def _set_input (self):        
        """ This function tries its best to generate an appropriate
        input for the Normals.  If one has an input StructuredGrid or
        StructuredPoints or even a RectilinearGrid the PolyDataNormals
        will not work.  In order for it to work an appropriate
        intermediate filter is used to create the correct output."""        
        debug ("In PolyDataNormals::_set_input ()")
        out = self.prev_fil.GetOutput ()
        f = None
        if out.IsA ('vtkStructuredGrid'):
            f = vtk.vtkStructuredGridGeometryFilter ()
        elif out.IsA ('vtkRectilinearGrid'):
            f = vtk.vtkRectilinearGridGeometryFilter ()
        elif out.IsA ('vtkStructuredPoints') or out.IsA('vtkImageData'):
            if hasattr (vtk, 'vtkImageDataGeometryFilter'):
                f = vtk.vtkImageDataGeometryFilter ()
            else:
                f = vtk.vtkStructuredPointsGeometryFilter ()
        elif out.IsA('vtkUnstructuredGrid'):
            f = vtk.vtkGeometryFilter()
        elif out.IsA('vtkPolyData'):
            f = None
        else:
            msg = "This module does not support the given "\
                  "output - %s "%(out.GetClassName ())
            raise Base.Objects.ModuleException, msg

        if f:
            f.SetInput (out)
            self.fil.SetInput (f.GetOutput ())
        else:
            self.fil.SetInput(out)
    
    def set_input_source (self, source):
        debug ("In PolyDataNormals::set_input_source ()")
        Common.state.busy ()
        self.prev_filter = source
        self._set_input ()
        self.fil.Update ()
        Common.state.idle ()

    def configure (self, master=None):
        """Configures the filter using a ConfigVtkObj instance."""
        debug ("In Filter::configure ()")
        c = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        c.set_update_method (self.mod_m.Update)
        c.configure (self.root, self.fil)
        c.root.transient (master)

