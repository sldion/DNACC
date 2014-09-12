#!/usr/bin/env python
""" 
Author: Prabhu Ramachandran <prabhu_r@users.sf.net>

Description:

A simple, powerful lookup table editor.  Useful to edit and modify
lookup tables by hand tuning them.  This can be used in a standalone
fashion and can also be used from another python script.  The user
interface uses Tkinter and some of the builtin, cool, widgets that
come with it.

The format of the data file that the lookup tables is exactly the same
as the format used by VTK.  Refer the VTK book or the VTK data format
document avaliable at http://www.kitware.com/FileFormats.pdf. The data
has to be in ASCII.

The editor currently can handle only 32 colors (I can increase it but
32 is enough).  One can hand edit the data files too since they are
plain text and merge two or more and thereby obtain a larger number of
colors and use this lookup table elsewhere.  One can insert/delete and
modify colors easily.

Double click on a color to edit it.  Use the edit menu to delete or
insert colors.

Bugs:
The classes are not documented.

License:

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2000-2002, Prabhu Ramachandran.
"""

import Tkinter
import tkMessageBox
import tkFileDialog
import tkSimpleDialog
import tkColorChooser
import string, sys

def set_lut (vtk_lut, lut_lst):
    n_col = len (lut_lst)
    vtk_lut.SetNumberOfColors (n_col)
    vtk_lut.Build ()
    for i in range (0, n_col):
        lt = lut_lst[i]
        vtk_lut.SetTableValue (i, lt[0], lt[1], lt[2], lt[3])

    return vtk_lut


def print_err (str):
    tkMessageBox.showerror ("ERROR", str)

class LutParseError (Exception):
    pass

def check_lut_first_line (line):
    first = string.split (line)
    if first[0] != "LOOKUP_TABLE":
        errmsg = "Error: The input data file \"%s\"\n"%(file_name)
        errmsg = errmsg+ "is not a proper lookup table file."\
                 " No LOOKUP_TABLE tag in first line. Try again."
        print_err (errmsg)
        raise LutParseError
    try:
        n_color = first[2]
    except:
        print_err ("Error: No size for LookupTable specified.")
        raise LutParseError
    else:
        return n_color

def parse_lut_file (file_name):
    input = open (file_name, "r")

    line = input.readline ()
    n_color = check_lut_first_line (line)

    lut = []
    for line in input.readlines ():
        entr = string.split (line)
        if len (entr) != 4:
            errmsg="Error: insufficient or too much data in line "\
                    "-- \"%s\""%(entr)
            print_err (errmsg)
            raise LutParseError

        tmp = []
        for color in entr:
            try:
                tmp.append (string.atof (color))
            except:
                print_err ("Unknown entry in lookup table input.")
                raise LutParseError
        lut.append (tmp)

    return lut


def write_lut_to_file (file_name, lut):
    output = open (file_name, "w")
    n_col = len (lut)
    output.write ("LOOKUP_TABLE some_name %d\n"%(n_col))
    for i in range (0, n_col):
        c = lut[i]
        str = "%f %f %f %f\n"%(c[0], c[1], c[2], c[3])
        output.write (str)
    output.close ()


def tk_2_lut_color (tk_col):
    # The alpha values are not changed.  They all default to 1.0
    ONE_255 = 1.0/255.0
    return [tk_col[0]*ONE_255, tk_col[1]*ONE_255, tk_col[2]*ONE_255, 1.0]


LUT_EDITOR_MAX_COLORS=32

