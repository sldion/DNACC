"""

This filter takes a cut plane of any given input data set.  It
interpolates the attributes onto a plane.  The position and
orientation of the plane are configurable using a GUI.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.3 $"
__date__ = "$Date: 2005/08/02 18:26:24 $"

import Base.Objects, Common
import vtk
import vtkPipeline.ConfigVtkObj
import Tkinter
import math

debug = Common.debug

class CutPlane (Base.Objects.Filter):

    """ This filter takes a cut plane of any given input data set.  It
    interpolates the attributes onto a plane.  The position and
    orientation of the plane are configurable using a GUI.  """

    def initialize (self):
        debug ("In CutPlane::initialize ()")
        self.plane = vtk.vtkPlane ()
        self.fil = vtk.vtkCutter ()
        out = self.prev_fil.GetOutput()
        self.fil.SetInput (out)
        self.fil.SetCutFunction (self.plane)

        self.center = out.GetCenter ()
        self.plane.SetOrigin (self.center)
        self.plane.SetNormal (0.0, 0.0, 1.0)

        self.step_var = Tkinter.DoubleVar ()
        self.n_step_var = Tkinter.IntVar ()
        self.resoln_var = Tkinter.DoubleVar ()
        self.resoln_var.set (1.0)
        self.slider = []
        self.set_def_step_size ()
        self.step_var.set (self.step_size)
        self.n_step_var.set (10)        
        self.slider_pos = 0
        self._auto_sweep_init ()
        self.sweep_step.set (1)

        self.fil.Update ()


    def set_def_step_size (self):
        out = self.prev_fil.GetOutput()
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

        l = vol/float(n)
        if data_2d == 1:
            self.step_size = math.sqrt (l)
        else:
            self.step_size = math.pow (l, 1.0/3.0)
        
    def set_input_source (self, source):
        debug ("In CutPlane::set_input_source ()")
        Common.state.busy ()
        self.fil.SetInput (source.GetOutput ())
        self.prev_filter = source
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In CutPlane::save_config ()")
        file.write ("%d, %d, %f\n"%(self.slider_pos,
                                    self.n_step_var.get (),
                                    self.step_size))
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.plane, self.fil):
            p.dump (obj, file)

    def load_config (self, file): 
        debug ("In CutPlane::load_config ()")
        self.slider_pos, n_s, self.step_size = eval (file.readline ())
        self.n_step_var.set (n_s)
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.plane, self.fil):        
            p.load (obj, file)

    def make_main_gui (self): 
        debug ("In CutPlane::make_main_gui ()")
        self.make_cut_plane_gui ()
        self.make_auto_sweep_gui ()

    def get_angles (self):
        debug ("In CutPlane::get_angles ()")
        nor = self.plane.GetNormal ()
        pos = self.plane.GetOrigin ()
        zang = math.acos (nor[2])
        xang = math.atan2 (nor[1], nor[0])
        if xang < 0:
            xang = xang + 2.0*math.pi

        zang = zang*180.0/math.pi
        xang = xang*180.0/math.pi
        return (zang, xang)    

    def config_extents (self, val):
        debug ("In CutPlane::config_extents ()")
        zang = val[0]*math.pi/180.0
        xang = val[1]*math.pi/180.0
        ds = val[2]*self.step_size
        cos1 = math.cos (zang)
        sin1 = math.sin (zang)
        cos2 = math.cos (xang)
        sin2 = math.sin (xang)
        nor = (sin1*cos2, sin1*sin2, cos1)
        cen = self.center
        pos = (cen[0] + ds*nor[0], cen[1] + ds*nor[1], cen[2] + ds*nor[2])
        self.plane.SetNormal (nor)
        self.plane.SetOrigin (pos)

    def make_cut_plane_gui (self):
        debug ("In CutPlane::make_cut_plane_gui ()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)

        angle = self.get_angles ()
        self.slider = []
        sl = Tkinter.Scale (frame, label="Angle from Z-axis", from_=0,
                            to=180, length="8c", orient='horizontal')
        sl.set (angle[0])
        sl.pack (side='top')
        sl.bind ("<ButtonRelease>", self.change_slider)
        self.slider.append (sl)
        
        sl = Tkinter.Scale (frame, label="Angle from X-axis", from_=0,
                            to=360, length="8c", orient='horizontal')
        sl.set (angle[1])
        sl.pack (side='top')
        sl.bind ("<ButtonRelease>", self.change_slider)
        self.slider.append (sl)
        
        val = self.n_step_var.get ()
        sl = Tkinter.Scale (frame, length="8c", 
                            label="Distance from center along normal",
                            from_=-val, to=val, orient='horizontal')
        sl.set (self.slider_pos)
        sl.pack (side='top')
        sl.bind ("<ButtonRelease>", self.change_slider)
        self.slider.append (sl)

        f = Tkinter.Frame (frame)
        f.pack (side='top')

        rw = 0
        labl = Tkinter.Label (f, text="Angle resolution:")
        labl.grid (row=rw, column=0, sticky='w')
        self.step_entr = Tkinter.Entry (f, width=5, relief='sunken',
                                        textvariable=self.resoln_var)
        self.step_entr.grid (row=rw, column=1, sticky='we')
        self.step_entr.bind ("<Return>", self.change_resoln)
        rw = rw + 1

        labl = Tkinter.Label (f, text="Distance step:")
        labl.grid (row=rw, column=0, sticky='w')
        self.step_entr = Tkinter.Entry (f, width=5, relief='sunken',
                                        textvariable=self.step_var)
        self.step_entr.grid (row=rw, column=1, sticky='we')
        self.step_entr.bind ("<Return>", self.change_cut)
        rw = rw + 1

        labl = Tkinter.Label (f, text="Step bounds:")
        labl.grid (row=rw, column=0, sticky='w')
        self.n_step_entr = Tkinter.Entry (f, width=5, relief='sunken',
                                          textvariable=self.n_step_var)
        self.n_step_entr.grid (row=rw, column=1, sticky='we')
        self.n_step_entr.bind ("<Return>", self.change_cut)
    
    def change_cut (self, event=None):
        debug ("In CutPlane::change_cut ()")
        self.step_size = self.step_var.get ()
        n_s = self.n_step_var.get ()
        self.slider[2].config (from_=-n_s, to=n_s)
        self.change_slider (event)

    def change_slider (self, event=None):
        debug ("In CutPlane::change_slider ()")
        Common.state.busy ()
        val = []
        for i in range (3):
            val.append (self.slider[i].get ())

        self.slider_pos = val[2]
        self.config_extents (val)
        self.fil.Update()
        self.mod_m.Update()
        self.renwin.Render ()
        Common.state.idle ()    

    def change_resoln (self, event=None):
        debug ("In CutPlane::change_resoln ()")
        val = self.resoln_var.get ()
        for i in range (0, 2):
            self.slider[i].config (resolution=val)        
    
    def do_sweep (self, event=None):
        debug ("In CutPlane::do_sweep ()")
        if self.sweep_var.get ():
            val = int (1000*self.sweep_delay.get ())
            self.root.after (val, self.update_sweep)

    def update_sweep (self):
        debug ("In CutPlane::update_sweep ()")
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
