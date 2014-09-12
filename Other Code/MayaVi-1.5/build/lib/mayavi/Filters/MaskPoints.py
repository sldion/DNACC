"""

This wraps the vtkMaskPoints filter.  The problem with this filter is
that its output is Polygonal data.  This means that if you add this
filter to a ModuleManager with visualizations apart from HedgeHog or
other velocity vector data you won't see anything!  If that happens
create another ModuleManager and show the other visualizations
there. Also, this means that this filter should be typically inserted
at the end of the list of filters.

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

class MaskPoints (Base.Objects.Filter):

    """ This wraps the vtkMaskPoints filter.  The problem with this
    filter is that its output is Polygonal data.  This means that if
    you add this filter to a ModuleManager with visualizations apart
    from HedgeHog or other velocity vector data you won't see
    anything!  If that happens create another ModuleManager and show
    the other visualizations there. Also, this means that this filter
    should be typically inserted at the end of the list of filters."""

    def initialize (self):
        debug ("In MaskPoints::__init__ ()")
        self.fil = vtk.vtkMaskPoints ()
        self.fil.SetInput (self.prev_fil.GetOutput ())
        self.fil.Update ()        

    def set_input_source (self, source):
        debug ("In MaskPoints::set_input_source ()")
        Common.state.busy ()
        self.fil.SetInput (source.GetOutput ())
        self.prev_filter = source
        self.fil.Update ()
        Common.state.idle ()

    def configure (self, master=None):
        debug ("In MaskPoints::configure ()")
        c = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        c.set_update_method (self.mod_m.Update)
        c.configure (self.root, self.fil)
        c.root.transient (master)
