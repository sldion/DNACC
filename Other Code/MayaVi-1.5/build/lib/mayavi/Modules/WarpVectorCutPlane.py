"""

This module takes a cut plane and warps it using a vtkWarpVector as
per the vector times a scale factor.  This will work for any dataset.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.5 $"
__date__ = "$Date: 2005/08/02 18:30:14 $"

import Base.Objects, Common
import Tkinter, tkColorChooser, math
import vtk
import vtkPipeline.vtkMethodParser

debug = Common.debug

class WarpVectorCutPlane (Base.Objects.CutPlaneModule):

    """ This module takes a cut plane and warps it using a
    vtkWarpVector as per the vector times a scale factor.  This will
    work for any dataset. """

    def __init__ (self, mod_m): 
        debug ("In WarpVectorCutPlane::__init__ ()")
        Common.state.busy ()
        Base.Objects.CutPlaneModule.__init__ (self, mod_m)
        self.cut = vtk.vtkCutter ()
        self.warp = vtk.vtkWarpVector ()
        self.norm = vtk.vtkPolyDataNormals ()
        self.mapper = self.map = vtk.vtkPolyDataMapper ()
        self.map.SetLookupTable (self.mod_m.get_scalar_lut ())
        self.actor = self.act = vtk.vtkActor ()
        self.data_out = self.mod_m.GetOutput ()
        self._initialize ()
        self._gui_init ()
        self.renwin.Render ()
        Common.state.idle ()

    def __del__ (self): 
        debug ("In WarpVectorCutPlane::__del__ ()")
        if self.act:
            self.renwin.remove_actors (self.act)
        self.renwin.Render ()

    def _initialize (self):
        debug ("In WarpVectorCutPlane::_initialize ()")
        self.cut.SetInput (self.data_out)
        self.cut.SetCutFunction (self.plane)
        self.warp.SetScaleFactor (1.0)
        self.warp.SetInput (self.cut.GetOutput ())
        self.map.SetInput (self.warp.GetOutput ())
        self.act.SetMapper (self.map)
        self.data_range = self.mod_m.get_scalar_data_range ()
        self.map.SetScalarRange (self.data_range)
        self.act.GetProperty ().BackfaceCullingOff ()
        self.act.GetProperty ().FrontfaceCullingOff ()
        self.center = self.data_out.GetCenter ()
        self.plane.SetOrigin (self.center)
        self.plane.SetNormal (0.0, 0.0, 1.0)
        self.set_def_step_size ()
        self.slider_pos = 0
        self.renwin.add_actors (self.act)
        # used for the pipeline browser
        self.pipe_objs = self.act
        
    def set_def_step_size (self):
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
        debug ("In WarpVectorCutPlane::_gui_init ()")
        self.step_var.set (self.step_size)
        self.n_step_var.set (10)
        self._auto_sweep_init ()
        self.sweep_step.set (1)
        self.normals_on = Tkinter.IntVar ()
        self.normals_on.set (0)
        self.angle_var = Tkinter.DoubleVar ()
        self.angle_var.set (45)

    def SetInput (self, source): 
        debug ("In WarpVectorCutPlane::SetInput ()")
        Common.state.busy ()
        self.data_out = source
        self.cut.SetInput (self.data_out)
        dr = self.mod_m.get_scalar_data_range ()
        if (dr[0] != self.data_range[0]) or (dr[1] != self.data_range[1]):
            self.data_range = dr
            self.map.SetScalarRange (dr)
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In WarpVectorCutPlane::save_config ()")
        file.write ("%d, %d, %f, %d, %f\n"%(self.slider_pos,
                                            self.n_step_var.get (),
                                            self.step_size,
                                            self.normals_on.get (),
                                            self.angle_var.get ()))
        
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.plane, self.cut, self.warp, self.map,
                    self.act, self.act.GetProperty ()):
            p.dump (obj, file)

    def load_config (self, file):
        debug ("In WarpVectorCutPlane::load_config ()")
        self.slider_pos, n_s, self.step_size, \
                         nor, ang = eval (file.readline ())
        self.n_step_var.set (n_s)
        self.normals_on.set (nor)
        self.angle_var.set (ang)
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.plane, self.cut, self.warp, self.map,
                    self.act, self.act.GetProperty ()):        
            p.load (obj, file)

        self.do_normals ()

    def config_changed (self): 
        debug ("In WarpVectorCutPlane::config_changed ()")
        pass

    def make_main_gui (self): 
        debug ("In WarpVectorCutPlane::make_main_gui ()")
        self.make_cut_plane_gui ()
        self.make_my_gui ()
        self.make_actor_gui (compact=1)
        self.make_auto_sweep_gui ()

    def _get_ranges (self, val):
        debug ("In WarpVectorCutPlane::_get_ranges ()")
        if val == 0.0:
            res, min_v, max_v = 0.1, -1.0, 1.0
        elif val > 0:
            res = val/10.0
            min_v = val - 50*res
            max_v = val + 50*res
            #min_v = max (0, min_v)
        else:
            res = abs (val)/10.0
            min_v = val - 50*res
            max_v = val + 50*res
            #max_v = min (0, max_v)
        return res, min_v, max_v

    def make_my_gui (self):
        debug ("In WarpVectorCutPlane::make_my_gui()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)
        self.make_warp_gui (frame)
        self.make_normals_gui (frame)

    def make_normals_gui (self, master):
        debug ("In WarpVectorCutPlane::make_normals_gui ()")
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)
        rw = 0
        norm = Tkinter.Checkbutton (frame, text="PolyDataNormals", 
                                    variable=self.normals_on, onvalue=1,
                                    offvalue=0, command=self.do_normals)
        norm.grid (row=rw, columnspan=1, sticky='w')
        #rw = rw + 1
        lab = Tkinter.Label (frame, text="Angle: ")
        lab.grid (row=rw, column=1, sticky='w')
        entry = Tkinter.Entry (frame, width=10, relief='sunken', 
                               textvariable=self.angle_var)
        entry.grid (row=rw, column=2, sticky='ew')
        entry.bind ("<Return>", self.do_normals)

    def make_warp_gui (self, master):
        debug ("In WarpVectorCutPlane::make_warp_gui ()")
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)

        cur_scale = self.warp.GetScaleFactor ()
        res, min_v, max_v = self._get_ranges (cur_scale)
        
        self.scale_res_var = Tkinter.DoubleVar ()
        self.scale_res_var.set (res)
        self.min_scale_var = Tkinter.DoubleVar ()
        self.min_scale_var.set (min_v)
        self.max_scale_var = Tkinter.DoubleVar ()
        self.max_scale_var.set (max_v)

        rw = 0
        sl = Tkinter.Scale (frame, label="Set Scale Factor", 
                            from_= self.min_scale_var.get (),
                            to = self.max_scale_var.get (),
                            length="5c", orient='horizontal', 
                            resolution=self.scale_res_var.get ())
        sl.set (cur_scale)
        sl.grid (row=rw, column=0, columnspan=3, sticky='ew')
        rw = rw + 1
        sl.bind ("<ButtonRelease>", self.change_scale)
        self.scale_slider = sl
        lab = Tkinter.Label (frame,
                             text="Scale slider: Min, Max, Resolution")
        lab.grid (row=rw, column=0, columnspan=3, sticky='w')
        rw = rw+1
        # min
        entry = Tkinter.Entry (frame, width=10, relief='sunken', 
                               textvariable=self.min_scale_var)
        entry.grid (row=rw, column=0, sticky='we')
        entry.bind ("<Return>", self.change_scale_limits)

        # max
        entry = Tkinter.Entry (frame, width=10, relief='sunken', 
                               textvariable=self.max_scale_var)
        entry.grid (row=rw, column=1, sticky='we')
        entry.bind ("<Return>", self.change_scale_limits)

        # resolution
        entr = Tkinter.Entry (frame, width=10, relief='sunken',
                              textvariable=self.scale_res_var)
        entr.grid (row=rw, column=2, sticky='ew')
        entr.bind ("<Return>", self.set_scale_resolution)


    def set_scale_resolution (self, event=None):
        """ Called when the scale slider resolution is changed. """
        debug ("In WarpVectorCutPlane::set_scale_resolution()")
        self.scale_slider.config (resolution=self.scale_res_var.get ())

    def change_scale (self, event=None):
        debug ("In WarpVectorCutPlane::change_scale()")
        Common.state.busy ()
        self.warp.SetScaleFactor (self.scale_slider.get())
        self.mod_m.Update ()
        Common.state.idle ()

    def change_scale_limits (self, event=None):
        debug ("In WarpVectorCutPlane::change_scale_limits()")
        self.scale_slider.config (from_ = self.min_scale_var.get(),
                                  to = self.max_scale_var.get())

    def do_normals (self, event=None):
        debug ("In WarpVectorCutPlane::do_normals ()")
        Common.state.busy ()
        if self.normals_on.get ():
            self.norm.SetInput (self.warp.GetOutput ())
            self.norm.SetFeatureAngle (self.angle_var.get ())
            self.map.SetInput (self.norm.GetOutput ())
        else:
            self.map.SetInput (self.warp.GetOutput ())
        self.renwin.Render ()
        Common.state.idle ()

    def do_sweep (self, event=None):
        debug ("In WarpVectorCutPlane::do_sweep ()")
        if self.sweep_var.get ():
            val = int (1000*self.sweep_delay.get ())
            self.root.after (val, self.update_sweep)

    def update_sweep (self):
        debug ("In WarpVectorCutPlane::update_sweep ()")
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
