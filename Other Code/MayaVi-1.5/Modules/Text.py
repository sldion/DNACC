"""

Displays simple text on the screen.  The text properties and position
are configurable.  The text can also be multi-line if newlines are
embedded in it.
    
This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.2 $"
__date__ = "$Date: 2005/08/02 18:30:13 $"

import Base.Objects, Common
import Tkinter, tkColorChooser
import vtk
import vtkPipeline.vtkMethodParser
import vtkPipeline.ConfigVtkObj

debug = Common.debug

class Text (Base.Objects.Module):

    """ Displays simple text on the screen.  The text properties and
    position are configurable.  The text can also be multi-line if
    newlines are embedded in it."""
    
    def __init__ (self, mod_m):
        debug ("In Text::__init__ ()")
        Common.state.busy ()
        Base.Objects.Module.__init__ (self, mod_m)
        data_src = self.mod_m.get_data_source ()
        self.actor = self.act = vtk.vtkTextActor()
        self.tprop = self.act.GetTextProperty()

        self._initialize()
        self.renwin.add_actors (self.act)
        # used for the pipeline browser
        self.pipe_objs = self.act
        self.renwin.Render ()
        Common.state.idle ()

    def __del__ (self): 
        debug ("In Text::__del__ ()")
        if self.act:
            self.renwin.remove_actors (self.act)
        self.renwin.Render ()

    def _initialize(self):
        debug ("In Text::_initialize ()")
        self.act.SetInput("Text")
        c = self.act.GetPositionCoordinate()
        c.SetCoordinateSystemToNormalizedViewport()
        c.SetValue(0.5, 0.5)
        c = self.act.GetPosition2Coordinate()
        c.SetCoordinateSystemToNormalizedViewport()

        self.act.ScaledTextOn()
        self.act.SetWidth(0.4)
        self.act.SetHeight(0.1)
        self.tprop.SetColor (*Common.config.fg_color)
        self.tprop.SetOpacity(1.0)

    def SetInput (self, source): 
        debug ("In Text::SetInput ()")
        pass
    
    def save_config (self, file): 
        debug ("In Text::save_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.act, self.act.GetProperty(), self.tprop):
            p.dump (obj, file)

    def load_config (self, file): 
        debug ("In Text::load_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.act, self.act.GetProperty(), self.tprop):
            p.load (obj, file)            
        
    def config_changed (self): 
        debug ("In Text::config_changed ()")
        self.tprop.SetColor (*Common.config.fg_color)

    def make_main_gui (self):
        """Create the GUI configuration controls for this object."""
        debug ("In Text::make_main_gui ()")

        frame = Tkinter.Frame (self.root)
        frame.pack(side='top', fill='both', expand=1)
        self.pos_var = Tkinter.StringVar()
        x, y = self.act.GetPosition()
        self.pos_var.set("(%.3f, %.3f)"%(x, y))
        self.slider = []
        rw = 1
        sl = Tkinter.Scale (frame, label='X Position', from_=0,
                            to=1.0, length="8c", orient='horizontal',
                            resolution=0.01)
        sl.set (x)
        sl.grid (row=rw, column=0, columnspan=2)
        sl.bind ("<ButtonRelease>", self.change_slider_gui)
        self.slider.append (sl)
        rw += 1
        sl = Tkinter.Scale (frame, label='Y Position', from_=0,
                            to=1.0, length="8c", orient='horizontal',
                            resolution=0.01)
        sl.set (y)
        sl.grid (row=rw, column=0, columnspan=2)
        sl.bind ("<ButtonRelease>", self.change_slider_gui)
        self.slider.append (sl)           
        rw += 1
        
        lab = Tkinter.Label (frame, text="Position:")
        lab.grid (row=rw, column=0, sticky='ew')
        entr = Tkinter.Entry (frame, width=10, relief='sunken',
                              textvariable=self.pos_var)
        entr.grid(row=rw, column=1, sticky='ew')
        entr.bind ("<Return>", self.set_position_gui)

        frame = Tkinter.Frame (self.root)
        frame.pack(side='top', fill='both', expand=1)
        CVOF = vtkPipeline.ConfigVtkObj.ConfigVtkObjFrame
        gui = CVOF(frame, self.renwin)
        t_m = ['ScaledTextOn', 'VisibilityOn']
        gs_m = ['Input', 'Width', 'Height']
        gui.configure(self.act, get=[], toggle=t_m, get_set=gs_m,
                      auto_update=1, one_frame=1)
        gui.pack(side='top', fill='both', expand=1)        
        
        gui = CVOF(frame, self.renwin)
        t_m = ['!DebugOn']
        gs_m = ['Color', 'FontSize', 'Opacity', 'VerticalJustification']
        s_m = [['SetFontFamilyToArial', 'SetFontFamilyToCourier',
                'SetFontFamilyToTimes']]

        gui.configure(self.tprop, get=[], toggle=t_m, get_set=gs_m,
                      state=s_m, auto_update=1, one_frame=1)
        gui.pack(side='top', fill='both', expand=1)
        

    def change_slider_gui(self, event=None):
        debug("Text::change_slider_gui()")
        x = self.slider[0].get()
        y = self.slider[1].get()
        self.pos_var.set("(%.3f, %.3f)"%(x, y))
        self.act.SetPosition(x, y)
        self.renwin.Render()
    
    def set_position_gui(self, event=None):
        debug("Text::set_position_gui()")
        x, y = eval (self.pos_var.get())
        self.slider[0].set(x)
        self.slider[1].set(y)
        self.act.SetPosition(x, y)
        self.renwin.Render()
    
