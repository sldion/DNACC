#!/usr/bin/env python
#
# $Id: ConfigVtkObj.py,v 1.30 2005/08/02 18:30:14 prabhu_r Exp $
#
# This python program/module takes a VTK object and provides a GUI 
# configuration for it.
#
# This code is distributed under the conditions of the BSD license.
# See LICENSE.txt for details.
#
# Copyright (c) 2000-2002, Prabhu Ramachandran.
#
# This software is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the above copyright notice for more information.
#
# Author contact information:
#   Prabhu Ramachandran <prabhu_r@users.sf.net>
#   http://www.aero.iitm.ernet.in/~prabhu/

""" This program/module takes a VTK object and provides a GUI
configuration for it.  Right now Tkinter is used for the GUI.

"""

import vtkMethodParser
import types, string, re

try:
    import Tkinter
except ImportError:
    print "Cannot import the Tkinter module. Install it and try again."
    sys.exit (1)

try:
    import tkMessageBox
    import tkColorChooser
except ImportError:
    print "Cannot import the tkMessageBox or tkColorChooser module."
    print "Install the modules and try again."
    sys.exit (1)

print_info = tkMessageBox.showinfo

def print_err (msg):
    tkMessageBox.showerror ("ERROR", msg)

# use this to print stuff for the user command run from the GUI
def prn (x):
    print x

def tk_2_vtk_color (tk_col):
    "Converts a Tk RGB color to a VTK RGB color."
    ONE_255 = 1.0/255.0
    return (tk_col[0]*ONE_255, tk_col[1]*ONE_255, tk_col[2]*ONE_255)


class VtkShowDoc:
    
    """ This class displays the documentation included in the __doc__
    attribute of the VTK object and its methods."""

    def __init__ (self, master=None):
        self.master = master
        
    def check_obj (self):
        try:
            self.obj.GetClassName ()
        except AttributeError:            
            msg = "Sorry! The object passed does not seem to be a "\
                  "VTK object!!"
            print_err (msg)
            return 0
        try:
            doc_ = self.obj.__doc__
        except AttributeError:
            msg = "Sorry! This particular version of the VTK-Python "\
                  "bindings does not feature embedded documentation "\
                  "of the class and its methods.  Please use a more "\
                  "up to date version of VTK."
            print_err (msg)
            return 0
        else:
            return 1

    def show_doc (self, vtk_obj):
        self.obj = vtk_obj
        if self.check_obj ():
            self.setup ()
            self.add_doc ()

    def setup (self):
        self.root = Tkinter.Toplevel (self.master)
        self.root.title ("Class Documentation for %s"%
                         self.obj.GetClassName ())
        self.root.protocol ("WM_DELETE_WINDOW", self.quit)
        f = Tkinter.Frame (self.root)
        f.pack (side='top', fill='both', expand=1)
        f.rowconfigure (0, weight=1)
        f.columnconfigure (0, weight=1)
        scr1 = Tkinter.Scrollbar (f, orient='vertical')
        scr2 = Tkinter.Scrollbar (f, orient='horizontal')
        self.txt = Tkinter.Text (f, yscrollcommand=scr1.set,
                                 xscrollcommand=scr2.set,state='normal')
        scr1.config (command=self.txt.yview) 
        scr2.config (command=self.txt.xview) 
        self.txt.grid (row=0, column=0, sticky='ewns')
        scr1.grid (row=0, column=1, sticky='ns')
        scr2.grid (row=1, column=0, columnspan=2, sticky='ew')

        self.close_but = Tkinter.Button (self.root, text="Close", fg="red",
                                         underline=0, command=self.quit)

        self.close_but.pack (side='bottom')
        self.root.bind ("<Alt-c>", self.quit)
            
        self.txt.tag_config ("heading", foreground="blue",
                             underline=1, justify='center')
        self.txt.tag_config ("subheading", foreground="blue",
                             underline=1, justify='left')
        self.txt.tag_config ("item", underline=1, justify='left')
        self.txt.tag_config ("data", wrap='word')
    
    def add_doc (self):
        data_ = self.obj.GetClassName ()
        self.txt.insert ('end', "Class Documentation for %s\n\n"%data_,
                         "heading")
        data_ = self.obj.__doc__ + "\n\n"
        self.txt.insert ('end', data_, "data")
        data_ = "Please note that all the documented methods are not "\
                "configurable using the GUI provided.\n\n\n"
        self.txt.insert ('end', data_, "data")
        
        data_ = "Class method documentation:\n\n"
        self.txt.insert ('end', data_, "subheading")

        for i in dir (self.obj):
            if i == '__class__':
                continue
            try:
                data_ = eval ("self.obj.%s.__doc__"%i)
            except AttributeError:
                pass
            else:
                self.txt.insert ('end', i + ":\n", "item")
                self.txt.insert ('end', data_ +"\n\n", "data")

    def quit (self, event=None):
        self.root.destroy ()


