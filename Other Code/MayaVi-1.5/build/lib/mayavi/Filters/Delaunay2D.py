"""
This filter wraps around the vtkDelaunay2D filter and lets you do 2D
triangulation of a collection of points.  The key parameters are
Tolerance and the Alpha value.  Tolerance gives the criteria for
joining neighbouring data points and alpha is the threshold for the
circumference of a caluculated triangulated polygon.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__= "$Revision: 1.2 $"
__date__   = "$Date: 2005/08/02 18:26:24 $"

import Base.Objects, Common
import Tkinter
import vtk
import vtkPipeline.ConfigVtkObj

debug = Common.debug

class Delaunay2D(Base.Objects.Filter):
    
    """ This filter wraps around the vtkDelaunay2D filter and lets you
    do 2D triangulation of a collection of points.  The key parameters
    are Tolerance and the Alpha value.  Tolerance gives the criteria
    for joining neighbouring data points and alpha is the threshold
    for the circumference of a caluculated triangulated polygon.  """
    
    def initialize(self):
        debug("In Delaunay2D::initialize()")
        self.fil = vtk.vtkDelaunay2D()
        self.fil.SetInput(self.prev_fil.GetOutput())
        self.fil.Update()

    def set_input_source(self, source):
        debug("In Delaunay2D::set_input_source ()")
        Common.state.busy()
        self.fil.SetInput(source.GetOutput ())
        self.prev_filter = source
        self.fil.Update()
        Common.state.idle()
        
    def configure(self, master=None):
        debug("In Delaunay2D::configure ()")
        c = vtkPipeline.ConfigVtkObj.ConfigVtkObj(self.renwin)
        c.configure(self.root, self.fil, get=[], toggle=['!AbortExecuteOn'],
                    one_frame=1, run_command=0, auto_update=1)
        c.root.transient(master)
