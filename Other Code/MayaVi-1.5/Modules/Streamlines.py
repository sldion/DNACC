"""

This module makes it possible to view streamlines, streamtubes, and
stream ribbons for any type of vector data.  Any number of point
sources can be added and deleted.  A fairly powerful UI is provided.
This module should work with any dataset.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.8 $"
__date__ = "$Date: 2005/08/02 18:30:13 $"

import Base.Objects, Common
import Tkinter, tkColorChooser, tkMessageBox, tkFileDialog, math
import vtk
import vtkPipeline.vtkMethodParser
import vtkPipeline.ConfigVtkObj

tk_fopen = tkFileDialog.askopenfilename
tk_fsave = tkFileDialog.asksaveasfilename
debug = Common.debug


class SeedManager:

    """ Abstracts out a seed manager.  This class is capable of
    handling a vtkPointSource as well as a vtkDiskSource.  The
    DiskSource is used for 2D data.  The DiskSource is appropriately
    oriented so that it is on the right plane."""
    
    def __init__(self):        
        """ Create the SeedManager. Call initialize to setup the seed."""
        debug ("In SeedManager::__init__ ()")
        self.dim = 0
        self.last_cen = [0.0]*3
        self.seed = None
        self.transform = None
        
    def initialize (self, valid_coord):        
        """ Initializes the seed given an array of valid co-ordinate
        directions. [x-axis, y-axis, z_axis] is the format.  For
        instance if x-axis == 0 then the data is along the YZ plane.
        This method is responsible for actually creating the seed. """

        debug ("In SeedManager::initialize ()")
        assert len (valid_coord) == 3
        self.dim = reduce (lambda x, y: x+y, valid_coord)
        if self.dim == 3:
            self.seed = vtk.vtkPointSource ()
        else:
            self.seed = vtk.vtkDiskSource ()
            self.seed.SetRadialResolution (1)
            self.seed.SetInnerRadius (0.0)
            self.transform = vtk.vtkTransformFilter ()
            self.transform.SetTransform (vtk.vtkTransform ())
            self.transform.SetInput (self.seed.GetOutput ())
            self.orient_2d (valid_coord)
                
    def orient_2d (self, valid_coord):
        """ Orients the vtkDiskSource for the given co-ordinates."""
        debug ("In SeedManager::orient_2d ()")
        assert len (valid_coord) == 3
        transform = self.transform.GetTransform ()
        if valid_coord[0] == 0: # Data plane is along YZ plane
            transform.RotateY(90)
        elif valid_coord[1] == 0: # Data plane is along XZ plane
            transform.RotateX(90)
        elif valid_coord[2] == 0: # Data plane is along XY plane
            pass # default orientation!

    def set_n_points (self, n):
        """ Set the number of points created by the seed."""
        debug ("In SeedManager::set_n_points ()")
        if self.dim == 3:
            self.seed.SetNumberOfPoints (n)
        else:
            self.seed.SetCircumferentialResolution (n)
        
    def get_n_points (self):
        """ Get the number of seed points."""
        debug ("In SeedManager::get_n_points ()")
        if self.dim == 3:
            return self.seed.GetNumberOfPoints ()
        else:
            return self.seed.GetCircumferentialResolution ()

    def set_radius (self, rad):
        """ Set the seed radius. """
        debug ("In SeedManager::set_radius ()")
        if self.dim == 3:
            self.seed.SetRadius (rad)
        else:
            self.seed.SetOuterRadius (rad)

    def set_center (self, cen):
        """ Set the seed's center given an array of co-ordinates."""
        debug ("In SeedManager::set_center ()")
        if self.dim == 3:
            self.seed.SetCenter (*cen)
        else:
            diff = map (lambda x, y: x-y, cen, self.last_cen)
            tr = self.transform.GetTransform ()
            tr.Translate (*diff)
            self.last_cen = cen[:]

    def GetOutput (self):
        """ Get the VTK Output of the appropriate seed."""
        debug ("In SeedManager::GetOutput ()")
        if self.dim == 3:
            return self.seed.GetOutput ()
        else:
            return self.transform.GetOutput ()


