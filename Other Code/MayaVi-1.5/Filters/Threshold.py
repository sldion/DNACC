"""

This wraps the vtkThreshold filter.  The problem with this filter is
that its output is an Unstructured Grid.  This means that if you add
this filter to a ModuleManager of a gridded dataset and you have a few
grid planes, then your grid planes won't show anymore.  If that
happens create another ModuleManager and show the grid planes there
acting on unfiltered data.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.8 $"
__date__ = "$Date: 2005/08/02 18:26:25 $"

import Base.Objects, Common
import Tkinter
import vtk
import vtkPipeline.vtkMethodParser

debug = Common.debug

class Threshold (Base.Objects.Filter):

    """ This wraps the vtkThreshold filter.  The problem with this
    filter is that its output is an Unstructured Grid.  This means
    that if you add this filter to a ModuleManager of a gridded
    dataset and you have a few grid planes, then your grid planes
    won't show anymore.  If that happens create another ModuleManager
    and show the grid planes there acting on unfiltered data. """

    def initialize (self):
        debug ("In Threshold::initialize ()")
        self.fil = vtk.vtkThreshold ()
        self.fil.SetInput (self.prev_fil.GetOutput ())
        self.data_name = self.mod_m.get_scalar_data_name ()
        dr = self.mod_m.get_scalar_data_range ()
        self.fil.ThresholdBetween (dr[0], dr[1])
        self.fil.Update ()        

    def set_input_source (self, source):
        debug ("In Threshold::set_input_source ()")
        Common.state.busy ()
        self.fil.SetInput (source.GetOutput ())
        self.prev_filter = source
        name = self.prev_fil.get_scalar_data_name ()
        if self.data_name != name:
            dr = self.mod_m.get_scalar_data_range ()
            self.data_name = name
            self.fil.ThresholdBetween (dr[0], dr[1])
            self.fil.Update()
            try:
                self.thresh_min_var.set (self.fil.GetLowerThreshold ())
                self.thresh_max_var.set (self.fil.GetUpperThreshold ())
            except AttributeError, Tkinter.TclError: 
                pass
        Common.state.idle ()

    def save_config (self, file):
        debug ("In Threshold::save_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.fil, ):
            p.dump (obj, file)
        min = self.fil.GetLowerThreshold ()
        max = self.fil.GetUpperThreshold ()
        file.write ("%f, %f\n"%(min, max))
        
    def load_config (self, file):
        debug ("In Threshold::load_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.fil, ):
            p.load (obj, file)

        # VTK >= 4.5 deprecates the attribute mode.
        if hasattr(self.fil, 'SetInputArrayToProcess'):
            self.fil.SetAttributeMode(-1)
            
        min, max = eval (file.readline ()[:-1])
        self.fil.ThresholdBetween (min, max)
        self.fil.Update ()
        
    def make_custom_gui (self):
        debug ("In Threshold::make_custom_gui ()")
        self.make_main_gui ()
        self.make_close_button ()

    def make_main_gui (self):
        debug ("In Threshold::make_main_gui ()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top')
        self.thresh_on_var = Tkinter.IntVar ()
        self.thresh_on_var.set (0)
        self.att_mode_var = Tkinter.IntVar ()
        self.att_mode_var.set(self.fil.GetAttributeMode())
        lab = Tkinter.Label (frame, text="Threshold points using scalars")
        lab.grid (row=0, columnspan=2)

        labl = Tkinter.Label (frame, text="Minimum threshold:")
        labl.grid (row=1, column=0, sticky='w')
        self.thresh_min_var = Tkinter.DoubleVar ()
        self.thresh_min_var.set (self.fil.GetLowerThreshold ())
        entr = Tkinter.Entry (frame, width=15, relief='sunken', 
                              textvariable=self.thresh_min_var)
        entr.grid (row=1, column=1, sticky='we')
        entr.bind ("<Return>", self.change_threshold)

        labl = Tkinter.Label (frame, text="Maximum threshold:")
        labl.grid (row=2, column=0, sticky='w')
        self.thresh_max_var = Tkinter.DoubleVar ()
        self.thresh_max_var.set (self.fil.GetUpperThreshold ())
        entr = Tkinter.Entry (frame, width=15, relief='sunken', 
                              textvariable=self.thresh_max_var)
        entr.grid (row=2, column=1, sticky='we')
        entr.bind ("<Return>", self.change_threshold)

        rw = 3
        if not hasattr(self.fil, 'SetInputArrayToProcess'):
            rb = Tkinter.Radiobutton (frame, text="Use Points/Cells",
                                      variable=self.att_mode_var, value=0,
                                      command=self.set_attribute_mode)
            rb.grid (row=rw, column=0, sticky='w')
            rw = rw + 1
            rb = Tkinter.Radiobutton (frame, text="Use Points",
                                      variable=self.att_mode_var, value=1,
                                      command=self.set_attribute_mode)
            rb.grid (row=rw, column=0, sticky='w')
            rw = rw + 1
            rb = Tkinter.Radiobutton (frame, text="Use Cells",
                                      variable=self.att_mode_var, value=2,
                                      command=self.set_attribute_mode)
            rb.grid (row=rw, column=0, sticky='w')
            rw = rw + 1
            
        but = Tkinter.Button(frame, text="More configure options",
                             underline=1,  command=self.config_threshold)
        but.grid (row=rw, column=0, columnspan=2, sticky='wens')
        self.root.bind('<Alt-o>', self.config_threshold)
        rw = rw + 1       
        
    def change_threshold (self, event=None):
        debug ("In Threshold::change_threshold ()")
        Common.state.busy ()
        min = self.thresh_min_var.get ()
        max = self.thresh_max_var.get ()
        self.fil.ThresholdBetween (min, max)
        self.fil.Update ()
        self.mod_m.Update ()
        Common.state.idle ()

    def set_attribute_mode (self, event=None):
        debug ("In Threshold::set_attribute_mode ()")
        Common.state.busy ()
        val = self.att_mode_var.get()
        if val == 0:
            self.fil.SetAttributeModeToDefault ()
        elif val == 1:
            self.fil.SetAttributeModeToUsePointData ()
        elif val == 2:
            self.fil.SetAttributeModeToUseCellData ()
        self.fil.Update ()
        self.mod_m.Update ()
        Common.state.idle ()

    def config_threshold(self, event=None):
        debug("In Threshold::config_threshold()")
        conf = vtkPipeline.ConfigVtkObj.ConfigVtkObj(self.renwin)
        t_m = ['!AbortExecuteOn']
        if hasattr(self.fil, 'SetInputArrayToProcess'):
            s_m = [['SetComponentModeToUseSelected',
                    'SetComponentModeToUseAll',
                    'SetComponentModeToUseAny']]
            conf.configure (None, self.fil, toggle=t_m, state=s_m)
        else:
            conf.configure (None, self.fil, toggle=t_m)
            
