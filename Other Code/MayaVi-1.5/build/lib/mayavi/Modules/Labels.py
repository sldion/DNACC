"""

Displays text labels of input data.  When instantiated, the class can
be given a module name (the same name as listed in the Modules GUI) or
an index of the module (starting from 0) in the current module
manager.  If this is not provided the module will ask the user to
choose a particular module or choose filtered data.  The module will
then generate text lables for the data in the chosen module and
display it.  The module provides many configuration options.  It also
lets one turn on and off the use of a vtkSelectVisiblePoints filter.
Using this filter will cause the module to only display visible
points.  Note that if the module that is being labeled has changed
significantly or is deleted this Labels module will have to be updated
by changing one of the settings (like the RandomModeOn check button)
to a different value and then back to the original one.
Alternatively, choose the module to be labeled again.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.5 $"
__date__ = "$Date: 2005/08/02 18:30:13 $"

import Base.Objects, Common
import Tkinter, tkColorChooser
import vtk
import vtkPipeline.vtkMethodParser
import vtkPipeline.ConfigVtkObj
import tkSimpleDialog

debug = Common.debug

class ChooseModuleDialog(tkSimpleDialog.Dialog):
    def __init__(self, parent, mod_m, max_index, cur_index):
        self.mod_m = mod_m
        self.max_index = max_index
        self.cur_index = cur_index
        tkSimpleDialog.Dialog.__init__ (self, parent,
                                        "Choose module to label.")

    def body (self, master):
        rw = 0
        lab = Tkinter.Label(master, text="Choose the module to label")
        lab.grid(row=rw, column=0, columnspan=2)
        rw += 1
        scr = Tkinter.Scrollbar (master, orient='vertical')
        lst = Tkinter.Listbox (master, yscrollcommand=scr.set, 
                               selectmode='single', height=6,
                               exportselection=0)
        self.mod_lst = lst
        scr.config (command=lst.yview)
        lst.grid (row=rw, column=0, sticky='ewns')
        scr.grid (row=rw, column=1, sticky='ns')
        rw += 1

        lst.insert('end', 'Use Filtered data')
        names = self.mod_m.get_module_names()
        for i in range(self.max_index):
            lst.insert('end', names[i])
        lst.select_set(self.cur_index + 1)

    def ok (self, event=None):
        self.result = self.mod_lst.get('active')
        if self.result.lower() == "use filtered data":
            self.result = -1
        tkSimpleDialog.Dialog.ok (self, event)

    def cancel(self, event=None):
        del self.mod_m 
        tkSimpleDialog.Dialog.cancel (self, event)
   

class Labels (Base.Objects.Module):

    """ Displays text labels of input data.  When instantiated, the
    class can be given a module name (the same name as listed in the
    Modules GUI) or an index of the module (starting from 0) in the
    current module manager.  If this is not provided the module will
    ask the user to choose a particular module or choose filtered
    data.  The module will then generate text lables for the data in
    the chosen module and display it.  The module provides many
    configuration options.  It also lets one turn on and off the use
    of a vtkSelectVisiblePoints filter.  Using this filter will cause
    the module to only display visible points.  Note that if the
    module that is being labeled has changed significantly or is
    deleted this Labels module will have to be updated by changing one
    of the settings (like the RandomModeOn check button) to a
    different value and then back to the original one.  Alternatively,
    choose the module to be labeled again.
    """

    def __init__ (self, mod_m, module=None, n_points=25, vis_points=0):
        """Input arguments:

        mod_m -- Module manager that manages this module.

        module -- Module to label.  Can be given a module name (the
        same name as listed in the Modules GUI) or an index of the
        module (starting from 0) in the current module manager.  If
        the value is -1, then the filtered data from the module
        manager is used.  The value defaults to None where the user is
        asked to specify the module to label.

        n_points -- Number of points to label.  Defaults to 25.

        vis_points -- If 1 turns on the vtkSelectVisiblePoints filter.
        Defaults to 0.    
        """
        debug ("In Labels::__init__ ()")
        Base.Objects.Module.__init__ (self, mod_m)

        self.act = None
        self.input = None
        self.mod_num = -1
        if module is not None:
            self._set_input(module)
        if not self.input:
            res = self._get_input_gui()
            self._set_input(res)
        
        if not self.input:
            msg = "Sorry, you need to choose a valid module in order to "\
                  "use this module."
            raise Base.Objects.ModuleException, msg
        input = self.input
        
        Common.state.busy ()
        self.n_points = n_points
        self.vis_points = vis_points
        self.mask = vtk.vtkMaskPoints ()
        n = input.GetNumberOfPoints ()
        self.mask.SetInput (input)
        self.mask.SetOnRatio (max(n/n_points, 1))
        self.mask.GenerateVerticesOn()
        self.mask.RandomModeOn ()
        self.vis_pnts = vtk.vtkSelectVisiblePoints ()
        self.vis_pnts.SetRenderer(self.renwin.get_renderer())
        self.mapper = self.map = vtk.vtkLabeledDataMapper ()
        self.mapper.SetLabelModeToLabelScalars()
        self.tprop = None
        if hasattr(self.mapper, "GetLabelTextProperty"):
            self.tprop = self.mapper.GetLabelTextProperty()
            self.tprop.SetColor (*Common.config.fg_color)
            self.tprop.SetOpacity(1.0)

        if vis_points:
            self.vis_pnts.SetInput (self.mask.GetOutput ())
            self.mapper.SetInput (self.vis_pnts.GetOutput ())
        else:
            self.mapper.SetInput (self.mask.GetOutput ())
            
        self.actor = self.act = vtk.vtkActor2D ()
        self.actor.SetMapper (self.mapper)
        self.vis_pnt_gui = None
        self.act.GetProperty ().SetColor (*Common.config.fg_color)
        self.renwin.add_actors (self.act)
        # used for the pipeline browser
        self.pipe_objs = self.act
        self.renwin.Render ()
        Common.state.idle ()

    def __del__ (self): 
        debug ("In Labels::__del__ ()")
        if self.act:
            self.renwin.remove_actors (self.act)
        self.renwin.Render ()

    def _set_input(self, module):
        if type(module) == type('string'):
            mod = self.mod_m.get_module(module)
            if mod:
                self.mod_num = self.mod_m.get_module_names().index(module)
            self.input = mod.actor.GetMapper().GetInput()
        elif type(module) == type(1):
            if module < 0:
                self.mod_num = -1
                self.input = self.mod_m.GetOutput()
            else:
                mod = self.mod_m.get_module(module)
                if mod:
                    self.mod_num = module
                self.input = mod.actor.GetMapper().GetInput()

    def _get_input_gui(self, master=None):
        # find my index in mod_m
        names = self.mod_m.get_module_names()
        my_id = len(names)
        for i in range(len(names)):
            if self.mod_m.get_module(i) == self:
                my_id = i
                break
        d = ChooseModuleDialog(master, self.mod_m, my_id,
                               self.mod_num)
        return d.result
                               
    def SetInput (self, source):
        debug ("In Labels::SetInput ()")
        Common.state.busy ()
        try:
            self._set_input(self.mod_m.get_module(self.mod_num))
        except IndexError:
            self._set_input(self.mod_m.get_module(-1))
        self.mask.SetInput (self.input)
        n = self.input.GetNumberOfPoints()
        self.mask.SetOnRatio (max(n/self.n_points, 1))
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In Labels::save_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        s = {}
        s['vis_points'] = self.vis_points
        s['mod_num'] = self.mod_num
        s['n_points'] = self.n_points
        for key, obj in (('map_config', self.map),
                         ('act_config', self.act),
                         ('act_prop_config', self.act.GetProperty()),
                         ('mask_config', self.mask),
                         ('tprop_config', self.tprop),
                         ('vis_pnts_config', self.vis_pnts)):
            cfg = {}
            p.dump(obj, cfg)
            s[key] = cfg
        
        file.write("%s\n"%s)
        
    def load_config (self, file): 
        debug ("In Labels::load_config ()")
        s = eval(file.readline())
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for key, obj in (('map_config', self.map),
                         ('act_config', self.act),
                         ('act_prop_config', self.act.GetProperty()),
                         ('mask_config', self.mask),
                         ('tprop_config', self.tprop),
                         ('vis_pnts_config', self.vis_pnts)):            
            p.load (obj, s[key])

        self._set_input(s['mod_num'])
        self.set_n_points(s['n_points'])
        self.toggle_visible_points(s['vis_points'])
        self.renwin.Render ()
        
    def config_changed (self): 
        debug ("In Labels::config_changed ()")
        self.act.GetProperty ().SetColor (*Common.config.fg_color)

    def make_main_gui (self):
        debug ("In Labels::make_main_gui ()")
        self.make_other_gui()
        self.make_label_gui()

    def make_label_gui(self):
        debug ("In Labels::make_label_gui ()")
        frame = Tkinter.Frame(self.root)
        frame.pack(side='top', fill='both', expand=1)

        CVOF = vtkPipeline.ConfigVtkObj.ConfigVtkObjFrame

        rw = 0
        gui = CVOF(frame, self.renwin)
        gui.configure(self.mask, get=[], toggle=['RandomModeOn'],
                      get_set=[], state=[], auto_update=1, one_frame=1)
        gui.grid(row=rw, column=0, sticky='wens')
        rw += 1

        gui = CVOF(frame, self.renwin)
        if self.tprop:
            t_m = []
            s_m = [ ['SetLabelModeToLabelFieldData',
                     'SetLabelModeToLabelIds',
                     'SetLabelModeToLabelNormals',
                     'SetLabelModeToLabelScalars',
                     'SetLabelModeToLabelTCoords',
                     'SetLabelModeToLabelTensors',
                     'SetLabelModeToLabelVectors'] ]
            gs_m = ['LabelFormat', 'LabeledComponent']
            gui.configure(self.map, get=[], toggle=t_m, state=s_m,
                          get_set=gs_m, auto_update=1, one_frame=1)
        else:
            t_m = ['!AbortExecuteOn', '!DebugOn']
            gui.configure(self.map, get=[], toggle=t_m,
                          auto_update=1, one_frame=1)            
            
        gui.grid(row=rw, column=0, sticky='wens')
        rw += 1
        
        if self.tprop:
            gui = CVOF(frame, self.renwin)
            t_m = ['!DebugOn']
            gs_m = ['Color', 'FontSize', 'Opacity']
            s_m = [['SetFontFamilyToArial', 'SetFontFamilyToCourier',
                    'SetFontFamilyToTimes']]

            gui.configure(self.tprop, get=[], toggle=t_m, get_set=gs_m,
                          state=s_m, auto_update=1, one_frame=1)
            gui.grid(row=rw, column=0, sticky='wens')
            rw += 1

        self.vis_pnt_var = Tkinter.IntVar()
        self.vis_pnt_var.set(self.vis_points)
        cb = Tkinter.Checkbutton(frame, text="Select visible points",
                                 variable = self.vis_pnt_var,
                                 onvalue=1, offvalue=0,
                                 command=self.toggle_visible_points_gui)
        cb.grid(row=rw, column=0, sticky='wens')
        rw += 1
        self.vis_pnt_frame = Tkinter.Frame(frame)
        self.vis_pnt_frame.grid(row=rw, column=0, sticky='wens')
        self.vis_pnt_gui = None
        rw += 1
        if self.vis_points:
            self.make_vis_pnt_gui()
        
    def make_other_gui(self):
        debug ("In Labels::make_other_gui ()")
        frame = Tkinter.Frame(self.root)
        frame.pack(side='top', fill='both', expand=1)

        rw = 0
        but = Tkinter.Button(frame, text="Choose module to label",
                             command=self.select_module_gui)
        but.grid(row=rw, column=0, columnspan=2, sticky='ew')
        rw += 1

        self.n_pnt_var = Tkinter.IntVar()
        self.n_pnt_var.set(self.n_points)
        lab = Tkinter.Label(frame, text="Number of labels:")
        lab.grid(row=rw, column=0, sticky='e')
        entr = Tkinter.Entry (frame, width=10, relief='sunken',
                              textvariable=self.n_pnt_var)
        entr.grid(row=rw, column=1, sticky='ew')
        entr.bind ("<Return>", self.set_n_points_gui)
        rw += 1

    def make_vis_pnt_gui(self):
        debug ("In Labels::make_vis_pnt_gui ()")
        if self.vis_pnt_gui:
            self.vis_pnt_gui.destroy()
            
        CVOF = vtkPipeline.ConfigVtkObj.ConfigVtkObjFrame
        if self.vis_points:
            gui = CVOF(self.vis_pnt_frame, self.renwin)
            t_m = ['SelectInvisibleOn', 'SelectionWindowOn']
            gui.configure(self.vis_pnts, get=[], toggle=t_m,
                          auto_update=1, one_frame=1)
            gui.pack()
            self.vis_pnt_gui = gui
        else:
            self.vis_pnt_gui = None            

    def set_n_points_gui(self, event=None):
        debug ("In Labels::set_n_points_gui ()")
        n = self.n_pnt_var.get()
        self.set_n_points(n)

    def toggle_visible_points_gui(self, event=None):
        debug ("In Labels::toggle_visible_points_gui ()")
        val = self.vis_pnt_var.get()
        self.toggle_visible_points(val)
        self.make_vis_pnt_gui()
            
    def toggle_visible_points(self, val):
        debug ("In Labels::toggle_visible_points ()")
        if val != self.vis_points:
            self.vis_points = val
        else:
            return
        Common.state.busy ()
        if val:
            self.vis_pnts.SetInput (self.mask.GetOutput ())
            self.mapper.SetInput (self.vis_pnts.GetOutput ())
        else:
            self.mapper.SetInput (self.mask.GetOutput ())
        self.renwin.Render()
        Common.state.idle ()        
        
    def set_n_points(self, n):
        debug ("In Labels::set_n_points ()")
        Common.state.busy ()
        self.n_points = n
        n = self.input.GetNumberOfPoints()
        self.mask.SetOnRatio (max(n/self.n_points, 1))
        self.renwin.Render()
        Common.state.idle ()
        
    def select_module_gui(self, event=None):
        debug ("In Labels::select_module_gui ()")
        res = self._get_input_gui(self.root)
        if res is None:
            res == -1
        Common.state.busy ()
        self._set_input(res)
        self.mask.SetInput (self.input)
        n = self.input.GetNumberOfPoints()
        self.mask.SetOnRatio (max(n/self.n_points, 1))
        self.renwin.Render()
        Common.state.idle ()
        
