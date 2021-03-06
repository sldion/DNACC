"""

This module displays cone glyphs scaled and colored as per the
vector or scalar data on a cut plane.  This will work for any
dataset.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.10 $"
__date__ = "$Date: 2005/08/02 18:30:13 $"

import Base.Objects, Common
import Tkinter, tkColorChooser, math
import vtk
import vtkPipeline.vtkMethodParser
import vtkPipeline.ConfigVtkObj

debug = Common.debug

class VectorCutPlane (Base.Objects.CutPlaneModule):

    """ This module displays cone glyphs scaled and colored as per the
    vector or scalar data on cut plane.  This will work for any
    dataset. """

    def __init__ (self, mod_m): 
        debug ("In VectorCutPlane::__init__ ()")
        Common.state.busy ()
        Base.Objects.CutPlaneModule.__init__ (self, mod_m)
        self.cut = vtk.vtkCutter ()
        self.glyph2d_src = vtk.vtkGlyphSource2D ()
        self.cone = vtk.vtkConeSource ()
        self.arrow = vtk.vtkArrowSource ()
        self.glyph_src = self.cone
        self.glyph3d = vtk.vtkGlyph3D ()
        self.mapper = self.map = vtk.vtkPolyDataMapper ()
        self.actor = self.act = vtk.vtkActor ()
        # used to orient the cone properly
        self.glph_trfm = vtk.vtkTransformFilter ()
        self.glph_trfm.SetTransform (vtk.vtkTransform ())
        self.data_out = self.mod_m.GetOutput ()

        # Point of glyph that is attached -- -1 is tail, 0 is center,
        # 1 is head.
        self.glyph_pos = -1 
        self.scale = 1.0
        self.color_mode = 2 #2 is vector, 1 is scalar, -1 none
        self._initialize ()
        self._gui_init ()
        self.renwin.Render ()
        Common.state.idle ()

    def __del__ (self): 
        debug ("In VectorCutPlane::__del__ ()")
        if self.act:
            self.renwin.remove_actors (self.act)
        self.renwin.Render ()

    def _initialize (self):
        debug ("In VectorCutPlane::_initialize ()")
        self.cut.SetInput (self.data_out)
        self.cut.SetCutFunction (self.plane)
        self.glyph2d_src.SetGlyphTypeToArrow ()
        self.glyph2d_src.SetFilled (0)

        self.cone.SetResolution (5)
        self.cone.SetHeight (1)
        self.cone.SetRadius (0.2)
        self.glph_trfm.SetInput (self.glyph_src.GetOutput ())
        
        self.orient_glyph ()
        
        self.glyph3d.SetInput (self.cut.GetOutput ())
        self.glyph3d.SetSource (self.glyph2d_src.GetOutput ())
        self.glyph3d.SetScaleFactor (self.scale)
        self.glyph3d.SetScaleModeToScaleByVector ()
        self.glyph3d.SetColorModeToColorByVector ()
        self.glyph3d.SetClamping (1)
        dr = self.mod_m.get_vector_data_range ()
        self.glyph3d.SetRange (dr)

        self.map.SetInput (self.glyph3d.GetOutput ())
        self.act.SetMapper (self.map)
        self.map.SetScalarRange (dr)
        self.map.SetLookupTable (self.mod_m.get_vector_lut ())
        self.act.GetProperty ().SetLineWidth (2)
        self.act.GetProperty ().BackfaceCullingOff ()
        self.act.GetProperty ().FrontfaceCullingOff ()
        self.act.GetProperty ().SetColor (Common.config.fg_color)
        self.center = self.data_out.GetCenter ()
        self.plane.SetOrigin (self.center)
        self.plane.SetNormal (0.0, 0.0, 1.0)
        self.set_def_step_size ()
        self.slider_pos = 0
        self.renwin.add_actors (self.act)
        # used for the pipeline browser
        self.pipe_objs = self.act
        
    def set_def_step_size (self):
        debug ("In VectorCutPlane::set_def_step_size ()")
        out = self.data_out
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
        
    def _gui_init (self): 
        debug ("In VectorCutPlane::_gui_init ()")
        self.glyph_gui_frame = None
        self.glyph_gui = None
        self.step_var.set (self.step_size)
        self.n_step_var.set (10)
        self.glyph_var = Tkinter.IntVar ()
        self.glyph_var.set (self.glyph2d_src.GetGlyphType ())
        self._auto_sweep_init ()
        self.sweep_step.set (1)

    def SetInput (self, source): 
        debug ("In VectorCutPlane::SetInput ()")
        Common.state.busy ()
        self.data_out = source
        self.cut.SetInput (self.data_out)
        self.do_color_mode ()
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In VectorCutPlane::save_config ()")
        file.write ("%d, %d, %d, %f, %d\n"%(self.glyph_var.get (),
                                            self.slider_pos,
                                            self.n_step_var.get (),
                                            self.step_size, self.glyph_pos))
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.plane, self.cut, self.glyph_src, self.glyph2d_src,
                    self.glyph3d, self.map, self.act,
                    self.act.GetProperty ()):
            p.dump (obj, file)

    def load_config (self, file): 
        debug ("In VectorCutPlane::load_config ()")
        val = file.readline ()
        glyph_pos = self.glyph_pos
        try:
            g_t, self.slider_pos, n_s, self.step_size,glyph_pos = eval (val)
        except ValueError: # old format 
            g_t, self.slider_pos, n_s, self.step_size = eval (val)
           
        self.glyph_var.set (g_t)
        self.n_step_var.set (n_s)
        if g_t == -2:
            self.glyph_src = self.arrow
        elif g_t == -1:
            self.glyph_src = self.cone
            
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.plane, self.cut, self.glyph_src, self.glyph2d_src,
                    self.glyph3d, self.map, self.act,
                    self.act.GetProperty ()):
            p.load (obj, file)

        self.set_glyph_mode ()
        self.color_mode = self.glyph3d.GetColorMode ()
        if self.color_mode == 0: # I Dislike Scale colouring.
            self.color_mode = 2
        if self.map.GetScalarVisibility () == 0:
            self.color_mode = -1
        self.do_color_mode ()
        self.change_glyph_pos (glyph_pos)

    def config_changed (self): 
        debug ("In VectorCutPlane::config_changed ()")
        self.act.GetProperty ().SetColor (*Common.config.fg_color)

    def make_main_gui (self): 
        debug ("In VectorCutPlane::make_main_gui ()")
        self.make_cut_plane_gui ()
        self.make_glyph_prop_gui ()
        self.make_choice_gui ()
        self.make_actor_gui (color=0, scalar=0, compact=1)
        self.make_auto_sweep_gui ()

    def make_choice_gui (self):
        debug ("In VectorCutPlane::make_choice_gui ()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)
        self.make_glyph_choice_gui (frame)
        self.make_color_mode_gui (frame)

    def make_glyph_prop_gui (self):
        debug ("In VectorCutPlane::make_glyph_prop_gui ()")
        frame = Tkinter.Frame (self.root)
        frame.pack (side='top', fill='both', expand=1)
        self.make_glyph_position_gui (frame)
        self.make_glyph_src_gui (frame)

    def make_glyph_choice_gui (self, master):
        debug ("In VectorCutPlane::make_glyph_choice_gui ()")
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='left', fill='both', expand=1)
        rw = 0
        rb = Tkinter.Radiobutton (frame, text="Normal Arrow",
                                  variable=self.glyph_var, value=9,
                                  command=self.set_glyph_mode)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text="Thick Arrow",
                                  variable=self.glyph_var, value=10,
                                  command=self.set_glyph_mode)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text="Other 2D glyph",
                                  variable=self.glyph_var, value=0,
                                  command=self.set_glyph_mode)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text="Cone",
                                  variable=self.glyph_var, value=-1,
                                  command=self.set_glyph_mode)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text="3D Arrow",
                                  variable=self.glyph_var, value=-2,
                                  command=self.set_glyph_mode)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        
    def make_color_mode_gui (self, master):
        debug ("In VectorCutPlane::make_color_mode_gui ()")
        frame = Tkinter.Frame (master, relief="ridge", bd=2)
        frame.pack (side='left', fill='both', expand=1)
        self.color_var = Tkinter.IntVar ()
        self.color_var.set (self.color_mode)
        rb = Tkinter.Radiobutton (frame, text="No Coloring",
                                  variable=self.color_var, value=-1,
                                  command=self.set_color_mode_gui)
        rb.grid (row=0, column=0, sticky='w')
        rb = Tkinter.Radiobutton (frame, text="Scalar Coloring",
                                  variable=self.color_var, value=1,
                                  command=self.set_color_mode_gui)
        rb.grid (row=1, column=0, sticky='w')
        rb = Tkinter.Radiobutton (frame, text="Vector Coloring",
                                  variable=self.color_var, value=2,
                                  command=self.set_color_mode_gui)
        rb.grid (row=2, column=0, sticky='w')
        but = Tkinter.Button (frame, text="Change Color",
                              command=self.set_actor_color)
        but.grid (row=3, column=0, sticky='ew')

    def make_glyph_src_gui (self, master):
        debug ("In VectorCutPlane::make_glyph_src_gui ()")

        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='left', fill='both', expand=1)

        rw = 0
        labl = Tkinter.Label (frame, text="Vector scale factor:")
        labl.grid (row=rw, column=0, sticky='w')
        self.scale_var = Tkinter.DoubleVar ()
        self.scale_var.set (self.glyph3d.GetScaleFactor ())
        scale_entr = Tkinter.Entry (frame, width=5, relief='sunken',
                                    textvariable=self.scale_var)
        scale_entr.grid (row=rw, column=1, sticky='we')
        scale_entr.bind ("<Return>", self.change_scale)
        rw = rw + 1

        f = Tkinter.Frame(frame)
        f.grid(row=rw, column=0, columnspan=2, sticky='we')
        self.glyph_gui_frame = f
        self.make_glyph_gui()
        
    def make_glyph_gui (self):
        debug ("In VectorCutPlane::make_glyph_gui ()")
        master = self.glyph_gui_frame
        if self.glyph_gui:
            self.glyph_gui.destroy()

        CVOF = vtkPipeline.ConfigVtkObj.ConfigVtkObjFrame
        val = self.glyph_var.get ()
        gui = None
        if val == -1:
            gs_m = ['Radius', 'Resolution']
            gui = CVOF(master, self.renwin)
            gui.configure(self.glyph_src, get=[], toggle=[], get_set=gs_m,
                          state=[], auto_update=1, one_frame=1)
        elif val == -2:
            gui = CVOF(master, self.renwin)
            gui.configure(self.glyph_src, get=[], toggle=[],
                          state=[], auto_update=1, one_frame=1)
        elif val in [0, 9, 10]:
            gui = Tkinter.Frame(master)
            but = Tkinter.Button(gui, text = "Configure 2D Glyph",
                                 command=self.config_glyph2d)
            but.pack(side='top', fill='both', expand=1)

        gui.pack(side='top', fill='both', expand=1)
        self.glyph_gui = gui

    def make_glyph_position_gui (self, master):
        debug ("In VectorCutPlane::make_glyph_position_gui ()")
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='left', fill='both', expand=1)

        self.glyph_pos_var = Tkinter.IntVar ()
        self.glyph_pos_var.set (self.glyph_pos)
        rw = 0
        labl = Tkinter.Label (frame, text="Glyph position:")
        labl.grid (row=rw, column=0, sticky='ew')
        rw = rw + 1        
        rb = Tkinter.Radiobutton (frame, text="Tail",
                                  variable=self.glyph_pos_var, value=-1,
                                  command=self.set_glyph_pos)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text="Center",
                                  variable=self.glyph_pos_var, value=0,
                                  command=self.set_glyph_pos)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text="Head",
                                  variable=self.glyph_pos_var, value=1,
                                  command=self.set_glyph_pos)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1        

    def change_scale (self, event=None):
        debug ("In VectorCutPlane::change_scale ()")
        Common.state.busy ()
        self.glyph3d.SetScaleFactor (self.scale_var.get ())
        self.renwin.Render ()
        Common.state.idle ()

    def set_color_mode_gui (self, event=None):
        "This sets up the data to setup the actual coloring mode."
        debug ("In VectorCutPlane::set_color_mode_gui ()")
        Common.state.busy ()
        self.color_mode = self.color_var.get ()
        self.do_color_mode ()
        self.renwin.Render ()
        Common.state.idle ()

    def do_color_mode (self):
        debug ("In VectorCutPlane::do_color_mode ()")
        self.glyph3d.SetRange (self.mod_m.get_vector_data_range ())
        if self.color_mode == 2: # Vector Coloring
            dr = self.mod_m.get_vector_data_range ()
            self.glyph3d.SetColorModeToColorByVector ()
            self.map.ScalarVisibilityOn ()
            self.map.SetScalarRange (dr)
            self.map.SetLookupTable (self.mod_m.get_vector_lut ())
        elif self.color_mode == 1: # Scalar Coloring
            self.glyph3d.SetColorModeToColorByScalar ()
            self.map.ScalarVisibilityOn ()
            dr = self.mod_m.get_scalar_data_range ()
            self.map.SetScalarRange (dr)
            self.map.SetLookupTable (self.mod_m.get_scalar_lut ())
        elif self.color_mode == -1: # No colouring
            self.map.ScalarVisibilityOff ()

    def set_actor_color (self, event=None):
        debug ("In VectorCutPlane::set_actor_color ()")
        clr = self.act.GetProperty ().GetColor ()
        init_clr = "#%02x%02x%02x"%(clr[0]*255, clr[1]*255, clr[2]*255)
        color = tkColorChooser.askcolor (title="Change object color", 
                                         initialcolor=init_clr)
        if color[1] is not None:
            Common.state.busy ()
            clr = Common.tk_2_vtk_color (color[0])
            self.act.GetProperty ().SetColor (*clr)
            self.renwin.Render ()
            Common.state.idle ()
            if self.color_mode != -1:
                msg = "Warning: This setting will have effect only if "\
                      "the coloring mode is set to 'No Coloring'."
                Common.print_err (msg)

    def do_sweep (self, event=None):
        debug ("In VectorCutPlane::do_sweep ()")
        if self.sweep_var.get ():
            val = int (1000*self.sweep_delay.get ())
            self.root.after (val, self.update_sweep)

    def update_sweep (self):
        debug ("In VectorCutPlane::update_sweep ()")
        if self.sweep_var.get ():
            d_pos = self.sweep_step.get ()
            pos = self.slider_pos + d_pos
            if (d_pos > 0) and (pos > self.n_step_var.get ()):
                pos = -self.n_step_var.get ()
            elif (d_pos < 0) and (pos < -self.n_step_var.get ()):
                pos = self.n_step_var.get ()
            self.slider[2].set (pos)
            self.change_slider ()            
            val = int (1000*self.sweep_delay.get ())
            self.root.after (val, self.update_sweep)

    def set_glyph_mode (self, event=None):
        debug ("In VectorCutPlane::set_glyph_mode ()")
        Common.state.busy ()
        val = self.glyph_var.get ()
        if val == 9: # normal arrow
            self.glyph_src = self.cone # reset so save/reload works
            self.glyph2d_src.SetGlyphTypeToArrow ()
            self.glyph2d_src.SetFilled (0)
            self.glyph3d.SetSource (self.glyph2d_src.GetOutput ())
        elif val == 10: # Thick arrow
            self.glyph_src = self.cone # reset so save/reload works
            self.glyph2d_src.SetGlyphTypeToThickArrow ()
            self.glyph2d_src.SetFilled (1)
            self.glyph3d.SetSource (self.glyph2d_src.GetOutput ())
        elif val == 0: # Some other 2D glyph
            self.glyph_src = self.cone # reset so save/reload works
            self.glyph3d.SetSource (self.glyph2d_src.GetOutput ())
        elif val == -1: # Cone
            self.glyph_src = self.cone
            self.glph_trfm.SetInput (self.glyph_src.GetOutput ())
            self.glyph3d.SetSource (self.glph_trfm.GetOutput ())
            self.orient_glyph()
        elif val == -2: # 3D arrow
            self.glyph_src = self.arrow
            self.glph_trfm.SetInput (self.glyph_src.GetOutput ())
            self.glyph3d.SetSource (self.glph_trfm.GetOutput ())
            self.orient_glyph()
            
        if self.root and self.root.winfo_exists():
            self.make_glyph_gui()

        self.renwin.Render ()
        Common.state.idle ()

    def set_glyph_pos (self, event=None):
        debug ("In VectorCutPlane::change_glyph_pos ()")        
        Common.state.busy ()
        self.change_glyph_pos (self.glyph_pos_var.get ())
        self.renwin.Render ()
        Common.state.idle ()        
        
    def change_glyph_pos (self, new_pos):
        debug ("In VectorCutPlane::change_glyph_pos ()")
        old_pos = self.glyph_pos
        if old_pos == new_pos:
            return
        else:
            self.glyph_pos = new_pos
            self.orient_glyph ()

    def orient_glyph (self):
        debug ("In VectorCutPlane::orient_glyph ()")
        tr = self.glph_trfm.GetTransform ()
        tr.Identity()
        
        if hasattr(self, 'glyph_var'):
            g_t = self.glyph_var.get()            
        elif self.glyph_src == self.cone:
            g_t = -1
        elif self.glyph_src == self.arrow:
            g_t = -2
            
        if self.glyph_pos == -1:
            if g_t == -1:
                tr.Translate (0.5, 0.0, 0.0)
            self.glyph2d_src.SetCenter (0.5, 0.0, 0.0)
        elif self.glyph_pos == 1:
            if g_t == -1:
                tr.Translate (-0.5, 0.0, 0.0)
            elif g_t == -2:
                tr.Translate (-1, 0.0, 0.0)
            self.glyph2d_src.SetCenter (-0.5, 0.0, 0.0)
        else:
            if g_t == -2:
                tr.Translate (-0.5, 0.0, 0.0)
            self.glyph2d_src.SetCenter (0.0, 0.0, 0.0)

    def config_glyph2d(self, event=None):
        debug ("In VectorCutPlane::config_glyph2d ()")
        conf = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        g_t = self.glyph_var.get()
        if g_t == 0:
            conf.configure (None, self.glyph2d_src, get=[],
                            toggle=['!AbortExecuteOn'])
        else:
            conf.configure (None, self.glyph2d_src, get=[],
                            toggle=['!AbortExecuteOn', '!FilledOn'],
                            state=[])
