"""

This module displays glyphs scaled and colored as per the input data.
This will work for any dataset and can be used for both scalar and
vector data.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.5 $"
__date__ = "$Date: 2005/08/02 18:30:13 $"

import Base.Objects, Common
import Tkinter, tkColorChooser, math
import vtk
import vtkPipeline.vtkMethodParser
import vtkPipeline.ConfigVtkObj

debug = Common.debug


class Glyph (Base.Objects.Module):

    """ This module displays glyphs scaled and colored as per the
    input data.  This will work for any dataset and can be used for
    both scalar and vector data. """

    def __init__ (self, mod_m): 
        debug ("In Glyph::__init__ ()")
        Common.state.busy ()
        Base.Objects.Module.__init__ (self, mod_m)
        self.glyph_src = vtk.vtkGlyphSource2D ()
        self.glyph = vtk.vtkGlyph3D ()
        self.mapper = self.map = vtk.vtkPolyDataMapper ()
        self.actor = self.act = vtk.vtkActor ()
        self.data_out = self.mod_m.GetOutput ()
        
        self._initialize ()
        self._gui_init ()
        self.renwin.Render ()
        Common.state.idle ()

    def __del__ (self): 
        debug ("In Glyph::__del__ ()")
        if self.actor:
            self.renwin.remove_actors (self.act)
        self.renwin.Render ()

    def _initialize (self):
        debug ("In Glyph::_initialize ()")
        self.glyph_src.SetGlyphTypeToArrow ()
        self.glyph_src.SetFilled (1)

        self.glyph.SetInput (self.mod_m.GetOutput ())
        self.glyph.SetSource (self.glyph_src.GetOutput ())
        self.glyph.SetScaleModeToScaleByScalar ()
        self.glyph.SetColorModeToColorByScalar ()
        self.glyph.SetClamping (1)
        dr = self.mod_m.get_scalar_data_range ()
        self.glyph.SetRange (dr)

        self.map.SetInput (self.glyph.GetOutput ())
        self.act.SetMapper (self.map)
        self.map.SetScalarRange (dr)
        self.map.SetLookupTable (self.mod_m.get_scalar_lut ())
        self.act.GetProperty ().SetLineWidth (2)
        self.act.GetProperty ().BackfaceCullingOff ()
        self.act.GetProperty ().FrontfaceCullingOff ()
        self.act.GetProperty ().SetColor (*Common.config.fg_color)
        self.center = self.data_out.GetCenter ()
        self.renwin.add_actors (self.act)
        # used for the pipeline browser
        self.pipe_objs = self.actor
        
    def _gui_init (self): 
        debug ("In Glyph::_gui_init ()")
        self.root = None
        self.glyph_gui = None
        self.glyph_var = Tkinter.IntVar ()
        self.glyph_var.set (0)

    def SetInput (self, source): 
        debug ("In Glyph::SetInput ()")
        Common.state.busy ()
        self.data_out = source
        self.glyph.SetInput (self.data_out)
        self.update_color_mode()
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In Glyph::save_config ()")
        file.write ("%d\n"%(self.glyph_var.get ()))
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.glyph, self.glyph_src,
                    self.map, self.act, self.act.GetProperty ()):
            p.dump (obj, file)

    def load_config (self, file):
        debug ("In Glyph::load_config ()")
        val = file.readline ()
        g_t = eval (val)
        self.glyph_var.set (g_t)
        self.set_glyph_mode ()
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.glyph, self.glyph_src,
                    self.map, self.act, self.act.GetProperty ()):
            p.load (obj, file)

        self.update_color_mode()

    def config_changed (self): 
        debug ("In Glyph::config_changed ()")
        self.act.GetProperty ().SetColor (*Common.config.fg_color)

    def make_main_gui (self): 
        debug ("In Glyph::make_main_gui ()")
        CVOF = vtkPipeline.ConfigVtkObj.ConfigVtkObjFrame
        self.glyph_gui = gg = CVOF(self.root, self.renwin)
        t_m = ["ClampingOn", "OrientOn", "ScalingOn"]
        gs_m = ["Range", "ScaleFactor"]
        st_m = [['SetColorModeToColorByScalar',
                 'SetColorModeToColorByVector'],
                ['SetScaleModeToDataScalingOff',
                 'SetScaleModeToScaleByScalar',
                 'SetScaleModeToScaleByVector',
                 'SetScaleModeToScaleByVectorComponents'],
                ['SetVectorModeToUseNormal',
                 'SetVectorModeToUseVector',
                 'SetVectorModeToVectorRotationOff']]
        gg.configure(self.glyph, get=[], toggle=t_m, get_set=gs_m,
                     state=st_m, auto_update=1, one_frame=1)
        gg.set_update_method(self.update_color_mode)
        gg.pack(side='top', fill='both', expand=1)
        self.make_choice_gui ()

    def make_choice_gui (self):
        debug ("In Glyph::make_choice_gui ()")
        frame = Tkinter.Frame (self.root)
        frame.pack (side='top', fill='both', expand=1)        
        self.make_glyph_gui (frame)

    def make_glyph_gui (self, master):
        debug ("In Glyph::make_glyph_gui ()")        
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='left', fill='both', expand=1)
        rw = 0
        rb = Tkinter.Radiobutton (frame, text="2D Glyphs",
                                  variable=self.glyph_var, value=0,
                                  command=self.set_glyph_mode)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text="Cone",
                                  variable=self.glyph_var, value=1,
                                  command=self.set_glyph_mode)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text="Sphere",
                                  variable=self.glyph_var, value=2,
                                  command=self.set_glyph_mode)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text="Cube",
                                  variable=self.glyph_var, value=3,
                                  command=self.set_glyph_mode)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text="Cylinder",
                                  variable=self.glyph_var, value=4,
                                  command=self.set_glyph_mode)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text="3D Arrow",
                                  variable=self.glyph_var, value=5,
                                  command=self.set_glyph_mode)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        
        but = Tkinter.Button(frame, text="Configure Glyph Source",
                             underline=1,
                             command=self.config_glyph_src_gui)
        but.grid (row=rw, column=0, sticky='wens')
        self.root.bind('<Alt-o>', self.config_glyph_src_gui)
        rw = rw + 1
        
    def set_glyph_mode (self, event=None):
        debug ("In Glyph::set_glyph_mode ()")
        Common.state.busy ()
        val = self.glyph_var.get ()
        if val == 0: # 2d glyph 
            self.glyph_src = vtk.vtkGlyphSource2D ()
            self.glyph_src.SetGlyphTypeToArrow ()
        elif val == 1: # Cone
            self.glyph_src = vtk.vtkConeSource()
        elif val == 2: # Sphere
            self.glyph_src = vtk.vtkSphereSource()
            self.glyph_src.SetPhiResolution(4)
            self.glyph_src.SetThetaResolution(4)
        elif val == 3: # Cube
            self.glyph_src = vtk.vtkCubeSource()
        elif val == 4: # Cylinder
            self.glyph_src = vtk.vtkCylinderSource()
        elif val == 5: # 3D arrow
            self.glyph_src = vtk.vtkArrowSource()
        self.glyph.SetSource (self.glyph_src.GetOutput ())

        self.renwin.Render ()
        Common.state.idle ()

    def update_color_mode(self, event=None):
        cm = self.glyph.GetColorModeAsString()
        if cm == 'ColorByScalar':
            self.map.ScalarVisibilityOn ()
            dr = self.mod_m.get_scalar_data_range ()
            self.map.SetScalarRange (dr)
            self.glyph.SetRange(dr)
            self.map.SetLookupTable (self.mod_m.get_scalar_lut ())
        elif cm == 'ColorByVector':
            dr = self.mod_m.get_vector_data_range ()
            self.map.ScalarVisibilityOn ()
            self.map.SetScalarRange (dr)
            self.glyph.SetRange(dr)
            self.map.SetLookupTable (self.mod_m.get_vector_lut ())
        if self.root and self.glyph_gui and self.root.winfo_exists():
            self.glyph_gui.update_gui()        

    def config_glyph_src_gui(self, event=None):
        debug("In Glyph::config_glyph_src_gui()")
        conf = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        conf.configure (None, self.glyph_src, run_command=0)

    def close_gui(self, event=None):        
        """Called when the 'close' button is clicked.  Overridden to
        handle cyclic references."""
        debug ("In Glyph::close_gui ()")
        del self.glyph_gui
        Base.Objects.Module.close_gui(self, event)