class PointStreamer (Base.Objects.Module):
    """Provides the basic class for streamline support. """
    def __init__ (self, mod_m):
        debug ("In PointStreamer::__init__ ()")
        Common.state.busy ()
        Base.Objects.Module.__init__ (self, mod_m)
        self.sphere_src = vtk.vtkSphereSource ()
        self.sphere_map = vtk.vtkPolyDataMapper ()
        self.sphere_act = vtk.vtkActor ()        
        self.seed = SeedManager ()
        self.radius = 1.0
        self.cen = [0.0, 0.0, 0.0]
        self.n_pnt = 50
        self.strmln_mode = 0
        self.color_mode = 1 # 1 is vector, 0 is scalar, -1 is no color
        self.integration_mode = 2 # 2 is Runge-Kutta 2 and 4 is RK 4.

        self.strmln = vtk.vtkStreamLine ()
        self.ribbonf = vtk.vtkRibbonFilter ()
        self.tubef = vtk.vtkTubeFilter ()
        self.mapper = self.stream_map = vtk.vtkPolyDataMapper ()
        self.actor = self.stream_act = vtk.vtkActor ()
        self.done_init = 0
        Common.state.idle ()

    def __del__ (self):
        debug ("In PointStreamer::__del__ ()")
        Common.state.busy ()
        self.renwin.remove_actors ((self.sphere_act, self.stream_act))
        self.renwin.Render ()
        Common.state.idle ()

    def get_defaults (self):
        debug ("In PointStreamer::get_defaults ()")
        self.resoln_var = []
        self.def_dim = []
        self.dim = []
        self.data_dimn = 0
        self.coord = [0,0,0]
        dim1 = self.mod_m.get_data_source ().GetOutput ().GetBounds ()
        max_len = -1.0
        for i in range (0,3):
            self.dim.append ((dim1[2*i], dim1[2*i+1]))
            val = dim1[2*i] + dim1[2*i+1]
            self.def_dim.append (val*0.5)
            mag = abs (dim1[2*i+1] - dim1[2*i])
            if mag > max_len:
                max_len = mag
            var = Tkinter.DoubleVar ()
            var.set (mag*0.02)
            self.resoln_var.append (var)
            if dim1[2*i] != dim1[2*i+1]:
                self.coord[i] = 1
                self.data_dimn = self.data_dimn + 1

        # now that we know enough about the data - initialize the seed.
        self.seed.initialize (self.coord)

        self.cen = self.def_dim
        self.radius = max_len*0.1
        self.sphere_src.SetCenter (*self.cen)
        self.sphere_src.SetRadius(self.radius)
        # setting some sane defaults
        self.ribbonf.SetWidth (self.radius*0.075)
        self.tubef.SetRadius (self.radius*0.075)

    def initialize (self, master=None):
        debug ("In PointStreamer::initialize ()")
        self.get_defaults ()
        self.sphere_src.SetThetaResolution (10)
        self.sphere_src.SetPhiResolution (10)
        self.sphere_map.SetInput (self.sphere_src.GetOutput ())
        self.sphere_act.SetMapper (self.sphere_map)
        self.sphere_act.GetProperty ().SetColor (0.0, 0.0, 0.5)
        self.sphere_act.GetProperty ().SetOpacity (0.5)
        self.max_v = self.mod_m.get_vector_data_range ()[1]

        self.seed.set_n_points (self.n_pnt)
        self.strmln.SetSource (self.seed.GetOutput ())
        self.strmln.SpeedScalarsOn ()
        self.stream_map.SetInput (self.strmln.GetOutput ())
        self.stream_map.SetScalarRange (0, self.max_v)
        self.stream_map.SetLookupTable (self.mod_m.get_vector_lut ())
        self.stream_act.SetMapper (self.stream_map)

        self.stream_act.VisibilityOff ()
        self.renwin.add_actors ((self.sphere_act, self.stream_act))
        self.configure (master)

    def SetInput (self, source):
        debug ("In PointStreamer::SetInput ()")
        self.strmln.SetInput (source)
        self.do_color_mode ()

    def make_ball_gui (self, master):
        debug ("In PointStreamer::make_ball_gui ()")
        frame = Tkinter.Frame (master, relief="ridge", bd=2)
        frame.pack (side='top')
        self.coord_var = Tkinter.StringVar ()
        self.coord_var.set (self.cen)
        lab = Tkinter.Label (frame, text="Center of Source:")
        lab.grid (row=0, column=0, columnspan=1, sticky='w')
        entr = Tkinter.Entry (frame, width=20, relief='sunken', 
                      textvariable=self.coord_var)
        entr.grid (row=0, column=1, columnspan=2, sticky='w')

        def_name = ["Move along X-axis", "Move along Y-axis ", 
                    "Move along Z-axis"]
        res_name = ["X resolution:", "Y resolution:", "Z resolution:"]
        self.slider = []
        
        rw = 1
        for i in range (0,3):
            if self.coord[i] == 1:
                sl = Tkinter.Scale (frame, label=def_name[i], 
                                    from_=self.dim[i][0],
                                    to=self.dim[i][1], 
                                    length="8c", orient='horizontal', 
                                    resolution=self.resoln_var[i].get ())
                sl.set (self.cen[i])
                sl.grid (row=rw, column=0, columnspan=3, sticky='ew')
                rw = rw + 1
                sl.bind ("<ButtonRelease>", self.change_locator)
                lab = Tkinter.Label (frame, text=res_name[i])
                lab.grid (row=rw, column=0, sticky='w')
                entr = Tkinter.Entry (frame, width=5,
                                      relief='sunken',
                                      textvariable=self.resoln_var[i])
                entr.grid (row=rw, column=1, sticky='w')
                entr.bind ("<Return>", self.set_resolution)
                rw = rw+1
                self.slider.append (sl)        

        self.radius_var = Tkinter.DoubleVar ()
        self.radius_var.set (self.radius)
        self.n_pnt_var = Tkinter.DoubleVar ()
        self.n_pnt_var.set (self.n_pnt)
        lab = Tkinter.Label (frame, text="Radius of source:")
        lab.grid (row=rw, column=0, sticky='w')
        entr = Tkinter.Entry (frame, width=5, relief='sunken',
                              textvariable=self.radius_var)
        entr.grid (row=rw, column=1, sticky='w')
        entr.bind ("<Return>", self.setup_ball)
        rw = rw + 1
        lab = Tkinter.Label (frame, text="Number of seed points:")
        lab.grid (row=rw, column=0, sticky='w')
        entr = Tkinter.Entry (frame, width=5, relief='sunken',
                      textvariable=self.n_pnt_var)
        entr.grid (row=rw, column=1, sticky='w')
        rw = rw + 1
        entr.bind ("<Return>", self.setup_ball)
        self.ball_var = Tkinter.IntVar ()
        self.ball_var.set (1)
        cb = Tkinter.Checkbutton (frame, text="Show PointSource",
                                  variable=self.ball_var, onvalue=1,
                                  offvalue=0, command=self.show_ball)
        cb.grid (row=rw, column=0, columnspan=2, sticky='w')

    def make_color_mode_gui (self, master):
        debug ("In PointStreamer::make_color_mode_gui ()")
        f = Tkinter.Frame (master, bd=2)
        f.pack (side='top')
        frame = Tkinter.Frame (f, relief="ridge")
        frame.grid (row=0, column=0, sticky='w')
        self.color_var = Tkinter.IntVar ()
        self.color_var.set (self.color_mode)
        rb = Tkinter.Radiobutton (frame, text="No Coloring",
                                  variable=self.color_var, value=-1,
                                  command=self.set_color_mode_gui)
        rb.grid (row=0, column=0, sticky='w')
        rb = Tkinter.Radiobutton (frame, text="Scalar Coloring",
                                  variable=self.color_var, value=0,
                                  command=self.set_color_mode_gui)
        rb.grid (row=1, column=0, sticky='w')
        rb = Tkinter.Radiobutton (frame, text="Vector Coloring",
                                  variable=self.color_var, value=1,
                                  command=self.set_color_mode_gui)
        rb.grid (row=2, column=0, sticky='w')
        but = Tkinter.Button (frame, text="Streamline Color",
                              command=self.set_stream_color)
        but.grid (row=3, column=0, sticky='ew')

        frame = Tkinter.Frame (f, relief="ridge")
        frame.grid (row=0, column=1, sticky='w')
        self.integration_var = Tkinter.IntVar ()
        self.integration_var.set (self.integration_mode)
        lab = Tkinter.Label (frame, text="Integration Type")
        lab.grid (row=0, column=0, columnspan=1, sticky='ew')
        rb = Tkinter.Radiobutton (frame, text="Runge-Kutta 2nd Order",
                                  variable=self.integration_var, value=2,
                                  command=self.set_integration_gui)
        rb.grid (row=1, column=0, sticky='w')
        rb = Tkinter.Radiobutton (frame, text="Runge-Kutta 4th Order",
                                  variable=self.integration_var, value=4,
                                  command=self.set_integration_gui)
        rb.grid (row=2, column=0, sticky='w')

    def make_other_gui (self, master):
        debug ("In PointStreamer::make_other_gui ()")
        frame = Tkinter.Frame (master, relief="ridge", bd=2)
        frame.pack (side='top')
        lab = Tkinter.Label (frame, text="Integration parameters:")
        lab.grid (row=0, column=0, sticky='w', pady=5)
        but = Tkinter.Button (frame, text="Configure",
                              command=self.setup_strmln)
        but.grid (row=0, column=1, sticky='w')
        self.strmln_var = Tkinter.IntVar ()
        self.strmln_var.set (self.strmln_mode)
        rb = Tkinter.Radiobutton (frame, text="Show Streamlines",
                                  variable=self.strmln_var, value=0,
                                  command=self.set_streamline_mode)
        rb.grid (row=1, column=0, sticky='w')
        rb = Tkinter.Radiobutton (frame, text="Show Streamribbons",
                                  variable=self.strmln_var, value=1,
                                  command=self.set_streamline_mode)
        rb.grid (row=2, column=0, sticky='w')
        but = Tkinter.Button (frame, text="Configure",
                              command=self.setup_ribbonf)
        but.grid (row=2, column=1, sticky='w')
        rb = Tkinter.Radiobutton (frame, text="Show Streamtubes",
                                  variable=self.strmln_var, value=2,
                                  command=self.set_streamline_mode)
        rb.grid (row=3, column=0, sticky='w')
        but = Tkinter.Button (frame, text="Configure",
                              command=self.setup_tubef)
        but.grid (row=3, column=1, sticky='w')        
        
        but = Tkinter.Button (frame, text="Update changes", 
                      command=self.update, underline=0)
        but.grid (row=4, column=0, sticky='w')        
        self.root.bind ("<Alt-u>", self.update)
        but = Tkinter.Button (frame, text="Close", 
                      command=self.quit, underline=0)
        but.grid (row=4, column=1, sticky='w')
        self.root.bind ("<Alt-c>", self.quit)        

    def _lift (self):
        """Lifts an already created configuration window to the
        top."""
        debug ("In PointStreamer::_lift ()")
        self.root.deiconify ()
        self.root.lift ()
        self.root.focus_set ()

    def configure (self, master=None):
        debug ("In PointStreamer::configure ()")
        if (self.root and self.root.winfo_exists ()):
            return self._lift ()
        self.n_pnt = self.seed.get_n_points ()
        self.radius = self.sphere_src.GetRadius ()
        self.cen = list (self.sphere_src.GetCenter ())
        self.root = Tkinter.Toplevel (master)
        self.root.transient (master)
        self.root.title ("Configure the streamlines.")
        self.make_ball_gui (self.root)
        self.make_color_mode_gui (self.root)
        self.make_actor_gui (scalar=0, color=0, compact=1)
        self.make_other_gui (self.root)
        self.sphere_act.VisibilityOn ()
        self.renwin.Render ()

    def setup_ball (self, event=None):
        debug ("In PointStreamer::setup_ball ()")
        Common.state.busy ()
        val = self.n_pnt_var.get ()        
        self.n_pnt = val
        self.seed.set_n_points (self.n_pnt)
        val = self.radius_var.get ()
        self.radius = val
        #self.seed.set_radius (self.radius)
        self.sphere_src.SetRadius(self.radius)
        self.renwin.Render ()
        Common.state.idle ()

    def set_streamline_mode (self, event=None):
        debug ("In PointStreamer::set_streamline_mode ()")
        Common.state.busy ()
        self.strmln_mode = self.strmln_var.get ()
        self.setup_stream_pipeline ()
        self.renwin.Render ()
        Common.state.idle ()

    def setup_stream_pipeline (self):
        debug ("In PointStreamer::setup_stream_pipeline ()")
        val = self.strmln_mode
        if val == 0:
            self.stream_map.SetInput (self.strmln.GetOutput ())
        elif val == 1:
            self.ribbonf.SetInput (self.strmln.GetOutput ())
            self.stream_map.SetInput (self.ribbonf.GetOutput ())
        elif val == 2:
            self.tubef.SetInput (self.strmln.GetOutput ())
            self.stream_map.SetInput (self.tubef.GetOutput ())

    def setup_ribbonf (self, event=None):
        debug ("In PointStreamer::setup_ribbonf ()")
        conf = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        conf.configure (None, self.ribbonf)

    def setup_tubef (self, event=None):
        debug ("In PointStreamer::setup_tubef ()")
        conf = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        conf.configure (None, self.tubef)

    def setup_strmln (self, event=None):
        debug ("In PointStreamer::setup_strmln ()")
        conf = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        conf.configure (None, self.strmln)
    
    def change_locator (self, event=None):
        debug ("In PointStreamer::change_locator ()")
        val = []
        for i in range (0, 3):
            if self.coord[i] == 1:
                val.append (self.slider[i].get ())
            else:
                val.append (self.cen[i])
        
        self.sphere_src.SetCenter (*val)
        self.cen = val
        self.coord_var.set (val)
        self.renwin.Render ()

    def show_ball (self, event=None):
        debug ("In PointStreamer::show_ball ()")
        Common.state.busy ()
        val = self.ball_var.get ()
        if val == 1:
            self.sphere_act.VisibilityOn ()
        elif val == 0:
            self.sphere_act.VisibilityOff ()
        self.renwin.Render ()
        Common.state.idle ()

    def set_resolution (self, event=None):
        debug ("In PointStreamer::set_resolution ()")
        for i in range (0, 3):
            if self.coord[i] == 1:
                val = self.resoln_var[i].get ()
                self.slider[i].config (resolution=val)

    def set_color_mode_gui (self, event=None):
        "This sets up the data to setup the actual coloring mode."
        debug ("In PointStreamer::set_color_mode_gui ()")
        Common.state.busy ()
        self.color_mode = self.color_var.get ()
        self.do_color_mode ()
        self.renwin.Render ()
        Common.state.idle ()

    def do_color_mode (self):
        debug ("In PointStreamer::do_color_mode ()")
        if self.color_mode == 1: # Vector Coloring
            dr = self.mod_m.get_vector_data_range ()
            self.max_v = dr[1]
            self.stream_map.ScalarVisibilityOn ()
            self.strmln.SpeedScalarsOn ()
            self.stream_map.SetScalarRange (dr)
            self.stream_map.SetLookupTable (self.mod_m.get_vector_lut ())
        elif self.color_mode == 0: # Scalar Coloring
            self.stream_map.ScalarVisibilityOn ()
            self.strmln.SpeedScalarsOff ()
            dr = self.mod_m.get_scalar_data_range ()
            self.stream_map.SetScalarRange (dr)
            self.stream_map.SetLookupTable (self.mod_m.get_scalar_lut ())
        elif self.color_mode == -1: # No colouring
            self.stream_map.ScalarVisibilityOff ()
            self.strmln.SpeedScalarsOff ()

    def set_stream_color (self, event=None):
        debug ("In PointStreamer::set_stream_color ()")
        clr = self.stream_act.GetProperty ().GetColor ()
        init_clr = "#%02x%02x%02x"%(clr[0]*255, clr[1]*255, clr[2]*255)
        color = tkColorChooser.askcolor (title="Change axes color", 
                                         initialcolor=init_clr)
        if color[1] is not None:
            Common.state.busy ()
            clr = Common.tk_2_vtk_color (color[0])
            self.stream_act.GetProperty ().SetColor (*clr)
            self.renwin.Render ()        
            Common.state.idle ()
            if self.color_mode != -1:
                msg = "Warning: This setting will have effect only if "\
                      "the coloring mode is set to 'No Coloring'."
                Common.print_err (msg)

    def set_integration_gui (self, event=None):
        debug ("In PointStreamer::set_integration_gui ()")
        val = self.integration_var.get()
        self.integration_mode = val
        self.update_integration_mode ()

    def update_integration_mode (self):
        debug ("In PointStreamer::update_integration_mode ()")
        Common.state.busy ()
        val = self.integration_mode
        try:
            if val == 2:
                self.strmln.SetIntegrator (vtk.vtkRungeKutta2 ())
            elif val == 4:
                self.strmln.SetIntegrator (vtk.vtkRungeKutta4 ())
        except AttributeError, err:            
            msg = "Sorry unable to change the integration type. "\
                  "Try upgrading your VTK installation to a more "\
                  "recent version."
            Common.print_err (msg)            
        self.renwin.Render ()
        Common.state.idle ()
            
    def update (self, event=None):
        debug ("In PointStreamer::update ()")
        Common.state.busy ()
        self.seed.set_center (self.cen)
        self.seed.set_radius (self.radius)
        self.seed.set_n_points (self.n_pnt)
        if not self.done_init:
            self.strmln.SetInput (self.mod_m.GetOutput ())
            self.done_init = 1
            self.stream_act.VisibilityOn ()
        self.strmln.Update ()
        self.renwin.Render ()
        Common.state.idle ()
        
    def save_config (self, file):
        debug ("In PointStreamer::save_config ()")
        file.write ("%d, %d, %d\n"%(self.n_pnt, self.strmln_mode,
                                    self.integration_mode))
        # For backward compatibility - the dummy is actually unused.
        dummy_seed = vtk.vtkPointSource ()
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for i in (self.sphere_src, self.sphere_map, self.sphere_act, 
                  self.sphere_act.GetProperty (),
                  dummy_seed, self.strmln, self.ribbonf, self.tubef, 
                  self.stream_map, self.stream_act,
                  self.stream_act.GetProperty ()):
            p.dump (i, file)

    def load_config (self, file):
        debug ("In PointStreamer::load_config ()")
        self.setup_pipeline ()
        val = file.readline ()
        try:
            self.n_pnt, self.strmln_mode, self.integration_mode = eval (val)
        except ValueError: # old format
            self.n_pnt, self.strmln_mode = eval (val)
        # For backward compatibility - the dummy is actually unused.
        dummy_seed = vtk.vtkPointSource ()        
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for i in (self.sphere_src, self.sphere_map, self.sphere_act,
                  self.sphere_act.GetProperty (),
                  dummy_seed, self.strmln, self.ribbonf, self.tubef, 
                  self.stream_map, self.stream_act,
                  self.stream_act.GetProperty ()):
            p.load (i, file)
        self.setup_stream_pipeline ()
        self.radius = self.sphere_src.GetRadius ()
        self.cen = list (self.sphere_src.GetCenter ())
        self.color_mode = self.strmln.GetSpeedScalars ()
        if self.stream_map.GetScalarVisibility () == 0:
            self.color_mode = -1
        self.do_color_mode ()
        self.update ()
        self.update_integration_mode ()

    def setup_pipeline (self):
        debug ("In PointStreamer::setup_pipeline ()")
        self.get_defaults ()
        self.sphere_map.SetInput (self.sphere_src.GetOutput ())
        self.sphere_act.SetMapper (self.sphere_map)
        self.max_v = self.mod_m.get_vector_data_range ()[1]

        self.strmln.SetSource (self.seed.GetOutput ())
        self.stream_map.SetInput (self.strmln.GetOutput ())
        self.stream_map.SetScalarRange (0, self.max_v)
        self.stream_map.SetLookupTable (self.mod_m.get_vector_lut ())
        self.stream_act.SetMapper (self.stream_map)

        self.stream_act.VisibilityOff ()
        self.renwin.add_actors ((self.sphere_act, self.stream_act))        

    def quit (self, event=None):
        debug ("In PointStreamer::quit ()")
        self.sphere_act.VisibilityOff ()
        self.renwin.Render ()
        self.root.destroy ()
        self.root = None

    def get_actors (self):
        debug ("In PointStreamer::get_actors ()")
        return [self.sphere_act, self.stream_act]


