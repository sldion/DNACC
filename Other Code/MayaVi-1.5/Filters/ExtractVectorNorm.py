"""

This wraps the vtkVectorNorm filter and produces an output scalar data
with the magnitude of the vector.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.5 $"
__date__ = "$Date: 2005/08/02 18:26:25 $"

import Base.Objects, Common
import vtk
import vtkPipeline.ConfigVtkObj

debug = Common.debug

class ExtractVectorNorm (Base.Objects.Filter):

    """ This wraps the vtkVectorNorm filter and produces an output
    scalar data with the magnitude of the vector. """

    def initialize (self):
        debug ("In ExtractVectorNorm::initialize ()")
        self.fil = vtk.vtkVectorNorm ()
        self.fil.SetInput (self.prev_fil.GetOutput ())
        self.fil.Update ()

    def set_input_source (self, source):
        debug ("In ExtractVectorNorm::set_input_source ()")
        Common.state.busy ()
        self.fil.SetInput (source.GetOutput ())
        self.prev_filter = source
        Common.state.idle ()

    def get_scalar_data_name (self):
        debug ("In ExtractVectorNorm::get_scalar_data_name ()")
        name = self.prev_fil.get_vector_data_name ()
        return name + ' magnitude'

    def configure (self, master=None):
        debug ("In ExtractVectorNorm::configure ()")
        c = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        c.set_update_method (self.mod_m.Update)
        c.configure (self.root, self.fil)
        c.root.transient (master)

