"""

Displays an Outline for any data input.

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

class Outline (Base.Objects.Module):
    """ Displays an Outline for any data input."""
    def __init__ (self, mod_m):
        debug ("In Outline::__init__ ()")
        Common.state.busy ()
        Base.Objects.Module.__init__ (self, mod_m)
        data_src = self.mod_m.get_data_source ()
        self.type = data_src.get_grid_type ()
        self.outline = vtk.vtkOutlineFilter ()
        self.outline.SetInput (mod_m.GetOutput ())
        self.mapper = self.map = vtk.vtkPolyDataMapper ()
        self.map.SetInput (self.outline.GetOutput ())
        self.actor = self.act = vtk.vtkActor ()  
        self.act.SetMapper (self.map)
        self.act.GetProperty ().SetColor (*Common.config.fg_color)
        self.renwin.add_actors (self.act)
        # used for the pipeline browser
        self.pipe_objs = self.act
        self.renwin.Render ()
        Common.state.idle ()

    def __del__ (self): 
        debug ("In Outline::__del__ ()")
        if self.act:
            self.renwin.remove_actors (self.act)
        self.renwin.Render ()

    def SetInput (self, source): 
        debug ("In Outline::SetInput ()")
        Common.state.busy ()
        self.outline.SetInput (source)
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In Outline::save_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.act, self.act.GetProperty ()):
            p.dump (obj, file)

    def load_config (self, file): 
        debug ("In Outline::load_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.act, self.act.GetProperty ()):
            p.load (obj, file)
        # need this in case you load the module for different data.
        self.outline.SetInput (self.mod_m.GetOutput ())
        self.renwin.Render ()
        
    def config_changed (self): 
        debug ("In Outline::config_changed ()")
        self.act.GetProperty ().SetColor (*Common.config.fg_color)

    def make_main_gui (self):
        debug ("In Outline::make_main_gui ()")
        "Create the GUI configuration controls for this object."
        self.make_actor_gui (representation=0, scalar=0)
