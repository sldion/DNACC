"""

Warps the geometry using the vtkWarpVector filter.  vtkWarpVector is a
filter that modifies point coordinates by moving points along vector
times the scale factor.  Useful for showing flow profiles or
mechanical deformation.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu@aero.iitm.ernet.in>"
__version__ = "$Revision: 1.5 $"
__date__ = "$Date: 2005/08/02 18:26:25 $"
__credits__ = """Many thanks to Jose Paulo <moitinho@civil.ist.utl.pt>
for providing an initial version of this Filter."""

import PolyDataNormals, Base.Objects
import Common
import Tkinter
import vtk
import vtkPipeline.vtkMethodParser

debug = Common.debug

class WarpVector (PolyDataNormals.PolyDataNormals):

    """ Warps the geometry using the vtkWarpVector filter.
    vtkWarpVector is a filter that modifies point coordinates by
    moving points along vector times the scale factor. Useful for
    showing flow profiles or mechanical deformation."""
    
    def initialize (self):
        debug ("In WarpVector::initialize ()")
        self.fil = vtk.vtkWarpVector ()
        self._set_input ()

        self.scale_var = Tkinter.DoubleVar ()
        self.scale_var.set (1.)
        res, min_v, max_v = self._get_ranges (self.scale_var.get())
        self.scale_res_var = Tkinter.DoubleVar ()
        self.scale_res_var.set (res)
        self.min_scale_var = Tkinter.DoubleVar ()
        self.min_scale_var.set (min_v)
        self.max_scale_var = Tkinter.DoubleVar ()
        self.max_scale_var.set (max_v)

        self.fil.SetScaleFactor (self.scale_var.get ()) # Default setting
        self.fil.Update ()

    configure = Base.Objects.Filter.configure

    def make_custom_gui (self):
        debug ("In WarpVector::make_custom_gui()")
        self.make_main_gui ()
        self.make_close_button ()

    def _get_ranges (self, val):
        debug ("In WarpVector::_get_ranges ()")
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

    def make_main_gui (self):
        debug ("In WarpVector::make_main_gui()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)

        rw = 0
        sl = Tkinter.Scale (frame, label="Set Scale Factor", 
                            from_= self.min_scale_var.get (),
                            to = self.max_scale_var.get (),
                            length="5c", orient='horizontal', 
                            resolution=self.scale_res_var.get ())
        sl.set (self.fil.GetScaleFactor ())
        sl.grid (row=rw, column=0, columnspan=2, sticky='ew')
        rw = rw + 1
        sl.bind ("<ButtonRelease>", self.change_scale)
        self.scale_slider = sl
        lab = Tkinter.Label (frame, text="Scale resolution: ")
        lab.grid (row=rw, column=0, sticky='w')
        entr = Tkinter.Entry (frame, width=5, relief='sunken',
                              textvariable=self.scale_res_var)
        entr.grid (row=rw, column=1, sticky='ew')
        entr.bind ("<Return>", self.set_scale_resolution)
        rw = rw+1

        lab = Tkinter.Label (frame, text="Minimum scale:")
        lab.grid (row=rw, column=0, sticky='w')
        entry = Tkinter.Entry (frame, width=10, relief='sunken', 
                               textvariable=self.min_scale_var)
        entry.grid (row=rw, column=1, sticky='we')
        entry.bind ("<Return>", self.change_scale_limits)
        rw = rw+1

        lab = Tkinter.Label (frame, text="Maximum scale:")
        lab.grid (row=rw, column=0, sticky='w')
        entry = Tkinter.Entry (frame, width=10, relief='sunken', 
                               textvariable=self.max_scale_var)
        entry.grid (row=rw, column=1, sticky='we')
        entry.bind ("<Return>", self.change_scale_limits)

    def set_scale_resolution (self, event=None):
        """ Called when the scale slider resolution is changed. """
        debug ("In WarpVector::set_scale_resolution()")
        self.scale_slider.config (resolution=self.scale_res_var.get ())

    def change_scale (self, event=None):
        debug ("In WarpVector::change_scale()")
        Common.state.busy ()
        self.fil.SetScaleFactor (self.scale_slider.get())
        self.mod_m.Update ()
        Common.state.idle ()

    def change_scale_limits (self, event=None):
        debug ("In WarpVector::change_scale_limits()")
        self.scale_slider.config (from_ = self.min_scale_var.get(),
                                  to = self.max_scale_var.get())

    def save_config (self, file):
        debug ("In WarpVector::save_config ()")
        cfg = {'scale_res': self.scale_res_var.get(),
               'min_scale': self.min_scale_var.get(),
               'max_scale': self.max_scale_var.get()}
        file.write("%s\n"%cfg)
        PolyDataNormals.PolyDataNormals.save_config(self, file)

    def load_config (self, file):
        debug ("In WarpVector::load_config ()")
        pos = file.tell()
        cfg = {}
        try:
            cfg = eval(file.readline())
        except NameError: # Oops old format.
            # rewind.
            file.seek(pos)
        else:
            self.scale_res_var.set (cfg['scale_res'])
            self.min_scale_var.set (cfg['min_scale'])
            self.max_scale_var.set (cfg['max_scale'])
        PolyDataNormals.PolyDataNormals.load_config(self,file)
