"""

This file defines the DataVizManager that controls a list of
ModuleManagers.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.6 $"
__date__ = "$Date: 2004/07/06 04:29:30 $"

import ModuleManager, Common, Tkinter

debug = Common.debug

class DataVizManager:

    """ This class controls a list of ModuleManagers."""

    def __init__ (self, data_src, renwin=None):        
        """ The argument 'data_src' refers to a data source instance
        and 'renwin' to a RenderWindow instance."""
        debug ("In DataVizManager::__init__ ()")
        self.data_src = data_src
        self.renwin=renwin
        self.mod_mgr = {}
        self.mm_name = []
        self.cur_mm_name = ""
        self.n_mm = 0        
        # The GUI list box
        self.mm_lst = None
        self.frame = None

    def __del__ (self):
        debug ("In DataVizManager::__del__ ()")

    def clear (self): 
        """This is needed to prevent self-referential loops and is
        usually called before a DataVizManager object is destroyed."""
        debug ("In DataVizManager::clear ()")
        if self.frame:
            self.close_gui ()
        for mm_name in self.mm_name[:]:
            self.del_module_mgr (mm_name)
        del self.data_src

    def config_changed (self): 
        debug ("In DataVizManager::config_changed ()")
        for mm in self.mod_mgr.values ():
            mm.config_changed ()

    def get_data_source (self): 
        debug ("In DataVizManager::get_data_source ()")
        return self.data_src

    def get_render_window (self): 
        debug ("In DataVizManager::get_render_window ()")
        return self.renwin

    def get_current_module_mgr (self): 
        debug ("In DataVizManager::get_current_module_mgr ()")
        if self.cur_mm_name:
            return self.mod_mgr[self.cur_mm_name]
        else:
            return None

    def add_module_mgr (self, mm): 
        debug ("In DataVizManager::add_module_mgr ()")
        self.n_mm = self.n_mm + 1
        k = '%d. %s'%(self.n_mm, mm.__class__.__name__)
        self.mod_mgr[k] = mm
        self.cur_mm_name = k
        self.mm_name.append (k)

    def del_module_mgr (self, key): 
        debug ("In DataVizManager::del_module_mgr ()")
        try:
            self.mod_mgr[key].clear ()
            del self.mod_mgr[key]
        except KeyError:
            msg = "Error: cannot delete ModuleManager with key: %s"%key
            raise KeyError, msg

        indx = self.mm_name.index (key)
        if len (self.mm_name) > 1:
            if indx == 0:
                self.cur_mm_name = self.mm_name[indx + 1]
            else:
                self.cur_mm_name = self.mm_name[indx - 1]
        else:
            self.cur_mm_name = ""

        del self.mm_name[indx]

    def _write_msg (self, file, msg): 
        file.write (msg)
        debug (msg)

    def save_current_module_mgr (self, file): 
        debug ("In DataVizManager::save_current_module_mgr ()")
        self._write_msg (file, "### ModuleManagers ###\n")
        file.write ("1\n")
        self._write_msg (file, "### %s ###\n"%self.cur_mm_name)
        mm = self.mod_mgr[self.cur_mm_name]
        mm.save_config (file)
        self._write_msg (file, "### End of %s ###\n"%self.cur_mm_name)
        self._write_msg (file, "### End of ModuleManagers ###\n")

    def save_config (self, file): 
        debug ("In DataVizManager::save_config ()")
        self._write_msg (file, "### ModuleManagers ###\n")
        file.write ("%d\n"%len (self.mm_name))
        for mm_name in self.mm_name:
            self._write_msg (file, "### %s ###\n"%mm_name)
            mm = self.mod_mgr[mm_name]
            mm.save_config (file)
            self._write_msg (file, "### End of %s ###\n"%mm_name)
        self._write_msg (file, "### End of ModuleManagers ###\n")

    def _read_msg (self, file): 
        debug (file.readline ())

    def load_current_module_mgr (self, file): 
        debug ("In DataVizManager::load_current_module_mgr ()")
        # Get the config from the file
        #self._read_msg (file)
        tmp = file.readline ()
        debug (tmp)
        if tmp != "### ModuleManagers ###\n":
            msg = "Error: Expected data for ModuleManagers not found.\n"\
                  "You have  possibly chosen the wrong file.\n"
            raise ParseException, msg
        n = int (file.readline ())
        # Read the first module manager to the current one.
        self._read_msg (file)
        mm = self.mod_mgr[self.cur_mm_name]
        mm.load_config (file)
        self._read_msg (file)
        # Read the rest separately.
        for i in range (1, n):
            self._read_msg (file)
            self.add_module_mgr_gui ()
            self.mod_mgr[self.cur_mm_name].load_config (file)
            self._read_msg (file)
        self._read_msg (file)

    def load_config (self, file): 
        debug ("In DataVizManager::load_config ()")
        # Get the config from the file
        tmp = file.readline ()
        debug (tmp)
        if tmp != "### ModuleManagers ###\n":
            msg = "Error: Expected data for ModuleManagers not found. "\
                  "You have  possibly chosen the wrong file."
            raise ParseException, msg
        n = int (file.readline ())
        for i in range (n):
            self._read_msg (file)
            self.add_module_mgr_gui ()
            self.mod_mgr[self.cur_mm_name].load_config (file)
            self._read_msg (file)
        self._read_msg (file)

    def create_module_gui (self, master): 
        debug ("In DataVizManager::create_module_gui ()")
        frame = Tkinter.Frame (master)
        frame.pack (side='top', fill='y')
        #label = Tkinter.Label (frame, text="Module Managers")
        #label.grid (row=0, column=0, sticky='ew', columnspan=2)
        scr = Tkinter.Scrollbar (frame, orient='vertical')
        self.mm_lst = Tkinter.Listbox (frame, yscrollcommand=scr.set, 
                                        selectmode='single', height=3,
                                        exportselection=0)
        scr.config (command=self.mm_lst.yview)
        self.mm_lst.grid (row=0, column=0, sticky='ewns')
        scr.grid (row=0, column=1, sticky='ns')
        self.mm_lst.bind ("<Double-Button-1>", self.show_mm)
        
        but_f = Tkinter.Frame (master)
        but_f.pack (side='top', fill='y')
        but1 = Tkinter.Button (but_f, text="Show",
                               command=self.show_mm)
        but1.grid (row=0, column=0, sticky="ew")
        but2 = Tkinter.Button (but_f, text="New",
                               command=self.add_module_mgr_gui)
        but2.grid (row=0, column=1, sticky="ew")        
        but3 = Tkinter.Button (but_f, text="Delete",
                               command=self.del_module_mgr_gui)
        but3.grid (row=0, column=2, sticky="ew")

        lab = "ModuleManager: %s"%self.cur_mm_name
        self.data_label = Tkinter.Label (but_f, text=lab)
        self.data_label.grid (row=1, column=0, columnspan=3, pady=0)

        for mm in self.mm_name:
            self.mm_lst.insert ('end', mm)

        if self.cur_mm_name:
            self.mm_lst.select_clear (0, 'end')
            indx = self.mm_name.index (self.cur_mm_name)
            self.mm_lst.activate (indx)
            self.mm_lst.select_set (indx)

        if self.cur_mm_name:
            self.mm_lst.activate (self.mm_name.index (self.cur_mm_name))
        self.cur_mm_name = ""
        self.show_mm ()
 
    def create_gui (self, master): 
        debug ("In DataVizManager::create_gui ()")
        if not master:
            debug ("In DataVizManager::create_gui: Error: No master widget.")
            return None        
        self.frame = Tkinter.Frame (master, relief='ridge', bd=2)
        self.frame.pack (side='top', fill='y', expand=1)
        self.create_module_gui (self.frame)

    def close_gui (self, event=None): 
        debug ("In DataVizManager::close_gui ()")
        self.frame.destroy ()

    def show_mm (self, event=None): 
        debug ("In DataVizManager::show_mm ()")
        mm_name = self.mm_lst.get ('active')
        if not mm_name:
            return
        if (self.cur_mm_name != mm_name) or (not self.cur_mm_name) :
            if self.cur_mm_name:
                old_mm = self.mod_mgr[self.cur_mm_name]
                old_mm.close_gui ()
            self.cur_mm_name = mm_name
            self.update_label ()
            mm = self.mod_mgr[self.cur_mm_name]
            mm.create_gui (self.frame)

    def update_label (self): 
        debug ("In DataVizManager::update_label ()")
        lab = "ModuleManager: %s"%self.cur_mm_name
        self.data_label.config (text=lab)

    def del_module_mgr_gui (self, event=None): 
        debug ("In DataVizManager::del_module_mgr_gui ()")
        key = self.mm_lst.get ('active')
        self.mm_lst.delete ('active')
        if key:
            if self.cur_mm_name:
                old_mm = self.mod_mgr[self.cur_mm_name]
                old_mm.close_gui ()
            self.del_module_mgr (key)
            if self.cur_mm_name:
                indx = self.mm_name.index (self.cur_mm_name)
                self.mm_lst.select_clear (0, 'end')
                self.mm_lst.activate (indx)
                self.mm_lst.select_set (indx)
                self.cur_mm_name = ""
                self.show_mm ()
            self.update_label ()

    def add_module_mgr_gui (self, event=None): 
        debug ("In DataVizManager::add_module_mgr_gui ()")
        if self.cur_mm_name:
            old_mm = self.mod_mgr[self.cur_mm_name]
            old_mm.close_gui ()
        mm = ModuleManager.ModuleManager (self)
        self.add_module_mgr (mm)
        self.mm_lst.insert ('end', self.cur_mm_name)
        self.mm_lst.select_clear (0, 'end')
        self.mm_lst.activate ('end')
        self.mm_lst.select_set ('end')
        self.cur_mm_name = ""
        self.show_mm ()

    def config_lut (self): 
        debug ("In DataVizManager::config_lut ()")
        self.lut_h.configure (self.frame)

