"""

This module defines the basic classes used by MayaVi.  The debug
function enables a rudimentary debug support.  Using this one can in
theory fix bugs faster.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.17 $"
__date__ = "$Date: 2005/08/02 18:26:23 $"
__credits__ = """Many thanks to Jose Paulo <moitinho@civil.ist.utl.pt> 
for adding tensor data support."""


import Tkinter, tkColorChooser
import vtk
import math
import Common, vtkPipeline.vtkPipeline 
import vtkPipeline.vtkMethodParser
import re
import glob
import os.path

debug = Common.debug


class ParseException (Exception):
    """ An exception that is raised when there is a problem with
    parsing a file."""
    pass


class ModuleException (Exception):
    """ An exception that is raised when there is a problem running a
    particular visualization module."""
    pass


class BaseObject:

    """ The basic object type."""

    def save_config (self, file): 
        """Save the objects configuration to file."""
        debug ("In BaseObject::save_config ()")
        debug ("BaseObject::save_config not implemented.")

    def load_config (self, file): 
        """Load the saved objects configuration from a file."""
        debug ("In BaseObject::load_config ()")
        debug ("BaseObject::load_config not implemented.")

    def config_changed (self): 
        """The configuration file has changed - take notice."""
        debug ("In BaseObject::config_changed ()")
        debug ("BaseObject::config_changed not implemented.")
        

class VizObject (BaseObject):

    """ The basic object type for visualization components."""

    def __init__ (self):
        debug ("In VizObject::__init__ ()")
        self.pipe_objs = None
        self.renwin = None
        self.root = None

    def _auto_sweep_init (self):
        """ Initialize variables for the autosweep GUI controls."""
        debug ("In VizObject::_auto_sweep_init ()")
        self.sweep_var = Tkinter.IntVar ()
        self.sweep_var.set (0)
        self.sweep_step = Tkinter.IntVar ()
        self.sweep_step.set (10)
        self.sweep_delay = Tkinter.DoubleVar ()
        self.sweep_delay.set (1.0)

    def _lift (self):
        """Lifts an already created configuration window to the
        top."""
        debug ("In VizObject::_lift ()")
        self.root.deiconify ()
        self.root.lift ()
        self.root.focus_set ()

    def configure (self, master=None): 
        "Create the GUI configuration controls for this object."
        debug ("In VizObject::configure ()")
        if (self.root and self.root.winfo_exists ()):
            return self._lift ()
        self.root = Tkinter.Toplevel (master)
        main_win = self.root.master.winfo_toplevel ()
        self.root.geometry ("+%d+%d" % (main_win.winfo_rootx()+5,
                                        main_win.winfo_rooty()+5))
        self.root.focus_set ()
        self.root.title ("Configure %s module"%self.__class__.__name__)
        self.root.protocol ("WM_DELETE_WINDOW", self.close_gui)

        self.make_custom_gui ()

    def make_custom_gui (self):
        """ This function is called by configure().  Use this to
        customize your own GUI."""
        debug ("In VizObject::configure ()")
        self.make_pipeline_gui ()
        self.make_main_gui ()
        #self.make_auto_sweep_gui ()
        self.make_close_button ()

    def make_pipeline_gui (self):
        """ Create the GUI for the segmented pipeline browser."""
        debug ("In VizObject::make_pipeline_gui ()")
        self.pipe_frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        self.pipe_frame.pack (side='top', fill='both', expand=1)
        self.pipe_var = Tkinter.IntVar ()
        self.pipe_var.set (0)
        cb = Tkinter.Checkbutton (self.pipe_frame, text="Show Pipeline",
                                  variable=self.pipe_var, onvalue=1,
                                  offvalue=0, command=self.show_pipeline)
        cb.pack(side='top', fill='both', expand=1)

    def make_auto_sweep_gui (self, master=None):
        """ Create the GUI controls for the auto-sweep animation."""
        debug ("In VizObject::make_auto_sweep_gui ()")
        if master is None:
            master = self.root
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)

        cb = Tkinter.Checkbutton (frame, text='Auto Sweep',
                                  variable=self.sweep_var,
                                  command=self.do_sweep)
        cb.grid (row=0, column=0, columnspan=2, sticky='w')

        lab = Tkinter.Label (frame, text="Auto Sweep Step:")
        lab.grid (row=1, column=0, sticky='w')
        entry = Tkinter.Entry (frame, width=5, relief='sunken', 
                               textvariable=self.sweep_step)
        entry.grid (row=1, column=1, sticky='we')
        entry.bind ("<Return>", self.sweep_step_validate)

        lab = Tkinter.Label (frame, text="Auto Sweep Delay:")
        lab.grid (row=2, column=0, sticky='w')
        entry = Tkinter.Entry (frame, width=5, relief='sunken', 
                               textvariable=self.sweep_delay)
        entry.grid (row=2, column=1, sticky='we')
        entry.bind ("<Return>", self.sweep_delay_validate)
        
    def make_close_button (self):
        """ Create a close button for the GUI control."""
        debug ("In VizObject::make_close_button ()")
        but = Tkinter.Button (self.root, text="Close", underline=0,
                               command=self.close_gui)
        but.pack (side='bottom', fill='both', expand=1)
        self.root.bind ("<Alt-c>", self.close_gui)

    def show_pipeline (self, event=None):
        """ Show the segmented pipeline browser when required."""
        debug ("In VizObject::show_pipeline ()")
        val = self.pipe_var.get ()
        if val:
            self.p_frame = Tkinter.Frame (self.pipe_frame)
            self.p_frame.pack (side='top', fill='both', expand=1)
            cl_obj = vtkPipeline.vtkPipeline.vtkPipelineSegmentBrowser
            pipe = cl_obj (self.p_frame, self.pipe_objs, self.renwin)
            pipe.pack (side='top', fill='both', expand=1)
        else:
            if self.p_frame:
                self.p_frame.destroy ()        

    def do_sweep (self, event=None):
        """Called when the user requests auto-sweeping."""
        debug ("In VizObject::do_sweep ()")
        debug ("VizObject::do_sweep () is not implemented.")

    def sweep_step_validate(self, event=None):
        """Validate the sweep step set by the user. """
        debug ("In VizObject::sweep_step_validate ()")
        #if self.sweep_step.get() < 1 :
        #self.sweep_step.set(1)
        pass

    def sweep_delay_validate(self, event=None):
        """Validate the sweep delay set by the user. """
        debug ("In VizObject::sweep_delay_validate ()")
        if self.sweep_delay.get() <= 0:
           self.sweep_delay.set(1.0)

    def close_gui (self, event=None):
        """Called when the 'close' button is clicked."""
        debug ("In VizObject::close_gui ()")
        self.root.master.focus_set ()
        self.root.destroy ()
        self.root = None
        try:
            self.sweep_var.set (0)
        except AttributeError:
            pass
            

class Source (VizObject):
    
    """Basic source object.  The source is similar in concept to a VTK
    source object.  It is basically a source of data."""

    def __init__ (self):
        VizObject.__init__ (self)
        
    def GetOutput (self): 
        """Output of the vtkSource object wrapped."""
        debug ("In Source::GetOutput ()")
        debug ("Source::GetOutput not implemented.")


def get_file_list (file_name):
    
    """ Given a file name, this function treats the file as a part of
    a series of files based on the index of the file and tries to
    determine the list of files in the series.  The file name of a
    file in a time series must be of the form 'some_name[0-9]*.ext'.
    That is the integers at the end of the file determine what part of
    the time series the file belongs to.  The files are then sorted as
    per this index."""
    
    debug ("In get_timestep_list ()")

    # The matching is done only for the basename of the file.
    f_dir, f_base = os.path.split (file_name)
    # Find the head and tail of the file pattern.
    head = re.sub("[0-9]+[^0-9]*$", "", f_base)
    tail = re.sub("^.*[0-9]+", "", f_base)
    pattern = head+"[0-9]*"+tail
    # Glob the files for the pattern.
    _files = glob.glob (os.path.join(f_dir, pattern))

    # A simple function to get the index from the file.
    def _get_index(f, head=head, tail=tail):
        base = os.path.split(f)[1]
        result = base.replace(head, '')
        return float(result.replace(tail, ''))

    # Before sorting make sure the files in the globbed series are
    # really part of a timeseries.  This can happen in cases like so:
    # 5_2_1.vtk and 5_2_1s.vtk will be globbed but 5_2_1s.vtk is
    # obviously not a valid time series file.
    files = []
    for x in _files:
        try:
            _get_index(x)
        except ValueError:
            pass
        else:
            files.append(x)
        
    # Sort the globbed files based on the index value.
    def file_sort(x, y):
        x1 = _get_index(x)
        y1 = _get_index(y)
        if x1 > y1:
            return 1
        elif y1 > x1:
            return -1
        else:
            return 0

    files.sort(file_sort)
    return files
    

class DataSource (Source):

    """ The basic class from which all are Data source classes are
    derived. """

    def __init__ (self): 
        debug ("In DataSource::__init__ ()")
        Source.__init__ (self)
        self.file_name = ""
        self.scalar_data_name = ""
        self.vector_data_name = ""        
        self.tensor_data_name = ""
        self.ref_lst = []
        self.file_list = [] # used if the file is part of a time series
        self.timestep = 0
        self.grid_type = ""
        self.root = None
    
    def initialize (self, file_name): 
        """Initialize the object given a valid file name."""
        debug ("In DataSource::initialize ()")
        self.file_list = get_file_list(file_name)
        try:
            self.timestep = self.file_list.index(file_name)
        except ValueError:
            pass
        if len(self.file_list) > 1:
            self._auto_sweep_init()
            self.sweep_step.set(1)

    def set_file_name(self, file_name):
        """Abstracts the call to self.reader.Set*FileName(). Useful
        when using this class as a base for other classes.  Override
        this if needed."""
        debug ("In DataSource::set_file_name ()")
        debug ("DataSource::set_file_name () is not implemented")        

    def get_file_name (self):
        """Get the data file name. """
        debug ("In DataSource::get_file_name ()")
        return self.file_name

    def get_file_list (self):
        """Get the list of data files. """
        debug ("In DataSource::get_file_list ()")
        return self.file_list

    def get_timestep (self):
        return self.timestep

    def set_timestep (self, timestep):
        """Used to change the time level of the file if it is part of
        a time series.  The time step must be an integer."""
        debug ("In DataSource::set_timestep ()")
        self.set_file_name(self.file_list[timestep])
        self.timestep = timestep

    def add_reference (self, ref):
        """ Add a reference object that is notified each time anything
        is changed in the DataSource object.  This is used for all
        ModuleManager instances."""
        debug ("In DataSource::add_reference ()")
        if ref in self.ref_lst:
            msg = "In DataSource::add_reference: Cannot add "\
                  "reference since reference already exists."
            debug (msg)
            return
        else:
            self.ref_lst.append (ref)

    def del_reference (self, ref):
        """ Remove an object that is to be notified of changes in
        self.  This is called when a ModuleManager is being
        deleted."""
        debug ("In DataSource::del_reference ()")
        self.ref_lst.remove (ref)

    def update_references (self):        
        """ Called when the configuration of the DataSource has
        changed.  This updates all the necessary objects via their
        update method."""
        debug ("In DataSource::update_references ()")
        for ref in self.ref_lst:
            ref.Update ()

    def config_changed (self):
        """ Called when the configuration options (in the Preferences
        menu) is changed."""
        debug ("In DataSource::config_changed ()")
        pass

    def GetOutput (self): 
        """Get the Data reader's output. """
        debug ("In DataSource::GetOutput ()")
        pass

    def get_grid_type (self): 
        """Get the type of grid used in the data file."""
        debug ("In DataSource::get_grid_type ()")
        return self.grid_type

    def get_scalar_data_name (self): 
        """Get the name of the scalar data attribute being used."""
        debug ("In DataSource::get_scalar_data_name ()")
        return self.scalar_data_name

    def get_vector_data_name (self): 
        """Get the name of the vector data attribute being used."""
        debug ("In DataSource::get_vector_data_name ()")
        return self.vector_data_name

    def get_tensor_data_name (self):
        """Get the name of the tensor data attribute being used."""
        debug ("In DataSource::get_tensor_data_name ()")
        return self.tensor_data_name

    def make_timestep_gui (self, master):
        debug ("In DataSource::make_timestep_gui()")
        nf = len(self.file_list)
        if nf < 2:
            return
        
        sl = Tkinter.Scale (master, label="Set Time Step", 
                            from_=0, to=nf-1,
                            length="5c", orient='horizontal', 
                            resolution=1)
        sl.set (self.timestep)
        sl.pack (side='top', fill='both', expand=1)
        sl.bind ("<ButtonRelease>", self.set_timestep_gui)
        self.timestep_var = sl
        
        self.make_auto_sweep_gui(master)

    def do_sweep (self, event=None):
        """Called when the user requests auto-sweeping."""
        debug ("In DataSource::do_sweep ()")
        if self.sweep_var.get ():
            val = int (1000*self.sweep_delay.get ())
            self.root.after (val, self.update_sweep)
            
    def update_sweep (self):
        debug ("In DataSource::update_sweep ()")
        if self.sweep_var.get ():
            val = int (1000*self.sweep_delay.get ())
            timestep = (self.timestep + self.sweep_step.get())%len(self.file_list)
            self.timestep_var.set (timestep)
            self.set_timestep_gui ()
            self.root.after (val, self.update_sweep)
    
    def set_timestep_gui (self, event=None): 
        debug ("In DataSource::set_timestep_gui ()")
        timestep = self.timestep_var.get()
        if timestep == self.timestep:
            return
        Common.state.busy ()
        self.set_timestep (timestep)
        self.reread_file ()
        self.file_name_label.config(text=self.file_name)
        Common.state.idle ()


