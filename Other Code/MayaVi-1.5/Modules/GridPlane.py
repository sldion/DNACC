"""

This module shows a grid plane of the given input grid.  The plane can
be shown as a wireframe or coloured surface with or without scalar
visibility.  This works only for structured grid, structured point and
rectilinear grid data.  Useful for debugging and displaying your
created grid.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.11 $"
__date__ = "$Date: 2005/08/02 18:30:13 $"

import Base.Objects, Common
import Tkinter, tkColorChooser
import vtk
import vtkPipeline.vtkMethodParser

debug = Common.debug

def set_extents (plane, lst):
    debug ("In set_extents ()")
    plane.SetExtent (lst[0], lst[1], lst[2], lst[3], lst[4], lst[5])

class GridPlane (Base.Objects.Module):

    """ This module shows a grid plane of the given input grid.  The
    plane can be shown as a wireframe or coloured surface with or
    without scalar visibility.  This works only for structured grid,
    structured point and rectilinear grid data.  Useful for debugging
    and displaying your created grid."""

    def __init__ (self, mod_m): 
        debug ("In GridPlane::__init__ ()")
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
        
        self.mapper = self.map = vtk.vtkPolyDataMapper ()
        self.actor = self.act = vtk.vtkActor ()
        self._initialize ()
        self._gui_init ()
        self.renwin.Render ()
        Common.state.idle ()

    def __del__ (self): 
        debug ("In GridPlane::__del__ ()")
        if self.act:
            self.renwin.remove_actors (self.act)
        self.renwin.Render ()

    def _initialize (self): 
        debug ("In GridPlane::_initialize ()")
        self.map.SetLookupTable (self.mod_m.get_scalar_lut ())
        self.map.SetScalarRange (self.mod_m.get_scalar_data_range ())
        data_out = self.mod_m.GetOutput ()
        dim = data_out.GetDimensions ()
        self.dim = [dim[0] -1, dim[1] -1, dim[2] -1]
        self.plane.SetInput (data_out)
        self.map.SetInput (self.plane.GetOutput ())
        self.act.SetMapper (self.map)
        self.act.GetProperty ().SetColor (*Common.config.fg_color)
        self.act.GetProperty ().BackfaceCullingOff ()
        self.act.GetProperty ().FrontfaceCullingOff ()
        self.act.GetProperty ().SetRepresentation (1)
        self.map.SetScalarVisibility (0)
        data_out = self.mod_m.GetOutput ()
        self.renwin.add_actors (self.act)
        # used for the pipeline browser
        self.pipe_objs = self.act
        
    def _gui_init (self): 
        debug ("In GridPlane::_gui_init ()")
        self.axis_var = Tkinter.IntVar ()
        self.slider = None
        self.slider_pos = 0
        self.axis_var.set (0)
        self.change_axis ()
        self._auto_sweep_init ()
        self.sweep_step.set (1)
        
    def SetInput (self, source): 
        debug ("In GridPlane::SetInput ()")
        Common.state.busy ()
        self.plane.SetInput (source)
        dr = self.mod_m.get_scalar_data_range ()
        self.map.SetScalarRange (dr)
        dim = source.GetDimensions ()
        self.dim = [dim[0] -1, dim[1] -1, dim[2] -1]
        self.config_extents()
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In GridPlane::save_config ()")
        file.write ("%d, %d\n"%(self.axis_var.get (), self.slider_pos))
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.plane, self.map, self.act,
                    self.act.GetProperty ()):
            p.dump (obj, file)

    def load_config (self, file): 
        debug ("In GridPlane::load_config ()")
        a, pos = eval (file.readline ())
        self.axis_var.set (a)
        self.slider_pos = pos
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        if self.plane.GetClassName () == 'vtkImageDataGeometryFilter':
            p.load (self.plane, file, 'vtkStructuredPointsGeometryFilter')
        else:
            p.load (self.plane, file, 'vtkImageDataGeometryFilter')
        for obj in (self.map, self.act,
                    self.act.GetProperty ()):        
            p.load (obj, file)
        self.config_extents ()
        
    def config_changed (self): 
        debug ("In GridPlane::config_changed ()")
        self.act.GetProperty ().SetColor (*Common.config.fg_color)

    def make_main_gui (self): 
        debug ("In GridPlane::make_main_gui ()")
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

        self.make_actor_gui ()
        self.make_auto_sweep_gui ()

    def config_extents (self): 
        debug ("In GridPlane::config_extents ()")
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
        debug ("In GridPlane::change_axis ()")
        i = self.axis_var.get ()
        if self.slider:
            self.slider.config (from_=0, to=self.dim[i])
        self.config_extents ()

    def change_slider (self, event=None): 
        debug ("In GridPlane::change_slider ()")
        val = self.slider.get ()
        self.slider_pos = val
        self.config_extents ()

    def do_sweep (self, event=None):
        debug ("In GridPlane::do_sweep ()")
        if self.sweep_var.get ():
            val = int (1000*self.sweep_delay.get ())
            self.root.after (val, self.update_sweep)

    def update_sweep (self):
        debug ("In GridPlane::update_sweep ()")
        if self.sweep_var.get ():
            d_pos = self.sweep_step.get ()
            pos = self.slider_pos + d_pos
            if ((d_pos > 0) and (pos > self.dim[self.axis_var.get ()])):
                pos = 0
            elif (d_pos < 0) and (pos < 0):
                pos = self.dim[self.axis_var.get ()]
            self.slider.set (pos)
            self.change_slider ()            
            val = int (1000*self.sweep_delay.get ())
            self.root.after (val, self.update_sweep)