class Lut_Editor:
    def __init__ (self, parent, height=600, width=130):
        self.height=height
        self.width=width
        self.ONE_255=1.0/255.0
        self.root = Tkinter.Toplevel (parent)
        self.root.title ("Lookup Table Editor")
        self.make_menus ()

        self.lut_changed = 0
        self.edit_lut_mode = 0
        self.vtk_lut = None
        self.lut = []
        self.lut_but = []
        self.file_name = ""
        self.current_but = Tkinter.IntVar ()

    def make_menus (self):
        self.menu = Tkinter.Menu (self.root, tearoff=0)
        self.root.config (menu=self.menu)

        self.filemenu = Tkinter.Menu (self.menu, tearoff=0)
        self.menu.add_cascade (label="File", menu=self.filemenu, 
                               underline=0)
        self.editmenu = Tkinter.Menu (self.menu, tearoff=0)
        self.menu.add_cascade (label="Edit", menu=self.editmenu, 
                               underline=0)

        self.filemenu.add_command (label="New", underline=0, 
                                   command=self.open_new)
        self.filemenu.add_command (label="Open", underline=0, 
                                   command=self.open)
        self.filemenu.add_command (label="Save", underline=0, 
                                   command=self.save, state='disabled')
        self.filemenu.add_command (label="Save As", underline=5, 
                                   command=self.save_as, state='disabled')
        self.filemenu.add_command (label="Close", underline=1, 
                                   command=self.close, state='disabled')

        self.filemenu.add_command (label="Exit", underline=1, 
                                   command=self.quit)

        self.editmenu.add_command (label="Insert Color", underline=0,
                                   command=self.insert_color, 
                                   state='disabled')
        self.editmenu.add_command (label="Delete Color", underline=0,
                                   command=self.delete_color, 
                                   state='disabled')
        self.editmenu.add_command (label="Change Color", underline=0,
                                   command=self.change_color, 
                                   state='disabled')

    def initialize (self):
        n_col = len (self.lut)
        if n_col > LUT_EDITOR_MAX_COLORS:
            tkMessageBox.showerror ("ERROR", "ERROR:\nSorry, the "\
                                    "lookuptable editor supports "\
                                    "only less than 33 colors.")
            sys.exit (1)            
        self.frame = Tkinter.Frame (self.root, height=self.height,
                                    width=self.width)
        self.frame.pack (expand='true', fill='both')
        self.frame.bind ("<Configure>", self.resize)

        self.current_but.set (-1)

        for i in range (0, n_col):
            tmp = self.lut[i]
            color = "#%02x%02x%02x"% (tmp[0]*255, tmp[1]*255, tmp[2]*255)
            but = Tkinter.Radiobutton (self.frame, bg=color, 
                                       activebackground=color,
                                       selectcolor=color,
                                       variable=self.current_but, value=i,
                                       indicatoron='false')
            but.bind ("<Double-1>", self.change_color)
            self.lut_but.append (but)

        self.enable_menus ()
        self.place_colors ()

    def enable_menus (self):
        self.filemenu.entryconfig ("New", state='disabled')
        self.filemenu.entryconfig ("Open", state='disabled')
        for entr in ["Save", "Save As", "Close"]:
            self.filemenu.entryconfig (entr, state='normal')
        for entr in ["Insert Color", "Delete Color", "Change Color"]:
            self.editmenu.entryconfig (entr, state='normal')

    def disable_menus (self):
        self.filemenu.entryconfig ("New", state='normal')
        self.filemenu.entryconfig ("Open", state='normal')
        for entr in ["Save", "Save As", "Close"]:
            self.filemenu.entryconfig (entr, state='disabled')
        for entr in ["Insert Color", "Delete Color", "Change Color"]:
            self.editmenu.entryconfig (entr, state='disabled')

    def resize (self, event):
        if len (self.lut_but) != 0:
            self.height = event.height
            self.width = event.width
            self.place_colors ()

    def place_colors (self):
        n_col = len (self.lut_but)
        but_ht = self.height/n_col
        for i in range (0, n_col):
            self.lut_but[i].place (x=0, y=i*but_ht, width=self.width,
                                   height=but_ht)

    def change_color (self, event=None):
        but_no = self.current_but.get ()
        if but_no > -1:
            tmp = self.lut[but_no]
            cur_col = "#%02x%02x%02x"% (tmp[0]*255, tmp[1]*255, tmp[2]*255)
            new_color = tkColorChooser.askcolor (initialcolor=cur_col)
            if new_color[1] != None:
                self.lut_changed = 1
                self.lut_but[but_no].config (bg=new_color[1], 
                                             activebackground=new_color[1],
                                             selectcolor=new_color[1])

                tmp = tk_2_lut_color (new_color[0])
                self.lut[but_no] = tmp
                if self.edit_lut_mode == 1:
                    self.vtk_lut.SetTableValue (but_no, tmp[0], tmp[1], 
                                                tmp[2], tmp[3])

    def insert_color (self, event=None):
        if len (self.lut) == 0:
            return None
        but_no = self.current_but.get ()
        if but_no < 0:
            print_err ("Sorry, no color selected. Select color to "\
                       "insert the new color at. ")
            return None
        if len (self.lut) > LUT_EDITOR_MAX_COLORS:
            tkMessageBox.showerror ("ERROR", "ERROR:\nSorry, the "\
                                    "lookuptabe editor supports only "\
                                    "less than 33 colors.")
            return None
        self.lut_changed = 1
        tmp = self.lut[but_no]
        cur_col = "#%02x%02x%02x"% (tmp[0]*255, tmp[1]*255, tmp[2]*255)
        but = Tkinter.Radiobutton (self.frame, bg=cur_col, 
                                   activebackground=cur_col,
                                   selectcolor=cur_col,
                                   indicatoron='false',
                                   variable=self.current_but, value=but_no)
        but.bind ("<Double-1>", self.change_color)
        self.lut.insert (but_no, tmp)
        self.lut_but.insert (but_no, but)

        for i in range (but_no+1, len (self.lut)):
            self.lut_but[i].config (value=i)

        self.place_colors ()
        if self.edit_lut_mode == 1:
            set_lut (self.vtk_lut, self.lut)

    def delete_color (self, event=None):
        if len (self.lut) == 0:
            return None
        but_no = self.current_but.get ()
        if but_no < 0:
            print_err ("Sorry, no color selected. Select color to delete. ")
            return None

        self.lut_changed = 1
        for i in range (0, len (self.lut)):
            self.lut_but[i].place_forget ()

        del self.lut[but_no]
        del self.lut_but[but_no]

        for i in range (but_no, len (self.lut)):
            self.lut_but[i].config (value=i)

        self.place_colors ()
        if self.edit_lut_mode == 1:
            set_lut (self.vtk_lut, self.lut)

    def open_new (self):
        n_col = tkSimpleDialog.askinteger ("N_Colors", "Enter the number "\
                                           "of colors in new lookup table.",
                                           initialvalue=16, 
                                           minvalue=0,
                                           maxvalue=LUT_EDITOR_MAX_COLORS,
                                           parent=self.root)
        if n_col is None:
            return None

        cur_col = ((0,0,255), '#0000fe')
        ans = tkMessageBox.askyesno ("Choose color?", 
                                     "Choose individual colors? "\
                                     "Answer no to choose one color only.")
        if ans == 1:        
            for i in range (0, n_col):
                col = tkColorChooser.askcolor (title="Color number %d"%(i),
                                               initialcolor=cur_col[1])
                if col[1] is not None:
                    self.lut.append (tk_2_lut_color (col[0]))
                    cur_col = col
                else:
                    self.lut.append (tk_2_lut_color (cur_col[0]))
        else:
            col = tkColorChooser.askcolor (title="Choose default color", 
                                           initialcolor=cur_col[1])
            if col[1] is None:
                col = cur_col
            for i in range (0, n_col):
                self.lut.append (tk_2_lut_color (col[0]))
            
        self.lut_changed = 1
        self.initialize ()

    def open (self, event=None):
        gui_of = tkFileDialog.askopenfilename
        file_name = gui_of (title="Open LUT file",  
                            filetypes=[("Lookup table files", "*.lut"), 
                                       ("All files", "*")])
        if len (file_name) != 0:
            try:
                self.lut = parse_lut_file (file_name)
            except LutParseError:
                pass
            else:
                self.initialize ()

    def save (self, event=None):
        if self.lut_changed != 0:
            if len (self.file_name) != 0:
                self.lut_changed=0
                write_lut_to_file (self.file_name, self.lut)
            else:
                self.save_as ()

    def save_as (self, event=None):
        if len (self.lut) != 0:
            gui_sf = tkFileDialog.asksaveasfilename
            f_name = gui_sf (title="Save LUT to file", 
                             defaultextension=".lut",
                             filetypes=[("Lookup table files", "*.lut"), 
                                        ("All files", "*")])
            if len (f_name) != 0:
                self.file_name = f_name
                self.lut_changed = 1
                self.save ()
        else:
            print_err ("Nothing to save!")

    def clear (self):
        self.lut_changed = 0
        self.edit_lut_mode = 0
        self.vtk_lut = None
        self.file_name = ""
        self.lut = []
        self.lut_but = []
        self.current_but.set (-1)

    def close (self, event=None):
        if self.lut_changed != 0 and len (self.lut) != 0:
            msg = "Warning:\n The lookup table has been edited "\
                  "and you havent saved the changes to a file.  "\
                  "Are you sure you want to close?"
            ans = tkMessageBox.askyesno ("Close", msg)
            if ans == 1:
                self.frame.destroy ()
                self.disable_menus ()
                self.clear ()
        else:
            self.frame.destroy ()
            self.disable_menus ()
            self.clear ()

    def quit (self, event=None):
        if self.lut_changed != 0:
            msg = "Warning:\n The lookup table has been edited "\
                  "and you havent saved the changes to a file.  "\
                  "Are you sure you want to exit?"
            ans = tkMessageBox.askyesno ("Exit", msg)
            if ans == 1:
                self.root.destroy ()
        else:
            self.root.destroy ()


    def edit_lut (self, vtk_lut):
        gui_get_int = tkSimpleDialog.askinteger
        n_col =  gui_get_int ("N_Colors", "Enter the number of colors "\
                              "in the edited lookup table.", 
                              initialvalue=16, minvalue=0, 
                              maxvalue=LUT_EDITOR_MAX_COLORS,
                              parent=self.root)
        if n_col is None:
            return None

        #vtk_lut.Allocate (0,0)
        vtk_lut.SetNumberOfColors (n_col)
        vtk_lut.Build ()
        for i in range (0, n_col):
            lt = vtk_lut.GetTableValue (i)
            self.lut.append ([lt[0], lt[1], lt[2], lt[3]])

        self.lut_changed = 1
        self.edit_lut_mode = 1
        self.vtk_lut = vtk_lut
        self.initialize ()

    def run (self):
        self.root.wait_window (self.root)
        return self.file_name


if __name__ == "__main__":
    import vtk 
    root = Tkinter.Tk ()
    root.withdraw ()
    app = Lut_Editor (root)
    # create a new lookup table and edit it.
    # need this to create a new table from a hue range and also to set
    # the lut.
    lt = vtk.vtkLookupTable ()
    lt.SetHueRange (0.66667, 0.0)
    app.edit_lut (lt)
    app.run ()
    root.destroy ()
