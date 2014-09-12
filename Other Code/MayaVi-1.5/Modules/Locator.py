"""

This module creates a 'Locator' axis, that can be used to mark a three
dimensional point in your data.

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

class Locator (Base.Objects.Module):

    """ This module creates a 'Locator' axis, that can be used to mark
    a three dimensional point in your data. """

    def __init__ (self, mod_m):
        debug ("In Locator::__init__ ()")
        Common.state.busy ()
        Base.Objects.Module.__init__ (self, mod_m)
        self.axes = vtk.vtkAxes ()
        self.axes.SymmetricOn ()
        self.mapper = self.ax_map = vtk.vtkPolyDataMapper ()
        self.ax_map.SetInput (self.axes.GetOutput ())
        self.actor = self.locator = vtk.vtkActor ()
        self.locator.SetMapper (self.ax_map)
        self.locator.GetProperty ().SetLineWidth (3.0)
        self.locator.GetProperty ().SetColor (*Common.config.fg_color)
        
        self.root = None
        self.resoln_var = []
        self.slider = []
        for i in range (3):
            self.resoln_var.append (Tkinter.DoubleVar ())

        self.coord_var = Tkinter.StringVar ()
        self.locator_var = Tkinter.IntVar ()
        self.scale_var = Tkinter.DoubleVar ()
        self.data_out = self.mod_m.GetOutput ()        
        self._initialize ()
        self.axes.SetOrigin (self.def_dim[0], self.def_dim[1], 
                             self.def_dim[2])
        self.axes.SetScaleFactor (self.max_len*0.3)
        self.actor.GetProperty().SetAmbient(1.0)
        self.actor.GetProperty().SetDiffuse(0.0)
        self.renwin.add_actors (self.locator)
        self.pipe_objs = self.locator
        self.renwin.Render ()
        Common.state.idle ()
        
    def _initialize (self):
        debug ("In Locator::_initialize ()")
        self.def_dim = []
        self.dim = []
        self.coord = [0, 0, 0]
        dim1 = self.data_out.GetBounds ()
        self.max_len = -1.0
        for i in range (3):
            self.dim.append ((dim1[2*i], dim1[2*i+1]))
            val = dim1[2*i] + dim1[2*i+1]
            self.def_dim.append (val*0.5)
            mag = abs (dim1[2*i]) + abs (dim1[2*i+1])
            if mag > self.max_len:
                self.max_len = mag
            self.resoln_var[i].set (mag*0.01)
            if dim1[2*i] != dim1[2*i+1]:
                self.coord[i] = 1
        self.set_resolution ()

    def __del__ (self):
        debug ("In Locator::__del__ ()")
        if self.locator:
            self.renwin.remove_actors (self.locator)
        self.renwin.Render ()        

    def SetInput (self, source):
        debug ("In Locator::SetInput ()")
        Common.state.busy ()
        self.data_out = source
        self._initialize ()
        Common.state.idle ()        

    def save_config (self, file): 
        debug ("In Locator::save_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.axes, self.ax_map, self.locator,
                    self.locator.GetProperty ()):
            p.dump (obj, file)

    def load_config (self, file): 
        debug ("In Locator::load_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.axes, self.ax_map, self.locator,
                    self.locator.GetProperty ()):
            p.load (obj, file)

        self._initialize ()
        self.renwin.Render ()
        
    def config_changed (self): 
        debug ("In Locator::config_changed ()")
        self.locator.GetProperty ().SetColor (*Common.config.fg_color)

    def make_main_gui (self):
        debug ("In Locator::make_main_gui ()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', pady=2, fill='both', expand=1)
        self.locator_var.set (self.locator.GetVisibility())
        locator_but = Tkinter.Checkbutton (frame,
                                           text="Toggle Locator Axis", 
                                           variable=self.locator_var,
                                           onvalue=1, offvalue=0,
                                           command=self.set_locator)
        locator_but.grid (row=0, column=0, columnspan=3,
                          pady=4, sticky='w')

        rw = 1
        self.scale_var.set (self.axes.GetScaleFactor ())
        lab = Tkinter.Label (frame, text="Scale Factor: ")
        lab.grid (row=rw, column=0, columnspan=1, sticky='w', pady=4)
        entr = Tkinter.Entry (frame, width=10, relief='sunken', 
                              textvariable=self.scale_var)
        entr.grid (row=rw, column=1, columnspan=2, sticky='w', pady=4)
        entr.bind ("<Return>", self.set_scale_factor)
        rw = rw + 1
        
        self.coord_var.set (self.axes.GetOrigin ())
        lab = Tkinter.Label (frame, text="Locator position:")
        lab.grid (row=rw, column=0, columnspan=1, sticky='w')
        entr = Tkinter.Entry (frame, width=20, relief='sunken', 
                              textvariable=self.coord_var)
        entr.grid (row=rw, column=1, columnspan=2, sticky='w')
        rw = rw + 1

        def_name = ["Move along X-axis", "Move along Y-axis ", 
                    "Move along Z-axis"]
        res_name = ["X resolution:", "Y resolution:", "Z resolution:"]
        pos = self.axes.GetOrigin ()
        
        for i in range (0,3):
            if self.coord[i] == 1:
                sl = Tkinter.Scale (frame, label=def_name[i], 
                                    from_=self.dim[i][0], to=self.dim[i][1],
                                    length="8c", orient='horizontal', 
                                    resolution=self.resoln_var[i].get ())
                sl.set (pos[i])
                sl.grid (row=rw, column=0, columnspan=3, sticky='ew')
                rw = rw + 1
                sl.bind ("<ButtonRelease>", self.change_locator)
                lab = Tkinter.Label (frame, text=res_name[i])
                lab.grid (row=rw, column=0, sticky='w')
                entr = Tkinter.Entry (frame, width=5, relief='sunken',
                                      textvariable=self.resoln_var[i])
                entr.grid (row=rw, column=1, sticky='w')
                entr.bind ("<Return>", self.set_resolution)
                rw = rw+1
                self.slider.append (sl) 

        self.make_actor_gui (representation=0)

    def set_locator (self, event=None):
        debug ("In Locator::set_locator ()")
        self.locator.SetVisibility (self.locator_var.get ())
        self.renwin.Render ()

    def change_locator (self, event=None):
        debug ("In Locator::change_locator ()")
        val = []
        for i in range (0, 3):
            if self.coord[i] == 1:
                val.append (self.slider[i].get ())
            else:
                val.append (self.def_dim[i])
        
        self.axes.SetOrigin (*val)
        self.coord_var.set (val)
        self.renwin.Render ()
        
    def set_resolution (self, event=None):
        debug ("In Locator::set_resolution ()")
        if self.slider:
            for i in range (3):
                if self.coord[i] == 1:
                    val = self.resoln_var[i].get ()
                    self.slider[i].config (resolution=val)

    def set_scale_factor (self, event=None):
        debug ("In Locator::set_scale_factor ()")
        self.axes.SetScaleFactor (self.scale_var.get ())
        self.renwin.Render ()

    def close_gui (self, event=None):
        debug ("In Locator::close_gui ()")
        Base.Objects.VizObject.close_gui (self, event)
        self.slider = []
