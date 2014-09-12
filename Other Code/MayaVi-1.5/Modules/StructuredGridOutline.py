"""

Displays an Outline for a structured grid.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.6 $"
__date__ = "$Date: 2005/08/02 18:30:13 $"

import Base.Objects, Common
import Tkinter, tkColorChooser
import vtk
import vtkPipeline.vtkMethodParser

debug = Common.debug

class StructuredGridOutline (Base.Objects.Module):
    """ Displays an Outline for a structured grid."""
    def __init__ (self, mod_m):
        debug ("In StructuredGridOutline::__init__ ()")
        Common.state.busy ()
        Base.Objects.Module.__init__ (self, mod_m)
        self.act = None
        data_src = self.mod_m.get_data_source ()
        self.type = data_src.get_grid_type ()

        if self.type != "STRUCTURED_GRID":
            msg = "This module does not support the %s dataset."%(self.type)
            msg = msg + "\nOnly STRUCTURED_GRID data is supported by "\
                  "this module."
            raise Base.Objects.ModuleException, msg

        self.outline = vtk.vtkStructuredGridOutlineFilter ()
        self.outline.SetInput (mod_m.GetOutput ())
        self.mapper = self.map = vtk.vtkPolyDataMapper ()
        self.map.SetInput (self.outline.GetOutput ())
        self.map.SetScalarVisibility (0)
        self.actor = self.act = vtk.vtkActor ()  
        self.act.SetMapper (self.map)
        self.act.GetProperty ().SetColor (*Common.config.fg_color)
        self.renwin.add_actors (self.act)
        # used for the pipeline browser
        self.pipe_objs = self.act
        self.renwin.Render ()
        Common.state.idle ()

    def __del__ (self): 
        debug ("In StructuredGridOutline::__del__ ()")
        if self.act:
            self.renwin.remove_actors (self.act)
        self.renwin.Render ()

    def SetInput (self, source): 
        debug ("In StructuredGridOutline::SetInput ()")
        Common.state.busy ()
        self.outline.SetInput (source)
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In StructuredGridOutline::save_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.act, self.act.GetProperty ()):
            p.dump (obj, file)

    def load_config (self, file): 
        debug ("In StructuredGridOutline::load_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.act, self.act.GetProperty ()):
            p.load (obj, file)
        
    def config_changed (self): 
        debug ("In StructuredGridOutline::config_changed ()")
        self.act.GetProperty ().SetColor (*Common.config.fg_color)

    def make_main_gui (self): 
        debug ("In StructuredGridOutline::make_main_gui ()")
        "Create the GUI configuration controls for this object."
        self.make_actor_gui (representation=0, scalar=0)
