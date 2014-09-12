"""

This file defines a class LutHandler that creates and manages a lookup
table and a scalar bar (legend) for it.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.17 $"
__date__ = "$Date: 2005/08/02 18:26:25 $"

import Tkinter, tkFileDialog, types
import vtk, os
import Common, Base.Objects
import vtkPipeline.vtkMethodParser
import Lut_Editor
import GradientEditor

tk_fopen = tkFileDialog.askopenfilename
debug = Common.debug


def getLutIndices (lut, min_v, max_v):
    """Returns a list of indices in the lookup table that correspond
    to min_v and max_v."""
    
    debug ("In getLutIndices ()")    
    if hasattr(lut, 'GetIndex'):
        return [lut.GetIndex (min_v), lut.GetIndex (max_v)]
    else:
        c_min = lut.GetColor (min_v)
        c_max = lut.GetColor (max_v)
        nc = lut.GetNumberOfColors ()
        ret = [0,  nc-1]
        for i in range (nc):
            if lut.GetTableValue (i)[:-1] == c_min:
                ret[0] = i
            if lut.GetTableValue (i)[:-1] == c_max:
                ret[1] = i
                return ret
        return ret


def check_range (val, def_rng):
    debug ("In check_range ()")
    rng = list (def_rng)
    try:
        rng = eval (val)
        len (rng)
    except: # XXX Fixme.
        msg = "Invalid range: Please enter a list of two numbers!"
        Common.print_err (msg)
        return rng

    if len (rng) != 2:
        rng = rng[:2]

    try:
        v = (float (rng[0]), float (rng[1]))
    except ValueError:
        rng = def_rng

    if rng[0] > rng[1]:
        rng = [rng[1], rng[0]]

    return rng


class LutHandler (Base.Objects.VizObject):
    """  
    Creates and manages a lookup table and a scalar bar (legend).
    Overload functions appropriately to get user defined behaviour."""
    def __init__ (self): 
        debug ("In LutHandler::__init__ ()")
        Base.Objects.VizObject.__init__ (self)
        self.lut_var = Tkinter.IntVar ()
        self.lut_var.set (1)
        self.reverse_lut_var = Tkinter.IntVar()
        self.reverse_lut_var.set(0)
        self.legend_on = Tkinter.IntVar ()
        self.legend_on.set (0)
        self.legend_orient = Tkinter.IntVar ()
        self.legend_orient.set (0)        
        self.n_label = Tkinter.IntVar ()
        self.n_label.set (8)
        self.n_color_var = Tkinter.IntVar ()
        self.n_color_var.set (256)
        self.shadow_on_var = Tkinter.IntVar ()
        self.shadow_on_var.set (0)
        self.label_var = Tkinter.StringVar ()
        self.label_var.set ('')
        self.file_name = ""

        self.data_range = [0.0, 1.0]
        self.orig_data_range = [0.0, 1.0]
        self.range_var = Tkinter.StringVar ()
        self.range_var.set (str (self.data_range))
        self.range_on_var = Tkinter.IntVar ()
        self.range_on_var.set (0)

        self.visible_data_range = [0.0, 1.0]
        self.v_range_var = Tkinter.StringVar ()
        self.v_range_var.set (str (self.visible_data_range))
        self.v_range_on_var = Tkinter.IntVar ()
        self.v_range_on_var.set (0)
        
    def __del__ (self):
        debug ("In LutHandler::__del__ ()")
        self.module_mgr.get_render_window().remove_actors(self.sc_bar)

    def initialize (self, module_mgr): 
        "Initialize data, given a ModuleManager object."
        debug ("In LutHandler::initialize ()")
        self.module_mgr = module_mgr
        self.init_lut ()
        self.init_scalar_bar ()
        self.pipe_objs = (self.lut, self.sc_bar)
        self.renwin = module_mgr.get_render_window ()

    def init_lut (self): 
        "Set up the default LookupTable. Defaults to a blue to red table."
        debug ("In LutHandler::init_lut ()")
        self.lut = vtk.vtkLookupTable ()
        self.lut.SetHueRange (0.667, 0.0)
        self.lut.SetNumberOfTableValues (self.n_color_var.get ())
        self.lut.SetRampToSQRT()
        self.lut.Build ()
        
    def init_scalar_bar (self): 
        "Sets up the default scalar bar."
        debug ("In LutHandler::init_scalar_bar ()")
        self.sc_bar = vtk.vtkScalarBarActor ()
        self.sc_bar.SetLookupTable (self.lut)
        self.sc_bar.GetPositionCoordinate ().SetCoordinateSystemToNormalizedViewport ()
        self.set_horizontal ()
        self.sc_bar.SetVisibility (0)
        self.sc_bar.SetNumberOfLabels (8)
        fg_color = Common.config.fg_color
        self.sc_bar.GetProperty ().SetColor(fg_color)
        if hasattr(self.sc_bar, "GetTitleTextProperty"):
            ttp = self.sc_bar.GetTitleTextProperty()
            ltp = self.sc_bar.GetLabelTextProperty()
            ttp.SetShadow (self.shadow_on_var.get ())
            ltp.SetShadow (self.shadow_on_var.get ())
            ttp.SetColor(fg_color)
            ltp.SetColor(fg_color)
        else:
            self.sc_bar.SetShadow (self.shadow_on_var.get ())
        self.module_mgr.get_render_window ().add_actors (self.sc_bar)
            
    def save_config_to_dict (self, base_file_name):
        """Save the configuration of this object and return a
        dictionary.

        base_file_name -- The absolute file name relative to which the
        relative filename will be stored.
        """        
        debug ("In LutHandler::save_config ()")
        s = {}
        s['lut_var'] = self.lut_var.get()
        s['reverse_lut_var'] = self.reverse_lut_var.get()
        s['range_on_var'] = self.range_on_var.get()
        s['v_range_on_var'] = self.v_range_on_var.get()
        s['visible_data_range'] = self.visible_data_range
        s['base_file_name'] = base_file_name
        if self.file_name:
            s['file_name'] = os.path.abspath(self.file_name)
        else:
            s['file_name'] = self.file_name
        
        rel_file_name = ""
        if (self.file_name):
            rel_file_name = Common.get_relative_file_name (base_file_name,
                                                           self.file_name)
        s['rel_file_name'] = rel_file_name
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for key, obj in (('lut_config', self.lut),
                         ('sc_bar_config', self.sc_bar),
                         ('sc_bar_prop_config',
                          self.sc_bar.GetProperty()),
                         ('sc_bar_pos_config',
                          self.sc_bar.GetPositionCoordinate()),
                         ('sc_bar_pos2_config',
                          self.sc_bar.GetPosition2Coordinate())):
            cfg = {}
            p.dump (obj, cfg)
            s[key] = cfg

        return s

    def save_config (self, file):
        """Save configuration of this object to passed file."""
        s = self.save_config_to_dict(file.name)
        file.write("%s\n"%str(s))

    def _setup_config(self, file_name):
        self.data_range = self.lut.GetTableRange ()
        self.legend_on.set (self.sc_bar.GetVisibility ())
        self.legend_orient.set (self.sc_bar.GetOrientation ())
        self.n_label.set (self.sc_bar.GetNumberOfLabels ())
        self.n_color_var.set (self.lut.GetNumberOfTableValues ())
        if hasattr(self.sc_bar, "GetTitleTextProperty"):
            self.shadow_on_var.set (self.sc_bar.GetTitleTextProperty().GetShadow ())
        else:
            self.shadow_on_var.set (self.sc_bar.GetShadow ())

        if file_name:
            self.load_lut_from_file (file_name)
        else:
            self.change_lut ()
        self.change_legend_orient ()

        self.range_var.set (str (self.data_range))
        self.v_range_var.set (str (self.visible_data_range))

        self.set_data_range (self.orig_data_range)
        if self.v_range_on_var.get ():
            self._make_transparent_lut ()

    def load_config (self, input):
        """Load configuration for this object.

         file -- input can be either a file or a dictionary.
         """        
        debug ("In LutHandler::load_config ()")
        isfile = 1
        if type(input) == type({}):
            isfile = 0
            base_file_name = input['base_file_name']
            inp = input
        else:
            base_file_name = input.name
            pos = input.tell()
            val = input.read(1)
            input.seek(pos)
            if val == '{':
                isfile = 0
                inp = eval(input.readline())
            else:
                inp = input
                
        if isfile:
            val = inp.readline ()
            lut_v, r_on, v_r_on, v_d_r = (self.lut_var.get(),
                                          self.range_on_var.get(),
                                          self.v_range_on_var.get(),
                                          self.visible_data_range)
            try:
                lut_v, r_on, v_r_on, v_d_r = eval (val)
            except (TypeError, ValueError): # old format
                lut_v = int (val)

            if lut_v in [2, 4]:
                # these values were used before reverse_lut existed
                self.reverse_lut_var.set(1)
            lut_v = [0, 1, 1, 2, 2][lut_v]
            file_name = inp.readline ()[:-1]
        else:
            lut_v, r_on = (inp['lut_var'], inp['range_on_var'])
            v_r_on, v_d_r = (inp['v_range_on_var'],
                             inp['visible_data_range'])
            self.reverse_lut_var.set(inp['reverse_lut_var'])
            file_name = inp['rel_file_name']            

        self.lut_var.set (lut_v)
        self.range_on_var.set (r_on)
        self.v_range_on_var.set (v_r_on)
        self.visible_data_range = v_d_r

        if file_name:
            file_name = Common.get_abs_file_name (base_file_name,
                                                  file_name)
            if not isfile:
                if not os.path.isfile(file_name):
                    file_name = inp['file_name']
                
            if not os.path.isfile (file_name):
                msg = "Unable to open Lookup Table file: " + file_name
                msg = msg + "\n\nPlease try selecting the file manually."
                Common.print_err (msg)
                file_name = tk_fopen (title="Open LuT file", 
                                      filetypes=[("Lookup table files",
                                                  "*.lut"), 
                                                 ("All files", "*")])

        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        if isfile:
            for obj in (self.lut, self.sc_bar, self.sc_bar.GetProperty (),
                        self.sc_bar.GetPositionCoordinate (),
                        self.sc_bar.GetPosition2Coordinate ()):
                p.load (obj, inp)
        else:
            for key, obj in (('lut_config', self.lut),
                             ('sc_bar_config', self.sc_bar),
                             ('sc_bar_prop_config',
                              self.sc_bar.GetProperty()),
                             ('sc_bar_pos_config',
                              self.sc_bar.GetPositionCoordinate()),
                             ('sc_bar_pos2_config',
                              self.sc_bar.GetPosition2Coordinate())):
                p.load (obj, inp[key])

        if hasattr(self.sc_bar, "GetTitleTextProperty"):
            color = self.sc_bar.GetProperty().GetColor()
            self.sc_bar.GetTitleTextProperty().SetColor(color)
            self.sc_bar.GetLabelTextProperty().SetColor(color)

        self._setup_config(file_name)

    def config_changed (self): 
        debug ("In LutHandler::config_changed ()")
        color = Common.config.fg_color
        self.sc_bar.GetProperty ().SetColor(color)
        if hasattr(self.sc_bar, "GetTitleTextProperty"):
            self.sc_bar.GetTitleTextProperty().SetColor(color)
            self.sc_bar.GetLabelTextProperty().SetColor(color)

    def set_horizontal (self): 
        "Makes the legend horizontal with default values."
        debug ("In LutHandler::set_horizontal ()")
        self.sc_bar.GetPositionCoordinate().SetValue (0.1,0.01)
        self.sc_bar.SetOrientationToHorizontal ()
        self.sc_bar.SetWidth (0.8)
        self.sc_bar.SetHeight (0.14)

    def set_vertical (self): 
        "Makes the legend horizontal with default values."
        debug ("In LutHandler::set_vertical ()")
        self.sc_bar.GetPositionCoordinate().SetValue (0.01,0.15)
        self.sc_bar.SetOrientationToVertical ()
        self.sc_bar.SetWidth (0.14)
        self.sc_bar.SetHeight (0.85)

    def set_lut_bw (self): 
        "Change the lookup table to a black and white one."
        debug ("In LutHandler::set_lut_bw ()")
        self.lut.Allocate(0,0)
        self.lut.SetHueRange (0.0, 0.0)
        self.lut.SetSaturationRange (0.0, 0.0)
        self.lut.SetValueRange (0.0, 1.0)
        self.lut.SetNumberOfTableValues (self.n_color_var.get ())
        self.lut.SetRampToSQRT()
        self.lut.ForceBuild ()
        self.sc_bar.Modified ()

    def set_lut_wb (self): 
        "Change the lookup table to a white and black one."
        debug ("In LutHandler::set_lut_wb ()")
        self.lut.Allocate(0,0)
        self.lut.SetHueRange (0.0, 0.0)
        self.lut.SetSaturationRange (0.0, 0.0)
        self.lut.SetValueRange (1.0, 0.0)
        self.lut.SetNumberOfTableValues (self.n_color_var.get ())
        self.lut.SetRampToSQRT()
        self.lut.ForceBuild ()
        self.sc_bar.Modified ()

    def set_lut_blue_red (self): 
        "Change the lookup table to a blue to red one."
        debug ("In LutHandler::set_lut_blue_red ()")
        self.lut.Allocate(0,0)
        self.lut.SetHueRange (0.6667, 0.0)
        self.lut.SetSaturationRange (1.0, 1.0)
        self.lut.SetValueRange (1.0, 1.0)
        self.lut.SetNumberOfTableValues (self.n_color_var.get ())
        self.lut.SetRampToSQRT()
        self.lut.ForceBuild ()
        self.sc_bar.Modified ()

    def set_lut_red_blue (self): 
        "Change the lookup table to a red to blue one."
        debug ("In LutHandler::set_lut_red_blue ()")
        self.lut.Allocate(0,0)
        self.lut.SetHueRange (0.0, 0.6667)
        self.lut.SetSaturationRange (1.0, 1.0)
        self.lut.SetValueRange (1.0, 1.0)
        self.lut.SetNumberOfTableValues (self.n_color_var.get ())
        self.lut.SetRampToSQRT()
        self.lut.ForceBuild ()
        self.sc_bar.Modified ()

    def _make_transparent_lut (self):        
        """Takes makes the lut such that only the visible range is
        opaque.  The rest are made visible."""        
        debug ("In LutHandler::_make_transparent_lut ()")
        if self.v_range_on_var.get ():
            lut = self.lut
            n_colors = lut.GetNumberOfTableValues ()
            ldr = self.visible_data_range
            if type (ldr[0]) not in (types.TupleType, types.ListType):
                ldr = [ldr]
            # make everything transparent.
            saved_alpha = [1.0]*n_colors
            for i in range (n_colors):
                val = lut.GetTableValue (i)
                saved_alpha[i] = val[-1]
                lut.SetTableValue (i, val[0], val[1], val[2], 0.0)

            # now set the visible range.
            for dr in ldr:
                irange = getLutIndices (lut, dr[0], dr[1])
                for i in range (irange[0], irange[1] + 1):
                    val = lut.GetTableValue (i)
                    lut.SetTableValue (i, val[0], val[1], val[2],
                                       saved_alpha[i])

    def _restore_lut (self):        
        """Restores the lut to its original non-transparent state"""        
        debug ("In LutHandler::_restore_lut ()")
        val = self.lut_var.get ()
        if val == 0:
            self.load_lut_from_file (self.file_name)
        else:
            self.change_lut ()
            
    def set_data_range (self, data_range): 
        debug ("In LutHandler::set_data_range ()")
        old_range = list(self.data_range)
        self.orig_data_range = data_range
        if self.range_on_var.get () == 0:
            self.data_range = data_range
            self.range_var.set (str (data_range))
        if self.v_range_on_var.get () == 0:
            self.visible_data_range = data_range
            self.v_range_var.set (str (data_range))
        else:
            if old_range != self.data_range:
                self._make_transparent_lut ()

        dr = self.data_range
        self.lut.SetRange (dr[0], dr[1])
        self.sc_bar.Modified ()

    def get_data_range (self):
        debug ("In LutHandler::get_data_range ()")
        return self.data_range

    def set_data_name (self, data_name): 
        debug ("In LutHandler::set_data_name ()")
        self.data_name = data_name
        self.sc_bar.SetTitle (data_name)
        self.sc_bar.Modified ()

    def get_lut (self): 
        debug ("In LutHandler::get_lut ()")
        return self.lut

    def get_scalarbar (self): 
        debug ("In LutHandler::get_scalarbar ()")
        return self.sc_bar

    def make_main_gui (self): 
        debug ("In LutHandler::make_main_gui ()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)

        self.make_lut_gui (frame)
        self.make_range_gui (frame)
        self.make_scbar_gui (frame)

    def make_lut_gui (self, master): 
        debug ("In LutHandler::make_lut_gui ()")
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)
        rw = 0
        but = Tkinter.Button (frame, text="Load Lookup Table",
                              command=self.load_lut)
        but.grid (row=rw, column=0, pady=2)
        rw += 1
        but = Tkinter.Button (frame, text="Edit Lookup Table",
                              command=self.edit_lut)
        but.grid (row=rw, column=0, pady=2)
        rw += 1
        but = Tkinter.Button (frame, text="Create Lookup Table",
                              command=self.create_lut)
        but.grid (row=rw, column=0, pady=2)
        rw += 1
        
        rb = Tkinter.Radiobutton (frame, text='blue-red colormap',
                                  value=1, variable=self.lut_var,
                                  command=self.change_lut)
        rb.grid (row=rw, column=0, pady=2, sticky='w')
        rw += 1
        rb = Tkinter.Radiobutton (frame, text='black-white colormap',
                                  value=2, variable=self.lut_var,
                                  command=self.change_lut)
        rb.grid (row=rw, column=0, pady=2, sticky='w')
        rw += 1

        cb = Tkinter.Checkbutton(frame, text='Reverse LUT',
                                 onvalue=1, offvalue=0,
                                 variable=self.reverse_lut_var,
                                 command=self.reverse_lut_gui)
        cb.grid (row=rw, column=0, pady=2, sticky='ew')
        rw += 1

    def make_range_gui (self, master):
        debug ("In LutHandler::make_range_gui ()")
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)
        rw = 0
        cb = Tkinter.Checkbutton (frame, text="Use specified data range",
                                  variable=self.range_on_var,
                                  onvalue=1, offvalue=0,
                                  command=self.set_range_on)
        cb.grid (row=rw, column=0, columnspan=2, pady=2, sticky='w')
        rw = rw + 1
        lab = Tkinter.Label (frame, text="Data Range:")
        lab.grid (row=rw, column=0, pady=2, sticky='w')
        entr = Tkinter.Entry (frame, width=10, relief='sunken',
                              textvariable=self.range_var)
        entr.grid (row=rw, column=1, pady=2, sticky='ew')
        entr.bind ("<Return>", self.set_range_var)

        rw = rw + 1
        cb = Tkinter.Checkbutton (frame, text="Use visible range",
                                  variable=self.v_range_on_var,
                                  onvalue=1, offvalue=0,
                                  command=self.set_v_range_on)
        cb.grid (row=rw, column=0, columnspan=2, pady=2, sticky='w')
        rw = rw + 1
        lab = Tkinter.Label (frame, text="Visible Range:")
        lab.grid (row=rw, column=0, pady=2, sticky='w')
        entr = Tkinter.Entry (frame, width=10, relief='sunken',
                              textvariable=self.v_range_var)
        entr.grid (row=rw, column=1, pady=2, sticky='ew')
        entr.bind ("<Return>", self.set_v_range_var)        

    def make_scbar_gui (self, master): 
        debug ("In LutHandler::make_scbar_gui ()")
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)
        rw = 0
        cb = Tkinter.Checkbutton (frame, text="Show Legend",
                                  variable=self.legend_on,
                                  onvalue=1, offvalue=0,
                                  command=self.legend_on_off)
        cb.grid (row=rw, column=0, columnspan=2, pady=2, sticky='w')
        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text='Horizontal',
                                  value=0, variable=self.legend_orient,
                                  command=self.change_legend_orient)
        rb.grid (row=rw, column=0, columnspan=2, pady=2, sticky='w')
        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text='Vertical',
                                  value=1, variable=self.legend_orient,
                                  command=self.change_legend_orient)
        rb.grid (row=rw, column=0, columnspan=2, pady=2, sticky='w')
        rw = rw + 1
        b = Tkinter.Checkbutton (frame, text="Shadow Legend", 
                                 variable=self.shadow_on_var,
                                 onvalue=1, offvalue=0,
                                 command=self.set_shadow)
        b.grid (row=rw, column=0, columnspan=2, pady=2, sticky='w')
        rw = rw + 1        
        lab = Tkinter.Label (frame, text="Number of Labels:")
        lab.grid (row=rw, column=0, pady=2, sticky='w')
        entr = Tkinter.Entry (frame, width=5, relief='sunken',
                              textvariable=self.n_label)
        entr.grid (row=rw, column=1, pady=2, sticky='ew')
        entr.bind ("<Return>", self.set_n_label)

        rw = rw + 1
        lab = Tkinter.Label (frame, text="Number of Colors:")
        lab.grid (row=rw, column=0, pady=2, sticky='w')
        entr = Tkinter.Entry (frame, width=5, relief='sunken',
                              textvariable=self.n_color_var)
        entr.grid (row=rw, column=1, pady=2, sticky='ew')
        entr.bind ("<Return>", self.set_n_color)
        rw = rw + 1

        self.label_var.set (self.sc_bar.GetTitle ())
        lab = Tkinter.Label (frame, text="Legend text:")
        lab.grid (row=rw, column=0, pady=2, sticky='w')
        entr = Tkinter.Entry (frame, width=10, relief='sunken',
                              textvariable=self.label_var)
        entr.grid (row=rw, column=1, pady=2, sticky='ew')
        entr.bind ("<Return>", self.set_label)
        
    def load_lut (self, event=None): 
        debug ("In LutHandler::load_lut ()")
        file_name = tk_fopen (title="Open LuT file", 
                              initialdir=Common.config.initial_dir,
                              filetypes=[("Lookup table files", "*.lut"), 
                                         ("All files", "*")])
        self.load_lut_from_file (file_name)
        self._make_transparent_lut ()

    def load_lut_from_file (self, file_name): 
        debug ("In LutHandler::load_lut_from_file ()")
        lut_list = []
        if file_name:
            try:
                f = open (file_name, 'r')
            except IOError:
                msg = "Sorry cannot open Lookup Table file: %s"%file_name
                raise IOError, msg
            else:
                f.close()
                try:
                    lut_list = Lut_Editor.parse_lut_file (file_name)
                except Lut_Editor.LutParseError:
                    msg = "Sorry Lut_Editor couldn't parse "\
                          "file: %s"%file_name
                    raise Lut_Editor.LutParseError, msg
                else:
                    Common.state.busy ()
                    if self.reverse_lut_var.get():
                        lut_list.reverse()
                    Lut_Editor.set_lut (self.lut, lut_list)
                    self.file_name = file_name
                    self.lut_var.set (0)
                    self.n_color_var.set(len(lut_list))
                    self.renwin.Render ()
                    Common.state.idle ()

    def edit_lut (self, event=None): 
        debug ("In LutHandler::edit_lut ()")
        self.lut_var.set (0)
        app = Lut_Editor.Lut_Editor (self.root)
        app.edit_lut (self.lut)
        self.file_name = app.run ()
        self._make_transparent_lut ()

    def create_lut (self, event=None): 
        debug ("In LutHandler::create_lut ()")
        self.lut_var.set (0)
        def OnChangeColorTable():
            self.renwin.Render()
        cge = GradientEditor.GradientEditor(self.root, self.lut,
                                            OnChangeColorTable)

    def change_lut (self): 
        "Changes the lookup table to use."
        debug ("In LutHandler::change_lut ()")
        self.reverse_lut(self.reverse_lut_var.get())

    def change_legend_orient (self): 
        "Changes orientation of the legend."
        debug ("In LutHandler::change_legend_orient ()")
        val = self.legend_orient.get ()
        if val == 0:
            self.set_horizontal ()
        elif val == 1:
            self.set_vertical ()
        self.renwin.Render ()

    def legend_on_off (self): 
        debug ("In LutHandler::legend_on_off ()")
        self.sc_bar.SetVisibility (self.legend_on.get ())
        self.renwin.Render ()

    def set_n_label (self, event=None):
        debug ("In LutHandler::set_n_label ()")
        self.sc_bar.SetNumberOfLabels (self.n_label.get ())
        self.sc_bar.Modified ()
        self.renwin.Render ()

    def set_n_color (self, event=None):
        debug ("In LutHandler::set_n_color ()")
        n = self.n_color_var.get ()
        if self.lut_var.get():
            self.lut.SetNumberOfTableValues (n)
            self.lut.Modified ()
            self.lut.Build()
            self.renwin.Render () # this is needed!
            self.sc_bar.SetMaximumNumberOfColors (n)
            self.sc_bar.Modified ()
            self.renwin.Render ()

    def set_shadow (self, event=None):
        debug ("In LutHandler::set_shadow ()")
        if hasattr(self.sc_bar, "GetTitleTextProperty"):
            self.sc_bar.GetTitleTextProperty ().SetShadow (self.shadow_on_var.get ())
            self.sc_bar.GetLabelTextProperty ().SetShadow (self.shadow_on_var.get ())
        else:
            self.sc_bar.SetShadow (self.shadow_on_var.get ())
        self.sc_bar.Modified ()
        self.renwin.Render ()

    def set_label (self, event=None):
        debug ("In LutHandler::set_label ()")
        self.sc_bar.SetTitle (self.label_var.get ())
        self.sc_bar.Modified ()
        self.renwin.Render ()

    def set_range_on (self, event=None):
        debug ("In LutHandler::set_range_on ()")
        val = self.range_on_var.get ()
        self.set_data_range (self.orig_data_range)
        self.module_mgr.Update ()

    def set_range_var (self, event=None):
        debug ("In LutHandler::set_range_var ()")
        val = self.range_var.get ()
        rng = check_range (val, self.data_range)
        self.range_var.set (str(rng))
        self.data_range = rng
        self.set_data_range (self.orig_data_range)
        if self.range_on_var.get ():
            self.module_mgr.Update ()

    def set_v_range_on (self, event=None):
        debug ("In LutHandler::set_v_range_on ()")
        val = self.v_range_on_var.get ()
        if val:
            self._make_transparent_lut ()
        else:
            self._restore_lut ()
        self.sc_bar.Modified ()
        self.renwin.Render ()

    def set_v_range_var (self, event=None):
        old_range = list (self.visible_data_range)
        val = self.v_range_var.get ()
        try:
            vr = eval (val)
        except: # XXX Fixme.
            msg = "Invalid range(s): Please enter a list of two "\
                  "numbers or a list of list of two numbers!"
            Common.print_err (msg)
            vr = old_range

        nr = 1
        try:
            list (vr[0])
        except TypeError:
            vr = [vr]
        else:
            nr = len (vr)

        if type (old_range[0]) in (types.TupleType, types.ListType):
            d_rng = [old_range[-1]]*(nr - len (old_range))
            def_rng = old_range + d_rng
        else:
            def_rng = [old_range]*nr

        rng = []
        for i in range (nr):
            r = check_range (str (vr[i]), def_rng[i])
            rng.append (r)
            
        self.v_range_var.set (str (rng))
        self.visible_data_range = rng
        if self.v_range_on_var.get () and (old_range != rng):
            self._restore_lut ()
            self._make_transparent_lut ()
            
        self.sc_bar.Modified ()
        self.renwin.Render ()

    def reverse_lut_gui(self, event=None):
        val = self.reverse_lut_var.get()
        self.reverse_lut(val)

    def reverse_lut(self, val):
        Common.state.busy ()
        self.reverse_lut_var.set(val)
        lut_n = self.lut_var.get()
        if lut_n == 1:
            self.file_name = ""
            if val:
                self.set_lut_red_blue()
            else:
                self.set_lut_blue_red()
        elif lut_n == 2:
            self.file_name = ""
            if val:
                self.set_lut_wb()
            else:
                self.set_lut_bw()
        else:
            self.load_lut_from_file(self.file_name)
        self._make_transparent_lut ()
        self.renwin.Render ()
        Common.state.idle ()