class ConfigVtkObjFrame(Tkinter.Frame):
    
    """ This class finds the methods for a given vtkObject and creates
    a GUI to configure the object.  It uses the output from the
    VtkMethodParser class. It is subclassed from Tkinter.Frame so that
    it can be embedded inside another widget."""

    def __init__(self, master, renwin=None):
        Tkinter.Frame.__init__(self, master)
        self.renwin = renwin
        self.parser = vtkMethodParser.VtkMethodParser ()
        self.state_patn = re.compile ("To[A-Z0-9]")
        self.update_meth = None
        self.vtk_obj = None

    def _parse_methods (self, vtk_obj):
        self.parser.parse_methods (vtk_obj)
        self.toggle_meths = self.parser.toggle_methods ()
        self.state_meths = self.parser.state_methods ()
        self.get_set_meths = self.parser.get_set_methods ()
        self.get_meths = self.parser.get_methods ()

    def _get_state (self, meths):
        end = self.state_patn.search (meths[0]).start ()
        get_m = 'G'+meths[0][1:end]
        orig = eval ("self.vtk_obj.%s()"%get_m)
        for i in range (len(meths)):
            m = meths[i]
            eval ("self.vtk_obj.%s()"%m)
            val = eval ("self.vtk_obj.%s()"%get_m)
            if val == orig:
                break
        return i

    def _select_methods(self, get, toggle, state, get_set):        
        """ Selects or eliminates certain methods from being
        configured.  get, toggle, state and get_set are lists
        containing strings that are methods that one wants in the GUI
        or if the name is preprended with a '^' or '!' then those
        methods are removed from the default list.  You obviously
        cannot mix the negative and the positive selection (and
        neither does it make sense)!  So ['!AAA', 'BBB'] will simply
        unselect AAA and enable *everything* else. """
        def _choose_meths(from_arr, in_arr):
            # remove methods if needed.
            removed = 0
            for i in in_arr:
                if i[0] in ['!', '^']:
                    removed = 1
                    if i[1:] in from_arr:
                        from_arr.remove(i[1:])
            if removed:
                return
            tmp = from_arr[:]
            from_arr[:] = []
            for i in in_arr:
                if i in tmp:
                    from_arr.append(i)

        if get == []:
            self.get_meths = []
        elif get:
            _choose_meths(self.get_meths, get)

        if toggle == []:
            self.toggle_meths = []
        elif toggle:
            _choose_meths(self.toggle_meths, toggle)

        if state == [] or state:
            self.state_meths = state

        # Remove Get/SetProgress since its completely useless
        if 'Progress' in self.get_set_meths:
            self.get_set_meths.remove('Progress')
            
        if get_set == []:
            self.get_set_meths = []
        elif get_set:
            _choose_meths(self.get_set_meths, get_set)
            
    def _make_gui (self, one_frame=0):
        "Makes the configuration GUI."
        frame = Tkinter.Frame (self)
        frame.pack (side='top', expand=1, fill='both')
        if one_frame:
            left = frame
            right = frame
        else:
            left = Tkinter.Frame (frame)
            left.grid (row=0, column=0, sticky='nw')
            right = Tkinter.Frame (frame)
            right.grid (row=0, column=1, sticky='nw')

        self._make_gui_vars ()
        self._make_toggle_gui (left)
        self._make_state_gui (left)
        self._make_get_gui (right)
        self._make_get_set_gui (right)

    def _make_gui_vars (self):
        "Create the various variables used for the GUI."
        self.toggle_var = []
        for i in range (0, len (self.toggle_meths)):
            self.toggle_var.append (Tkinter.IntVar ())
            self.toggle_var[i].set (-1)

        self.state_var = []
        for i in range (0, len (self.state_meths)):
            self.state_var.append (Tkinter.IntVar ())
            self.state_var[i].set (-1)

        self.get_set_var = []
        for i in range (0, len (self.get_set_meths)):
            self.get_set_var.append (Tkinter.StringVar ())
            self.get_set_var[i].set ("")

        self.get_lab = []
        for i in range (0, len (self.get_meths)):
            self.get_lab.append (None)

    def _make_toggle_gui (self, master):
        "Create the toggle methods.  (On/Off methods)"
        n_meth = len (self.toggle_meths)
        if not n_meth:
            return
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top', expand=1, fill='both')
        for i in range (0, n_meth):
            m = "Get"+self.toggle_meths[i][:-2]
            self.toggle_var[i].set (eval ("self.vtk_obj.%s ()"%m))
            b = Tkinter.Checkbutton (frame, text=self.toggle_meths[i], 
                                     variable=self.toggle_var[i],
                                     onvalue=1, offvalue=0,
                                     command=lambda s=self, index=i:
                                     s._toggle_changed(index))
            b.grid (row=i, column=0, sticky='w')
            
    def _make_state_gui (self, master):
        "Create the state methods.  (SetAToB methods)"
        n_meth = len (self.state_meths)
        if not n_meth:
            return
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top', expand=1, fill='both')
        rw = 0
        for i in range (0, n_meth):
            meths = self.state_meths[i]
            self.state_var[i].set (self._get_state (meths))
            for j in range (0, len (meths)):
                b = Tkinter.Radiobutton (frame, text=meths[j], 
                                         variable=self.state_var[i],
                                         value=j,
                                         command=lambda s=self, index=i:
                                         s._state_changed(index))
                b.grid (row=rw, column=0, sticky='w')
                rw = rw + 1

    def _make_get_set_gui (self, master):
        "Create the Get/Set methods"
        n_meth = len (self.get_set_meths)
        if not n_meth:
            return
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top', expand=1, fill='both')
        for i in range (0, n_meth):
            m = "Get"+self.get_set_meths[i]
            self.get_set_var[i].set (str (eval ("self.vtk_obj.%s ()"%m)))

            # if the method requires a color make a button so the user
            # can choose the color!
            if string.find (m[-5:], "Color") > -1:
                but = Tkinter.Button (frame, text="Set"+m[3:],
                                      textvariable=i,
                                      command=lambda e: None, padx=1)
                but.grid (row=i, column=0, sticky='w')
                but.bind ("<1>", self._set_color)
            else:
                lab = Tkinter.Label (frame, text="Set"+m[3:])
                lab.grid (row=i, column=0, sticky='w')
            entr = Tkinter.Entry (frame, width=20, relief='sunken', 
                                  textvariable=self.get_set_var[i])
            entr.grid (row=i, column=1, sticky='ew')
            entr.bind ("<Return>", lambda e=None, s=self, index=i:
                       s._get_set_changed(index))
            
    def _make_get_gui (self, master):
        "Create the Get methods that have no Set equivalent."
        n_meth = len (self.get_meths)
        if not n_meth:
            return
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top', expand=1, fill='both')
        for i in range (0, n_meth):
            res = str (eval ("self.vtk_obj.%s ()"% self.get_meths[i]))
            lab = Tkinter.Label (frame, text=self.get_meths[i]+": ")
            lab.grid (row=i, column=0, sticky='w')
            self.get_lab[i] = Tkinter.Label (frame, text=res)
            self.get_lab[i].grid (row=i, column=1, sticky='w')

    def _set_color (self, event=None):
        "Choose and set a color from a GUI color chooser."
        if event is None:
            return "break"
        # index of the relevant method is stored in the textvariable.
        index = int (str(event.widget['textvariable']))

        m = "Get"+self.get_set_meths[index]
        col = eval ("self.vtk_obj.%s ()"%m)
        cur_col = "#%02x%02x%02x"% (col[0]*255, col[1]*255, col[2]*255)
        new_color = tkColorChooser.askcolor (title="Set"+m[3:],
                                             initialcolor=cur_col)
        if new_color[1] != None:
            col = tk_2_vtk_color (new_color[0])
            self.get_set_var[index].set (str (col))
            m = "Set"+self.get_set_meths[index]
            getattr(self.vtk_obj, m)(*col)
            self.update_gui ()

        return "break"

    def _toggle_changed(self, index):
        """One of the toggle buttons was clicked."""
        if not self.auto_update:
            return
        val = self.toggle_var[index].get()
        m = self.toggle_meths[index][:-2]
        if val == 1:
            getattr(self.vtk_obj, '%sOn'%m)()
        else:
            getattr(self.vtk_obj, '%sOff'%m)()
        self.render ()
        
    def _state_changed(self, index):
        """One of the state buttons was clicked."""
        if not self.auto_update:
            return
        val = self.state_var[index].get()
        m = self.state_meths[index][val]
        if val != -1:
            getattr(self.vtk_obj, "%s"%m)()
        self.render ()

    def _get_set_changed(self, index):
        """One of the get_set entries were changed."""
        if not self.auto_update:
            return
        var = self.get_set_var[index]
        val = var.get()
        m = self.get_set_meths[index]
        if string.find (val, "(") == 0:
            val = val[1:-1]
        st = 0
        val_tst = eval ("self.vtk_obj.Get%s ()"%m)
        if type (val_tst) is types.StringType:
            st = 1
        m = "Set" + m
        if st is 0:
            eval ("self.vtk_obj.%s (%s)"%(m, val))
        else:
            eval ("self.vtk_obj.%s (\"%s\")"%(m, val))

        self.render ()

    def configure(self, vtk_obj, get=None, toggle=None, state=None,
                  get_set=None, one_frame=0, auto_update=0):        
        """Configure the vtk_object passed and create the
        configuration widgets in self.  This class is a subclass of
        Tkinter.Frame.

        Input Arguments:

          vtk_obj -- VTK object to configure.

          get -- The Get* methods to display.  Defaults to None where
          all the options are displayed.  Provide an empty list if you
          do not want these to be displayed at all.  If the method
          name is preprended with a '^' or '!' then those methods are
          removed from the default list.  You obviously cannot mix the
          negative and the positive selection (and neither does it
          make sense)!  So ['!AAA', 'BBB'] will simply unselect AAA
          and enable *everything* else.  To specify a VTK method
          'GetGoo' you must specify 'GetGoo' or '!GetGoo' or
          '^GetGoo'.

          toggle -- The SetValueOn/Off type methods to configure.
          Defaults to None where all the methods are displayed.  To
          specify a VTK method 'GooOn' or 'GooOff' you must specify
          'GooOn' or '!GooOn' or '^GooOn'.

          state -- The SetValueToState type methods to configure
          Defaults to None where all the methods are displayed.  To
          specify a set of VTK method states [['SetGooToMoo',
          'SetGooToBoo']] you must pass them as specified.  You cannot
          specify the methods in the negative i.e. you can only pick
          the states you want.

          get_set -- The Get/SetValue methods to configure.  Defaults
          to None where all the methods are displayed.  To specify a
          VTK method 'Get/SetGoo' you must specify 'Goo' or '!Goo'
          or '^Goo'.

          one_frame -- If True, put all the GUI elements in one frame
          instead of a left and right one.  Defaults to 0.

          auto_update -- If True, updates the object as soon as the
          option is changed.  Defaults to 0 when the objects are
          updated using the apply_changes method.          
        """
        self.vtk_obj = vtk_obj
        self.auto_update = auto_update
        
        self.vtk_warn = -1
        try:
            self.vtk_warn = vtk_obj.GetGlobalWarningDisplay ()
        except AttributeError:
            pass
        else:
            vtk_obj.GlobalWarningDisplayOff ()
        self._parse_methods (vtk_obj)
        self._select_methods(get, toggle, state, get_set)
        
        self._make_gui (one_frame)
        if self.vtk_warn > -1:
            self.vtk_obj.SetGlobalWarningDisplay (self.vtk_warn)

    def set_render_window (self, renwin):
        self.renwin = renwin

    def set_update_method (self, method):
        """ This sets a method that the instance will call when any
        changes are made."""
        self.update_meth = method

    def apply_changes (self, event=None):
        "Apply the changes made to configuration."
        if self.vtk_warn > -1:
            self.vtk_obj.GlobalWarningDisplayOff ()

        n_meth = len (self.toggle_meths)
        for i in range (0, n_meth):
            val = self.toggle_var[i].get ()
            m = self.toggle_meths[i][:-2]
            if val == 1:
                eval ("self.vtk_obj.%sOn ()"%m)
            else:
                eval ("self.vtk_obj.%sOff ()"%m)                

        n_meth = len (self.state_meths)
        for i in range (0, n_meth):
            val = self.state_var[i].get ()
            m = self.state_meths[i][val]
            if val != -1:
                eval ("self.vtk_obj.%s ()"%m)
        
        n_meth = len (self.get_set_meths)
        for i in range (0, n_meth):
            val = self.get_set_var[i].get ()
            if string.find (val, "(") == 0:
                val = val[1:-1]
            st = 0
            val_tst = eval ("self.vtk_obj.Get%s ()"% self.get_set_meths[i])
            if type (val_tst) is types.StringType:
                st = 1
            m = "Set"+self.get_set_meths[i]
            if st is 0:
                eval ("self.vtk_obj.%s (%s)"%(m, val))
            else:
                eval ("self.vtk_obj.%s (\"%s\")"%(m, val))

        n_meth = len (self.get_meths)
        for i in range (0, n_meth):
            res = str (eval ("self.vtk_obj.%s ()"% self.get_meths[i]))
            self.get_lab[i].config (text=res)

        self.render ()
        if self.vtk_warn > -1:
            self.vtk_obj.SetGlobalWarningDisplay (self.vtk_warn)
                
    def render (self):
        "Render scene and update anything that needs updating."
        if self.update_meth and callable (self.update_meth):
            self.update_meth ()
        if self.renwin:
            try:
                self.renwin.Render ()
            except:
                pass

    def update_gui (self, event=None):
        "Update the values if anything has changed outside."
        if self.vtk_warn > -1:
            self.vtk_obj.GlobalWarningDisplayOff ()

        n_meth = len (self.toggle_meths)
        for i in range (0, n_meth):
            m = "Get"+self.toggle_meths[i][:-2]
            self.toggle_var[i].set (eval ("self.vtk_obj.%s ()"%m))

        for i in range (len (self.state_meths)):
            m = self.state_meths[i]
            self.state_var[i].set (self._get_state (m))

        n_meth = len (self.get_set_meths)
        for i in range (0, n_meth):
            m = "Get"+self.get_set_meths[i]
            self.get_set_var[i].set (str (eval ("self.vtk_obj.%s ()"%m)))
        n_meth = len (self.get_meths)
        for i in range (0, n_meth):
            res = str (eval ("self.vtk_obj.%s ()"% self.get_meths[i]))
            self.get_lab[i].config (text=res)

        if self.vtk_warn > -1:
            self.vtk_obj.GlobalWarningDisplayOn ()

    def destroy(self):
        Tkinter.Frame.destroy(self)
        self.vtk_obj = None
        self.renwin = None
        self.update_meth = None