class Streamlines (Base.Objects.Module):

    """ This module makes it possible to view streamlines,
    streamtubes, and stream ribbons for any type of vector data.  Any
    number of point sources can be added and deleted.  A fairly
    powerful UI is provided.  This module should work with any
    dataset.  """

    def __init__ (self, mod_m):
        debug ("In Streamlines::__init__ ()")
        Common.state.busy ()
        Base.Objects.Module.__init__ (self, mod_m)
        self.stream_ctl = {}
        self.pipe_objs = []
        self.n_streams = 0
        Common.state.idle ()

    def __del__ (self):
        debug ("In Streamlines::__del__ ()")
        Common.state.busy ()
        for key in self.stream_ctl.keys ():
            del self.stream_ctl[key]
        del self.pipe_objs
        self.renwin.Render ()
        Common.state.idle ()

    def SetInput (self, source):
        debug ("In Streamlines::SetInput ()")
        Common.state.busy ()
        for obj in self.stream_ctl.values ():
            obj.SetInput (source)
        Common.state.idle ()

    def add_streamline (self, key):
        debug ("In Streamlines::add_streamline ()")
        ctl = PointStreamer (self.mod_m)
        ctl.initialize (self.root.master)
        self.stream_ctl[key] = ctl
        self.pipe_objs.extend (ctl.get_actors ())

    def config_streamline (self, key):
        debug ("In Streamlines::config_streamline ()")
        self.stream_ctl[key].configure (self.root.master)

    def delete_streamline (self, key):
        debug ("In Streamlines::delete_streamline ()")
        del self.stream_ctl[key]
        
    def save_config (self, file):
        debug ("In Streamlines::save_config ()")
        n = len (self.stream_ctl)
        file.write ("%d\n"%n)
        for key in self.stream_ctl.keys ():
            self.stream_ctl[key].save_config (file)
        file.flush ()

    def load_config (self, file):
        debug ("In Streamlines::load_config ()")
        start_val = self.n_streams
        n = eval (file.readline ())
        for i in range (0, n):
            ctl = PointStreamer (self.mod_m)
            ctl.load_config (file)
            key = "PointSource%d"%(start_val+i)
            self.stream_ctl[key] = ctl
            self.pipe_objs.extend (ctl.get_actors ())
            self.n_streams = self.n_streams + 1

    def make_custom_gui (self):
        debug ("In Streamlines::make_custom_gui ()")
        self.make_pipeline_gui ()
        self.make_main_gui ()
        self.make_close_button ()

    def make_main_gui (self):
        debug ("In Streamlines::make_main_gui ()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top')
        scr = Tkinter.Scrollbar (frame, orient='vertical')
        self.str_lst = Tkinter.Listbox (frame, yscrollcommand=scr.set, 
                                        selectmode='single')
        scr.config (command=self.str_lst.yview)        
        self.str_lst.grid (row=0, column=0, sticky='ewns')
        scr.grid (row=0, column=1, sticky='ns')
        self.str_lst.bind ("<Double-Button-1>", self.config_streamline_gui)

        for key in self.stream_ctl.keys ():
            self.str_lst.insert ('end', key)

        but1 = Tkinter.Button (frame, text="Add streamline source", 
                               command=self.add_streamline_gui)
        but2 = Tkinter.Button (frame, text="Delete streamline source", 
                               command=self.delete_streamline_gui)
        but1.grid (row=1, column=0, columnspan=2, sticky='ew')
        but2.grid (row=2, column=0, columnspan=2, sticky='ew')
        but2 = Tkinter.Button (frame, text="Save streamlines", 
                               command=self.save)
        but2.grid (row=3, column=0, columnspan=2, sticky='ew')
        but2 = Tkinter.Button (frame, text="Load streamlines",
                               command=self.load)
        but2.grid (row=4, column=0, columnspan=2, sticky='ew')
        
    def add_streamline_gui (self):
        debug ("In Streamlines::add_streamline_gui ()")
        Common.state.busy ()
        str = "PointSource%d"%self.n_streams
        self.str_lst.insert ('end', str)
        self.n_streams = self.n_streams + 1
        self.add_streamline (str)
        Common.state.idle ()

    def delete_streamline_gui (self):
        debug ("In Streamlines::delete_streamline_gui ()")
        Common.state.busy ()
        str = self.str_lst.get ('active')
        msg = "You are about to delete the streamlines due to the "\
              "%s. Are you sure you want to do this?" %(str)
        ans = tkMessageBox.askyesno ("Delete Streamline?", msg)
        if ans == 1:
            self.str_lst.delete ('active')            
            self.delete_streamline (str)
        Common.state.idle ()

    def config_streamline_gui (self, event=None):
        debug ("In Streamlines::config_streamline_gui ()")
        str = self.str_lst.get ('active')
        self.config_streamline (str)

    def save (self):
        debug ("In Streamlines::save ()")
        file_name = tk_fsave (title="Save streamlines", 
                              initialdir=Common.config.initial_dir,
                              defaultextension=".str",
                              filetypes=[("Streamline files", "*.str"), 
                                         ("All files", "*")])
        if file_name:
            Common.state.busy ()
            file = open (file_name, "w")
            self.save_config (file)
            file.close ()
            Common.state.idle ()

    def load (self):
        debug ("In Streamlines::load ()")
        file_name = tk_fopen (title="Load streamlines", 
                              initialdir=Common.config.initial_dir,
                              filetypes=[("Streamline files", "*.str"), 
                                         ("All files", "*")])
        if file_name:
            Common.state.busy ()
            file = open (file_name, "r")
            n_orig = len (self.stream_ctl)
            self.load_config (file)
            n = len (self.stream_ctl) - n_orig
            for i in range (0, n):
                str = "PointSource%d"%self.n_streams
                self.str_lst.insert ('end', str)
                self.n_streams = self.n_streams + 1
            file.close ()
            Common.state.idle ()
