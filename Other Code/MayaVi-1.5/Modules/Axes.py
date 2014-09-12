"""

This module creates and manages a set of three axes for your data.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.11 $"
__date__ = "$Date: 2005/08/02 18:30:13 $"

import Common, Base.Objects
import Tkinter, tkColorChooser
import vtk
import vtkPipeline.vtkMethodParser

debug = Common.debug

class Axes (Base.Objects.Module):

    """ This module creates and manages a set of three axes for your
    data.  The class uses a vtkCubeAxesActor2D."""

    def __init__ (self, mod_m):
        debug ("In Axes::__init__ ()")
        Common.state.busy ()
        Base.Objects.Module.__init__ (self, mod_m)
        self.axes = vtk.vtkCubeAxesActor2D ()
        txt = ("X", "Y", "Z")
        for i in range (0, 3):
            eval ("self.axes.%sAxisVisibilityOn ()"%(txt[i]))

        self.axes.SetNumberOfLabels (2)
        self.axes.SetFontFactor (1.35)
        self.axes.SetFlyModeToOuterEdges ()
        self.axes.SetCornerOffset (0.0)
        self.axes.ScalingOff ()
        self.axes.GetProperty ().SetColor (*Common.config.fg_color)
        self.axes.SetCamera (self.renwin.get_active_camera ())
        if hasattr(self.axes, "GetAxisTitleTextProperty"):
            ttp = self.axes.GetAxisTitleTextProperty()
            ltp = self.axes.GetAxisLabelTextProperty()
            ttp.ShadowOff()
            fg_color = Common.config.fg_color
            ttp.SetColor(fg_color)
            ltp.SetColor(fg_color)
            ltp.ShadowOff()
        else:
            self.axes.ShadowOff ()
        self.renwin.add_actors (self.axes)
        self.axes.SetInput (self.mod_m.GetOutput ())
        self.actor = self.axes
        # used for the pipeline browser
        self.pipe_objs = self.axes
        self._gui_init ()
        Common.state.idle ()

    def _gui_init (self):
        debug ("In Axes::_gui_init ()")
        self.root = None
        txt = ("X", "Y", "Z")
        self.axis_on_var = []
        self.axis_txt_var = []
        for i in range (0, 3):
            self.axis_on_var.append (Tkinter.IntVar ())
            self.axis_txt_var.append (Tkinter.StringVar ())

        self.n_lab = Tkinter.IntVar ()
        self.font_sz = Tkinter.DoubleVar ()
        self.mode_var = Tkinter.IntVar ()
        self.offset_var = Tkinter.DoubleVar ()
        self.shadow_on_var = Tkinter.IntVar ()
        self.scaling_on_var = Tkinter.IntVar ()
        self._gui_vars_init ()

    def _gui_vars_init (self):
        debug ("In Axes::_gui_vars_init ()")
        txt = ("X", "Y", "Z")
        for i in range (0, 3):
            val = eval ("self.axes.Get%sAxisVisibility ()"%txt[i])
            self.axis_on_var[i].set (val)
            val = eval ("self.axes.Get%sLabel()"%txt[i])
            self.axis_txt_var[i].set (val)

        self.n_lab.set (self.axes.GetNumberOfLabels ())
        self.font_sz.set (self.axes.GetFontFactor ())
        self.mode_var.set (self.axes.GetFlyMode ())
        self.offset_var.set (self.axes.GetCornerOffset ())
        if hasattr(self.axes, "GetAxisTitleTextProperty"):
            self.shadow_on_var.set (self.axes.GetAxisTitleTextProperty().GetShadow ())
        else:
            self.shadow_on_var.set (self.axes.GetShadow ())
        self.scaling_on_var.set (self.axes.GetScaling ())        
        self.renwin.Render ()

    def __del__ (self): 
        debug ("In Axes::__del__ ()")
        if self.axes:
            self.renwin.remove_actors (self.axes)
        self.renwin.Render ()

    def SetInput (self, source):
        debug ("In Axes::SetInput ()")
        Common.state.busy ()
        self.axes.SetInput (source)
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In Axes::save_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.axes, self.axes.GetProperty ()):
            p.dump (obj, file)

    def load_config (self, file): 
        debug ("In Axes::load_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.axes, self.axes.GetProperty ()):
            p.load (obj, file)

        if hasattr(self.axes, "GetAxisTitleTextProperty"):
            clr = self.axes.GetProperty().GetColor()
            self.axes.GetAxisTitleTextProperty().SetColor(clr)
            self.axes.GetAxisLabelTextProperty().SetColor(clr)

        self._gui_vars_init ()

    def config_changed (self): 
        debug ("In Axes::config_changed ()")
        fg_color = Common.config.fg_color
        self.axes.GetProperty ().SetColor (fg_color)
        if hasattr(self.axes, "GetAxisTitleTextProperty"):
            self.axes.GetAxisTitleTextProperty().SetColor(fg_color)
            self.axes.GetAxisLabelTextProperty().SetColor(fg_color)
        
    def make_main_gui (self):
        debug ("In Axes::make_main_gui ()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)
        txt = ("X-Axis", "Y-Axis", "Z-Axis")
        for i in range (0, 3):
            b = Tkinter.Checkbutton (frame, text=txt[i], 
                                     variable=self.axis_on_var[i],
                                     onvalue=1, offvalue=0,
                                     command=self.setup)
            b.grid (row=i, columnspan=2)

        txt = ("X-Axis label:", "Y-Axis label:", "Z-Axis label:")
        rw = 3
        for i in range (0, 3):
            lab = Tkinter.Label (frame, text=txt[i])
            lab.grid (row=rw+i, column=0, sticky='w')
            entr = Tkinter.Entry (frame, width=10, relief='sunken', 
                                  textvariable=self.axis_txt_var[i])
            entr.grid (row=rw+i, column=1)
            entr.bind ("<Return>", self.setup)
        
        rw = 6
        lab = Tkinter.Label (frame, text="Number of labels")
        lab.grid (row=rw, column=0, sticky='w')
        entr = Tkinter.Entry (frame, width=10, relief='sunken', 
                              textvariable=self.n_lab)
        entr.grid (row=rw, column=1)
        entr.bind ("<Return>", self.setup)
        
        rw = 7
        lab = Tkinter.Label (frame, text="Font size factor")
        lab.grid (row=rw, column=0, sticky='w')
        entr = Tkinter.Entry (frame, width=10, relief='sunken', 
                              textvariable=self.font_sz)
        entr.grid (row=rw, column=1)
        entr.bind ("<Return>", self.setup)

        rw = 8
        lab = Tkinter.Label (frame, text="Offset from corner")
        lab.grid (row=rw, column=0, sticky='w')
        entr = Tkinter.Entry (frame, width=10, relief='sunken', 
                              textvariable=self.offset_var)
        entr.grid (row=rw, column=1)
        entr.bind ("<Return>", self.change_offset)

        rw = 9
        rb = Tkinter.Radiobutton (frame, text="Fly mode to outer edges", 
                                  variable=self.mode_var, value=0, 
                                  command=self.set_fly_mode)
        rb.grid (row=rw, columnspan=2, sticky='w')
        rw = 10
        rb = Tkinter.Radiobutton (frame, text="Fly mode to closest triad", 
                                  variable=self.mode_var, value=1, 
                                  command=self.set_fly_mode)
        rb.grid (row=rw, columnspan=2, sticky='w')
        rw = rw + 1
        b = Tkinter.Checkbutton (frame, text="Shadow Axis", 
                                 variable=self.shadow_on_var,
                                 onvalue=1, offvalue=0,
                                 command=self.set_shadow)
        b.grid (row=rw, columnspan=2, sticky='w')
        rw = rw + 1
        b = Tkinter.Checkbutton (frame, text="Scale to fit screen", 
                                 variable=self.scaling_on_var,
                                 onvalue=1, offvalue=0,
                                 command=self.set_scaling)
        b.grid (row=rw, columnspan=2, sticky='w')
        
        self.make_actor_gui (scalar=0, representation=0)

    def setup (self, event=None):
        debug ("In Axes::setup ()")
        Common.state.busy ()
        txt = ("X", "Y", "Z")
        for i in range (0, 3):
            val = self.axis_on_var[i].get ()
            eval ("self.axes.Set%sAxisVisibility (val)"%txt[i])
            # Setting the labels
            str = self.axis_txt_var[i].get ()
            eval ("self.axes.Set%sLabel"%(txt[i]))(str)

        self.axes.SetNumberOfLabels (self.n_lab.get ())
        self.axes.SetFontFactor (self.font_sz.get ())
        self.renwin.Render ()
        Common.state.idle ()

    def set_shadow (self, event=None):
        debug ("In Axes::set_shadow ()")
        shadow = self.shadow_on_var.get()
        if hasattr(self.axes, "GetAxisTitleTextProperty"):
            self.axes.GetAxisTitleTextProperty().SetShadow (shadow)
            self.axes.GetAxisLabelTextProperty().SetShadow (shadow)
            
        else:
            self.axes.SetShadow (shadow)
        self.renwin.Render ()
        
    def set_scaling (self, event=None):
        debug ("In Axes::set_scaling ()")
        self.axes.SetScaling (self.scaling_on_var.get ())
        self.renwin.Render ()

    def set_fly_mode (self, event=None):
        debug ("In Axes::set_fly_mode ()")
        self.axes.SetFlyMode (self.mode_var.get ())
        self.renwin.Render ()

    def change_offset (self, event=None): 
        debug ("In Axes::change_offset ()")
        self.axes.SetCornerOffset (self.offset_var.get ())
        self.renwin.Render ()

    def change_color (self, event=None):
        debug ("In Axes::change_color ()")
        clr = self.axes.GetProperty ().GetColor ()
        init_clr = "#%02x%02x%02x"%(clr[0]*255, clr[1]*255, clr[2]*255)
        color = tkColorChooser.askcolor (title="Change axes color", 
                                         initialcolor=init_clr)
        if color[1] is not None:
            clr = Common.tk_2_vtk_color (color[0])
            self.axes.GetProperty ().SetColor (*clr)
            if hasattr(self.axes, "GetAxisTitleTextProperty"):
                self.axes.GetAxisTitleTextProperty().SetColor(clr)
                self.axes.GetAxisLabelTextProperty().SetColor(clr)
            self.renwin.Render ()
