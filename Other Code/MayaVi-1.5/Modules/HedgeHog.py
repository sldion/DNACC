"""

This module shows the given vector data as a 'hedge hog' plot.  The
lines can be colored based on the input scalar data.  This class
should work with any dataset.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.6 $"
__date__ = "$Date: 2005/08/02 18:30:13 $"

import Base.Objects, Common
import Tkinter, tkColorChooser
import vtk, math
import vtkPipeline.vtkMethodParser

debug = Common.debug

class HedgeHog (Base.Objects.Module):

    """ This module shows the given vector data as a 'hedge hog' plot.
    The lines can be colored based on the input scalar data.  This
    class should work with any dataset.  """

    def __init__ (self, mod_m):
        debug ("In HedgeHog::__init__ ()")
        Common.state.busy ()
        Base.Objects.Module.__init__ (self, mod_m)
        self.root = None
        self.hhog = vtk.vtkHedgeHog ()
        self.mapper = self.map = vtk.vtkPolyDataMapper ()
        self.actor  = self.act = vtk.vtkActor ()
        self._initialize ()
        self.renwin.Render ()
        Common.state.idle ()

    def __del__ (self): 
        debug ("In HedgeHog::__del__ ()")
        if self.act:
            self.renwin.remove_actors (self.act)
        self.renwin.Render ()

    def _initialize (self):
        debug ("In HedgeHog::_initialize ()")
        self.step_size = 1.0
        self.scale = 1.0
        self.color_mode = 1
        self.find_def_step_size ()
        self.hhog.SetInput (self.mod_m.GetOutput ())
        self.hhog.SetScaleFactor (self.scale)
        self.map.SetInput (self.hhog.GetOutput ())
        self.do_color_mode ()
        self.act.SetMapper (self.map)
        self.act.GetProperty ().SetColor (*Common.config.fg_color)
        # used for the pipeline browser
        self.pipe_objs = self.act
        self.renwin.add_actors (self.act)

    def find_def_step_size (self):
        debug ("In HedgeHog::find_def_step_size ()")
        out = self.mod_m.GetOutput ()
        bnd = out.GetBounds ()
        n = out.GetNumberOfCells ()
        if not n:
            n = out.GetNumberOfPoints ()
        data_2d = 0
        vol = 1.0
        for i in range (0,3):
            l = abs (bnd[2*i+1] - bnd[2*i])
            if l == 0.0:
                data_2d=1
            else:
                vol = vol*l
        
        l = vol/n
        if data_2d == 1:
            self.step_size = math.sqrt (l)
        else:
            self.step_size = math.pow (l, 1.0/3.0)

        self.scale = 2.0*self.step_size

    def SetInput (self, source): 
        debug ("In HedgeHog::SetInput ()")
        Common.state.busy ()
        self.hhog.SetInput (source)
        self.do_color_mode ()
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In HedgeHog::save_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.hhog, self.map, self.act,
                    self.act.GetProperty ()):
            p.dump (obj, file)

    def load_config (self, file): 
        debug ("In HedgeHog::load_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.hhog, self.map, self.act,
                    self.act.GetProperty ()):
            p.load (obj, file)
        self.color_mode = self.map.GetScalarVisibility ()
        self.do_color_mode ()
        
    def config_changed (self): 
        debug ("In HedgeHog::config_changed ()")
        self.act.GetProperty ().SetColor (*Common.config.fg_color)

    def make_main_gui (self, master=None): 
        debug ("In HedgeHog::make_main_gui ()")
        "Create the GUI configuration controls for this object."
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', pady=2, fill='both', expand=1)
        labl = Tkinter.Label (frame, text="Line scale factor:")
        labl.grid (row=0, column=0, sticky='w')

        self.scale_var = Tkinter.DoubleVar ()
        self.scale_var.set (self.hhog.GetScaleFactor ())
        scale_entr = Tkinter.Entry (frame, width=5, relief='sunken',
                                    textvariable=self.scale_var)
        scale_entr.grid (row=0, column=1, sticky='we')
        scale_entr.bind ("<Return>", self.change_scale)

        self.make_color_mode_gui ()
        self.make_actor_gui (color=0, scalar=0, representation=0)

    def make_color_mode_gui (self):
        debug ("In HedgeHog::make_color_mode_gui ()")
        frame = Tkinter.Frame (self.root, relief="ridge", bd=2)
        frame.pack (side='top')
        lab = Tkinter.Label (frame, text="Coloring mode:")
        lab.grid (row=0, column=0, sticky='ew', pady=5)

        self.color_var = Tkinter.IntVar ()
        self.color_var.set (self.color_mode)
        rb = Tkinter.Radiobutton (frame, text="No Coloring",
                                  variable=self.color_var, value=0,
                                  command=self.set_color_mode_gui)
        rb.grid (row=1, column=0, sticky='w')
        rb = Tkinter.Radiobutton (frame, text="Scalar Coloring",
                                  variable=self.color_var, value=1,
                                  command=self.set_color_mode_gui)
        rb.grid (row=2, column=0, sticky='w')
        but = Tkinter.Button (frame, text="Line Color",
                              command=self.set_line_color)
        but.grid (row=3, column=0, sticky='ew')

    def change_scale (self, event=None):
        debug ("In HedgeHog::change_scale ()")
        Common.state.busy ()
        self.hhog.SetScaleFactor (self.scale_var.get ())
        self.renwin.Render ()
        Common.state.idle ()    

    def set_color_mode_gui (self, event=None):
        "This sets up the data to setup the actual coloring mode."
        debug ("In HedgeHog::set_color_mode_gui ()")
        Common.state.busy ()
        self.color_mode = self.color_var.get ()
        self.do_color_mode ()
        self.renwin.Render ()
        Common.state.idle ()

    def do_color_mode (self):
        debug ("In HedgeHog::do_color_mode ()")
        if self.color_mode == 1: # Scalar Coloring
            self.map.ScalarVisibilityOn ()
            dr = self.mod_m.get_scalar_data_range ()
            self.map.SetScalarRange (dr)
            self.map.SetLookupTable (self.mod_m.get_scalar_lut ())
        elif self.color_mode == 0: # No colouring
            self.map.ScalarVisibilityOff ()

    def set_line_color (self, event=None):
        debug ("In HedgeHog::set_line_color ()")
        clr = self.act.GetProperty ().GetColor ()
        init_clr = "#%02x%02x%02x"%(clr[0]*255, clr[1]*255, clr[2]*255)
        color = tkColorChooser.askcolor (title="Change axes color", 
                                         initialcolor=init_clr)
        if color[1] is not None:
            Common.state.busy ()
            clr = Common.tk_2_vtk_color (color[0])
            self.act.GetProperty ().SetColor (*clr)
            self.renwin.Render ()        
            Common.state.idle ()
            if self.color_mode != 0:
                msg = "Warning: This setting will have effect only if "\
                      "the coloring mode is set to 'No Coloring'."
                Common.print_err (msg)
