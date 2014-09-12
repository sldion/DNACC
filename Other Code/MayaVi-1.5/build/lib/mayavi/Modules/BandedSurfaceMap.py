"""

Displays a surface map with special contouring using the
vtkBandedPolyDataContourFilter.  This contour filter produces filled
contours of the same color between two contour lines rather than
either a continuous color distribution or just individual contour
lines.  It should work for any input dataset.  It is best used for 2d
surfaces.  Note that one can either specify a total number of contours
between the minimum and maximum values by entering a single integer or
specify the individual contours by specifying a Python list/tuple in
the GUI. 

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.5 $"
__date__ = "$Date: 2005/09/08 18:01:42 $"

import Base.Objects
import Common
import Tkinter
import tkColorChooser
import vtk
import vtkPipeline.vtkMethodParser
import vtkPipeline.ConfigVtkObj

debug = Common.debug

class BandedSurfaceMap (Base.Objects.Module):

    """ Displays a surface map with special contouring using the
    vtkBandedPolyDataContourFilter.  This contour filter produces
    filled contours of the same color between two contour lines rather
    than either a continuous color distribution or just individual
    contour lines.  It should work for any input dataset.  It is best
    used for 2d surfaces.  Note that one can either specify a total
    number of contours between the minimum and maximum values by
    entering a single integer or specify the individual contours by
    specifying a Python list/tuple in the GUI."""

    def __init__ (self, mod_m):
        debug ("In BandedSurfaceMap::__init__ ()")
        Common.state.busy ()
        Base.Objects.Module.__init__ (self, mod_m)
        self.cont_fil = vtk.vtkBandedPolyDataContourFilter ()
        self.cont_fil.SetScalarModeToValue ()
        self.mapper = self.map = vtk.vtkDataSetMapper ()
        self.map.SetInput (mod_m.GetOutput ())
        self.actor = self.act = vtk.vtkActor ()
        self.act.SetMapper (self.map)
        self.data_range = self.mod_m.get_scalar_data_range ()
        self.map.SetLookupTable (self.mod_m.get_scalar_lut ())
        self.map.SetScalarRange (self.data_range)
        self.map.ScalarVisibilityOn ()
        self.act.GetProperty ().SetColor (Common.config.fg_color)
        self.act.GetProperty ().SetLineWidth (2)
        # surface mode.
        self.act.GetProperty ().SetRepresentation (2)
        # used for the pipeline browser
        self.pipe_objs = self.act
        self.renwin.add_actors (self.act)
        self._gui_init ()
        self.renwin.Render ()
        Common.state.idle ()

    def __del__ (self): 
        debug ("In BandedSurfaceMap::__del__ ()")
        if self.act:
            self.renwin.remove_actors (self.act)
        self.renwin.Render ()

    def _gui_init (self):
        self._contour_init ()

    def _contour_init (self):
        debug ("In BandedSurfaceMap::_contour_init ()")
        Base.Objects.Module._contour_init (self)
        self.contour_on.set (0)
        self.n_cnt.set ("10")
        dr = self.mod_m.get_scalar_data_range ()        
        self.min_cnt.set (dr[0])
        self.max_cnt.set (dr[1])
        
    def SetInput (self, source): 
        debug ("In BandedSurfaceMap::SetInput ()")
        Common.state.busy ()
        dr = self.mod_m.get_scalar_data_range ()
        self.map.SetInput (source)
        if (dr[0] != self.data_range[0]) or (dr[1] != self.data_range[1]):
            self.map.SetScalarRange (dr)
            self.data_range = dr
            self.min_cnt.set (dr[0])
            self.max_cnt.set (dr[1])
        self.do_contour ()
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In BandedSurfaceMap::save_config ()")
        file.write ("%d, %s, %f, %f\n"%(self.contour_on.get (),
                                        self.n_cnt.get (),
                                        self.min_cnt.get (),
                                        self.max_cnt.get ()))
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.cont_fil, self.map, self.act,
                    self.act.GetProperty ()):
            p.dump (obj, file)

    def load_config (self, file): 
        debug ("In BandedSurfaceMap::load_config ()")
        cnt_on, n_cnt, min_cnt, max_cnt = eval (file.readline ())
        self.contour_on.set (cnt_on)
        self.n_cnt.set (str(n_cnt))
        self.min_cnt.set (min_cnt)
        self.max_cnt.set (max_cnt)
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.cont_fil, self.map, self.act,
                    self.act.GetProperty ()):
            p.load (obj, file)

        self.do_contour ()
        
    def config_changed (self): 
        debug ("In BandedSurfaceMap::config_changed ()")
        self.act.GetProperty ().SetColor (Common.config.fg_color)

    def make_main_gui (self, master=None): 
        debug ("In BandedSurfaceMap::make_main_gui ()")
        "Create the GUI configuration controls for this object."
        self.make_actor_gui ()        
        CVOF = vtkPipeline.ConfigVtkObj.ConfigVtkObjFrame
        gui = CVOF(self.root, self.renwin)
        t_m = ['ClippingOn']
        gui.configure(self.cont_fil, get=[], toggle=t_m, get_set=[],
                      state=[], auto_update=1, one_frame=1)
        gui.pack(side='top', fill='both', expand=1)
        self.make_contour_gui ()

    def do_contour (self, event=None):
        debug ("In BandedSurfaceMap::do_contour ()")
        Common.state.busy ()
        if self.contour_on.get ():
            if not self.mod_m.get_scalar_data_name ():
                self.contour_on.set (0)
                msg = "Warning: No scalar data present to contour!"
                Common.print_err (msg)
                Common.state.idle ()
                return
            out = self.mod_m.GetOutput ()

            if out.IsA('vtkPolyData'):
                f = None
            elif out.IsA ('vtkStructuredGrid'):
                f = vtk.vtkStructuredGridGeometryFilter ()
            elif out.IsA ('vtkRectilinearGrid'):
                f = vtk.vtkRectilinearGridGeometryFilter ()
            elif out.IsA ('vtkStructuredPoints') or \
                 out.IsA('vtkImageData'):
                if hasattr (vtk, 'vtkImageDataGeometryFilter'):
                    f = vtk.vtkImageDataGeometryFilter ()
                else:
                    f = vtk.vtkStructuredPointsGeometryFilter ()
            elif out.IsA('vtkUnstructuredGrid'):
                f = vtk.vtkGeometryFilter()
            else:
                msg = "This module does not support the given "\
                      "output - %s "%(out.GetClassName ())
                raise Base.Objects.ModuleException, msg

            if f:
                f.SetInput (out)
                self.cont_fil.SetInput (f.GetOutput())
            else:
                self.cont_fil.SetInput (out)                

            self.map.SetInput (self.cont_fil.GetOutput ())
            self.map.SetScalarModeToUseCellData()
        else:
            self.map.SetInput (self.mod_m.GetOutput ())
            self.map.SetScalarModeToDefault()
        self.change_contour ()
        Common.state.idle ()

    def change_contour (self, event=None):
        debug ("In BandedSurfaceMap::change_contour ()")
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

