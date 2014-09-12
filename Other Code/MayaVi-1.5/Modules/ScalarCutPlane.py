"""

This module plots scalar data on a cut plane either as a color map or
with contour lines.  This will work for any dataset.  Note that one
can either specify a total number of contours between the minimum and
maximum values by entering a single integer or specify the individual
contours by specifying a Python list/tuple in the GUI.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.6 $"
__date__ = "$Date: 2005/08/02 18:30:13 $"

import Base.Objects, Common
import Tkinter, tkColorChooser, math
import vtk
import vtkPipeline.vtkMethodParser

debug = Common.debug

class ScalarCutPlane (Base.Objects.CutPlaneModule):

    """ This module plots scalar data on a cut plane either as a color
    map or with contour lines.  This will work for any dataset.  Note
    that one can either specify a total number of contours between the
    minimum and maximum values by entering a single integer or specify
    the individual contours by specifying a Python list/tuple in the
    GUI."""

    def __init__ (self, mod_m): 
        debug ("In ScalarCutPlane::__init__ ()")
        Common.state.busy ()
        Base.Objects.CutPlaneModule.__init__ (self, mod_m)
        self.cut = vtk.vtkCutter ()
        self.cont_fil = vtk.vtkContourFilter ()
        self.mapper = self.map = vtk.vtkPolyDataMapper ()
        self.map.SetLookupTable (self.mod_m.get_scalar_lut ())
        self.actor = self.act = vtk.vtkActor ()
        self.data_out = self.mod_m.GetOutput ()
        self._initialize ()
        self._gui_init ()
        self.renwin.Render ()
        Common.state.idle ()

    def __del__ (self): 
        debug ("In ScalarCutPlane::__del__ ()")
        if self.act:
            self.renwin.remove_actors (self.act)
        self.renwin.Render ()

    def _initialize (self):
        debug ("In ScalarCutPlane::_initialize ()")
        self.cut.SetInput (self.data_out)
        self.cut.SetCutFunction (self.plane)
        self.map.SetInput (self.cut.GetOutput ())
        self.act.SetMapper (self.map)
        self.data_range = self.mod_m.get_scalar_data_range ()
        self.map.SetScalarRange (self.data_range)
        self.act.GetProperty ().SetLineWidth (3.0)
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
        debug ("In ScalarCutPlane::_gui_init ()")
        self.step_var.set (self.step_size)
        self.n_step_var.set (10)        
        self._contour_init ()
        self._auto_sweep_init ()
        self.sweep_step.set (1)

    def _contour_init (self):
        debug ("In ScalarCutPlane::_contour_init ()")
        Base.Objects.Module._contour_init (self)
        self.contour_on.set (0)
        self.n_cnt.set ("10")
        dr = self.mod_m.get_scalar_data_range ()
        self.min_cnt.set (dr[0])
        self.max_cnt.set (dr[1])
        
    def SetInput (self, source): 
        debug ("In ScalarCutPlane::SetInput ()")
        Common.state.busy ()
        self.data_out = source
        self.cut.SetInput (self.data_out)
        dr = self.mod_m.get_scalar_data_range ()
        if (dr[0] != self.data_range[0]) or (dr[1] != self.data_range[1]):
            self.data_range = dr
            self.map.SetScalarRange (dr)
            self.min_cnt.set (dr[0])
            self.max_cnt.set (dr[1])
            self.change_contour ()
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In ScalarCutPlane::save_config ()")
        file.write ("%d, %d, %f\n"%(self.slider_pos,
                                    self.n_step_var.get (),
                                    self.step_size))
        file.write ("%d, %s, %f, %f\n"%(self.contour_on.get (),
                                        self.n_cnt.get (),
                                        self.min_cnt.get (),
                                        self.max_cnt.get ()))
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.plane, self.cut, self.cont_fil, self.map,
                    self.act, self.act.GetProperty ()):
            p.dump (obj, file)

    def load_config (self, file): 
        debug ("In ScalarCutPlane::load_config ()")
        self.slider_pos, n_s, self.step_size = eval (file.readline ())
        cnt_on, n_cnt, min_cnt, max_cnt = eval (file.readline ())
        self.n_step_var.set (n_s)
        self.contour_on.set (cnt_on)
        self.n_cnt.set (str(n_cnt))
        self.min_cnt.set (min_cnt)
        self.max_cnt.set (max_cnt)
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.plane, self.cut, self.cont_fil, self.map,
                    self.act, self.act.GetProperty ()):        
            p.load (obj, file)

        self.do_contour ()

    def config_changed (self): 
        debug ("In ScalarCutPlane::config_changed ()")
        pass

    def make_main_gui (self): 
        debug ("In ScalarCutPlane::make_main_gui ()")
        self.make_cut_plane_gui ()
        self.make_contour_gui ()
        self.make_actor_gui (compact=1)
        self.make_auto_sweep_gui ()

    def do_contour (self, event=None):
        debug ("In ScalarCutPlane::do_contour ()")
        Common.state.busy ()
        if self.contour_on.get ():
            if not self.mod_m.get_scalar_data_name ():
                self.contour_on.set (0)
                msg = "Warning: No scalar data present to contour!"
                Common.print_err (msg)
                return
            self.cont_fil.SetInput (self.cut.GetOutput ())
            self.map.SetInput (self.cont_fil.GetOutput ())
        else:
            self.map.SetInput (self.cut.GetOutput ())
        self.change_contour ()
        Common.state.idle ()

    def change_contour (self, event=None):
        debug ("In ScalarCutPlane::change_contour ()")
        Common.state.busy ()
        min_cnt = self.min_cnt.get ()
        max_cnt = self.max_cnt.get ()        
        if max_cnt < min_cnt:
            msg = "Error: Max. contour less than min. contour. "\
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
        debug ("In ScalarCutPlane::do_sweep ()")
        if self.sweep_var.get ():
            val = int (1000*self.sweep_delay.get ())
            self.root.after (val, self.update_sweep)

    def update_sweep (self):
        debug ("In ScalarCutPlane::update_sweep ()")
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