class ConfigVtkObj:

    """ This class finds the methods for a given vtkObject and creates
    a GUI to configure the object.  It uses the output from the
    VtkMethodParser class and uses the configuration widget from
    ConfigVtkObjFrame. """

    def __init__ (self, renwin=None):
        # This vairable is used to do a redraw on changing the objects
        # properties.
        self.renwin = renwin
        self.config_frame = None
        self.vtk_obj = None

    def set_render_window (self, renwin):
        self.renwin = renwin
        if self.config_frame:
            self.config_frame.set_render_window(renwin)

    def set_update_method (self, method):
        """ This sets a method that the instance will call when any
        changes are made."""
        if self.config_frame:
            self.config_frame.set_update_method(method)

    def configure (self, master, vtk_obj, get=None, toggle=None, state=None,
                   get_set=None, one_frame=0, auto_update=0, run_command=1,
                   class_doc=1):
        """Configure the vtk_object passed using a Toplevel widget.

        Input Arguments:

          master -- master widget for this toplevel widget.

          vtk_obj -- VTK object to configure.

          get -- The Get* methods to display.  Defaults to None where
          all the options are displayed.  Provide an empty list if you
          do not want these to be displayed at all.  If the method
          name is preprended with a '^' or '!' then those methods are
          removed from the default list.  You obviously cannot mix the
          negative and the positive selection (and neither does it
          make sense)!  So ['!AAA', 'BBB'] will simply unselect AAA
          and enable *everything* else.  To specify a VTK method
          'GetGoo' you must specify 'GetGoo' or '!GetGoo' or
          '^GetGoo'.

          toggle -- The SetValueOn/Off type methods to configure.
          Defaults to None where all the methods are displayed.  To
          specify a VTK method 'GooOn' or 'GooOff' you must specify
          'GooOn' or '!GooOn' or '^GooOn'.

          state -- The SetValueToState type methods to configure
          Defaults to None where all the methods are displayed.  To
          specify a set of VTK method states [['SetGooToMoo',
          'SetGooToBoo']] you must pass them as specified.  You cannot
          specify the methods in the negative i.e. you can only pick
          the states you want.

          get_set -- The Get/SetValue methods to configure.  Defaults
          to None where all the methods are displayed.  To specify a
          VTK method 'Get/SetGoo' you must specify 'Goo' or '!Goo'
          or '^Goo'.

          one_frame -- If True, put all the GUI elements in one frame
          instead of a left and right one.  Defaults to 0.

          auto_update -- If True, updates the object as soon as the
          option is changed.  Defaults to 0 when the objects are
          updated only when the OK or Apply buttons are pressed.  If
          True the OK/Apply/Cancel buttons are replaced with a close
          button.
          
          run_command -- If True (default), also generates a Entry to
          run arbitrary commands on the object.

          class_doc -- If True (default), presents a button that shows
          VTK class documentation when clicked.
        """        
        self.vtk_obj = vtk_obj

        self.root = Tkinter.Toplevel (master)
        self.root.title ("Configure %s"%self.vtk_obj.GetClassName ())
        self.root.protocol ("WM_DELETE_WINDOW", self.cancel)
        self.config_frame = ConfigVtkObjFrame(self.root, self.renwin)
        self.config_frame.configure(vtk_obj, get, toggle, state, get_set,
                                    one_frame, auto_update)
        self.config_frame.pack (side='top', expand=1, fill='both')
        self.make_control_gui (self.root, run_command, auto_update,
                               class_doc)

    def make_control_gui (self, master, run_command, auto_update,
                          class_doc):
        "Make the main controls and the user command entry."
        frame = Tkinter.Frame (master)
        frame.pack (side='bottom', expand=1, fill='both')
        rw = 0
        self.user_command = Tkinter.StringVar ()
        self.user_command.set("")
        if run_command:
            lab = Tkinter.Label (frame, text="Click on the \"Command\" "\
                                 "button for help on it.")
            lab.grid (row=0, column=0, columnspan=4, sticky='ew')
            rw += 1
            help = Tkinter.Button (frame, text="Command:", 
                                   command=self.help_user)
            help.grid (row=1, column=0, sticky='ew')
            entr = Tkinter.Entry (frame, width=20, relief='sunken', 
                                  textvariable=self.user_command)
            entr.grid (row=1, column=1,  columnspan=3, sticky='ew')
            entr.bind ("<Return>", self.run_command)
            rw += 1
        column = 0
        if class_doc:
            help_b = Tkinter.Button (frame, text="Class Documentation",
                                     underline=6, command=self.show_doc)
            help_b.grid (column=column, row=rw, padx=2, pady=2, sticky='ew')
            column += 1
        if auto_update:
            b2 = Tkinter.Button (frame, text="Close", underline=0,
                                 command=self.cancel)
            b2.grid (column=column, row=rw, padx=2, pady=2, sticky='ew')
            column += 1
        else:
            b0 = Tkinter.Button (frame, text="Update", underline=0, 
                                 command=self.config_frame.update_gui)
            b0.grid (column=column, row=rw, padx=2, pady=2, sticky='ew')
            column += 1
            b = Tkinter.Button (frame, text="Apply", underline=0,
                                command=self.config_frame.apply_changes)
            b.grid (column=column, row=rw, padx=2, pady=2, sticky='ew')
            column += 1
            b1 = Tkinter.Button (frame, text="Ok", underline=0,
                                 command=self.ok_done)
            b1.grid (column=column, row=rw, padx=2, pady=2, sticky='ew')
            column += 1
            b2 = Tkinter.Button (frame, text="Cancel", underline=0,
                                 command=self.cancel)
            b2.grid (column=column, row=rw, padx=2, pady=2, sticky='ew')
            column += 1
            
        rw +=1

        # keyboard accelerators
        self.root.bind ("<Alt-d>", self.show_doc)
        self.root.bind ("<Alt-u>", self.config_frame.update_gui)
        self.root.bind ("<Alt-a>", self.config_frame.apply_changes)
        self.root.bind ("<Alt-o>", self.ok_done)
        self.root.bind ("<Alt-c>", self.cancel)

    def run_command (self, event=None):
        """Run the command entered by the user."""
        st = self.user_command.get ()
        if len (st) == 0:
            return self.help_user ()
        obj = self.vtk_obj
        try:
            eval (st)
        except AttributeError, msg:
            print_err ("AttributeError: %s"%msg)
        except SyntaxError, msg:
            print_err ("SyntaxError: %s"%msg)
        except NameError, msg:
            print_err ("NameError: %s"%msg)
        except TypeError, msg:
            print_err ("TypeError: %s"%msg)
        except ValueError, msg:
            print_err ("ValueError: %s"%msg)
        except:
            print_err ("Unhandled exception.  Wrong input.")
        else:
            self.config_frame.render ()

    def help_user (self, event=None):
        """Provide help when user clicks the command button."""
        msg = "Enter a valid python command.  Please note the "\
              "following: The name \'obj\' refers to the vtkObject "\
              "being configured.  Use the function prn(arguments) "\
              "to print anything.  Use the enter key to run the "\
              "command.  Example: obj.SetColor(0.1,0.2,0.3)"
        print_info  ("Help", msg)

    def show_doc (self, event=None):
        "Show the class documentation."
        d = VtkShowDoc (self.root)
        d.show_doc (self.vtk_obj)
                
    def ok_done (self, event=None):
        "Ok button clicked."
        self.config_frame.apply_changes ()
        self.root.destroy ()
        self.renwin = None
        self.vtk_obj = None
        self.config_frame = None

    def cancel (self, event=None):
        "Cancel button clicked."
        self.root.destroy ()
        self.renwin = None
        self.vtk_obj = None
        self.config_frame = None

    def show (self):
        "Print the various methods of the vtkobject."
        print "Toggle Methods\n", self.config_frame.toggle_meths
        print "State Methods\n", self.config_frame.state_meths
        print "Get/Set methods\n", self.config_frame.get_set_meths
        print "Get methods\n", self.config_frame.get_meths


