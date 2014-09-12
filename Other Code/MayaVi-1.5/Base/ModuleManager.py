"""

This file defines the ModuleManager class that is responsible for
managing all the Modules and Filters for a particular data source.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.13 $"
__date__ = "$Date: 2004/07/06 23:06:31 $"

import Misc.LutHandler, Common, Tkinter

import sys
_PARENT = ''
if sys.modules.has_key ('mayavi'):
    _PARENT = 'mayavi.'

debug = Common.debug

class ModuleManager:
    
    """ This class manages a bunch of various Filters and Modules."""

    def __init__ (self, dvm):
        """ Argument 'dvm' is a DataVizManager instance."""
        debug ("In ModuleManager::__init__ ()")
        self.dvm = dvm
        self.data_src = dvm.get_data_source ()
        self.renwin= dvm.get_render_window ()
        self.filter = {}
        self.fil_name = []
        self.module = {}
        self.mod_name = []
        self.n_mod = 0
        self.n_fil = 0
        self.cur_mod_name = ""
        self.cur_fil_name = None
        # The GUI list boxes
        self.fil_lst = None
        self.mod_lst = None

        # LUTs
        self.scalar_lut_h = Misc.LutHandler.LutHandler ()
        self.scalar_lut_h.initialize (self)
        _cfg = Common.config.scalar_lut_cfg
        if _cfg:
            self.scalar_lut_h.load_config(_cfg)
        self.vector_lut_h = Misc.LutHandler.LutHandler ()
        self.vector_lut_h.initialize (self)
        _cfg = Common.config.vector_lut_cfg
        if _cfg:
            self.vector_lut_h.load_config(_cfg)
        
        self.scalar_data_range = [0.0, 1.0]
        self.vector_data_range = [0.0, 1.0]
        self.data_src.add_reference (self)
        self.Update ()

    def __del__ (self):
        debug ("In ModuleManager::__del__ ()")

    def clear (self):
        """This is needed to prevent self-referential loops and is
        usually called before a ModuleManager is destroyed."""
        debug ("In ModuleManager::clear ()")
        self.data_src.del_reference (self)
        for key in self.mod_name[:]:
            self.del_module (key)
        for key in self.fil_name[:]:
            self.del_filter (key)

        del self.scalar_lut_h
        del self.vector_lut_h
        self.renwin.Render ()

    def config_changed (self):
        """The configuration file has changed - take notice and update
        all modules and filters."""
        debug ("In ModuleManager::config_changed ()")
        self.scalar_lut_h.config_changed ()
        self.vector_lut_h.config_changed ()
        for fil in self.filter.values ():
            fil.config_changed ()
        for mod in self.module.values ():
            mod.config_changed ()

    def get_data_source (self): 
        """ Get the data source object for this object."""
        debug ("In ModuleManager::get_data_source ()")
        return self.data_src

    def get_render_window (self): 
        debug ("In ModuleManager::get_render_window ()")
        return self.renwin

    def get_scalar_lut_handler (self): 
        debug ("In ModuleManager::get_scalar_lut_handler ()")
        return self.scalar_lut_h

    def get_scalar_lut (self): 
        debug ("In ModuleManager::get_scalar_lut ()")
        return self.scalar_lut_h.get_lut ()

    def get_vector_lut_handler (self): 
        debug ("In ModuleManager::get_vector_lut_handler ()")
        return self.vector_lut_h

    def get_vector_lut (self): 
        debug ("In ModuleManager::get_vector_lut ()")
        return self.vector_lut_h.get_lut ()

    def get_scalar_data_range (self): 
        debug ("In ModuleManager::get_scalar_data_range ()")        
        return self.scalar_lut_h.get_data_range ()

    def get_vector_data_range (self): 
        debug ("In ModuleManager::get_vector_data_range ()")
        return self.vector_lut_h.get_data_range ()

    def get_scalar_data_name (self):
        debug ("In ModuleManager::get_scalar_data_name ()")
        return self.get_last_source ().get_scalar_data_name ()

    def get_vector_data_name (self):
        debug ("In ModuleManager::get_vector_data_name ()")
        return self.get_last_source ().get_vector_data_name ()

    def get_last_source (self):
        """Get the last source object.  If there are filters this
        returns the last of the filters if not it returns the data
        source."""        
        debug ("In ModuleManager::get_last_source ()")
        if not self.filter:
            return self.data_src
        else:
            return self.filter[self.fil_name[-1]]

    def GetOutput (self): 
        """Returns the output of the filtered data."""
        debug ("In ModuleManager::GetOutput ()")
        if not self.filter:
            f = self.data_src
        else:
            f = self.filter[self.fil_name[-1]]
        return f.GetOutput ()

    def get_module_names(self):
        """Returns the list of module names that are being managed."""
        return self.mod_name

    def get_module(self, val):
        """Returns the module given an integer index into the list of
        module names or the module name itself."""
        if type(val) == type("string"):
            return self.module.get(val)
        elif type(val) == type(1):
            if val < len(self.mod_name):
                return self.module[self.mod_name[val]]
        return None
    
    def _get_scalar_range (self, data_out):
        debug ("In ModuleManager::_get_scalar_range ()")
        sc_name = self.data_src.get_scalar_data_name ()
        pd = data_out.GetPointData ().GetScalars ()
        cd = data_out.GetCellData ().GetScalars ()
        dr = []
        if pd and cd:
            if hasattr (pd, 'GetName'): # VTK 4.0 and above
                if (sc_name == pd.GetName ()):
                    dr = pd.GetRange ()
                elif sc_name == cd.GetName ():
                    dr = cd.GetRange ()
            else: # old VTK release (this should not usually happen).
                pr = pd.GetRange ()
                cr = cd.GetRange ()
                dr = [min (cr[0], pr[0]), max (cr[1], pr[1])]
        elif pd:
            dr = pd.GetRange ()
        elif cd:
            dr = cd.GetRange ()
        if dr:
            self.scalar_data_range = dr
            val = self.get_scalar_data_name ()
            self.scalar_lut_h.set_data_name (val)
            self.scalar_lut_h.set_data_range (self.scalar_data_range)

    def _get_max_norm (self, data_out):
        debug ("In ModuleManager::_get_max_norm ()")
        vec_name = self.data_src.get_vector_data_name ()
        pd = data_out.GetPointData ().GetVectors ()
        cd = data_out.GetCellData ().GetVectors ()
        max_v = 0.0
        if pd and cd:
            if hasattr (pd, 'GetName'): # VTK 4.0 and above
                if (vec_name == pd.GetName ()):
                    max_v = pd.GetMaxNorm()
                elif vec_name == cd.GetName ():
                    max_v = cd.GetMaxNorm ()
                else: # old version of VTK. :(
                    max_v = max (pd.GetMaxNorm (), cd.GetMaxNorm ())
        elif pd:
            max_v = pd.GetMaxNorm ()
        elif cd:
            max_v = cd.GetMaxNorm ()
        if max_v:
            self.vector_data_range = [0.0, max_v]
            val = self.get_vector_data_name ()
            self.vector_lut_h.set_data_name (val)
            self.vector_lut_h.set_data_range (self.vector_data_range)

    def update_filters (self):
        debug ("In ModuleManager::update_filters ()")
        if not len (self.fil_name):
            return
        self._get_max_norm (self.data_src.GetOutput ())
        self._get_scalar_range (self.data_src.GetOutput ())
        self.filter[self.fil_name[0]].set_input_source (self.data_src)
        for i in range (1, len (self.fil_name)):
            prev = self.filter[self.fil_name[i-1]]
            self._get_max_norm (prev.GetOutput ())
            self._get_scalar_range (prev.GetOutput ())
            self.filter[self.fil_name[i]].set_input_source (prev)

    def update_modules (self):
        debug ("In ModuleManagers::update_modules ()")
        self.vector_data_range = [0.0, 0.0]
        self.scalar_data_range = [0.0, 0.0]
        out = self.GetOutput ()
        self._get_max_norm (out)
        self._get_scalar_range (out)
        self._set_module_input ()
        self.renwin.Render ()
        
    def Update (self):        
        """Update all the filters and modules.  Usually called when
        anything changes in the filters or Data sources."""        
        debug ("In ModuleManager::Update ()")
        self.update_filters ()
        self.update_modules ()

    def _set_module_input (self):
        """ Sets the input for all the modules."""
        debug ("In ModuleManager::_set_module_input ()")
        out = self.GetOutput ()
        for mod in self.module.values ():
            mod.SetInput (out)

    def add_module (self, module): 
        debug ("In ModuleManager::add_module ()")
        self.n_mod = self.n_mod + 1
        k = '%d. %s'%(self.n_mod, module.__class__.__name__)
        self.module[k] = module
        self.cur_mod_name = k
        self.mod_name.append (k)

    def add_filter (self, filter): 
        debug ("In ModuleManager::add_filter ()")
        self.n_fil = self.n_fil + 1
        k = '%d. %s'%(self.n_fil, filter.__class__.__name__)
        self.filter[k] = filter
        self.fil_name.append (k)
        self.cur_fil_name = k
        self.update_modules ()

    def del_module (self, key): 
        debug ("In ModuleManager::del_module ()")
        try:
            del self.module[key]
        except KeyError:
            msg = "Error: cannot delete module with key: %s"%key
            raise KeyError, msg

        indx = self.mod_name.index (key)
        if len (self.mod_name) > 1:
            if indx == 0:
                self.cur_mod_name = self.mod_name[indx + 1]
            else:
                self.cur_mod_name = self.mod_name[indx - 1]
        else:
            self.cur_mod_name = ""

        del self.mod_name[indx]

    def del_filter (self, key): 
        debug ("In ModuleManager::del_filter ()")
        try:
            del self.filter[key]
        except KeyError:
            msg = "Error: cannot delete filter with key: %s"%key
            raise KeyError, msg

        indx = self.fil_name.index (key)
        prev = None
        next = None
        self.cur_fil_name = ""
        if indx == 0:
            prev = self.data_src
        else:
            self.cur_fil_name = self.fil_name[indx-1]
            prev = self.filter[self.fil_name[indx-1]]
        if indx < (len (self.fil_name) - 1):
            next = self.filter[self.fil_name[indx+1]]
            self.cur_fil_name = self.fil_name[indx+1]

        if next:
            next.set_input_source (prev)

        del self.fil_name[indx]
        self.update_modules ()

    def get_current_module (self): 
        """ Get currently selected module."""
        debug ("In ModuleManager::get_current_module ()")
        return self.module[self.cur_mod_name]

    def _write_msg (self, file, msg):
        file.write (msg)
        debug (msg)

    def save_config (self, file): 
        """Save the object configurations to file."""
        debug ("In ModuleManager::save_config ()")
        self._write_msg (file, "### Scalar Lookup Table ###\n")
        self.scalar_lut_h.save_config (file)
        self._write_msg (file, "### End of Scalar Lookup Table ###\n")

        self._write_msg (file, "### Vector Lookup Table ###\n")
        self.vector_lut_h.save_config (file)
        self._write_msg (file, "### End Vector Lookup Table ###\n")

        self._write_msg (file, "### Filters ###\n")
        file.write ("%d\n"%len (self.fil_name))
        for f_name in self.fil_name:
            self._write_msg (file, "### %s ###\n"%f_name)
            fil = self.filter[f_name]
            if fil.__module__.find('Filters.') > -1:
                # standard filter.
                file.write ("%s\n"%fil.__class__.__name__)
            else:
                file.write ("User.%s\n"%fil.__class__.__name__)
            fil.save_config (file)
            self._write_msg (file, "### End of %s ###\n"%f_name)
        self._write_msg (file, "### End of Filters ###\n")

        self._write_msg (file, "### Modules ###\n")
        file.write ("%d\n"%len (self.mod_name))
        for m_name in self.mod_name:
            self._write_msg (file, "### %s ###\n"%m_name)
            mod = self.module[m_name]
            if mod.__module__.find('Modules.') > -1:
                file.write ("%s\n"%mod.__class__.__name__)
            else:
                file.write ("User.%s\n"%mod.__class__.__name__)
            mod.save_config (file)
            self._write_msg (file, "### End of %s ###\n"%m_name)
        self._write_msg (file, "### End of Modules ###\n")
            
    def _read_msg (self, file):
        debug (file.readline ())

    def load_config (self, file): 
        """Load the saved  object configuration from a file."""
        debug ("In ModuleManager::load_config ()")
        self._read_msg (file)
        self.scalar_lut_h.load_config (file)
        self._read_msg (file)

        self._read_msg (file)
        self.vector_lut_h.load_config (file)
        self._read_msg (file)

        self._read_msg (file)
        n = int (file.readline ())
        for i in range (n):
            self._read_msg (file)
            name = file.readline ()[:-1]
            arg = None
            if name == "UserDefined":
                arg = file.readline()[:-1]
            if name[:5] == 'User.':
                name = name[5:]
                fil_scr = Common.mod_fil_import('Filters', name,
                                                globals(), locals(), 1)
            else:
                fil_scr = __import__ ("%sFilters.%s"%(_PARENT, name),
                                      globals(), locals(), [name])
            if arg:
                fil = eval ("fil_scr.%s (self, arg)"%name)
            else:
                fil = eval ("fil_scr.%s (self)"%name)                
            self.add_filter_gui (fil)
            fil.load_config (file)
            self._read_msg (file)
        self._read_msg (file)

        self._read_msg (file)
        n = int (file.readline ())
        for i in range (n):
            self._read_msg (file)
            name = file.readline ()[:-1]
            arg = None
            if name == "Labels":
                arg = -1
            if name[:5] == 'User.':
                name = name[5:]
                mod_scr = Common.mod_fil_import('Modules', name,
                                                globals(), locals(), 1)
            else:
                mod_scr = __import__ ("%sModules.%s"%(_PARENT, name),
                                      globals(), locals(), [name])
            if arg:
                mod = eval ("mod_scr.%s (self, arg)"%name)
            else:
                mod = eval ("mod_scr.%s (self)"%name)
            self.add_module_gui (mod)
            mod.load_config (file)
            self._read_msg (file)
        self._read_msg (file)
        self.Update ()
            
    def create_filter_gui (self, master): 
        """ Create the GUI for the filters."""
        debug ("In ModuleManager::create_filter_gui ()")
        frame = Tkinter.Frame (master)
        frame.pack (side='top', fill='both', expand=1)
        label = Tkinter.Label (frame, text="Filters")
        label.grid (row=0, column=0, sticky='ew', columnspan=2)
        scr = Tkinter.Scrollbar (frame, orient='vertical')
        self.fil_lst = Tkinter.Listbox (frame, yscrollcommand=scr.set, 
                                        selectmode='single', height=3,
                                        exportselection=0)
        scr.config (command=self.fil_lst.yview)
        self.fil_lst.grid (row=1, column=0, sticky='ewns')
        scr.grid (row=1, column=1, sticky='ns')
        self.fil_lst.bind ("<Double-Button-1>", self.config_filter)
        
        but_f = Tkinter.Frame (master)
        but_f.pack (side='top', fill='both', expand=1)
        but1 = Tkinter.Button (but_f, text="Configure Filter",
                               command=self.config_filter)
        but1.grid (row=0, column=0, sticky="ew")
        but2 = Tkinter.Button (but_f, text="Delete Filter",
                               command=self.del_filter_gui)
        but2.grid (row=0, column=1, sticky="ew")

        for fil in self.fil_name:
            self.fil_lst.insert ('end', fil)

        if self.cur_fil_name:
            self.fil_lst.select_clear (0, 'end')
            indx = self.fil_name.index (self.cur_fil_name)
            self.fil_lst.activate (indx)
            self.fil_lst.select_set (indx)
 
    def create_module_gui (self, master): 
        """ Create the GUI for the modules."""
        debug ("In ModuleManager::create_module_gui ()")
        frame = Tkinter.Frame (master)
        frame.pack (side='top', fill='both', expand=1)
        label = Tkinter.Label (frame, text="Modules")
        label.grid (row=0, column=0, sticky='ew', columnspan=2)
        scr = Tkinter.Scrollbar (frame, orient='vertical')
        self.mod_lst = Tkinter.Listbox (frame, yscrollcommand=scr.set, 
                                        selectmode='single', height=4,
                                        exportselection=0)
        scr.config (command=self.mod_lst.yview)
        self.mod_lst.grid (row=1, column=0, sticky='ewns')
        scr.grid (row=1, column=1, sticky='ns')
        self.mod_lst.bind ("<Double-Button-1>", self.config_module)

        but_f = Tkinter.Frame (master)
        but_f.pack (side='top', fill='both', expand=1)
        but1 = Tkinter.Button (but_f, text="Configure",
                               command=self.config_module)
        but1.grid (row=0, column=0, sticky="ew")
        but2 = Tkinter.Button (but_f, text="Delete",
                               command=self.del_module_gui)
        but2.grid (row=0, column=1, sticky="ew")

        for mod in self.mod_name:
            self.mod_lst.insert ('end', mod)

        if self.cur_mod_name:
            self.mod_lst.select_clear (0, 'end')
            indx = self.mod_name.index (self.cur_mod_name)
            self.mod_lst.activate (indx)
            self.mod_lst.select_set (indx)

    def create_gui (self, master): 
        """ Create control GUI ModuleManager."""
        debug ("In ModuleManager::create_gui ()")
        if not master:
            debug ("In ModuleManager::create_gui: Error: No master widget.")
            return None
        self.frame = Tkinter.Frame (master, relief='ridge', bd=2)
        self.frame.pack (side='top', fill='both', expand=1)

        but_f = Tkinter.Frame (self.frame)
        but_f.pack (side='top')
        Tkinter.Button (but_f, text="Config Scalar Legend",
                        command=self.config_scalar_lut).pack (side='top')
        Tkinter.Button (but_f, text="Config Vector Legend",
                        command=self.config_vector_lut).pack (side='top')

        self.create_filter_gui (self.frame)
        self.create_module_gui (self.frame)

    def close_gui (self, event=None): 
        debug ("In ModuleManager::close_gui ()")
        self.frame.destroy ()

    def config_module (self, event=None): 
        debug ("In ModuleManager::config_module ()")
        key = self.mod_lst.get ('active')
        if key:
            self.module[key].configure (self.frame)

    def config_filter (self, event=None): 
        debug ("In ModuleManager::config_filter ()")
        key = self.fil_lst.get ('active')
        if key:
            self.filter[key].configure (self.frame)

    def del_filter_gui (self, event=None): 
        debug ("In ModuleManager::del_filter_gui ()")
        key = self.fil_lst.get ('active')
        self.fil_lst.delete ('active')
        if key:
            self.del_filter (key)

    def del_module_gui (self, event=None): 
        debug ("In ModuleManager::del_module_gui ()")
        key = self.mod_lst.get ('active')
        self.mod_lst.delete ('active')
        if key:
            self.del_module (key)

    def add_filter_gui (self, fil): 
        debug ("In ModuleManager::add_filter_gui ()")
        self.add_filter (fil)
        self.fil_lst.insert ('end', self.cur_fil_name)
        self.fil_lst.select_clear (0, 'end')
        self.fil_lst.activate ('end')
        self.fil_lst.select_set ('end')

    def add_module_gui (self, mod): 
        debug ("In ModuleManager::add_module_gui ()")
        self.add_module (mod)
        self.mod_lst.insert ('end', self.cur_mod_name)
        self.mod_lst.select_clear (0, 'end')
        self.mod_lst.activate ('end')
        self.mod_lst.select_set ('end')

    def config_scalar_lut (self): 
        debug ("In ModuleManager::config_scalar_lut ()")
        self.scalar_lut_h.configure (self.frame)

    def config_vector_lut (self): 
        debug ("In ModuleManager::config_vector_lut ()")
        self.vector_lut_h.configure (self.frame)

