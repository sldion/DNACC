"""

This wraps the vtkExtractUnstructuredGrid filter.  From the VTK docs:
vtkExtractUnstructuredGrid is a general-purpose filter to extract
geometry (and associated data) from an unstructured grid dataset. The
extraction process is controlled by specifying a range of point ids,
cell ids, or a bounding box (referred to as 'Extent').  Those cells
lying within these regions are sent to the output.  The user has the
choice of merging coincident points (Merging is on) or using the
original point set (Merging is off).

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.3 $"
__date__ = "$Date: 2005/08/02 18:26:24 $"

__credits__ = """Many thanks to Dr. Jean M. Favre <jfavre@cscs.ch> and
David Garcia <dgarcia@cscs.ch> of the Swiss Center for Scientific
Computing who provided a module that used this feature and encouraged
me to write this filter."""

import Base.Objects, Common
import vtk
import vtkPipeline.ConfigVtkObj

debug = Common.debug

class ExtractUnstructuredGrid (Base.Objects.Filter):

    """ This wraps the vtkExtractUnstructuredGrid filter.  From the
    VTK docs: vtkExtractUnstructuredGrid is a general-purpose filter
    to extract geometry (and associated data) from an unstructured
    grid dataset. The extraction process is controlled by specifying a
    range of point ids, cell ids, or a bounding box (referred to as
    'Extent').  Those cells lying within these regions are sent to the
    output.  The user has the choice of merging coincident points
    (Merging is on) or using the original point set (Merging is
    off)."""

    def initialize (self):
        debug ("In ExtractUnstructuredGrid::__init__ ()")
        self.fil = vtk.vtkExtractUnstructuredGrid ()
        self.fil.SetInput (self.prev_fil.GetOutput ())
        self.fil.Update ()        

    def set_input_source (self, source):
        debug ("In ExtractUnstructuredGrid::set_input_source ()")
        Common.state.busy ()
        self.fil.SetInput (source.GetOutput ())
        self.prev_filter = source
        self.fil.Update ()
        Common.state.idle ()

    def configure (self, master=None):
        debug ("In ExtractUnstructuredGrid::configure ()")
        c = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        c.set_update_method (self.mod_m.Update)
        c.configure (self.root, self.fil)
        c.root.transient (master)
