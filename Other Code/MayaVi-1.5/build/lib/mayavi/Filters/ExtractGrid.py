"""
Wraps vtkExtractGrid (structured grid), vtkExtractVOI
(imagedata/structured points) and vtkExtractRectilinearGrid
(rectilinear grids).  These filters enable one to select a portion of,
or subsample an input dataset.  Depending on the input data the
appropriate filter is used.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.4 $"
__date__ = "$Date: 2005/08/02 18:26:24 $"

import Base.Objects, Common
import vtk
import vtkPipeline.ConfigVtkObj
import Tkinter

debug = Common.debug

class ExtractGrid (Base.Objects.Filter):

    """ Wraps vtkExtractGrid (structured grid), vtkExtractVOI
    (imagedata/structured points) and vtkExtractRectilinearGrid
    (rectilinear grids).  These filters enable one to select a portion
    of, or subsample an input dataset.  Depending on the input data
    the appropriate filter is used.  """

    def initialize (self):
        debug ("In ExtractGrid::__init__ ()")
        self.fil = vtk.vtkExtractVOI()
        self.dim = [0,0,0]
        self._set_input()
        self.fil.UpdateWholeExtent()
        self.fil.Update ()
        self.voi_slider = []
        self.sr_slider = []

    def _set_input (self):        
        """ This function tries its best to use an appropriate filter
        for the given input data."""        
        debug ("In ExtractGrid::_set_input ()")
        out = self.prev_fil.GetOutput ()
        dim = out.GetDimensions ()
        self.dim = [dim[0] -1, dim[1] -1, dim[2] -1]
        if out.IsA ('vtkStructuredGrid'):
            f = vtk.vtkExtractGrid()
        elif out.IsA ('vtkRectilinearGrid'):
            f = vtk.vtkExtractRectilinearGrid()
        elif out.IsA ('vtkStructuredPoints') or out.IsA('vtkImageData'):
            f = vtk.vtkExtractVOI()
        else:
            msg = "This module does not support the given "\
                  "output - %s "%(out.GetClassName ())
            raise Base.Objects.ModuleException, msg
        if f.GetClassName() != self.fil.GetClassName():
            self.fil = f
        self.fil.SetInput (out)

    def set_input_source (self, source):
        debug ("In ExtractGrid::set_input_source ()")
        Common.state.busy ()
        self.prev_filter = source
        self._set_input()
        self.fil.UpdateWholeExtent()
        self.fil.Update ()
        Common.state.idle ()

    def make_custom_gui (self):
        debug ("In ExtractGrid::make_custom_gui()")
        self.make_main_gui ()
        self.make_close_button ()

    def make_main_gui (self):
        debug ("In ExtractGrid::make_main_gui()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)
        rw = 0
        l = Tkinter.Label(frame, text="Set Volume Of Interest (VOI)")
        l.grid(row=rw, column=0, sticky='ew')
        rw = rw + 1
        txt = ("X Min", "X Max", "Y Min", "Y Max", "Z Min", "Z Max")
        self.voi_slider = []
        voi = self.fil.GetVOI()
        for i in range (len(txt)):
            val = self.dim[i/2]
            sl = Tkinter.Scale (frame, label=txt[i], from_=0,
                                to=val, length="8c", orient='horizontal')
            sl.set (voi[i])
            sl.grid (row=rw, column=0)
            rw = rw + 1
            sl.bind ("<ButtonRelease>", self.change_voi_slider)
            self.voi_slider.append (sl)

        l = Tkinter.Label(frame, text="Set Sample Rates")
        l.grid(row=rw, column=0, sticky='ew')
        rw = rw + 1
        txt = ("X ratio", "Y ratio", "Z ratio")
        self.sr_slider = []
        sample_rate = self.fil.GetSampleRate()
        for i in range (len(txt)):
            val = self.dim[i]/2 + 1
            sl = Tkinter.Scale(frame, label=txt[i], from_=1, to=val, \
                 length="8c", orient='horizontal')
            sl.set (sample_rate[i])
            sl.grid (row=rw, column=0)
            rw = rw + 1
            sl.bind ("<ButtonRelease>", self.change_sr_slider)
            self.sr_slider.append (sl)            

        but = Tkinter.Button(frame, text="More Config options", \
              command=self.config_filter, underline=1)
        but.grid (row=rw, column=0, sticky='ew')
        self.root.bind ("<Alt-o>", self.config_filter)

    def change_voi_slider(self, event=None):
        debug ("In ExtractGrid::change_voi_slider()")
        voi = []
        for i in range(len(self.voi_slider)):
            voi.append(self.voi_slider[i].get ())
        self.fil.SetVOI(voi)
        self.mod_m.Update()
        
    def change_sr_slider(self, event=None):
        debug ("In ExtractGrid::change_sr_slider()")
        sr = []
        for i in range (len(self.sr_slider)):
            sr.append(self.sr_slider[i].get ())
        self.fil.SetSampleRate(sr)
        self.mod_m.Update()

    def config_filter (self, master=None):
        debug ("In ExtractGrid::config_filter ()")
        c = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        c.set_update_method (self.mod_m.Update)
        c.configure (self.root, self.fil)
