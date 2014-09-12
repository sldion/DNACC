"""

Displays any input polydata, nothing fancy.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.7 $"
__date__ = "$Date: 2005/08/02 18:30:13 $"

import Base.Objects, Common
import Tkinter, tkColorChooser
import vtk
import vtkPipeline.vtkMethodParser

debug = Common.debug

class PolyData (Base.Objects.Module):
    """ Displays any input polydata, nothing fancy."""
    def __init__ (self, mod_m):
        debug ("In PolyData::__init__ ()")
        Common.state.busy ()
        Base.Objects.Module.__init__ (self, mod_m)
        self.act = None
        out = mod_m.GetOutput ()
        if not out.IsA('vtkPolyData'):
            typ = out.__class__.__name__
            msg = "This module does not support the %s dataset."%(typ)
            msg = msg + "\nOnly POLYDATA is supported."
            raise Base.Objects.ModuleException, msg

        self.root = None
        self.mapper = self.map = vtk.vtkPolyDataMapper ()
        self.map.SetInput (mod_m.GetOutput ())
        self.map.SetLookupTable (self.mod_m.get_scalar_lut ())
        self.data_range = self.mod_m.get_scalar_data_range ()
        self.map.SetScalarRange (self.data_range)
        self.actor = self.act = vtk.vtkActor ()  
        self.act.SetMapper (self.map)
        self.act.GetProperty ().SetColor (0.0, 0.1, 0.8)
        # used for the pipeline browser
        self.pipe_objs = self.act
        self.renwin.add_actors (self.act)
        self.renwin.Render ()
        Common.state.idle ()

    def __del__ (self): 
        debug ("In PolyData::__del__ ()")
        if self.act:
            self.renwin.remove_actors (self.act)
        self.renwin.Render ()

    def SetInput (self, source): 
        debug ("In PolyData::SetInput ()")
        Common.state.busy ()
        self.map.SetInput (source)
        dr = self.mod_m.get_scalar_data_range ()
        if (dr[0] != self.data_range[0]) or (dr[1] != self.data_range[1]):
            self.map.SetScalarRange (dr)
            self.data_range = dr
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In PolyData::save_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.map, self.act, self.act.GetProperty ()):
            p.dump (obj, file)

    def load_config (self, file): 
        debug ("In PolyData::load_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.map, self.act, self.act.GetProperty ()):
            p.load (obj, file)
        
    def config_changed (self): 
        debug ("In PolyData::config_changed ()")
        self.act.GetProperty ().SetColor (*Common.config.fg_color)

    def make_main_gui (self, master=None): 
        debug ("In PolyData::make_main_gui ()")
        "Create the GUI configuration controls for this object."
        self.make_actor_gui ()

