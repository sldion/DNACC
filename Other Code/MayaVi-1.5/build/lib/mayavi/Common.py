"""

This module defines some useful classes and functions used by almost
all the code.  It also creates a few 'instance' variables that are
used for common access across all other files.

The debug function enables a rudimentary debug support.  Using this
one can in theory fix bugs faster.

Please note that this module *MUST* be imported before any other
mayavi modules.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.17 $"
__date__ = "$Date: 2005/03/21 12:05:12 $"
        
import os, sys, string, pickle
import Tkinter, tkColorChooser, tkMessageBox, tkFileDialog

def print_err (str):
    tkMessageBox.showerror ("ERROR", str)

def get_relative_file_name (base_f_name, f_name):

    """Returns a file name for f_name relative to base_f_name.
    base_f_name and f_name should be valid file names correct on the
    current os.  The returned name is a file name that has a POSIX
    path."""
    
    f_name = os.path.normpath (os.path.abspath (f_name))
    base_f_name = os.path.normpath (os.path.abspath (base_f_name))
    base_dir = os.path.dirname (base_f_name) + os.sep
    common = os.path.commonprefix ([base_dir, f_name])
    n_base = string.count (base_dir, os.sep)
    n_common  = string.count (common, os.sep)
    diff = (n_base - n_common)* (os.pardir+os.sep)
    ret = diff + f_name[len (common):]
    ret = os.path.normpath (ret)
    if os.sep is not '/':
        string.replace (ret, os.sep, '/')
    return ret

def get_abs_file_name (base_f_name, rel_file_name):    
    """ Returns the absolute file name given a base file name and
    another file name relative to the base name."""
    rel_file_name = os.path.normpath (rel_file_name)
    file_name = os.path.join (os.path.dirname (base_f_name),
                              rel_file_name)
    file_name = os.path.normpath (file_name)
    return file_name


# used to retain state even when this module is reloaded.
_app_cfg = {}
_app_state = {}
_log_data = {}

mod = None
if sys.modules.has_key ('mayavi.Common'):
    mod = sys.modules['mayavi.Common']
elif sys.modules.has_key ('Common'):
    mod = sys.modules['Common']

if mod:
    if hasattr (mod, 'AppConfig'):
        _app_cfg = mod.AppConfig._shared_data
    if hasattr (mod, 'AppState'):
        _app_state = mod.AppState._shared_data
    if hasattr (mod, 'LogWindow'):
        _log_data = mod.LogWindow._shared_data
del mod
# done resetting state from the Common module that was imported earlier.


class AppConfig:

    """ This class enables a simple configuration file to be used by
    the application.  It basically pickles a dictionary into a text
    file.  Using this it is possible to save and restore user specific
    application settings.  The class is Borg so it can be freely
    instantiated and used without fear of loss of data."""

    _shared_data = _app_cfg
    
    def __init__ (self):
        self.__dict__ = self._shared_data

        if not hasattr(self, 'is_initialized'):
            # First instantiation.
            self.__dict__['is_initialized'] = 1
            try:
                h = os.environ['HOME']
            except KeyError:
                os.environ['HOME'] = os.path.abspath (os.path.dirname (sys.argv[0]))

            home_dir = os.environ['HOME']
            self.__dict__['config_file'] = os.path.join (home_dir, ".mayavi")

            defaults = {"fg_color":(0.0, 0.0, 0.0),
                        "bg_color":(1.0, 1.0, 1.0),
                        "initial_dir" : '',
                        "magnification": 1,
                        "stereo": 0,
                        "light_cfg": None,
                        "scalar_lut_cfg": None,
                        "vector_lut_cfg": None,
                        "search_path":'',
                        }
            self.__dict__['data'] = defaults
            self.__dict__['upath'] = []
            self.__dict__['upath_filters'] = []
            self.__dict__['upath_modules'] = []            
            self.__dict__['upath_sources'] = []            
        
            if os.path.isfile (self.config_file):
                f = open (self.config_file, 'r')
                if f.readline () == "MayaVi Config file.\n":
                    cfg = pickle.load (f)
                    self.__dict__['data'].update(cfg)
                f.close ()
                
            if sys.platform == 'darwin':
                if self.initial_dir == '':
                    # initial_dir == '' is invalid on the Mac.
                    self.initial_dir = os.getcwd()

            self.update_search_paths()

    def update_search_paths(self):

        # Search also the user's search path as set in the Preferences
        # This is like PYTHONPATH, a ':'-separated string.  ~, ~user
        # and $VAR are all expanded.        
        spath = self.search_path.split(':')
        spath = map(os.path.expandvars, spath)
        spath = map(os.path.expanduser, spath)
        
        self.__dict__['upath'] = filter(os.path.isdir, spath)
        uf = []
        um = []
        us = []
        for user_dir in self.upath:
            uf.append(os.path.join(user_dir, 'Filters'))
            um.append(os.path.join(user_dir, 'Modules'))
            us.append(os.path.join(user_dir, 'Sources'))
        self.__dict__['upath_filters'] = uf
        self.__dict__['upath_modules'] = um
        self.__dict__['upath_sources'] = us

    def __getattr__ (self, name):
        return self.__dict__['data'][name]

    def __setattr__ (self, name, val):
        self.data[name] = val

    def save (self):
        """ Save the current settings to the configuration file."""
        f = open (self.config_file, 'w')
        f.write ("MayaVi Config file.\n")
        pickle.dump (self.data, f)
        f.close()


def tk_2_vtk_color (tk_col):
    "Converts a Tk RGB color to a VTK RGB color."
    ONE_255 = 1.0/255.0
    return (tk_col[0]*ONE_255, tk_col[1]*ONE_255, tk_col[2]*ONE_255)


class EditConfig:
    
    """ Provides a simple GUI to configure the Application
    defaults."""
    
    def __init__ (self, master, app, cfg):
        self.cfg = cfg
        self.app = app
        self.bg_color = Tkinter.StringVar ()
        self.fg_color = Tkinter.StringVar ()
        self.initial_dir = Tkinter.StringVar ()
        self.mag_fact = Tkinter.IntVar ()
        self.stereo = Tkinter.IntVar ()
        self.save_lights = Tkinter.IntVar ()
        self.save_sc_lut = Tkinter.IntVar ()
        self.save_vec_lut = Tkinter.IntVar ()
        self.bg_color.set (str (cfg.bg_color))
        self.fg_color.set (str (cfg.fg_color))
        self.initial_dir.set (cfg.initial_dir)
        self.mag_fact.set (cfg.magnification)
        self.stereo.set(cfg.stereo != 0)
        self.save_lights.set(0)
        self.save_sc_lut.set(0)
        self.save_vec_lut.set(0)

        self.search_path = Tkinter.StringVar ()
        self.search_path.set(str(cfg.search_path))
        
        self.root = Tkinter.Toplevel (master)
        self.root.transient (self.root.master)
        self.root.title ("Edit Preferences")
        self.root.protocol ("WM_DELETE_WINDOW", self.cancel)
        frame = Tkinter.Frame (self.root)
        frame.pack (side='top', expand=1, fill='both')
        self.make_config_gui (frame)
        frame = Tkinter.Frame (frame)
        frame.pack (side='top', expand=1, fill='both')
        self.make_control_gui (frame)

    def make_config_gui (self, master):
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top', expand=1, fill='both')
        rw = 1
        but = Tkinter.Button (frame, text="Default Background Color:",
                              command=self.set_bg_color, padx=1)
        but.grid (row=0, column=0, sticky='w', pady=2)
        entr = Tkinter.Entry (frame, width=20, relief='sunken', 
                              textvariable=self.bg_color)
        entr.grid (row=0, column=1, sticky='ew', pady=2)
        rw += 1
        
        but = Tkinter.Button (frame, text="Default Foreground Color:",
                              command=self.set_fg_color, padx=1)
        but.grid (row=rw, column=0, sticky='w', pady=2)
        entr = Tkinter.Entry (frame, width=20, relief='sunken', 
                              textvariable=self.fg_color)
        entr.grid (row=rw, column=1, sticky='ew', pady=2)
        rw += 1

        but = Tkinter.Button (frame, text="Default directory:",
                              command=self.get_dir, padx=1)
        but.grid (row=rw, column=0, sticky='w')
        entr = Tkinter.Entry (frame, width=20, relief='sunken', 
                              textvariable=self.initial_dir)
        entr.grid (row=rw, column=1, sticky='ew', pady=2)
        rw += 1

        lab = Tkinter.Label (frame, text="Search path:", padx=1)
        lab.grid (row=rw, column=0, sticky='w', pady=2)
        entr = Tkinter.Entry (frame, width=20, relief='sunken', 
                              textvariable=self.search_path)
        entr.grid (row=rw, column=1, sticky='ew', pady=2)
        rw += 1

        sl = Tkinter.Scale (frame,
                            label="Magnification factor for saving images",
                            from_=1, to=10, length="8c",
                            orient="horizontal", variable=self.mag_fact)
        sl.grid (row=rw, column=0, columnspan=2, sticky="ew")
        rw += 1

        cb = Tkinter.Checkbutton(frame, text="Use stereo rendering",
                                 variable=self.stereo)
        cb.grid (row=rw, column=0, columnspan=2, sticky="w")
        rw += 1

        cb = Tkinter.Checkbutton(frame, text="Save current lighting",
                                 variable=self.save_lights)
        cb.grid (row=rw, column=0, columnspan=2, sticky="w")
        rw += 1
        
        cb = Tkinter.Checkbutton(frame, text="Save current scalar legend",
                                 variable=self.save_sc_lut)
        cb.grid (row=rw, column=0, columnspan=2, sticky="w")
        rw += 1

        cb = Tkinter.Checkbutton(frame, text="Save current vector legend",
                                 variable=self.save_vec_lut)
        cb.grid (row=rw, column=0, columnspan=2, sticky="w")
        rw += 1

    def make_control_gui (self, master):
        frame = Tkinter.Frame (master)
        frame.pack (side='top', expand=1, fill='both')
        b = Tkinter.Button (frame, text="Apply", underline=0,
                            command=self.apply_changes)
        b.grid (row=0, column=0, padx=2, pady=2, sticky='ew') 
        b = Tkinter.Button (frame, text="Ok", underline=0,
                             command=self.ok_done)
        b.grid (row=0, column=1, padx=2, pady=2, sticky='ew')
        b = Tkinter.Button (frame, text="Save", underline=0,
                            command=self.save_changes)
        b.grid (row=0, column=2, padx=2, pady=2, sticky='ew')
        b = Tkinter.Button (frame, text="Cancel", underline=0,
                             command=self.cancel)
        b.grid (row=0, column=3, padx=2, pady=2, sticky='ew')
        # keyboard accelerators
        self.root.bind ("<Alt-a>", self.apply_changes)
        self.root.bind ("<Alt-o>", self.ok_done)
        self.root.bind ("<Alt-s>", self.save_changes)
        self.root.bind ("<Alt-c>", self.cancel)

    def set_bg_color (self, event=None):
        """Choose and set a background color from a GUI color chooser."""
        col = self.cfg.bg_color
        cur_col = "#%02x%02x%02x"% (col[0]*255, col[1]*255, col[2]*255)
        new_color = tkColorChooser.askcolor (title="Background color",
                                             initialcolor=cur_col)
        if new_color[1] != None:
            col = tk_2_vtk_color (new_color[0])
            self.bg_color.set (col)

    def set_fg_color (self, event=None):
        """Choose and set a foreground color from a GUI color chooser."""
        col = self.cfg.fg_color
        cur_col = "#%02x%02x%02x"% (col[0]*255, col[1]*255, col[2]*255)
        new_color = tkColorChooser.askcolor (title="Foreground color",
                                             initialcolor=cur_col)
        if new_color[1] != None:
            col = tk_2_vtk_color (new_color[0])
            self.fg_color.set (col)
        
    def get_dir (self, event=None):
        """Choose a directory from a file selected."""
        msg = "Please choose a file in the chosen directory.  "\
              "The directory from which the file was taken "\
              "will be chosen as the default directory. "\
              "If you enter an empty entry, an intelligent "\
              "choice of directory will be made automatically at run-time."
        tkMessageBox.showinfo ("Choose directory", msg)
        tk_fopen = tkFileDialog.askopenfilename
        f_name = tk_fopen (title="Choose file to select directory",
                           initialdir=self.cfg.initial_dir,
                           filetypes=[("All files", "*")])
        if f_name:
            direc = os.path.dirname (f_name)
            self.cfg.initial_dir = direc
            self.initial_dir.set (direc)

    def apply_changes (self, event=None):
        """ Apply the changes made to the configuration."""
        self.cfg.bg_color = eval (self.bg_color.get ())
        self.cfg.fg_color = eval (self.fg_color.get ())
        self.cfg.magnification = self.mag_fact.get()
        direc = self.initial_dir.get ()
        if direc and (not os.path.isdir (direc)):
            tkMessageBox.showwarning(
                "Bad input",
                "Illegal directory! Try again!!"
                )
            return 0
        self.cfg.initial_dir = direc
        self.cfg.search_path = self.search_path.get()
        self.cfg.update_search_paths()

        # Stereo
        rw = self.app.get_render_window()
        if self.stereo.get():
            v_rw = rw.get_render_window()
            self.cfg.stereo = (v_rw.GetStereoRender(), v_rw.GetStereoType())
        else:
            self.cfg.stereo = 0

        # Lights
        if self.save_lights.get():
            light_cfg = {}
            rw.get_light_manager().save_config(light_cfg)
            self.cfg.light_cfg = light_cfg

        # LUTs
        dvm = self.app.get_current_dvm()
        cfg_file_path = os.path.abspath(self.cfg.config_file)
        if dvm and self.save_sc_lut.get():
            mm = dvm.get_current_module_mgr()
            s_l_h = mm.get_scalar_lut_handler()
            s_l_c = s_l_h.save_config_to_dict(cfg_file_path)
            self.cfg.scalar_lut_cfg = s_l_c
        if dvm and self.save_vec_lut.get():
            mm = dvm.get_current_module_mgr()
            v_l_h = mm.get_vector_lut_handler()
            v_l_c = v_l_h.save_config_to_dict(cfg_file_path)
            self.cfg.vector_lut_cfg = v_l_c
            
        self.app.config_changed ()
        return 1
        
    def ok_done (self, event=None):
        """Called when the Ok button is clicked."""
        if not self.apply_changes ():
            return 0
        self.root.destroy ()

    def save_changes (self, event=None):
        """Save changes made to the configuration file."""
        rootbg = self.root.cget("background")
        self.root.config (background="red", cursor="watch")
        self.root.update_idletasks ()
        if not self.apply_changes ():
            self.root.config (background=rootbg, cursor="")
            return 0
        self.cfg.save ()
        self.root.config (background=rootbg, cursor="")
        return 1

    def cancel (self, event=None):
        """Cancel button clicked."""
        del self.app
        self.root.destroy ()


class AppState:

    """ This class provides a simple way to show that the application
    is busy doing something.  It does this by changing the cursor to a
    watch and changing the color of the 'registered' widgets to red.
    It keeps track of how many times the 'busy' method has been called
    and does the 'right thing' if the state is already busy.  The
    class is Borg so it can be freely instantiated and used without
    fear of loss of data."""

    _shared_data = _app_state
    def __init__ (self):
        self.__dict__ = self._shared_data
        
        if not hasattr (self, 'is_busy'):
            self.is_busy = 0
            self.window = []
            self.orig_bg = []

    def register (self, app_win):        
        """ Registers a particular widget to be color changed when the
        application is busy."""
        if app_win in self.window:
            return
        else:
            self.window.append (app_win)

    def unregister (self, app_win):
        """Unregisters the widget."""
        if app_win in self.window:
            indx = self.window.index (app_win)
            del self.window[indx]

    def busy (self):        
        """ Show that the application is busy doing something.  If
        already busy simply incremement a counter."""
        if self.is_busy:
            self.is_busy = self.is_busy + 1
            return
        self.orig_bg = []
        for win in self.window:
            self.orig_bg.append (win.cget ("background"))
            win.config (background="red", cursor="watch")
            win.update_idletasks ()
        self.is_busy = 1

    def force_idle (self):
        """ Force the state to be idle.  Typically used when an
        exception is hit."""        
        if self.is_busy:
            self.is_busy = 0
            for i in range (len (self.window)):
                self.window[i].config (background=self.orig_bg[i],
                                       cursor="")        

    def idle (self):        
        """ Application is idle, restore the GUI if the count of busy
        calls is zero if not decrement counter."""        
        if self.is_busy:
            self.is_busy = self.is_busy - 1
        if not self.is_busy:
            for i in range (len (self.window)):
                self.window[i].config (background=self.orig_bg[i],
                                       cursor="")


class LogWindow:
    
    """ This class prints the output of all the debug function calls
    made to a Tkinter.Text widget.  It also prints the debug logs to a
    terminal when available.  The class is Borg so it can be freely
    instantiated and used without fear of loss of data."""
    
    _shared_data = _log_data        
    def __init__ (self, master=None):
        self.__dict__ = self._shared_data
        
        if not hasattr (self, 'master'):
            self.master = master
            self.logging = 0
            self.root = None

    def show_log (self, event=None, old_log=None):
        """ Show the log window."""
        if self.logging:
            return
        self.logging = 1
        if self.master:
            self.root = Tkinter.Toplevel (self.master)
        else:
            self.root = Tkinter.Toplevel ()
        self.root.title ("MayaVi Log Window")
        self.root.protocol ("WM_DELETE_WINDOW", self.quit)
        f = Tkinter.Frame (self.root)
        f.pack (side='top', fill='both', expand=1)
        f.rowconfigure (0, weight=1)
        f.columnconfigure (0, weight=1)
        scr1 = Tkinter.Scrollbar (f, orient='vertical')
        scr2 = Tkinter.Scrollbar (f, orient='horizontal')
        self.txt = Tkinter.Text (f, yscrollcommand=scr1.set,
                                 xscrollcommand=scr2.set,
                                 state='normal', height=8, width=80)
        scr1.config (command=self.txt.yview) 
        scr2.config (command=self.txt.xview) 
        self.txt.grid (row=0, column=0, sticky='ewns')
        scr1.grid (row=0, column=1, sticky='ns')
        scr2.grid (row=1, column=0, columnspan=2, sticky='ew')
        self.close_but = Tkinter.Button (self.root, text="Close", fg="red",
                                         underline=0, command=self.quit)
        self.close_but.pack (side='bottom')
        self.root.bind ("<Alt-c>", self.quit)

        self.check_old_log (old_log)

    def check_old_log (self, old_log):        
        """ When a log window is reloaded one has to reinitialize the
        new instance so that the geometry and contents are the same.
        This is done by this method."""
        if old_log:
            self.root.geometry (old_log.root.geometry ())
            self.txt.insert ('end', old_log.txt.get (1.0, 'end'))
            self.txt.update_idletasks ()

    def write_log (self, data):
        """ Write data to the log window."""
        if self.logging:
            self.txt.insert ('end', data+'\n')
            self.txt.update_idletasks ()
            print data

    def quit (self, event=None):
        """ Quit the log window. """
        self.logging = 0
        if self.root:
            self.root.destroy ()
        

config = AppConfig ()
state = AppState ()
log_win = LogWindow ()

def debug (msg):
    """ Print a debug message to the log window.  The log window is an
    instance variable created when this module is imported for the
    first time or if it is reloaded."""
    log_win.write_log (msg)


def mod_fil_import(kind, name, globals, locals, user_paths=0):
    """
    Special importer which tries alternate paths.  Used to load
    Filters and Modules from user paths as well as MayaVi's internal
    one.  If the argument user_paths is true then the modules/filters
    are first searched for in the user specified paths obtained from
    config.search_path.
    """
    # User paths should override system defaults, so users can customize
    # their modules without system-wide write access
    assert kind in ['Modules', 'Filters', 'Sources']
    
    extra_path = ''
    if user_paths:
        if kind == 'Modules':
            extra_path = config.upath_modules
        elif kind == 'Filters':
            extra_path = config.upath_filters
        elif kind == 'Sources':
            extra_path = config.upath_sources
    try:
        if extra_path:
            try:
                spath = sys.path
                sys.path = extra_path + sys.path
                mod_scr = __import__ (name,globals)
            finally:
                sys.path = spath
        else:
            # so that the normal import kicks in
            raise ImportError
    # If a module isn't in the user's path
    except ImportError:
        mod_scr = __import__ ("%s.%s"%(kind, name), globals,
                              locals, [name])
    return mod_scr


del _app_cfg, _app_state, _log_data
