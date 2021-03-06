"""

This module shows a grid plane of the given input structured,
rectilinear or structured points grid with the scalar data either as a
color map or as contour lines.  This works only for structured grid,
structured point and rectilinear grid data.  Note that one can either
specify a total number of contours between the minimum and maximum
values by entering a single integer or specify the individual contours
by specifying a Python list/tuple in the GUI.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.12 $"
__date__ = "$Date: 2005/08/02 18:30:13 $"

import Base.Objects, Common
import Tkinter, tkColorChooser
import vtk
import vtkPipeline.vtkMethodParser

debug = Common.debug

def set_extents (plane, lst):
    debug ("In set_extents ()")
    plane.SetExtent (lst[0], lst[1], lst[2], lst[3], lst[4], lst[5])

class ContourGridPlane (Base.Objects.Module):

    """ This module shows a grid plane of the given input structured,
    rectilinear or structured points grid with the scalar data either
    as a color map or as contour lines.  This works only for
    structured grid, structured point and rectilinear grid data.  Note
    that one can either specify a total number of contours between the
    minimum and maximum values by entering a single integer or specify
    the individual contours by specifying a Python list/tuple in the
    GUI."""

    def __init__ (self, mod_m): 
        debug ("In ContourGridPlane::__init__ ()")
        Common.state.busy ()
        Base.Objects.Module.__init__ (self, mod_m)
        self.act = None
        out = self.mod_m.GetOutput ()
        if out.IsA('vtkStructuredGrid'):
            self.plane = vtk.vtkStructuredGridGeometryFilter ()
        elif out.IsA ('vtkStructuredPoints') or out.IsA('vtkImageData'):
            if hasattr (vtk, 'vtkImageDataGeometryFilter'):
                self.plane = vtk.vtkImageDataGeometryFilter ()
            else:
                self.plane = vtk.vtkStructuredPointsGeometryFilter ()
        elif out.IsA ('vtkRectilinearGrid'):
            self.plane = vtk.vtkRectilinearGridGeometryFilter ()
        else:
            msg = "This module does not support the %s dataset."%(out.GetClassName())
            raise Base.Objects.ModuleException, msg

        self.cont_fil = vtk.vtkContourFilter ()
        self.mapper = self.map = vtk.vtkPolyDataMapper ()
        self.actor = self.act = vtk.vtkActor ()

        self._initialize ()
        self._gui_init ()
        self.renwin.Render ()
        Common.state.idle ()

    def __del__ (self): 
        debug ("In ContourGridPlane::__del__ ()")
        if self.act:
            self.renwin.remove_actors (self.act)
        self.renwin.Render ()

    def _initialize (self):
        debug ("In ContourGridPlane::_initialize ()")
        self.map.SetLookupTable (self.mod_m.get_scalar_lut ())
        self.data_range = self.mod_m.get_scalar_data_range ()
        self.map.SetScalarRange (self.data_range)
        data_out = self.mod_m.GetOutput ()
        dim = data_out.GetDimensions ()
        self.dim = [dim[0] -1, dim[1] -1, dim[2] -1]
        self.plane.SetInput (data_out)
        self.map.SetInput (self.plane.GetOutput ())
        self.act.SetMapper (self.map)
        self.act.GetProperty ().SetColor (*Common.config.fg_color)
        self.act.GetProperty ().SetLineWidth (4)
        self.act.GetProperty ().BackfaceCullingOff ()
        self.act.GetProperty ().FrontfaceCullingOff ()
        self.renwin.add_actors (self.act)
        # used for the pipeline browser
        self.pipe_objs = self.act
        
    def _gui_init (self): 
        debug ("In ContourGridPlane::_gui_init ()")
        self.axis_var = Tkinter.IntVar ()
        self.slider = None
        self.slider_pos = 0
        self.axis_var.set (0)
        self.change_axis ()
        self.root = None
        self._contour_init ()
        self._auto_sweep_init ()
        self.sweep_step.set (1)

    def _contour_init (self):
        debug ("In ContourGridPlane::_contour_init ()")
        Base.Objects.Module._contour_init (self)
        self.contour_on.set (0)
        self.linew_var.set (self.act.GetProperty ().GetLineWidth ())
        self.n_cnt.set ("10")
        dr = self.mod_m.get_scalar_data_range ()
        self.min_cnt.set (dr[0])
        self.max_cnt.set (dr[1])
        
    def SetInput (self, source): 
        debug ("In ContourGridPlane::SetInput ()")
        Common.state.busy ()
        self.plane.SetInput (source)
        dim = source.GetDimensions ()
        self.dim = [dim[0] -1, dim[1] -1, dim[2] -1]
        dr = self.mod_m.get_scalar_data_range ()
        self.config_extents()
        if (dr[0] != self.data_range[0]) or (dr[1] != self.data_range[1]):
            self.map.SetScalarRange (dr)
            self.data_range = dr
            self.min_cnt.set (dr[0])
            self.max_cnt.set (dr[1])
            self.change_contour ()
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In ContourGridPlane::save_config ()")
        file.write ("%d, %d, %d, %s, %f, %f\n"%(self.axis_var.get (),
                                                self.slider_pos,
                                                self.contour_on.get (),
                                                self.n_cnt.get (),
                                                self.min_cnt.get (),
                                                self.max_cnt.get ()))
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.plane, self.cont_fil, self.map, self.act,
                    self.act.GetProperty ()):
            p.dump (obj, file)

    def load_config (self, file): 
        debug ("In ContourGridPlane::load_config ()")
        a, pos, cnt_on, n_cnt, min_cnt, max_cnt = eval (file.readline ())
        self.axis_var.set (a)
        self.slider_pos = pos
        self.contour_on.set (cnt_on)
        self.n_cnt.set (str(n_cnt))
        self.min_cnt.set (min_cnt)
        self.max_cnt.set (max_cnt)
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        if self.plane.GetClassName () == 'vtkImageDataGeometryFilter':
            p.load (self.plane, file, 'vtkStructuredPointsGeometryFilter')
        else:
            p.load (self.plane, file, 'vtkImageDataGeometryFilter')        
        for obj in (self.cont_fil, self.map, self.act,
                    self.act.GetProperty ()):        
            p.load (obj, file)
        self.config_extents ()
        self.do_contour ()
        
    def config_changed (self): 
        debug ("In ContourGridPlane::config_changed ()")
        self.act.GetProperty ().SetColor(*Common.config.fg_color)

    def make_main_gui (self): 
        debug ("In ContourGridPlane::make_main_gui ()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)
        txt = ("X-Axis", "Y-Axis", "Z-Axis")
        #self.axis_on_but = []
        for i in range (3):
            b = Tkinter.Radiobutton (frame, text=txt[i],
                                     variable=self.axis_var,
                                     value=i, command=self.change_axis)
            b.grid (row=i, column=0)
            #self.axis_on_but.append (b)

        val = self.dim[self.axis_var.get ()]
        self.slider = Tkinter.Scale (frame, label="Position", from_=0,
                                     to=val, length="8c",
                                     orient='horizontal')
        self.slider.set (self.slider_pos)
        self.slider.grid (row=3, column=0, pady=3)
        self.slider.bind ("<ButtonRelease>", self.change_slider)

        self.make_actor_gui (color=0, scalar=0, representation=0)
        self.make_contour_gui ()
        self.make_auto_sweep_gui ()

    def config_extents (self): 
        debug ("In ContourGridPlane::config_extents ()")
        Common.state.busy ()
        i = self.axis_var.get ()
        dim = self.dim
        extents = [0, dim[0], 0, dim[1], 0, dim[2]]
        extents[2*i] = self.slider_pos
        extents[2*i+1] = self.slider_pos
        set_extents (self.plane, extents)
        self.renwin.Render ()
        Common.state.idle ()

    def change_axis (self, event=None): 
        debug ("In ContourGridPlane::change_axis ()")
        i = self.axis_var.get ()
        if self.slider:
            self.slider.config (from_=0, to=self.dim[i])
        self.config_extents ()

    def change_slider (self, event=None): 
        debug ("In ContourGridPlane::change_slider ()")
        val = self.slider.get ()
        self.slider_pos = val
        self.config_extents ()

    def do_contour (self, event=None):
        debug ("In ContourGridPlane::do_contour ()")
        Common.state.busy ()
        if self.contour_on.get ():
            if not self.mod_m.get_scalar_data_name ():
                self.contour_on.set (0)
                msg = "Warning: No scalar data present to contour!"
                Common.print_err (msg)
                return
            self.cont_fil.SetInput (self.plane.GetOutput ())
            self.map.SetInput (self.cont_fil.GetOutput ())
        else:
            self.map.SetInput (self.plane.GetOutput ())
        self.change_contour ()
        Common.state.idle ()

    def change_contour (self, event=None):
        debug ("In ContourGridPlane::change_contour ()")
        Common.state.busy ()
        min_cnt = self.min_cnt.get ()
        max_cnt = self.max_cnt.get ()        
        if max_cnt < min_cnt:
            msg = "Error: Max. contour less than min. contour.  "\
                  "Setting to defaults."
            debug (msg)
            dr = self.data_range
            min_cnt, max_cnt = dr[0], dr[1]
            self.min_cnt.set (min_cnt)
            self.max_cnt.set (max_cnt)

        n_cnt = eval (self.n_cnt.get ())
        auto = 1
        if hasattr(n_cnt, "__getitem__"):
            auto = 0
        if self.contour_on.get ():
            if auto:
                self.cont_fil.GenerateValues (n_cnt, min_cnt, max_cnt)
            else:
                self.cont_fil.SetNumberOfContours(len(n_cnt))
                for i in range(len(n_cnt)):
                    self.cont_fil.SetValue(i, n_cnt[i])
            self.cont_fil.Update ()
        self.renwin.Render ()
        Common.state.idle ()

    def do_sweep (self, event=None):
        debug ("In ContourGridPlane::do_sweep ()")
        if self.sweep_var.get ():
            val = int (1000*self.sweep_delay.get ())
            self.root.after (val, self.update_sweep)

    def update_sweep (self):
        debug ("In ContourGridPlane::update_sweep ()")
        if self.sweep_var.get ():
            d_pos = self.sweep_step.get ()
            pos = self.slider_pos + d_pos
            if (d_pos > 0) and (pos > self.dim[self.axis_var.get ()]):
                pos = 0
            elif (d_pos < 0) and (pos < 0):
                pos = self.dim[self.axis_var.get ()]
            self.slider.set (pos)
            self.change_slider ()            
            val = int (1000*self.sweep_delay.get ())
            self.root.after (val, self.update_sweep)
