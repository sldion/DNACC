"""

This module defines the main application classes for MayaVi and the Tk
GUI for it.

Bugs:

  This file is *way* too big and complex.  Need to clean it up and
  possibly split it into smaller parts?

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2005, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.51 $"
__date__ = "$Date: 2005/08/24 10:45:20 $"

import os, traceback, glob, sys, string
import Tkinter, tkFileDialog, tkMessageBox, tkColorChooser
import Common, Base.Objects, Base.ModuleManager, Base.DataVizManager
import Sources.VtkDataReader, Sources.PLOT3DReader, Sources.VRMLImporter
import Sources.mv3DSImporter, Sources.VtkData
import Sources.VtkXMLDataReader
import Sources.VtkEnSightReader
import Misc.RenderWindow
import vtkPipeline.vtkPipeline
import vtk
from __version__ import version


tk_fopen = tkFileDialog.askopenfilename
tk_fsave = tkFileDialog.asksaveasfilename
debug = Common.debug
print_err = Common.print_err


def reload_all_modules ():

    """This function reloads all the currently loaded modules.  _Very_
    useful while debugging.  Please note that the configuration
    settings from Common.config will remain unchanged.  You _might_    also see funny behaviour for already instantiated objects."""

    debug ("In reload_all_modules")
    msg = "Warning: This reloads all the currently loaded modules. "\
          "This is a feature useful only for developers.  You _might_ "\
          "see funny behaviour for already instantiated objects.\n\n"\
          "Are you sure you want to do this?"
    if not tkMessageBox.askyesno ("Warning", msg):
        return

    my_dir = os.path.dirname (os.path.abspath (__file__))    

    dont_load = list (sys.builtin_module_names)

    Common.state.busy ()
    for key in sys.modules.keys ():
        if key not in dont_load:
            mod = sys.modules[key]
            if mod and hasattr (mod, '__file__'):
                p = os.path.abspath (mod.__file__)
                if os.path.commonprefix ([p, my_dir]) == my_dir:
                    debug ("Reloading %s"%key)
                    reload (mod)
    Common.state.idle ()


def exception ():
    
    """ This function handles any exception derived from Exception and
    prints it out in a message box.  Code merrily stolen from the
    Thinking in Python site."""
    
    try:
        type, value, tb = sys.exc_info ()
        info = traceback.extract_tb (tb)
        filename, lineno, function, text = info[-1] # last line only
        print_err ("Exception: %s:%d: %s: %s (in %s)" %\
                   (filename, lineno, type.__name__, str (value), function))
    finally:
        type = value = tb = None # clean up
        

def find_scripts (s_dir="Modules", extra_dirs=None, no_base=0):
    """Finds all scripts in the directory specified in the
    argument.

    Keyword arguments:

    extra_dirs -- List of directories to search for additional
    modules/filters.  Defaults to None.

    no_base -- If true, does not search for modules and filters inside
    the base directory.  Defaults to false.
    
    """    
    debug ("In find_scripts ()")
    # this handles frozen installs made using the Python Installer,
    home, exe = os.path.split (sys.executable)
    if string.lower (exe[:6]) == 'python' or \
       string.lower(exe[:9]) == 'vtkpython':
        base_dir = os.path.abspath (os.path.dirname (Common.__file__))
    else:
        base_dir = os.path.abspath (home)

    if not no_base:
        lst = glob.glob ("%s/%s/*.py"%(base_dir, s_dir))
    else:
        lst = []

    if extra_dirs is not None:
        for dd in extra_dirs:
            lst.extend(glob.glob ("%s/%s/*.py"%(dd, s_dir)))

    ret = []
    for name in lst:
        i = os.path.basename (name)
        ret.append (os.path.splitext (i)[0])
    try:
        ret.remove ("__init__")
    except ValueError:
        pass
    ret.sort ()
    return ret


def find_hot_key (name_list):    
    """This computes a hot key for each name in the list, this is used
    in the menu generation."""    
    debug ("In find_hot_key ()")
    hot_key = []
    done_list = []
    for name in name_list:
        name1 = string.lower (name)
        done = 0
        for i in range (len (name1)):
            if name1[i] not in done_list:
                hot_key.append (i)
                done_list.append (name1[i])
                done = 1
                break
        if not done:
            hot_key.append (-1)
            
    return hot_key

def check_file (file_name):
    
    """Checks if given file name exists or not. Returns 1 if file
    exists 0 if not."""

    if not file_name:
        return 0
    elif os.path.isfile (file_name):
        return 1
    else:
        msg = "Sorry, file: %s, does not exist."%file_name
        print_err (msg)
        return 0


class MayaVi:
    
    """ This is the main MayaVi class.  This does all the dirty stuff.
    The GUI class merely wraps around this."""

    n_app = 0
    def __init__ (self, gui): 
        debug ("In MayaVi::__init__ ()")
        self.gui = gui
        MayaVi.n_app = MayaVi.n_app + 1
        n = MayaVi.n_app

        self.data_viz_mgr = {}
        self.dvm_name = []
        self.cur_dvm_name = ""
        self.n_dvm = 0
        self.first_module = 1
        
        # vrml files
        self.vrml_files = {}
        self.n_vrml = 0

        # 3D Studio files.
        self.tds_files = {}
        self.n_tds = 0

    def __del__ (self):
        debug ("In MayaVi::__del__ ()")

    def get_current_dvm (self):
        "Returns the currently active dvm."
        debug ("In MayaVi::get_current_dvm ()")
        dvm = None
        if self.cur_dvm_name:
            dvm = self.data_viz_mgr[self.cur_dvm_name]
        return dvm

    def get_current_dvm_name (self):
        debug ("In MayaVi::get_current_dvm_name ()")
        return self.cur_dvm_name

    def get_dvm_names (self):
        debug ("In MayaVi::get_dvm_names ()")
        return self.dvm_name

    def get_current_file_name (self):
        debug ("In MayaVi::get_current_file_name ()")
        f_name = ""
        if self.cur_dvm_name:
            dvm = self.data_viz_mgr[self.cur_dvm_name]
            f_name = dvm.get_data_source ().get_file_name ()
        return f_name

    def has_active_dvm (self):
        debug("In MayaVi::has_dvm ()")
        if (not self.dvm_name) or (not self.cur_dvm_name):
            return 0
        else:
            return 1

    def get_n_vrml (self):
        debug("In MayaVi::get_n_vrml ()")
        return self.n_vrml

    def get_n_3ds (self):
        debug("In MayaVi::get_n_3ds ()")
        return self.n_tds

    def Render(self):
        debug ("In MayaVi::Render ()")
        self.gui.Render()

    def open_vtk (self, file_name, config=1): 
        """Open a VTK data file."""
        if not file_name:
            return
        try:
            rw = self.gui.get_render_window()
            data = Sources.VtkDataReader.VtkDataReader (rw)
            dvm = Base.DataVizManager.DataVizManager (data, rw)
            self.add_dvm (dvm)
            Common.state.busy ()
            data.initialize (file_name)
            self.gui.update_label ()
            Common.state.idle ()
            if config:
                data.configure (self.gui.root)
            dvm.add_module_mgr_gui ()
            return data
        except Exception, v:
            exception ()
            Common.state.force_idle ()

    def open_vtk_xml (self, file_name, config=1): 
        """Open a VTK XML data file."""
        if not file_name:
            return
        try:
            rw = self.gui.get_render_window()
            data = Sources.VtkXMLDataReader.VtkXMLDataReader (rw)
            dvm = Base.DataVizManager.DataVizManager (data, rw)
            self.add_dvm (dvm)
            Common.state.busy ()
            data.initialize (file_name)
            self.gui.update_label ()
            Common.state.idle ()
            if config:
                data.configure (self.gui.root)
            dvm.add_module_mgr_gui ()
            return data
        except Exception, v:
            exception ()
            Common.state.force_idle ()

    def open_vtk_data (self, obj):
        """Open a VTK data object - this creates a VtkData Source
        object.  It returns a VtkData instance.
        Input Arguments:
           obj -- This must be a VTK data object, vtkStructuredGrid,
                  vtkStructuredPoints, vtkRectilinearGrid,
                  vtkUnstructuredGrid, vtkPolyData (or the
                  corresponding reader) are all acceptable.
        """
        try:
            rw = self.gui.get_render_window()
            data = Sources.VtkData.VtkData (rw)
            dvm = Base.DataVizManager.DataVizManager (data, rw)
            self.add_dvm (dvm)
            Common.state.busy ()
            data.initialize (obj)
            self.gui.update_label ()
            Common.state.idle ()
            dvm.add_module_mgr_gui ()
            return data
        except Exception, v:
            exception ()
            Common.state.force_idle ()

    def open_plot3d (self, xyz_name, q_name="", multi=0, config=1):
        """Open a PLOT3D single-block data file."""
        debug ("In MayaVi::open_plot3d ()")
        if xyz_name == "":
            return
        try:
            rw = self.gui.get_render_window()
            data = Sources.PLOT3DReader.PLOT3DReader (rw)
            dvm = Base.DataVizManager.DataVizManager (data, rw)
            self.add_dvm (dvm)
            Common.state.busy ()
            data.initialize (xyz_name, q_name, multi)
            self.gui.update_label ()
            Common.state.idle ()
            if config:
                data.configure (self.gui.root)
            dvm.add_module_mgr_gui ()
            return data
        except Exception, v:
            exception ()
            Common.state.force_idle ()

    def open_ensight (self, file_name, config=1): 
        """Open an EnSight data file."""
        if not file_name:
            return
        try:
            rw = self.gui.get_render_window()
            data = Sources.VtkEnSightReader.VtkEnSightReader (rw)
            dvm = Base.DataVizManager.DataVizManager (data, rw)
            self.add_dvm (dvm)
            Common.state.busy ()
            data.initialize (file_name)
            self.gui.update_label ()
            Common.state.idle ()
            if config:
                data.configure (self.gui.root)
            dvm.add_module_mgr_gui ()
            return data
        except Exception, v:
            exception ()
            Common.state.force_idle ()

    def open_vrml2 (self, file_name):
        """Open a VRML2 data file."""
        debug ("In MayaVi::open_vrml2 ()")
        if file_name != "": 
            try:
                Common.state.busy ()
                self.n_vrml = self.n_vrml + 1                
                name = "%d. %s"%(self.n_vrml, os.path.basename (file_name))
                rw = self.gui.get_render_window().get_vtk_render_window ()
                vrml_imp = Sources.VRMLImporter.VRMLImporter (rw, file_name)
                self.vrml_files[name] = vrml_imp
                self._do_render ()
                Common.state.idle ()
            except Exception, v:
                exception ()
                Common.state.force_idle ()
            return name

    def open_3ds (self, file_name):
        """Open a 3D Studio data file."""
        debug ("In MayaVi::open_3ds ()")
        if file_name != "": 
            try:
                Common.state.busy ()
                self.n_tds = self.n_tds + 1                
                name = "%d. %s"%(self.n_tds, os.path.basename (file_name))
                rw = self.gui.get_render_window().get_vtk_render_window ()
                imp = Sources.mv3DSImporter.mv3DSImporter (rw, file_name)
                self.tds_files[name] = imp
                self._do_render ()
                Common.state.idle ()
            except Exception, v:
                exception ()
                Common.state.force_idle ()
            return name
        
    def open_user(self, rdr_name, filename, config=1, *args, **kw_args):
        """Opens a file using a user defined reader.

        Note that this method assumes that the class name of the
        reader is the same as the name of the Python module that
        defines the reader.  The code also tries to check for a
        'filetypes' attribute in the module.  This is used when the
        file-dialog is opened.


        Input Arguments:

          rdr_name -- A string containing a valid Reader name.
                      If the reader name has a 'User.' prepended to it
                      then the module is first searched for in the
                      user specified search paths and then in the
                      default system directories.  The search path can
                      be specified like PYTHONPATH, and is a
                      ':'-separated string.  ~, ~user and $VAR are all
                      expanded.  The path can be specified in the
                      Preferences dialog.

          filename -- The file name of the file to open.
          
          config -- if non-zero it pops up the configuration GUI for
                    the Filter after it is loaded.

          args -- optional non-keyword arguments, these are simply
                  passed to the module constructor.
          
          kw_args -- optional keyword arguments, these are simply
                     passed to the module constructor.
        """
        debug ("In MayaVi::open_user ()")
	if not filename or not rdr_name:
	  return
        try:
	    rw = self.gui.get_render_window()
            _imp = Common.mod_fil_import
            if rdr_name[:5] == 'User.':
                rdr_scr = _imp('Sources', rdr_name[5:], globals(),
                               locals(), 1)
                rdr_name = rdr_name[5:]
            else:
                rdr_scr = _imp('Sources', rdr_name, globals(),
                               locals(), 0)
	    data = getattr(rdr_scr, rdr_name)(rw, *args, **kw_args)
	    dvm = Base.DataVizManager.DataVizManager (data, rw)
	    self.add_dvm(dvm)
            Common.state.busy ()
            data.initialize (filename)
            self.gui.update_label ()
            Common.state.idle ()
            if config:
                data.configure (self.gui.root)
	    dvm.add_module_mgr_gui()
            return data
        except Exception, v:
            exception ()
            Common.state.force_idle ()

    def add_dvm (self, dvm): 
        """ Add a new DataVizManager instance."""
        debug ("In MayaVi::add_dvm ()")
        self.n_dvm = self.n_dvm + 1
        dvm_name = '%d. %s'%(self.n_dvm, dvm.__class__.__name__)
        #dvm_name = dvm_name + '(%s)'%self.cur_file_name
        self.data_viz_mgr[dvm_name] = dvm
        self.dvm_name.append (dvm_name)
        self.gui.add_dvm (dvm_name)

    def del_dvm (self, key): 
        debug ("In MayaVi::del_dvm ()")
        if self.cur_dvm_name:
            old_dvm = self.data_viz_mgr[self.cur_dvm_name]
            old_dvm.close_gui ()
        try:
            self.data_viz_mgr[key].clear ()
            del self.data_viz_mgr[key]
        except KeyError:
            print_err ("Bad error: cannot delete DataVizManager with key",
                       key)
            return None
        indx = self.dvm_name.index (key)
        if len (self.dvm_name) > 1:
            if indx == 0:
                self.cur_dvm_name = self.dvm_name[indx + 1]
            else:
                self.cur_dvm_name = self.dvm_name[indx - 1]
        else:
            self.cur_dvm_name = ""
        del self.dvm_name[indx]        
        if not self.dvm_name:
            self.first_module = 1

    def config_data (self): 
        debug ("In MayaVi::config_data ()")
        if not self.cur_dvm_name:
            return
        dvm = self.data_viz_mgr[self.cur_dvm_name]
        dvm.get_data_source ().configure (self.gui.root)

    def show_dvm (self, dvm_name, force=0):
        """Shows the dvm with the name passed."""        
        debug ("In MayaVi::show_dvm ()")
        if not dvm_name:
            return
        if (self.cur_dvm_name != dvm_name) or (not self.cur_dvm_name) \
           or force:
            if self.cur_dvm_name:
                old_dvm = self.data_viz_mgr[self.cur_dvm_name]
                old_dvm.close_gui ()
            self.cur_dvm_name = dvm_name
            dvm = self.data_viz_mgr[self.cur_dvm_name]
            self.gui.create_dvm_gui(dvm)

    def _do_render (self):
        debug ("In MayaVi::_do_render ()")
        rw = self.gui.get_render_window()
        if self.first_module:
            rw.isometric_view ()
            self.first_module = 0
        else:
            rw.Render ()        

    def load_module (self, mod_name, config=1, *args, **kw_args):        
        """ Loads a MayaVi module given the following arguments.  

        Keyword arguments:

        mod_name -- Name of the module (a string).  If the module name
        has a 'User.' prepended to it then the module is first
        searched for in the user specified search paths and then in
        the default system directories.  The search path can be
        specified like PYTHONPATH, and is a ':'-separated string.  ~,
        ~user and $VAR are all expanded.  The path can be specified in
        the Preferences dialog.
        
        config -- If true (default) shows a configuration GUI for the
        module as soon as it is loaded.

        args -- Positional arguments passed on to the module's
        constructor.        

        kw_args -- Keyword arguments passed on to the module's
        constructor.
        """        
        debug ("In MayaVi::load_module ()")
        if not self.dvm_name:
            msg = "You need to have some data opened to be able to "\
                  "load a module.  Click on the 'File' menu to "\
                  "open some data."
            print_err (msg)
            return
        dvm = self.data_viz_mgr[self.cur_dvm_name]
        mm = dvm.get_current_module_mgr ()
        if not mm:
            msg = "You need to have an active ModuleManager to "\
                  "load a module.  Click on the 'New' button to "\
                  "create one or select an existing but inactive "\
                  "ModuleManager and click on the 'Show' button to "\
                  "activate it."
            print_err (msg)
            return
        try:
            Common.state.busy ()
            _imp = Common.mod_fil_import
            if mod_name[:5] == 'User.':
                mod_scr = _imp('Modules', mod_name[5:], globals(),
                               locals(), 1)
                mod_name = mod_name[5:]
            else:
                mod_scr = _imp('Modules', mod_name, globals(),
                               locals(), 0)
                
            m = eval ("mod_scr.%s"%mod_name)(mm, *args, **kw_args)

            mm.add_module_gui (m)
            if config:
                m.configure (self.gui.root)
            self._do_render ()
            Common.state.idle ()
            return m
        except Exception, v:
            exception ()
            Common.state.force_idle ()

    def load_filter (self, fil_name, config=1, *args, **kw_args):
        """ Loads a MayaVi filter given the following arguments.

        Keyword arguments:

        fil_name -- Name of the filter (a string).  If the filter name
        has a 'User.' prepended to it then the filter is first
        searched for in the user specified search paths and then in
        the default system directories.  The search path can be
        specified like PYTHONPATH, and is a ':'-separated string.  ~,
        ~user and $VAR are all expanded.  The path can be specified in
        the Preferences dialog.
        
        config -- If true (default) shows a configuration GUI for the
        module as soon as it is loaded.
        
        args -- Positional arguments passed on to the filter's
        constructor.
        
        kw_args -- Keyword arguments passed on to the filter's
        constructor.
        """        
        debug ("In MayaVi::load_filter ()")
        if not self.dvm_name:
            msg = "You need to have some data opened to be able to "\
                  "load a filter.  Click on the 'File' menu to "\
                  "open some data."
            print_err (msg)
            return
        dvm = self.data_viz_mgr[self.cur_dvm_name]
        mm = dvm.get_current_module_mgr ()
        if not mm:
            msg = "You need to have an active ModuleManager to "\
                  "load a filter.  Click on the 'New' button to "\
                  "create one or select an existing but inactive "\
                  "ModuleManager and click on the 'Show' button to "\
                  "activate it."
            print_err (msg)
            return
        try:
            Common.state.busy ()
            _imp = Common.mod_fil_import
            if fil_name[:5] == 'User.':
                fil_name = fil_name[5:]
                fil_scr = _imp("Filters", fil_name, globals(),
                               locals (), 1)
                f = eval ("fil_scr.%s"%fil_name)(mm, *args, **kw_args)
            elif fil_name[:12] == 'UserDefined:':
                name = fil_name[:11]
                fil_scr = _imp("Filters", name, globals(),
                               locals (), 0)
                vtk_fil = fil_name[12:]
                f = eval ("fil_scr.%s (mm, vtk_fil, *args, **kw_args)"%fil_name[:11])
            else:
                fil_scr = _imp("Filters", fil_name, globals(),
                               locals (), 0)
                f = eval ("fil_scr.%s"%fil_name)(mm, *args, **kw_args)
            
            mm.add_filter_gui (f)
            if config:
                f.configure (self.gui.root)
            self.Render ()
            Common.state.idle ()
            return f
        except Exception, v:
            exception ()
            Common.state.force_idle ()

    def load_current_mm (self, file_name): 
        debug ("In MayaVi::load_current_mm ()")
        if (not self.dvm_name) or (not self.cur_dvm_name):
            return
        dvm = self.data_viz_mgr[self.cur_dvm_name]
        mm = dvm.get_current_module_mgr ()
        if not mm:
            return
        if not file_name:
            return
        try:
            Common.state.busy ()
            f = open (file_name, 'r')
            dvm.load_current_module_mgr (f)
            self._do_render ()
            Common.state.idle ()
        except Exception, v:
            exception ()
            Common.state.force_idle ()

    def load_mm (self, file_name): 
        debug ("In MayaVi::load_mm ()")
        if (not self.dvm_name) or (not self.cur_dvm_name):
            return
        dvm = self.data_viz_mgr[self.cur_dvm_name]
        if not file_name or not os.path.isfile (file_name):
            try:
                dvm.add_module_mgr_gui ()
            except Exception, v:
                exception ()
            return
        try:
            Common.state.busy ()
            f = open (file_name, 'r')        
            dvm.load_config (f)
            self._do_render ()
            Common.state.idle ()
        except Exception, v:
            exception ()
            Common.state.force_idle ()

    def save_current_mm (self, file_name): 
        debug ("In MayaVi::save_current_mm ()")
        if (not self.dvm_name) or (not self.cur_dvm_name):
            return
        dvm = self.data_viz_mgr[self.cur_dvm_name]
        mm = dvm.get_current_module_mgr ()
        if not mm:
            return
        if not file_name:
            return
        try:
            Common.state.busy ()
            f = open (file_name, 'w')
            dvm.save_current_module_mgr (f)
            Common.state.idle ()
        except Exception, v:
            exception ()
            Common.state.force_idle ()

    def save_all_mm (self, file_name): 
        debug ("In MayaVi::save_all_mm ()")
        if (not self.dvm_name) or (not self.cur_dvm_name):
            return
        dvm = self.data_viz_mgr[self.cur_dvm_name]
        if not file_name:
            return
        try:
            Common.state.busy ()
            f = open (file_name, 'w')
            dvm.save_config (f)
            Common.state.idle ()
        except Exception, v:
            exception ()
            Common.state.force_idle ()

    def _write_msg (self, file, msg): 
        file.write (msg)
        debug (msg)

    def _read_msg (self, file):
        debug (file.readline ())

    def save_current_dvm (self, file_name): 
        debug ("In MayaVi::save_current_dvm ()")
        if (not self.dvm_name) or (not self.cur_dvm_name):
            return
        if not file_name:
            return        
        try:
            Common.state.busy ()
            file = open (file_name, 'w')
            self._write_msg (file, "### DataVizManagers ###\n")
            file.write ("1\n")
            self._write_msg (file, "### %s ###\n"%self.cur_dvm_name)
            dvm = self.data_viz_mgr[self.cur_dvm_name]
            data_src = dvm.get_data_source ()
            d_name = data_src.__class__.__name__
            if data_src.__module__.find('Sources.') > -1:
                # standard source.                
                self._write_msg (file, "### %s ###\n"%d_name)
                file.write (d_name+'\n')
                data_src.save_config (file)
                self._write_msg (file, "### End of %s ###\n"%d_name)
            else:
                self._write_msg (file, "### User.%s ###\n"%d_name)
                file.write ("User.%s\n"%d_name)            
                data_src.save_config (file)
                self._write_msg (file, "### End of User.%s ###\n"%d_name)

            dvm.save_config (file)
            self._write_msg (file, "### End of %s ###\n"%self.cur_dvm_name)
            self._write_msg (file, "### End of DataVizManagers ###\n")
            self._write_msg (file, "### RenderWindow ###\n")
            rw = self.gui.get_render_window()
            rw.save_config (file)
            self._write_msg (file, "### End of RenderWindow ###\n")
            Common.state.idle ()
        except Exception, v:
            exception ()
            Common.state.force_idle ()

    def save_visualization (self, file_name): 
        debug ("In MayaVi::save_visualization ()")
        if (not self.dvm_name) or (not self.cur_dvm_name):
            return
        if not file_name:
            return

        try:
            Common.state.busy ()
            file = open (file_name, 'w')
        
            self._write_msg (file, "### DataVizManagers ###\n")
            file.write ("%d\n"%len (self.dvm_name))
            for dvm_name in self.dvm_name:
                self._write_msg (file, "### %s ###\n"%dvm_name)
                dvm = self.data_viz_mgr[dvm_name]
                data_src = dvm.get_data_source ()
                d_name = data_src.__class__.__name__
                if data_src.__module__.find('Sources.') > -1:
                    # standard source.                
                    self._write_msg (file, "### %s ###\n"%d_name)
                    file.write (d_name+'\n')
                    data_src.save_config (file)
                    self._write_msg (file, "### End of %s ###\n"%d_name)
                else:
                    self._write_msg (file, "### User.%s ###\n"%d_name)
                    file.write ("User.%s\n"%d_name)            
                    data_src.save_config (file)
                    self._write_msg (file, "### End of User.%s ###\n"%d_name)

                dvm.save_config (file)
                self._write_msg (file, "### End of %s ###\n"%dvm_name)
            self._write_msg (file, "### End of DataVizManagers ###\n")
            self._write_msg (file, "### RenderWindow ###\n")
            rw = self.gui.get_render_window()
            rw.save_config (file)
            self._write_msg (file, "### End of RenderWindow ###\n")
            Common.state.idle ()
        except Exception, v:
            exception ()
            Common.state.force_idle ()

    def load_visualization (self, file_name): 
        debug ("In MayaVi::load_visualization ()")
        if not file_name:
            return

        try:
            Common.state.busy ()
            rw = self.gui.get_render_window()
            file = open (file_name, 'r')
            tmp = file.readline ()
            debug (tmp)
            if tmp != "### DataVizManagers ###\n":
                msg = "Error: Expected data for DataVizManagers not "\
                      "found.  You have possibly chosen the wrong file."
                raise Base.Objects.ParseException, msg
            n = int (file.readline ())
            for i in range (n):
                self._read_msg (file)
                self._read_msg (file)
                name = file.readline ()[:-1]
                if name[:5] == 'User.':
                    name = name[5:]
                    data_mod = Common.mod_fil_import('Sources', name,
                                                     globals(), locals(), 1)
                    data_src = eval ("data_mod.%s(rw)"%name)
                else:
                    data_src = eval ("Sources.%s.%s(rw)"%(name, name))
                data_src.load_config (file)
                self._read_msg (file)
                dvm = Base.DataVizManager.DataVizManager (data_src, rw)
                self.add_dvm (dvm)
                dvm.load_config (file)
                self._read_msg (file)
            self._read_msg (file)
            self._read_msg (file)
            rw.load_config (file)
            self._read_msg (file)
            
            if self.first_module:
                self.first_module = 0
            self.Render ()
            Common.state.idle ()
        except Exception, v:
            exception ()
            Common.state.force_idle ()

    def close_all (self): 
        debug ("In MayaVi::close_all ()")
        if self.cur_dvm_name:
            old_dvm = self.data_viz_mgr[self.cur_dvm_name]
            old_dvm.close_gui ()
        for dvm_name in self.dvm_name:
            self.data_viz_mgr[dvm_name].clear ()
            del self.data_viz_mgr[dvm_name]
        self.dvm_name = []
        self.cur_dvm_name = ""
        self.n_dvm = 0
        for key in self.vrml_files.keys ():
            del self.vrml_files[key]
        for key in self.tds_files.keys ():
            del self.tds_files[key]
        self.first_module = 1
        self.n_vrml = 0
        self.n_tds = 0
        
    def close_vrml (self, name):
        debug ("In MayaVi::close_vrml ()")
        Common.state.busy ()
        del self.vrml_files[name]
        Common.state.idle ()

    def close_3ds (self, name):
        debug ("In MayaVi::close_3ds ()")
        Common.state.busy ()
        del self.tds_files[name]
        Common.state.idle ()

    def fg_color_changed (self):
        debug ("In MayaVi::fg_color_changed ()")
        Common.state.busy ()
        for dvm in self.data_viz_mgr.values ():
            dvm.config_changed ()
        self.Render ()
        Common.state.idle ()

    def reload_modules (self):
        debug ("In MayaVi::reload_modules ()")
        reload_all_modules ()

    def quit (self, event=None): 
        debug ("In MayaVi::quit ()")
        del self.vrml_files
        del self.tds_files
        MayaVi.n_app = MayaVi.n_app - 1


class DocHelper:
    """Handles the help menu related stuff."""

    def __init__ (self):
        home, exe = os.path.split (sys.executable)
        if string.lower (exe[:6]) == 'python':
            base_dir = os.path.abspath (os.path.dirname (Common.__file__))
        else:
            base_dir = os.path.abspath (home)

        # online docs -- default.
        self.guide = "http://mayavi.sourceforge.net/docs/guide/index.html"
        # for binaries and inside the source dir (CVS) based installs
        guide_dirs = [os.path.join (base_dir, 'doc')]
        # Debian
        guide_dirs.extend (glob.glob ("/usr/share/doc/mayavi*"))
        # Redhat
        guide_dirs.extend (glob.glob ("/usr/share/doc/MayaVi*"))
        # Add more relavant directories if the docs are elsewhere.
        for d in guide_dirs:
            g = os.path.join (d, 'guide', 'index.html')
            if os.path.isfile (g):
                self.guide = g
                break
        
        self.has_webbrowser = 1
        try:
            import webbrowser
        except ImportError:
            self.has_webbrowser = 0

        self.fail_msg = "Unable to import the webbrowser module. Please"\
                        " upgrade Python to version 2.0 or above.\n\n"

    def show_about_msg (self):
        msg = "The MayaVi Data Visualizer\n\n"\
              "A free, powerful, scientific data visualizer written "\
              "in Python.\n\n"\
              "Version: %s\n\n"\
              "License: BSD\n\n"\
              "Home page: http://mayavi.sourceforge.net\n\n"\
              "(c) Prabhu Ramachandran, 2000-2005\n"%(version,)
        return tkMessageBox.showinfo ("About MayaVi", msg)

    def show_home_page (self):
        if self.has_webbrowser:
            import webbrowser
            Common.state.busy ()
            webbrowser.open ("http://mayavi.sourceforge.net", 1)
            Common.state.idle ()
        else:
            msg = self.fail_msg + \
                  "The MayaVi home page is at:\n\n"\
                  "http://mayavi.sourceforge.net"             
            return tkMessageBox.showinfo("MayaVi home page", msg)

    def show_user_guide (self):
        if self.has_webbrowser:
            import webbrowser
            Common.state.busy ()
            webbrowser.open (self.guide, 1)
            Common.state.idle ()
        else:
            msg = self.fail_msg + \
                  "The MayaVi User guide should be available "\
                  "here:\n%s"%self.guide
            return tkMessageBox.showinfo ("MayaVi users guide", msg)        


class MayaViTkGUI:
    """ This is the main application and creates the GUI and controls
    everything."""

    def __init__ (self, master, geometry=None, root=None):
        """
        Constructor for the main MayaVi GUI window.
        
        Keyword Arguments:

        master -- Toplevel parentwindow.        

        geometry -- The geometry of the main window in standard X
        fashion (WxH+X+Y).

        root -- The root window into which MayaVi's GUI should be
        created.  This defaults to `None` in which case a new
        `Tkinter.Toplevel` widget is created.

        """
        debug ("In MayaViTkGUI::__init__ ()")
        self.master = master
        if not root:
            self.root = Tkinter.Toplevel (master)
        else:
            self.root = root
        self.mayavi = MayaVi (self)
        self.doc_helper = DocHelper ()
        
        n = MayaVi.n_app
        self.root.title ("MayaVi Data Visualizer %d"%n)
        self.root.protocol ("WM_DELETE_WINDOW", self.quit)
        if geometry:
            self.root.geometry(geometry)
        self.root.minsize (650, 600)
        #self.root.geometry ("600x600+0+0")
        master_f = Tkinter.Frame (self.root, relief='sunken', bd=2)
        master_f.pack (side='top', fill='both', expand=1)

        self.ctrl_frame = Tkinter.Frame (master_f, relief='sunken', bd=2)
        self.ctrl_frame.pack (side='left', fill='y', expand=0)

        self.renwin_frame = Tkinter.Frame (master_f)
        self.renwin_frame.pack (side='left', fill='both', expand=1)
        self.renwin = Misc.RenderWindow.RenderWindow (self.renwin_frame)
        self.renwin.Render ()

        self.status_frame = Tkinter.Frame (self.root, relief='sunken', bd=2,
                                           bg='white', height=20)
        self.status_frame.pack (side='bottom', fill='x', expand=0)
        
        Common.state.register (self.status_frame)
        Common.state.register (self.root)
        
        self.module_var = Tkinter.StringVar ()
        self.filter_var = Tkinter.StringVar ()
        self.reader_var = Tkinter.StringVar ()

        self.vrml_var = Tkinter.StringVar ()

        # for animation. -1 == unset, 0 == stopped, 1 == running
        self.anim = -1

        # 3D Studio files.
        self.tds_var = Tkinter.StringVar ()

        self.full_scr_var = Tkinter.IntVar ()
        self.full_scr_var.set (1)

        self.make_menus ()
        self.make_data_list ()

    def __del__ (self):
        debug ("In MayaViTkGUI::__del__ ()")

    def get_render_window(self):
        "Returns the render window used."
        debug ("In MayaViTkGUI::get_render_window ()")
        return self.renwin

    def Render(self):
        debug ("In MayaViTkGUI::Render ()")
        self.renwin.Render ()

    def make_menus (self): 
        debug ("In MayaViTkGUI::make_menus ()")
        self.menu = Tkinter.Menu (self.root, tearoff=0)
        self.root.config (menu=self.menu)

        self.file_menu = Tkinter.Menu (self.menu, name='file', tearoff=0)
        self.menu.add_cascade (label="File", menu=self.file_menu, 
                               underline=0)
        self.viz_menu = Tkinter.Menu (self.menu, name='visualize',
                                      tearoff=0)
        self.menu.add_cascade (label="Visualize", menu=self.viz_menu,
                               underline=0)
        self.option_menu = Tkinter.Menu (self.menu, name='options',
                                         tearoff=0)
        self.menu.add_cascade (label="Options", menu=self.option_menu,
                               underline=0)
        self.help_menu = Tkinter.Menu (self.menu, name='help', tearoff=0)
        self.menu.add_cascade (label="Help", menu=self.help_menu,
                               underline=0)

        ## File menus
        self.file_menu.add_command (label="New Window", underline=0, 
                                    command=self.new_window)        

        self.open_menu = Tkinter.Menu (self.file_menu, tearoff=0)
        self.file_menu.add_cascade (label="Open", underline=0,
                                    menu=self.open_menu)

        self.import_menu = Tkinter.Menu (self.file_menu, tearoff=0)
        self.file_menu.add_cascade (label="Import", underline=0,
                                    menu=self.import_menu)

        self.load_menu = Tkinter.Menu (self.file_menu, tearoff=0)
        self.file_menu.add_cascade (label="Load", underline=0,
                                    menu=self.load_menu)

        self.save_menu = Tkinter.Menu (self.file_menu, tearoff=0)
        self.file_menu.add_cascade (label="Save", underline=0,
                                    menu=self.save_menu)
        
        self.sshot_menu = Tkinter.Menu (self.file_menu, tearoff=0)
        self.file_menu.add_cascade (label="Save Scene to", underline=1, 
                                    menu=self.sshot_menu)

        self.close_menu = Tkinter.Menu (self.file_menu, tearoff=0)
        self.file_menu.add_cascade (label="Close", underline=0,
                                    menu=self.close_menu)
        self.file_menu.add_command (label="Close All", underline=4,
                                    command=self.close_all)
        self.file_menu.add_command (label="Exit", underline=1, 
                                    command=self.quit)
	self.make_open_menu()        

        ## Import menu
        self.import_menu.add_command (label="VRML2 scene",
                                      underline=0,
                                      command=self.open_vrml2_gui)
        self.import_menu.add_command (label="3D Studio scene",
                                      underline=0,
                                      command=self.open_3ds_gui)
        
        ## Plot3d menu
        self.pl3d_menu.add_command (label="Single-block file", underline=0,
                                    command=self.open_plot3d)
        self.pl3d_menu.add_command (label="Multi-block file", underline=0,
                                    command=self.open_plot3d_multi)        

        ## Load menu
        self.load_menu.add_command (label="Visualization",
                                    underline=0,
                                    command=self.load_visualization)
        self.load_menu.add_command (label="ModuleManagers",
                                    underline=0,
                                    command=self.load_mm)
        self.load_menu.add_command (label="ModuleManagers (Append)",
                                    underline=16,
                                    command=self.load_current_mm)

        ## close menu
        self.close_menu.add_command (label="Current DataVizManager",
                                     underline=0,
                                     command=self.del_dvm_gui)
        self.vrml_close_menu = Tkinter.Menu (self.close_menu, tearoff=0)
        self.close_menu.add_cascade (label="VRML2 file", underline=0,
                                     menu=self.vrml_close_menu)
        self.tds_close_menu = Tkinter.Menu (self.close_menu, tearoff=0)
        self.close_menu.add_cascade (label="3D Studio file", underline=0,
                                     menu=self.tds_close_menu)
        
        ## Save menu
        self.save_menu.add_command (label="Entire Visualization",
                                    underline=0,
                                    command=self.save_visualization)
        self.save_menu.add_command (label="Current DataVizManager",
                                    underline=0,
                                    command=self.save_current_dvm)
        self.save_menu.add_command (label="Current ModuleManager",
                                    underline=0,
                                    command=self.save_current_mm)
        self.save_menu.add_command (label="All ModuleManagers",
                                    underline=0,
                                    command=self.save_all_mm)
        ## Save Scene menus
        self.sshot_menu.add_command (label="PostScript image", underline=0,
                                     command=self.renwin.save_ps)
        self.sshot_menu.add_command (label="PPM image", underline=2,
                                     command=self.renwin.save_ppm)
        self.sshot_menu.add_command (label="BMP image", underline=0,
                                     command=self.renwin.save_bmp)
        self.sshot_menu.add_command (label="TIFF image", underline=0,
                                     command=self.renwin.save_tiff)
        self.sshot_menu.add_command (label="JPEG image", underline=0,
                                     command=self.renwin.save_jpg)
        self.sshot_menu.add_command (label="PNG image", underline=1,
                                     command=self.renwin.save_png)
        self.sshot_menu.add_command (label="OpenInventor", underline=0,
                                     command=self.renwin.save_iv)
        self.sshot_menu.add_command (label="Geomview", underline=0,
                                     command=self.renwin.save_oogl)
        self.sshot_menu.add_command (label="VRML", underline=0,
                                     command=self.renwin.save_vrml)
        self.sshot_menu.add_command (label="RenderMan RIB", underline=0,
                                     command=self.renwin.save_rib)
        self.sshot_menu.add_command (label="Vector PS/EPS/PDF/TeX (GL2PS)",
                                     underline=1,
                                     command=self.renwin.save_gl2ps)
        self.sshot_menu.add_command (label="Wavefront OBJ", underline=0,
                                     command=self.renwin.save_wavefront)

        ## Visualize menus
        self.module_menu = Tkinter.Menu (self.viz_menu, tearoff=0)
        self.viz_menu.add_cascade (label="Modules", underline=0,
                                   menu=self.module_menu)
        self.filter_menu = Tkinter.Menu (self.viz_menu, tearoff=0)
        self.viz_menu.add_cascade (label="Filters", underline=0,
                                   menu=self.filter_menu)

        self.make_module_menu ()
        self.make_filter_menu ()
        self.viz_menu.add_command (label="Pipeline browser", underline=0,
                                   command=self.pipeline_browse)

        ## Option menus
        self.option_menu.add_command (label="Preferences", underline=0,
                                      command=self.edit_prefs)
        self.option_menu.add_command (label="Configure RenderWindow",
                                      underline=16,
                                      command=self.config_renwin)
        self.option_menu.add_command (label="Change Foreground",
                                      underline=7,
                                      command=self.set_fg_color)
        self.option_menu.add_command (label="Change Background",
                                      underline=7,
                                      command=self.set_bg_color)
        self.option_menu.add_command (label="Configure Lights",
                                      underline=10,
                                      command=self.renwin.config_lights)
        self.option_menu.add_command (label="Show Debug Window",
                                      underline=5,
                                      command=self.show_log_win)
        self.option_menu.add_checkbutton (label="Show Control Panel",
                                          underline=5,
                                          onvalue=1, offvalue=0,
                                          variable=self.full_scr_var,
                                          command=self.show_ctrl_panel)
        self.option_menu.add_command (label="Reload Modules",
                                      underline=0,
                                      command=self.reload_modules)
        ## Help menu
        self.help_menu.add_command (label="About",
                                    underline=0,
                                    command=self.doc_helper.show_about_msg)
        self.help_menu.add_command (label="Users Guide",
                                    underline=0,
                                    command=self.doc_helper.show_user_guide)
        self.help_menu.add_command (label="Home page",
                                    underline=0,
                                    command=self.doc_helper.show_home_page)

    def make_open_menu(self):
        ## Open menu
        self.open_menu.add_command (label="VTK file", underline=0,
                                    command=self.open_vtk)
        self.open_menu.add_command (label="VTK XML file", underline=4,
                                    command=self.open_vtk_xml)
        self.open_menu.add_command (label="EnSight case file", underline=0,
                                    command=self.open_ensight)
        self.pl3d_menu = Tkinter.Menu (self.open_menu, tearoff=0)
        self.open_menu.add_cascade (label="PLOT3D file", underline=1,
                                    menu=self.pl3d_menu)

        ## Support for user defined readers.
	rdr_list = find_scripts("Sources", Common.config.upath, no_base=1)
	rdr_list.insert(0, 'User')
	hk_list = find_hot_key(rdr_list)

	self.user_reader_menu = Tkinter.Menu(self.open_menu, tearoff=0)
	self.open_menu.add_cascade(label="User", underline=hk_list[0],
					menu=self.user_reader_menu)

	for i in range(1, len(rdr_list) ):
	  rdr = rdr_list[i]
	  hk = hk_list[i]
	  self.user_reader_menu.add_radiobutton( label=rdr,
						 value='User.'+rdr,
						 variable=self.reader_var,
						 indicatoron=0,
						 underline=hk,
						 command=self.open_user)

    def make_module_menu (self):
        debug ("In MayaViTkGUI::make_module_menu ()")
        mod_list = find_scripts ("Modules")
        mod_list.insert(0, 'User')
        hk_list = find_hot_key (mod_list)
        for i in range (1, len (mod_list)):
            mod = mod_list[i]
            hk = hk_list[i]
            self.module_menu.add_radiobutton (label=mod, value=mod,
                                              variable=self.module_var,
                                              indicatoron=0, underline=hk,
                                              command=self.load_module)
        
        self.user_module_menu = Tkinter.Menu (self.viz_menu, tearoff=0)
        self.module_menu.add_cascade (label="User", underline=hk_list[0],
                                      menu=self.user_module_menu)
        
        mod_list = find_scripts ("Modules", Common.config.upath, no_base=1)
        hk_list = find_hot_key (mod_list)        
        for i in range (len (mod_list)):
            mod = mod_list[i]
            hk = hk_list[i]
            self.user_module_menu.add_radiobutton (label=mod,
                                                   value='User.'+mod,
                                                   variable=self.module_var,
                                                   indicatoron=0,
                                                   underline=hk,
                                                   command=self.load_module)

    def make_filter_menu (self):
        debug ("In MayaViTkGUI::make_filter_menu ()")
        fil_list = find_scripts ("Filters")
        fil_list.insert(0, 'User')
        hk_list = find_hot_key (fil_list)
        for i in range (1, len (fil_list)):
            fil = fil_list[i]
            hk = hk_list[i]
            self.filter_menu.add_radiobutton (label=fil, value=fil,
                                              variable=self.filter_var,
                                              indicatoron=0, underline=hk,
                                              command=self.load_filter)

        self.user_filter_menu = Tkinter.Menu (self.viz_menu, tearoff=0)
        self.filter_menu.add_cascade (label="User", underline=hk_list[0],
                                      menu=self.user_filter_menu)
        
        fil_list = find_scripts ("Filters", Common.config.upath, no_base=1)
        hk_list = find_hot_key (fil_list)        
        for i in range (len (fil_list)):
            fil = fil_list[i]
            hk = hk_list[i]
            self.user_filter_menu.add_radiobutton (label=fil,
                                                   value='User.'+fil,
                                                   variable=self.filter_var,
                                                   indicatoron=0,
                                                   underline=hk,
                                                   command=self.load_filter)

    def make_data_list (self): 
        debug ("In MayaViTkGUI::make_data_list ()")
        frame = Tkinter.Frame (self.ctrl_frame)
        frame.pack (side='top', fill='y', expand=0)
        scr = Tkinter.Scrollbar (frame, orient='vertical')
        self.dvm_lst = Tkinter.Listbox (frame, yscrollcommand=scr.set, 
                                        selectmode='single', height=3,
                                        exportselection=0)
        scr.config (command=self.dvm_lst.yview)
        self.dvm_lst.grid (row=0, column=0, sticky='ewns')
        scr.grid (row=0, column=1, sticky='ns')
        self.dvm_lst.bind ("<Double-Button-1>", self.show_dvm)

        but_f = Tkinter.Frame (self.ctrl_frame)
        but_f.pack (side='top', fill='y', expand=0)
        but1 = Tkinter.Button (but_f, text="Configure Data",
                               command=self.config_data)
        but1.grid (row=0, column=0, sticky="ew")
        but2 = Tkinter.Button (but_f, text="Show Pipeline",
                               command=self.show_dvm)
        but2.grid (row=0, column=1, sticky="ew")

        cur_dvm_name = self.mayavi.get_current_dvm_name ()
        lab = "DataVizManager: %s"%cur_dvm_name
        self.data_label = Tkinter.Label (but_f, text=lab)
        self.data_label.grid (row=1, column=0, columnspan=2, pady=0,
                              sticky='w')
        lab = "Filename: "
        self.f_name_label = Tkinter.Label (but_f, text=lab)
        self.f_name_label.grid (row=2, column=0, columnspan=2, pady=0,
                                sticky='w')

        dvm_names = self.mayavi.get_dvm_names()
        for dvm in dvm_names:
            self.dvm_lst.insert ('end', dvm)
        if cur_dvm_name:
            indx = dvm_names.index(cur_dvm_name)
            self.dvm_lst.activate (indx)
            
    def open_vtk (self, file_name="", config=1): 
        """Open a VTK data file.
        Input Arguments:
           file_name -- If passed opens the specified file else pops
                        a file chooser window.
           config -- If non-zero show configure window of relavant source.

        """
        debug ("In MayaViTkGUI::open_vtk ()")
        if not file_name:
            file_name = tk_fopen (title="Open VTK data file", 
                                  initialdir=Common.config.initial_dir,
                                  filetypes=[("VTK files", "*.vtk"), 
                                             ("All files", "*")])
        if check_file (file_name):
            return self.mayavi.open_vtk (file_name, config)

    def open_vtk_xml (self, file_name="", config=1): 
        """Open a VTK XML data file.
        Input Arguments:
           file_name -- If passed opens the specified file else pops
                        a file chooser window.
           config -- If non-zero show configure window of relavant source.

        """
        debug ("In MayaViTkGUI::open_vtk_xml ()")
        f_types = [("XML files", "*.xml"), ("Image Data", "*.vti"),
                   ("Poly Data", "*.vtp"), ("Rectilinear Grid", "*.vtr"),
                   ("Structured Grid", "*.vts"),
                   ("Unstructured Grid", "*.vtu"),
                   ("Parallel Image Data", "*.pvti"),
                   ("Parallel Poly Data", "*.pvtp"),
                   ("Parallel Rectilinear Grid", "*.pvtr"),
                   ("Parallel Structured Grid", "*.pvts"),
                   ("Parallel Unstructured Grid", "*.pvtu"),
                   ("All files", "*")]
        if not file_name:
            file_name = tk_fopen (title="Open VTK XML data file", 
                                  initialdir=Common.config.initial_dir,
                                  filetypes=f_types)
        if check_file (file_name):
            return self.mayavi.open_vtk_xml (file_name, config)

    def open_vtk_data (self, obj):
        """Open a VTK data object - this creates a VtkData Source
        object.  It returns a VtkData instance.
        Input Arguments:
           obj -- This must be a VTK data object, vtkStructuredGrid,
                  vtkStructuredPoints, vtkRectilinearGrid,
                  vtkUnstructuredGrid, vtkPolyData (or the
                  corresponding reader) are all acceptable.
        """
        debug ("In MayaViTkGUI::open_vtk_data ()")
        return self.mayavi.open_vtk_data (obj)

    def open_plot3d (self, xyz_name="", q_name="", config=1):
        """Open a PLOT3D single-block data file.
        Input Arguments:        
           xyz_name -- If passed opens the specified co-ordinate file
                       else pops a file chooser window.
           q_name -- The PLOT3D solution file
           config -- If non-zero show configure window of relavant source.

        """
        debug ("In MayaViTkGUI::open_plot3d ()")
        if not xyz_name:
            xyz_name = tk_fopen (title="Open XYZ Co-ordinate file", 
                                 initialdir=Common.config.initial_dir,
                                 filetypes=[("All files", "*")])
            if xyz_name != "":
                q_name = tk_fopen (title="Open Q Solution file",
                                   initialdir=Common.config.initial_dir,
                                   filetypes=[("All files", "*")])
                
        if q_name:
            check_file (q_name)
        
        if check_file (xyz_name):
            return self.mayavi.open_plot3d (xyz_name, q_name, multi=0,
                                            config=config)


    def open_plot3d_multi (self, xyz_name="", q_name="", config=1):
        """Open a PLOT3D multi-block data file.
        Input Arguments:        
           xyz_name -- If passed opens the specified co-ordinate file
                       else pops a file chooser window.
           q_name -- The PLOT3D solution file
           config -- If non-zero show configure window of relavant source.

        """
        debug ("In MayaViTkGUI::open_plot3d_multi ()")
        if not xyz_name:
            xyz_name = tk_fopen (title="Open XYZ Co-ordinate file", 
                                 initialdir=Common.config.initial_dir,
                                 filetypes=[("All files", "*")])
            if xyz_name != "":
                q_name = tk_fopen (title="Open Q Solution file",
                                   initialdir=Common.config.initial_dir,
                                   filetypes=[("All files", "*")])

        if q_name:
            check_file (q_name)
        
        if check_file (xyz_name):
            return self.mayavi.open_plot3d (xyz_name, q_name, multi=1,
                                            config=config)

    def open_ensight (self, file_name="", config=1): 
        """Open an EnSight data file.
        Input Arguments:
           file_name -- If passed opens the specified file else pops
                        a file chooser window.
           config -- If non-zero show configure window of relavant source.

        """
        debug ("In MayaViTkGUI::open_ensight ()")
        if not file_name:
            file_name = tk_fopen (title="Open EnSight case file", 
                                  initialdir=Common.config.initial_dir,
                                  filetypes=[("EnSight case files", "*.case"), 
                                             ("All files", "*")])
        if check_file (file_name):
            return self.mayavi.open_ensight (file_name, config)

    def open_vrml2 (self, file_name):
        """Open a VRML2 data file."""
        debug ("In MayaViTkGUI::open_vrml2 ()")
        if file_name != "": 
            name = self.mayavi.open_vrml2 (file_name)
            menu = self.vrml_close_menu
            menu.add_radiobutton (label=name, value=name,
                                  variable=self.vrml_var,
                                  indicatoron=0,
                                  command=self.close_vrml)        

    def open_vrml2_gui (self):
        """Open a VRML2 data file using a GUI file chooser."""
        debug ("In MayaViTkGUI::open_vrml2_gui ()")        
        file_name = tk_fopen (title="Open VRML2 file", 
                              initialdir=Common.config.initial_dir,
                              filetypes=[("VRML2 files", "*.wrl"), 
                                         ("All files", "*")])
        self.open_vrml2 (file_name)
        
    def open_3ds (self, file_name):
        """Open a 3D Studio data file."""
        debug ("In MayaViTkGUI::open_3ds ()")
        if file_name != "": 
            name = self.mayavi.open_3ds (file_name)
            menu = self.tds_close_menu
            menu.add_radiobutton (label=name, value=name,
                                  variable=self.tds_var,
                                  indicatoron=0,
                                  command=self.close_3ds)
 
    def open_3ds_gui (self):
        """Open a 3D Studio data file using a GUI file chooser."""
        debug ("In MayaViTkGUI::open_3ds_gui ()")
        file_name = tk_fopen (title="Open 3D Studio file", 
                              initialdir=Common.config.initial_dir,
                              filetypes=[("3D Studio files", "*.3ds"), 
                                         ("All files", "*")])
        self.open_3ds (file_name)

    def open_user_data(self, rdr_name="", obj=None, config=1,
                       *args, **kw_args):
        """Opens a data object using a user defined reader.

        Note that this method assumes that the class name of the
        reader is the same as the name of the Python module that
        defines the reader.  The code also tries to check for a
        'datatypes' attribute in the module.  This must be a list
        specifying the supported class names of the input data types.
        The reader must also support passing a data object instead of
        a file name.

        Input Arguments:

          rdr_name -- A string containing a valid Reader name.  If
                      this is empty, then the last value chosen via
                      the menu is used.  If the reader name has a
                      'User.' prepended to it then the module is first
                      searched for in the user specified search paths
                      and then in the default system directories.  The
                      search path can be specified like PYTHONPATH,
                      and is a ':'-separated string.  ~, ~user and
                      $VAR are all expanded.  The path can be
                      specified in the Preferences dialog.

          obj -- The data object to open.  Must be of a type listed in the
                 given readers datatypes attribute.

          config -- if non-zero it pops up the configuration GUI for
                    the Filter after it is loaded.

          args -- optional non-keyword arguments, these are simply
                  passed to the module constructor.

          kw_args -- optional keyword arguments, these are simply
                     passed to the module constructor.
        """
        if not rdr_name:
            rdr_name = self.reader_var.get()

        try:
            Common.state.busy ()
            _imp = Common.mod_fil_import
            if rdr_name[:5] == 'User.':
                rdr_scr = _imp('Sources', rdr_name[5:], globals(),
                               locals(), 1)
            else:
                rdr_scr = _imp('Sources', rdr_name, globals(),
                               locals(), 0)
            Common.state.idle ()
        except Exception, v:
            exception ()
            Common.state.force_idle ()
            return None

        if rdr_scr.__dict__.has_key('datatypes') and \
               obj.__class__.__name__ in rdr_scr.datatypes:
            return self.mayavi.open_user (rdr_name, obj, config,
                                          *args, **kw_args)
        else:
            msg = "Sorry, the datatype: %s,"\
                  " is not supported by the reader."%obj.__class__.__name__
            print_err (msg)
            return None

    def open_user(self, rdr_name="", filename="", config=1, *args, **kw_args):
        """Opens a file using a user defined reader.

        Note that this method assumes that the class name of the
        reader is the same as the name of the Python module that
        defines the reader.  The code also tries to check for a
        'filetypes' attribute in the module.  This is used when the
        file-dialog is opened.


        Input Arguments:

          rdr_name -- A string containing a valid Reader name.  If
                      this is empty, then the last value chosen via
                      the menu is used.  If the reader name has a
                      'User.' prepended to it then the module is first
                      searched for in the user specified search paths
                      and then in the default system directories.  The
                      search path can be specified like PYTHONPATH,
                      and is a ':'-separated string.  ~, ~user and
                      $VAR are all expanded.  The path can be
                      specified in the Preferences dialog.

          filename -- The file name of the file to open.  If not
                      specified a dialog box will pop up that lets you
                      choose the file.
          
          config -- if non-zero it pops up the configuration GUI for
                    the Filter after it is loaded.

          args -- optional non-keyword arguments, these are simply
                  passed to the module constructor.
          
          kw_args -- optional keyword arguments, these are simply
                     passed to the module constructor.
        """
        debug ("In MayaViTkGUI::open_user ()")

        if not rdr_name:
            rdr_name = self.reader_var.get()

        if not filename:
            # If no filename was specified try and open a dialog to
            # choose the file.
            try:
                Common.state.busy ()
                _imp = Common.mod_fil_import
                if rdr_name[:5] == 'User.':
                    rdr_scr = _imp('Sources', rdr_name[5:], globals(),
                                   locals(), 1)
                else:
                    rdr_scr = _imp('Sources', rdr_name, globals(),
                                   locals(), 0)
                Common.state.idle ()

            except Exception, v:
                exception ()
                Common.state.force_idle ()

            if rdr_scr.__dict__.has_key('filetypes'):
                rdr_filetypes = rdr_scr.filetypes
            else:
                rdr_filetypes = []
            rdr_filetypes.append(("All files", "*"))
            filename = tk_fopen (title="Open Data file",
                                 initialdir=Common.config.initial_dir,
                                 filetypes=rdr_filetypes)

        if check_file (filename):
            return self.mayavi.open_user (rdr_name, filename, config, 
                                          *args, **kw_args)

    def add_dvm (self, dvm_name): 
        """ Add a new DataVizManager to the GUI list."""
        debug ("In MayaViTkGUI::add_dvm ()")
        self.dvm_lst.insert ('end', dvm_name)
        self.dvm_lst.activate ('end')
        self.dvm_lst.select_clear (0, 'end')
        self.dvm_lst.select_set ('end')
        self.show_dvm ()

    def config_data (self, event=None): 
        debug ("In MayaViTkGUI::config_data ()")
        self.mayavi.config_data()

    def show_dvm (self, event=None, force=0): 
        debug ("In MayaViTkGUI::show_dvm ()")
        dvm_name = self.dvm_lst.get ('active')
        self.mayavi.show_dvm (dvm_name, force)
        self.update_label ()

    def create_dvm_gui(self, dvm):
        debug ("In MayaViTkGUI::create_dvm_gui ()")
        dvm.create_gui(self.ctrl_frame)

    def update_label (self): 
        debug ("In MayaViTkGUI::update_label ()")
        lab = "DataVizManager: %s"%self.mayavi.get_current_dvm_name()
        self.data_label.config (text=lab)
        f_name = self.mayavi.get_current_file_name()
        f_name = os.path.basename (f_name)
        lab = "Filename: %s"%f_name
        self.f_name_label.config (text=lab)        

    def load_module (self, mod_name="", config=1, *args, **kw_args):
        """Loads a Module.
        Input Arguments:
        
          mod_name -- A string containing a valid Module name.
          
          config -- if non-zero it pops up the configuration GUI for
                    the Module after it is loaded.

          args -- optional non-keyword arguments, these are simply
                  passed to the module constructor.
          
          kw_args -- optional keyword arguments, these are simply
                     passed to the module constructor.
        """        
        debug ("In MayaViTkGUI::load_module ()")
        if not mod_name:
            mod_name = self.module_var.get ()
        return self.mayavi.load_module(mod_name, config, *args, **kw_args)

    def load_filter (self, fil_name="", config=1, *args, **kw_args):
        """Loads a Filter.
        Input Arguments:
        
          fil_name -- A string containing a valid Filter name.  If the
                      filter is 'UserDefined' then it could be
                      specified as 'UserDefined:vtkSomeFilter' where
                      vtkSomeFilter is a valid VTK class.  In this
                      case the filter will not prompt you for the VTK
                      filter to use.
          
          config -- if non-zero it pops up the configuration GUI for
                    the Filter after it is loaded.

          args -- optional non-keyword arguments, these are simply
                  passed to the module constructor.
          
          kw_args -- optional keyword arguments, these are simply
                     passed to the module constructor.
        """        
        debug ("In MayaViTkGUI::load_filter ()")
        if not fil_name:
            fil_name = self.filter_var.get ()
        return self.mayavi.load_filter(fil_name, config, *args, **kw_args)

    def load_current_mm (self, file_name=""):
        """Load a ModuleManager from a file. This function loads the
        ModuleManager starting from the current ModuleManager.  If the
        file_name argument is passed it loads the ModuleManager from
        that particular file if not it pops up a file dialog to choose
        the file."""
        debug ("In MayaViTkGUI::load_current_mm ()")
        if not self.mayavi.has_active_dvm ():
            return
        if not file_name:
            file_name = tk_fopen (title="Open module data file", 
                                  initialdir=Common.config.initial_dir,
                                  filetypes=[("MayaVi Module files",
                                              "*.mod"), 
                                             ("All files", "*")])
            
        self.mayavi.load_current_mm (file_name)

    def load_mm (self, file_name=""):
        """Load a ModuleManager from a file. If the file_name argument
        is passed it loads the ModuleManager from that particular file
        if not it pops up a file dialog to choose the file."""
        debug ("In MayaViTkGUI::load_mm ()")
        if not self.mayavi.has_active_dvm ():
            return
        if not file_name:
            file_name = tk_fopen (title="Open module data file", 
                                  initialdir=Common.config.initial_dir,
                                  filetypes=[("MayaVi Module files",
                                              "*.mod"), 
                                             ("All files", "*")])
        self.mayavi.load_mm (file_name)

    def save_current_mm (self, file_name=""):
        """Save the current ModuleManager. If the file_name argument
        is passed it saves the ModuleManager to that particular file
        if not it pops up a file dialog to choose the file."""
        debug ("In MayaViTkGUI::save_current_mm ()")
        if not self.mayavi.has_active_dvm():
            return
        if not file_name:
            file_name = tk_fsave (title="Save module data file", 
                                  initialdir=Common.config.initial_dir,
                                  defaultextension=".mod",
                                  filetypes=[("MayaVi Module files",
                                              "*.mod"), 
                                             ("All files", "*")])
            
        self.mayavi.save_current_mm (file_name)


    def save_all_mm (self, file_name=""):
        """Save all the ModuleManagers. If the file_name argument is
        passed it saves the ModuleManagers to that particular file if
        not it pops up a file dialog to choose the file."""
        debug ("In MayaViTkGUI::save_all_mm ()")
        if not self.mayavi.has_active_dvm ():
            return
        if not file_name:
            file_name = tk_fsave (title="Save module data file", 
                                  initialdir=Common.config.initial_dir,
                                  defaultextension=".mod",
                                  filetypes=[("MayaVi Module files",
                                              "*.mod"), 
                                             ("All files", "*")])
        self.mayavi.save_all_mm (file_name)

    def save_current_dvm (self, file_name=""):
        """Save the current DataVizManager. If the file_name argument
        is passed it saves the DataVizManager to that particular file
        if not it pops up a file dialog to choose the file."""
        debug ("In MayaViTkGUI::save_current_dvm ()")
        if not self.mayavi.has_active_dvm ():
            return
        if not file_name:
            file_name = tk_fsave (title="Save MayaVi data file", 
                                  initialdir=Common.config.initial_dir,
                                  defaultextension=".mv",
                                  filetypes=[("MayaVi visualization files",
                                              "*.mv"), 
                                             ("All files", "*")])
        self.mayavi.save_current_dvm (file_name)

    def save_visualization (self, file_name=""):        
        """Save current visualization.  If the file_name argument is
        passed it saves the visualization to that particular file if
        not it pops up a file dialog to choose the file."""        
        debug ("In MayaViTkGUI::save_visualization ()")
        if not self.mayavi.has_active_dvm ():
            return
        if not file_name:
            file_name = tk_fsave (title="Save MayaVi data file", 
                                  initialdir=Common.config.initial_dir,
                                  defaultextension=".mv",
                                  filetypes=[("MayaVi visualization files",
                                              "*.mv"), 
                                             ("All files", "*")])
        self.mayavi.save_visualization (file_name)

    def load_visualization (self, file_name=""):        
        """Loads a saved visualization.  If the file_name argument is
        passed it opens that particular file if not it pops up a file
        dialog to choose the file."""        
        debug ("In MayaViTkGUI::load_visualization ()")
        if not file_name:
            file_name = tk_fopen (title="Load MayaVi data file", 
                                  initialdir=Common.config.initial_dir,
                                  filetypes=[("MayaVi visualization files",
                                              "*.mv"), 
                                             ("All files", "*")])
        if check_file (file_name):
            self.mayavi.load_visualization (file_name)

    def del_dvm_gui (self, event=None): 
        debug ("In MayaViTkGUI::del_dvm_gui ()")
        key = self.dvm_lst.get ('active')
        self.dvm_lst.delete ('active')
        if key:
            cur_dvm_name = self.mayavi.get_current_dvm_name ()
            indx = self.mayavi.get_dvm_names().index (cur_dvm_name)
            self.mayavi.del_dvm (key)
            cur_dvm_name = self.mayavi.get_current_dvm_name ()
            if cur_dvm_name:
                self.dvm_lst.select_clear (0, 'end')
                self.dvm_lst.activate (indx)
                self.dvm_lst.select_set (indx)
                self.show_dvm (None, 1)
            self.update_label ()

    def close_all (self, event=None):        
        """Close all the open visualizations.  This removes all the
        DataVizManagers, Filters, Modules, imported VRML and 3DS
        files."""        
        debug ("In MayaViTkGUI::close_all ()")
        self.dvm_lst.delete (0, 'end')
        self.vrml_close_menu.delete (0, self.mayavi.get_n_vrml ())
        self.tds_close_menu.delete (0, self.mayavi.get_n_3ds ())
        self.mayavi.close_all()
        self.update_label ()
        
    def close_vrml (self, event=None):
        debug ("In MayaViTkGUI::close_vrml ()")
        name = self.vrml_var.get ()
        self.mayavi.close_vrml (name)
        self.vrml_close_menu.delete (name)

    def close_3ds (self, event=None):
        debug ("In MayaViTkGUI::close_3ds ()")
        name = self.tds_var.get ()
        self.mayavi.close_3ds (name)
        self.tds_close_menu.delete (name)

    def set_fg_color (self, event=None):
        """Choose and set a color from a GUI color chooser and change
        the colors of all the actors."""
        debug ("In MayaViTkGUI::set_fg_color ()")
        col = Common.config.fg_color
        cur_col = "#%02x%02x%02x"% (col[0]*255, col[1]*255, col[2]*255)
        new_color = tkColorChooser.askcolor (title="Foreground color",
                                             initialcolor=cur_col)
        if new_color[1] != None:
            col = Common.tk_2_vtk_color (new_color[0])
            Common.config.fg_color = col
            self.mayavi.fg_color_changed ()

    def set_bg_color (self):
        """Choose and set a color from a GUI color chooser and change
        the colors of the background."""
        debug ("In MayaViTkGUI::set_bg_color ()")
        col = Common.config.bg_color
        rw_col = self.renwin.get_renderer ().GetBackground ()
        if rw_col != col:
            col = rw_col
        cur_col = "#%02x%02x%02x"% (col[0]*255, col[1]*255, col[2]*255)
        new_color = tkColorChooser.askcolor (title="Background color",
                                             initialcolor=cur_col)
        if new_color[1] != None:
            col = Common.tk_2_vtk_color (new_color[0])
            Common.config.bg_color = col
            Common.state.busy ()
            self.renwin.set_background (col)
            self.renwin.Render ()
            Common.state.idle ()

    def config_changed (self):
        "Called when the render windows configuration is changed."
        debug ("In MayaViTkGUI::config_changed ()")
        Common.state.busy ()
        self.renwin.config_changed ()
        self.renwin.Render ()
        Common.state.idle ()
        
    def edit_prefs (self, event=None):
        "Pops up a GUI to edit MayaVi's preferences."
        debug ("In MayaViTkGUI::edit_prefs ()")
        e = Common.EditConfig (self.root, self, Common.config)        

    def new_window (self):
        "Returns a new MayaViTkGUI window."
        debug ("In MayaViTkGUI::new_window ()")
        return MayaViTkGUI (self.master)

    def pipeline_browse (self, event=None):
        "Creates a graphical VTK pipeline browser."
        debug ("In MayaViTkGUI::pipeline_browser ()")
        Common.state.busy ()
        rw = self.renwin.get_vtk_render_window ()
        pipe_b = vtkPipeline.vtkPipeline.vtkPipelineBrowser (self.root, rw)
        pipe_b.browse ()
        Common.state.idle ()

    def show_log_win (self, event=None):
        "Displays the log window where debug messages are printed."
        debug ("In MayaViTkGUI::show_log_win ()")
        Common.log_win.show_log ()

    def reload_modules (self, event=None):        
        """Reloads all modules used by MayaVi.  Useful when developing
        MayaVi."""        
        debug ("In MayaViTkGUI::reload_modules ()")
        self.mayavi.reload_modules ()

    def show_ctrl_panel (self, val=None):        
        """When passed an argument of 1 this shows the control panel
        and when passed 0 disables showing the control panel."""        
        if val is None:
            val = self.full_scr_var.get ()
        if val:
            self.renwin_frame.pack_forget ()
            self.ctrl_frame.pack (side='left', fill='y', expand=0)
            self.renwin_frame.pack (side='left', fill='both', expand=1)
        else:
            self.ctrl_frame.pack_forget ()

    def config_renwin (self, event=None):
        "Creates a configuration window for the render window."
        debug ("In MayaViTkGUI::config_renwin ()")
        self.renwin.configure (self.root)
        
    def get_current_dvm (self):
        "Returns the currently active DataVizManager."
        debug ("In MayaViTkGUI::get_current_dvm ()")
        return self.mayavi.get_current_dvm ()

    def get_current_dvm_name (self):
        "Returns the name of the currently active DataVizManager."
        debug ("In MayaVi::get_current_dvm_name ()")
        return self.mayavi.get_current_dvm_name ()

    def get_dvm_names (self):
        "Returns the name of all the DataVizManagers."
        debug ("In MayaVi::get_dvm_names ()")
        return self.mayavi.get_dvm_names ()

    def quit (self, event=None):
        "Closes the window."
        debug ("In MayaViTkGUI::quit ()")
        Common.state.unregister (self.root)
        Common.state.unregister (self.status_frame)
        self.mayavi.quit()
        self.renwin.quit ()
        self.root.destroy ()
        if not MayaVi.n_app:
            Common.log_win.quit ()
            self.master.destroy ()

    def start_animation (self, delay, func, *args):
        """Starts a user defined animation.
        Input Arguments:

           delay -- time in milli-seconds to delay between calls to
           the function.

           func -- user defined function that will be called.

           args -- the remaining arguments will be used when the
           function is called.
        
        """
        if self.anim == 0:
            self.anim = -1
            return
        elif self.anim == -1:
            self.anim = 1
        if self.anim == 1:
            func (*args)
            l = [delay, self.start_animation, delay, func] + list (args)
            self.root.after (*l)
            
    def stop_animation (self):
        """Stops the animation."""
        if self.anim == 1:
            self.anim = 0   

    def do_callback (self, func, *args):
        """Proxies a function call so that MayaVi calls the function
        with the given args.  This is very useful when you need to
        call a function that does something MayaVi specific from
        another thread.
        
        Input Arguments:
        
           func -- user defined function that will be called.

           args -- the remaining arguments will be used when the
           function is called.
        """
        l = [0, func] + list (args)
        self.root.after (*l)


def mayavi (geometry=None):
    """ Returns a MayaViTkGUI Window.  This is to be used when using
    MayaVi from the Python interpreter.

    Keyword Arguments:

    geometry -- The geometry of the main window in standard X
    fashion (WxH+X+Y).
    """    
    r = Tkinter._default_root
    if not r:
        r = Tkinter.Tk ()
        r.withdraw ()
    t = Tkinter.Toplevel (r)
    t.withdraw ()
    app = MayaViTkGUI (t, geometry)
    return app


def main ():
    """ Starts Tkinter and then starts a session of the application.
    This is simply a useful sample."""
    r = Tkinter.Tk ()
    r.withdraw ()
    v = MayaViTkGUI (r)
    r.mainloop ()

if __name__ == "__main__":
    main ()