class Filter (Source):

    """ The basic Filter class from which all are filters
    derived. This implements sufficient functionality that more
    complex filters are pretty much trivial to create."""

    def __init__ (self, mod_m):
        """ The argument 'mod_m' is a ModuleManager."""
        debug ("In Filter::__init__ ()")
        Common.state.busy ()
        Source.__init__ (self)
        self.mod_m = mod_m
        self.renwin = mod_m.get_render_window ()
        self.prev_fil = mod_m.get_last_source ()
        # try to use this as your filter
        self.fil = None
        self.initialize ()
        Common.state.idle ()

    def initialize (self):
        """Override this to create the actual filter and do what you
        want.  Use self.fil as the wrapped filter."""
        debug ("In Filter::initialize ()")        
        pass

    def set_input_source (self, source):
        """Set the input source object for this Filter."""
        debug ("In Filter::set_input_source ()")
        debug ("Filter::set_input_source not implemented.")        

    def SetInputSource (self, source): 
        """Set the input source object for this Filter."""
        debug ("In Filter::SetInputSource ()")
        self.set_input_source (source)

    def GetOutput (self):
        debug ("In Filter::GetOutput ()")        
        return self.fil.GetOutput ()    

    def get_scalar_data_name (self):
        """Get the name of the scalar data attribute being used.
        Defaults to returning the previous filters scalar
        data_name."""
        debug ("In Filter::get_scalar_data_name ()")
        return self.prev_fil.get_scalar_data_name ()
        
    def get_vector_data_name (self):
        """Get the name of the vector data attribute being used.
        Defaults to returning the previous filters vector
        data_name."""
        debug ("In Filter::get_vector_data_name ()")
        return self.prev_fil.get_vector_data_name ()

    def get_tensor_data_name (self):
        """Get the name of the tensor data attribute being used.
        Defaults to returning the previous filters tensor
        data_name."""
        debug ("In Filter::get_tensor_data_name ()")
        return self.prev_fil.get_tensor_data_name ()

    def save_config (self, file):
        """Saves the filter config to passed file."""
        debug ("In Filter::save_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.fil, ):
            p.dump (obj, file)
        
    def load_config (self, file):
        """Loads the filter config from passed file."""
        debug ("In Filter::load_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.fil, ):
            p.load (obj, file)
        self.fil.Update ()


class Module (VizObject):
    
    """ The basic Module class from which all modules are derived."""

    def __init__ (self, mod_m): 
        """ The argument 'mod_m' is a ModuleManager."""
        debug ("In Module::__init__ ()")
        VizObject.__init__ (self)
        self.mod_m = mod_m
        self.renwin = mod_m.get_render_window ()
        # Set this to the actor you need to be able to configure
        self.actor = None
        self.mapper = None
    
    def SetInput (self, source):        
        """ Set the input for this Module.  This function is similar
        to the VTK obj1.SetInput(obj2.GetOutput()) kind of function
        call. """
        debug ("In Module::SetInput ()")
        debug ("Module::SetInput not implemented.")

    def _contour_init (self):
        """ Initialize variables for contour GUI controls."""
        debug ("In Module::_contour_init ()")
        self.contour_on = Tkinter.IntVar ()
        self.linew_var = Tkinter.DoubleVar ()
        self.n_cnt = Tkinter.StringVar ()
        self.min_cnt = Tkinter.DoubleVar ()
        self.max_cnt = Tkinter.DoubleVar ()

    def make_contour_gui (self):
        """ Create the GUI controls for contours."""
        debug ("In Module::make_contour_gui ()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)
        
        cb = Tkinter.Checkbutton (frame, text="Show Contours", 
                                  variable=self.contour_on, onvalue=1,
                                  offvalue=0, command=self.do_contour)
        cb.grid (row=0, column=0, sticky='w')
        
        lab = Tkinter.Label (frame, text="Contours:")
        lab.grid (row=1, column=0, sticky='w')
        entry = Tkinter.Entry (frame, width=15, relief='sunken', 
                               textvariable=self.n_cnt)
        entry.grid (row=1, column=1, sticky='we')
        entry.bind ("<Return>", self.change_contour)
        
        lab = Tkinter.Label (frame, text="Minimum contour:")
        lab.grid (row=2, column=0, sticky='w')
        entry = Tkinter.Entry (frame, width=15, relief='sunken', 
                               textvariable=self.min_cnt)
        entry.grid (row=2, column=1, sticky='we')
        entry.bind ("<Return>", self.change_contour)

        lab = Tkinter.Label (frame, text="Maximum contour:")
        lab.grid (row=3, column=0, sticky='w')
        entry = Tkinter.Entry (frame, width=15, relief='sunken', 
                               textvariable=self.max_cnt)
        entry.grid (row=3, column=1, sticky='we')
        entry.bind ("<Return>", self.change_contour)

    def make_actor_gui (self, event=None, color=1, linewidth=1,
                        scalar=1, representation=1, opacity=1,
                        compact=0):
        """Creates controls for the actor config.  This requires that
        there be an instance variable called self.actor and
        self.mapper."""        
        debug ("In Module::make_actor_gui ()")

        self.scalar_on_var = Tkinter.IntVar ()
        self.scalar_on_var.set (0)
        if self.mapper and hasattr(self.mapper, 'GetScalarVisibility'):
            self.scalar_on_var.set (self.mapper.GetScalarVisibility ())

        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)

        rw = 0
        if scalar:
            cb = Tkinter.Checkbutton (frame, text="Scalar Coloring",
                                      variable=self.scalar_on_var,
                                      onvalue=1, offvalue=0,
                                      command=self.scalar_config)
            cb.grid (row=rw, column=0, columnspan=2, pady=3, sticky='w')
            rw = rw + 1
        if color:
            but = Tkinter.Button (frame, text="Change Object Color",
                                  underline=2, command=self.change_color)
            but.grid (row=rw, column=0, columnspan=2, pady=3, sticky='ew')
            self.root.bind ("<Alt-a>", self.change_color)            
            rw = rw + 1

        if representation:
            self.rep_var = Tkinter.IntVar ()
            self.rep_var.set (self.actor.GetProperty().GetRepresentation())
            rb1 = Tkinter.Radiobutton (frame,
                                       text="Set Representation "\
                                       "to Wireframe",
                                       variable=self.rep_var, value=1,
                                       command=self.represent_config)
            rb1.grid (row=rw, column=0, columnspan=2, pady=3, sticky='w')
            rw = rw + 1
            rb2 = Tkinter.Radiobutton (frame,
                                       text="Set Representation to Surface",
                                       variable=self.rep_var, value=2,
                                       command=self.represent_config)
            rb2.grid (row=rw, column=0, columnspan=2, pady=3, sticky='w')
            rw = rw + 1

        if opacity:
            self.opaq_res_var = Tkinter.DoubleVar ()
            self.opaq_res_var.set (0.01)
            if compact:
                but = Tkinter.Button (frame, text="Change Object Opacity",
                                      underline=7,
                                      command=self.compact_opacity)
                but.grid (row=rw, column=0, columnspan=2, pady=3,
                          sticky='ew')
                self.root.bind ("<Alt-o>", self.compact_opacity)
                rw = rw + 1
            else:
                sl = Tkinter.Scale (frame, label="Set Opacity", 
                                    from_=0.0, to=1.0,
                                    length="5c", orient='horizontal', 
                                    resolution=self.opaq_res_var.get ())
                sl.set (self.actor.GetProperty ().GetOpacity ())
                sl.grid (row=rw, column=0, columnspan=2, sticky='ew')
                sl.bind ("<ButtonRelease>", self.change_opacity)
                self.opaq_slider = sl
                rw = rw + 1
                lab = Tkinter.Label (frame, text="Opacity resolution: ")
                lab.grid (row=rw, column=0, sticky='w')
                entr = Tkinter.Entry (frame, width=5, relief='sunken',
                                      textvariable=self.opaq_res_var)
                entr.grid (row=rw, column=1, sticky='ew')
                entr.bind ("<Return>", self.set_opacity_resolution)
                rw = rw+1

        if linewidth:
            self.linew_var = Tkinter.DoubleVar ()
            self.linew_var.set (self.actor.GetProperty ().GetLineWidth ())
            lab = Tkinter.Label (frame, text="Line width:")
            lab.grid (row=rw, column=0, sticky='w')
            entr = Tkinter.Entry (frame, width=5, relief='sunken',
                                  textvariable=self.linew_var)
            entr.grid (row=rw, column=1, sticky='we')
            entr.bind ("<Return>", self.set_linewidth)
            rw = rw + 1

    def do_contour (self, event=None):
        """Called when the user requests contour lines."""
        debug ("In Module::do_contour ()")
        debug ("Module::do_contour () is not implemented.")

    def change_contour (self, event=None):
        """Called when the user changes the contour line config."""
        debug ("In Module::change_contour ()")
        debug ("Module::change_contour () is not implemented.")

    def set_linewidth (self, event=None):
        """Called when the actor linewidth to be changed."""
        debug ("In Module::set_linewidth ()")
        Common.state.busy ()
        self.actor.GetProperty ().SetLineWidth (self.linew_var.get ())
        self.renwin.Render ()
        Common.state.idle ()

    def scalar_config (self, event=None):        
        """ Called when the user requests ScalarVisibility on or
        off."""
        debug ("In Module::scalar_config ()")
        Common.state.busy ()
        val = self.scalar_on_var.get ()
        self.mapper.SetScalarVisibility (val)
        self.renwin.Render ()
        Common.state.idle ()

    def represent_config (self, event=None):        
        """ Called when the user changes the Representation of the
        actor."""
        debug ("In Module::plane_config ()")
        Common.state.busy ()
        val = self.rep_var.get ()
        self.actor.GetProperty ().SetRepresentation (val)
        self.renwin.Render ()
        Common.state.idle ()

    def change_color (self, event=None): 
        """ Called when the user changes the color of the actor."""
        debug ("In Module::change_color ()")
        clr = self.actor.GetProperty ().GetColor ()
        init_clr = "#%02x%02x%02x"%(clr[0]*255, clr[1]*255, clr[2]*255)
        color = tkColorChooser.askcolor (title="Change object color", 
                                         initialcolor=init_clr)
        if color[1] is not None:
            Common.state.busy ()
            clr = Common.tk_2_vtk_color (color[0])
            self.actor.GetProperty ().SetColor (*clr)
            self.renwin.Render ()        
            Common.state.idle ()
            if self.scalar_on_var.get () != 0:
                msg = "Warning: This setting will have effect only if "\
                      "there is no ScalarVisibility."
                Common.print_err (msg)

    def change_opacity (self, event=None):
        """ Called when the opacity slider is changed."""
        debug ("In Module::change_opacity ()")
        Common.state.busy ()
        val = self.opaq_slider.get ()
        self.actor.GetProperty ().SetOpacity (val)
        self.renwin.Render ()
        Common.state.idle ()

    def set_opacity_resolution (self, event=None):
        """ Called when the opacity slider resolution is changed. """
        self.opaq_slider.config (resolution=self.opaq_res_var.get ())
        
    def compact_opacity (self, event=None):        
        """ Called when the opacity button (when compact=1) is
        clicked."""
        self.o_top = top = Tkinter.Toplevel (self.root)
        top.transient (self.root.master)
        top.protocol ("WM_DELETE_WINDOW", top.destroy)
        frame = Tkinter.Frame (top, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)
        rw = 0
        sl = Tkinter.Scale (frame, label="Set Opacity", 
                            from_=0.0, to=1.0,
                            length="5c", orient='horizontal', 
                            resolution=self.opaq_res_var.get ())
        sl.set (self.actor.GetProperty ().GetOpacity ())
        sl.grid (row=rw, column=0, columnspan=2, sticky='ew')
        sl.bind ("<ButtonRelease>", self.change_opacity)
        self.opaq_slider = sl
        rw = rw + 1
        lab = Tkinter.Label (frame, text="Opacity resolution: ")
        lab.grid (row=rw, column=0, sticky='w')
        entr = Tkinter.Entry (frame, width=5, relief='sunken',
                              textvariable=self.opaq_res_var)
        entr.grid (row=rw, column=1, sticky='ew')
        entr.bind ("<Return>", self.set_opacity_resolution)
        rw = rw+1
        but = Tkinter.Button (frame, text="Close", underline=0,
                              command=lambda t=top, e=None: t.destroy ())
        but.grid (row=rw, column=0, columnspan=2, sticky='ew')
        top.bind ("<Alt-c>", self.__opacity_quit)

    def __opacity_quit (self, event=None):
        self.o_top.destroy ()


class CutPlaneModule (Module):

    """ An abstraction for cut plane based modules. """

    def __init__ (self, mod_m):
        debug ("In CutPlaneModule::__init ()")
        Module.__init__ (self, mod_m)
        # this should be a vtkPlane
        self.plane = vtk.vtkPlane ()
        self.step_var = Tkinter.DoubleVar ()
        self.n_step_var = Tkinter.IntVar ()
        self.resoln_var = Tkinter.DoubleVar ()
        self.resoln_var.set (1.0)
        self.slider = []

    def get_angles (self):
        debug ("In CutPlaneModule::get_angles ()")
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
        debug ("In CutPlaneModule::config_extents ()")
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
        debug ("In CutPlaneModule::make_cut_plane_gui ()")
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
        debug ("In CutPlaneModule::change_cut ()")
        self.step_size = self.step_var.get ()
        n_s = self.n_step_var.get ()
        self.slider[2].config (from_=-n_s, to=n_s)
        self.change_slider (event)

    def change_slider (self, event=None):
        debug ("In CutPlaneModule::change_slider ()")
        Common.state.busy ()
        val = []
        for i in range (3):
            val.append (self.slider[i].get ())

        self.slider_pos = val[2]
        self.config_extents (val)
        self.renwin.Render ()
        Common.state.idle ()    

    def change_resoln (self, event=None):
        debug ("In CutPlaneModule::change_resoln ()")
        val = self.resoln_var.get ()
        for i in range (0, 2):
            self.slider[i].config (resolution=val)        
    