if __name__ == "__main__":  
    import vtk
    from vtk.tk import vtkTkRenderWidget
    cone = vtk.vtkConeSource()
    cone.SetResolution(8)
    coneMapper = vtk.vtkPolyDataMapper()
    coneMapper.SetInput(cone.GetOutput())
    coneActor = vtk.vtkActor()
    coneActor.SetMapper(coneMapper)
    axes = vtk.vtkCubeAxesActor2D ()

    def quit (event=None):
        root.destroy ()

    root = Tkinter.Tk ()
    wid = vtkTkRenderWidget.vtkTkRenderWidget (root, width=500, height=500)
    wid.pack (expand=1, fill='both')
    wid.bind ("<KeyPress-q>", quit)
    ren = vtk.vtkRenderer()
    renWin = wid.GetRenderWindow()
    renWin.AddRenderer(ren)
    renWin.SetSize(500,500)
    ren.AddActor (coneActor)
    ren.AddActor (axes)
    axes.SetCamera (ren.GetActiveCamera ())
    renWin.Render ()

    for obj in (renWin, ren, cone, coneMapper, coneActor, axes):
        print "Configuring", obj.GetClassName (), "..."
        conf = ConfigVtkObj (renWin)
        conf.configure (root, obj)

    root.mainloop ()
