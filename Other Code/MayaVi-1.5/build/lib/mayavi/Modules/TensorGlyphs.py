"""

This module displays glyphs scaled and colored as per the tensor data.
This will work for any dataset.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.5 $"
__date__ = "$Date: 2005/08/02 18:30:13 $"
__credits__ = """Many thanks to Jose Paulo <moitinho@civil.ist.utl.pt>
for contributing an initial version of this Module."""


import Base.Objects, Common
import Tkinter, tkColorChooser, math
import vtk
import vtkPipeline.vtkMethodParser

debug = Common.debug

class TensorGlyphs (Base.Objects.Module):

    """ This module displays glyphs, scaled and colored as per the
    tensor data.  This will work for any dataset. """

    def __init__ (self, mod_m): 
        debug ("In TensorGlyph::__init__ ()")
        Common.state.busy ()
        Base.Objects.Module.__init__ (self, mod_m)
        
        self.sphere = vtk.vtkSphereSource ()
        self.axes = vtk.vtkAxes ()
        self.glyphs = vtk.vtkTensorGlyph ()
        # The actual glyph used is controlled using self.glyph_var
        
        self.mapper = vtk.vtkPolyDataMapper ()
        self.actor = vtk.vtkActor ()

        self.data_out = self.mod_m.GetOutput ()
        self.color_mode = 1 # 1 is scalar, -1 none
        
        self._initialize ()
        self._gui_init ()
        self.do_color_mode()
        self.renwin.Render ()
        Common.state.idle ()

    def __del__ (self): 
        debug ("In TensorGlyphs::__del__ ()")
        if self.actor:
            self.renwin.remove_actors (self.actor)
        self.renwin.Render ()

    def _initialize (self):
        debug ("In TensorGlyphs::_initialize ()")

        self.sphere.SetThetaResolution (8)
        self.sphere.SetPhiResolution (8)

        self.glyphs.SetInput (self.data_out)
        self.glyphs.SetSource (self.sphere.GetOutput())
        self.glyphs.SetScaleFactor (1.0)
        self.glyphs.ClampScalingOn ()
        self.glyphs.SetMaxScaleFactor (5.0)

        self.normals = vtk.vtkPolyDataNormals ()
        self.normals.SetInput (self.glyphs.GetOutput ())
        
        self.mapper.SetInput (self.normals.GetOutput ())
        self.actor.SetMapper (self.mapper)

        self.actor.GetProperty ().SetLineWidth (2)
        self.actor.GetProperty ().BackfaceCullingOff ()
        # self.actor.GetProperty ().FrontfaceCullingOff ()

        self.actor.GetProperty ().SetColor (*Common.config.fg_color)
        self.center = self.data_out.GetCenter ()
        self.renwin.add_actors (self.actor)
        # used for the pipeline browser
        self.pipe_objs = self.actor
        
    def _gui_init (self): 
        debug ("In TensorGlyphs::_gui_init ()")
        self.root = None
        self.glyph_frame = None
        self.tensor_frame = None
        self.glyph_var = Tkinter.IntVar ()
        self.glyph_var.set (1)
        # 1 == sphere glyph, 2 == axes.

    def SetInput (self, source): 
        debug ("In TensorGlyphs::SetInput ()")
        Common.state.busy ()
        self.data_out = source
        self.glyphs.SetInput (self.data_out)
        self.do_color_mode ()
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In TensorGlyphs::save_config ()")
        file.write ("%d , %d\n"%(self.glyph_var.get (), \
                                 self.color_mode ))
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.sphere, self.axes, self.glyphs, self.normals,
                    self.mapper, self.actor, self.actor.GetProperty ()):
            p.dump (obj, file)

    def load_config (self, file): 
        debug ("In TensorGlyphs::load_config ()")
        val = file.readline ()
        (glyph , self.color_mode) = eval (val)
        self.glyph_var.set (glyph)

        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.sphere, self.axes, self.glyphs, self.normals,
                    self.mapper, self.actor, self.actor.GetProperty ()):
            p.load (obj, file)

        self.set_glyph_mode ()
        self.do_color_mode ()
        self.renwin.Render ()

    def config_changed (self): 
        debug ("In TensorGlyphs::config_changed ()")
        self.actor.GetProperty ().SetColor (*Common.config.fg_color)

    def make_main_gui (self): 
        debug ("In TensorGlyphs::make_main_gui ()")
        self.make_choice_gui ()
        self.make_tensor_prop_gui ()
        self.make_actor_gui (color=0, scalar=0)

    def make_choice_gui (self):
        debug ("In TensorGlyphs::make_choice_gui ()")
        frame = Tkinter.Frame (self.root)
        frame.pack (side='top', fill='both', expand=1)
        self.make_glyph_gui (frame)
        self.make_color_mode_gui (frame)

    def make_tensor_prop_gui (self):
        debug ("In TensorGlyphs::make_tensor_prop_gui ()")
        frame = Tkinter.Frame (self.root)
        frame.pack (side='top', fill='both', expand=1)
        self.make_tensor_gui (frame)

    def make_glyph_gui (self, master):
        debug ("In TensorGlyphs::make_glyph_gui ()")
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='left', fill='both', expand=1)
        #
        # The "value" in the radio button has to agree with
        # what is used in set_glyph_mode
        #
        lab = Tkinter.Label (frame, text="Tensor representation:")
        lab.grid (row=0, column=0, sticky='ew', pady=5)
        rw = 1
        rb = Tkinter.Radiobutton (frame, text="Ellipsoids",
                                   variable=self.glyph_var, value=1,
                                   command=self.set_glyph_mode)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text="Axes",
                                   variable=self.glyph_var, value=2,
                                   command=self.set_glyph_mode)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        
        # This buttons is disabled. Just there in case there is a need.
        rb = Tkinter.Radiobutton (frame, text="Cone",
                                  variable=self.glyph_var, value=-1,
                                  command=self.set_glyph_mode)
        rb.grid (row=rw, column=0, sticky='w')
        rb.config (state='disabled')
        rw = rw + 1
        
    def make_color_mode_gui (self, master):
        debug ("In TensorGlyphs::make_color_mode_gui ()")
        frame = Tkinter.Frame (master, relief="ridge", bd=2)
        frame.pack (side='left', fill='both', expand=1)
        rw = 0
        lab = Tkinter.Label (frame, text="Coloring mode:")
        lab.grid (row=rw, column=0, sticky='ew', pady=5)
        rw = rw + 1

        self.color_var = Tkinter.IntVar ()
        self.color_var.set (self.color_mode)

        but = Tkinter.Button (frame, text="Change Glyph Color",
                              command=self.set_actor_color)
        but.grid (row=rw, column=0, sticky='ew')
        rw = rw + 1

        rb = Tkinter.Radiobutton (frame, text="No Coloring",
                                  variable=self.color_var, value=-1,
                                  command=self.set_color_mode_gui)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        
        rb = Tkinter.Radiobutton (frame, text="Scalar Coloring",
                                  variable=self.color_var, value=1,
                                  command=self.set_color_mode_gui)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1

    def make_tensor_gui (self, master):
        debug ("In TensorGlyphs::make_tensor_gui ()")
        self.tensor_frame = Tkinter.Frame (master, bd=2)
        self.tensor_frame.pack (side='top', fill='both', expand=1)
        frame = Tkinter.Frame (self.tensor_frame, relief='ridge', bd=1)
        frame.pack (side='top', fill='both', expand=1)

        rw = 0
        labl = Tkinter.Label (frame, text="Tensor scale factor:")
        labl.grid (row=rw, column=0, sticky='w')
        self.scale_var = Tkinter.DoubleVar ()
        self.scale_var.set (self.glyphs.GetScaleFactor ())
        scale_entr = Tkinter.Entry (frame, width=5, relief='sunken',
                                    textvariable=self.scale_var)
        scale_entr.grid (row=rw, column=1, sticky='we')
        scale_entr.bind ("<Return>", self.change_scale)
        rw = rw + 1

        labl = Tkinter.Label (frame, text="Maximum tensor scale factor:")
        labl.grid (row=rw, column=0, sticky='w')
        self.max_scale_var = Tkinter.DoubleVar ()
        self.max_scale_var.set (self.glyphs.GetMaxScaleFactor ())
        max_scale_entr = Tkinter.Entry (frame, width=5, relief='sunken',
                                    textvariable=self.max_scale_var)
        max_scale_entr.grid (row=rw, column=1, sticky='we')
        max_scale_entr.bind ("<Return>", self.change_max_scale)

        val = self.glyph_var.get ()
        if val == 1:
            self.make_sphere_gui (self.tensor_frame)
        elif val == 2:
            self.make_axes_gui (self.tensor_frame)

    def make_axes_gui (self, master):
        debug ("In TensorGlyphs::make_axes_gui ()")
        frame = Tkinter.Frame (master, relief='ridge', bd=1)
        frame.pack (side='top', fill='both', expand=1)
        self.glyph_frame = frame
 
        rw = 0
        labl = Tkinter.Label (frame, text="Axes Scale factor:")
        labl.grid (row=rw, column=0, sticky='w')
        self.axes_scale_var = Tkinter.DoubleVar ()
        self.axes_scale_var.set (self.axes.GetScaleFactor ())
        entr = Tkinter.Entry (frame, width=5, relief='sunken',
                              textvariable=self.axes_scale_var)
        entr.grid (row=rw, column=1, sticky='we')
        entr.bind ("<Return>", self.change_axes_gui)
        
        rw = rw + 1
        self.axes_symm_var = Tkinter.IntVar ()
        self.axes_symm_var.set (self.axes.GetSymmetric ())
        b = Tkinter.Checkbutton (frame, text="Symmmetric Axes On",
                                 variable=self.axes_symm_var, onvalue=1,
                                 offvalue=0, command=self.change_axes_gui)
        b.grid (row=rw, column=0, columnspan=2, sticky='w')        

    def make_sphere_gui (self, master):
        debug ("In TensorGlyphs::make_sphere_gui ()")
        frame = Tkinter.Frame (master, relief='ridge', bd=1)
        frame.pack (side='top', fill='both', expand=1)
        self.glyph_frame = frame
 
        rw = 0
        labl = Tkinter.Label (frame, text="Ellipsoid theta resolution:")
        labl.grid (row=rw, column=0, sticky='w')
        self.ellipsoid_tres_var = Tkinter.IntVar ()
        self.ellipsoid_tres_var.set (self.sphere.GetThetaResolution ())
        entr = Tkinter.Entry (frame, width=5, relief='sunken',
                              textvariable=self.ellipsoid_tres_var)
        entr.grid (row=rw, column=1, sticky='we')
        entr.bind ("<Return>", self.change_sphere_gui)
        rw = rw + 1

        labl = Tkinter.Label (frame, text="Ellipsoid phi resolution:")
        labl.grid (row=rw, column=0, sticky='w')
        self.ellipsoid_pres_var = Tkinter.IntVar ()
        self.ellipsoid_pres_var.set (self.sphere.GetPhiResolution ())
        entr = Tkinter.Entry (frame, width=5, relief='sunken',
                              textvariable=self.ellipsoid_pres_var)
        entr.grid (row=rw, column=1, sticky='we')
        entr.bind ("<Return>", self.change_sphere_gui)
        rw = rw + 1

    def change_scale (self, event=None):
        debug ("In TensorGlyphs::change_scale ()")
        Common.state.busy ()
        self.glyphs.SetScaleFactor (self.scale_var.get ())
        self.renwin.Render ()
        Common.state.idle ()

    def change_max_scale (self, event=None):
        debug ("In TensorGlyphs::change_max_scale ()")
        Common.state.busy ()
        self.glyphs.SetMaxScaleFactor (self.max_scale_var.get ())
        self.renwin.Render ()
        Common.state.idle ()

    def change_sphere_gui (self, event=None):
        debug ("In TensorGlyphs::change_sphere_gui ()")
        Common.state.busy ()
        self.sphere.SetThetaResolution (self.ellipsoid_tres_var.get ())
        self.sphere.SetPhiResolution (self.ellipsoid_pres_var.get ())
        self.renwin.Render ()
        Common.state.idle ()

    def change_axes_gui (self, event=None):
        debug ("In TensorGlyphs::change_axes_gui ()")
        Common.state.busy ()
        self.axes.SetScaleFactor (self.axes_scale_var.get ())
        self.axes.SetSymmetric (self.axes_symm_var.get ())
        self.renwin.Render ()
        Common.state.idle ()

    def set_color_mode_gui (self, event=None):
        "This sets up the data to setup the actual coloring mode."
        debug ("In TensorGlyphs::set_color_mode_gui ()")
        Common.state.busy ()
        self.color_mode = self.color_var.get ()
        self.do_color_mode ()
        self.renwin.Render ()
        Common.state.idle ()

    def do_color_mode (self):
        debug ("In TensorGlyphs::do_color_mode ()")
        self.glyphs.ColorGlyphsOn ()
        if self.color_mode == 1: # Scalar Coloring
            self.mapper.ScalarVisibilityOn ()
            dr = self.mod_m.get_scalar_data_range ()
            self.mapper.SetScalarRange (dr)
            self.mapper.SetLookupTable (self.mod_m.get_scalar_lut ())
        elif self.color_mode == -1: # No colouring
            self.glyphs.ColorGlyphsOff ()
            self.mapper.ScalarVisibilityOff ()

    def set_actor_color (self, event=None):
        debug ("In TensorGlyphs::set_actor_color ()")
        clr = self.actor.GetProperty ().GetColor ()
        init_clr = "#%02x%02x%02x"%(clr[0]*255, clr[1]*255, clr[2]*255)
        color = tkColorChooser.askcolor (title="Change object color", 
                                         initialcolor=init_clr)
        if color[1] is not None:
            Common.state.busy ()
            clr = Common.tk_2_vtk_color (color[0])
            self.actor.GetProperty ().SetColor(*clr)
            self.renwin.Render ()        
            Common.state.idle ()
            if self.color_mode != -1:
                msg = "Warning: This setting will have effect only if "\
                      "the coloring mode is set to 'No Coloring'."
                Common.print_err (msg)

    def set_glyph_mode (self, event=None):
        debug ("In TensorGlyphs::set_glyph_mode ()")
        Common.state.busy ()
        val = self.glyph_var.get ()
        if val == 1: # Sphere
            self.glyphs.SetSource (self.sphere.GetOutput ())
            self.normals.SetInput (self.glyphs.GetOutput ())
            self.mapper.SetInput (self.normals.GetOutput ())
            if self.glyph_frame:
                self.glyph_frame.destroy ()
                self.make_sphere_gui (self.tensor_frame)
        elif val == 2: # Axes
            self.glyphs.SetSource (self.axes.GetOutput ())
            # normals wont work for this case.
            self.mapper.SetInput (self.glyphs.GetOutput ())
            if self.glyph_frame:
                self.glyph_frame.destroy ()
                self.make_axes_gui (self.tensor_frame)
        self.renwin.Render ()
        Common.state.idle ()
