"""
This module creates a 'Picker', that can interactively select a point
and/or a cell in the data.  It also can use a world point picker
(i.e. a generic point in space) and will probe for the data at that
point.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.6 $"
__date__ = "$Date: 2005/08/02 18:26:25 $"
__credits__ = """Jose Paulo <moitinho@civil.ist.utl.pt> provided an initial and valuable first implementation."""

import Common
import Tkinter
import vtk

debug = Common.debug

def format(point, data, id):
    """ Formats the picked data suitably for printing."""
    ret = ""
    if not point:
        return "No valid point picked."
    elif not data:
        return "No valid data at picked point."
    elif id < 0:
        return "No valid picked id."
    else:
        ret = "Picked position: %f, %f, %f\n"%(point[0], point[1], point[2])
        
    sc, vec, tens = data.GetScalars(), data.GetVectors(), data.GetTensors()

    val = None
    if sc:
        val = sc.GetTuple1(id)
    ret += "Scalar: %s\n"%str(val)

    val = None
    if vec:
        val = vec.GetTuple3(id)
    ret += "Vector: %s\n"%str(val)

    val = None
    if tens:
        val = tens.GetTuple9(id)
    if val:
        ret += "Tensor: %s\n\t%s\n\t%s\n"%\
               (str(val[:3]), str(val[3:6]), str(val[6:9]))
    else:
        ret += "Tensor: None\n"

    return ret


def get_last_input(data):
    """Attempts to get the deepest possible data value in the
    pipeline.  Used when probing a selected point."""
    tmp = inp = data
    while tmp:
        try:
            tmp = inp.GetInput()
            if tmp:
                inp = tmp
        except AttributeError:
            tmp = None
    return inp


class Picker:

    """This module creates a 'Picker', that can interactively select a
    point and/or a cell in the data.  It also can use a world point
    picker (i.e. a generic point in space) and will probe for the data
    at that point.  """

    def __init__ (self, master, renwin):
        debug ("In Picker::__init__ ()")
        self.renwin = renwin
        self.master = master
        self.pointpicker = vtk.vtkPointPicker()
        self.cellpicker = vtk.vtkCellPicker()
        self.worldpicker = vtk.vtkWorldPointPicker()
        self.probe_point = vtk.vtkPoints()
        self.probe_data = vtk.vtkPolyData()
        self.pick_type_var = Tkinter.IntVar()
        self.tol_var = Tkinter.DoubleVar ()
        self.tol_var.set(self.pointpicker.GetTolerance())
        self.root = None
        self.txt = None

        # Use a set of axis to show the picked point.
        self.p_source = vtk.vtkAxes ()
        self.p_mapper = vtk.vtkPolyDataMapper ()
        self.p_actor = vtk.vtkActor ()

        self._initialize ()
        
    def _initialize (self):
        debug ("In Picker::_initialize ()")
        self.p_source.SetSymmetric (1)
        self.p_actor.PickableOff()
        self.p_actor.VisibilityOff()
        self.p_actor.GetProperty().SetLineWidth(2)
        self.p_actor.GetProperty().SetAmbient(1.0)
        self.p_actor.GetProperty().SetDiffuse(0.0)        
        self.p_mapper.SetInput(self.p_source.GetOutput())
        self.p_actor.SetMapper(self.p_mapper)
        self.renwin.add_actors (self.p_actor)

        self.probe_point.SetNumberOfPoints(1)
        self.probe_point.SetPoint(0, 0.0, 0.0, 0.0)
        self.probe_data.SetPoints(self.probe_point)
        self.pick_type_var.set(1)

    def pick(self, event=None):
        """Calls the picker depending on the value of the variable."""
        debug ("In Picker::pick ()")
        self.show()
        val = self.pick_type_var.get()
        if val == 1:
            return self.pick_point(event)
        elif val == 2:
            return self.pick_cell(event)
        elif val == 3:
            return self.pick_world(event)

    def write_pick (self, data):
        """ Write data to the log window."""
        debug ("In Picker::write_pick ()")
        self.txt.insert ('end', data+'\n')
        self.txt.update_idletasks ()
        self.txt.see('end')
        # print data

    def pick_point (self, event=None):
        """ Picks the nearest point."""
        debug ("In Picker::pick_point ()")
        h = self.renwin.tkwidget.winfo_height() - 1
        self.pointpicker.Pick( (float(event.x), float(h-event.y), \
                                float(0)), self.renwin.get_renderer())

        pp = self.pointpicker   # convenience
        id = pp.GetPointId()

        if ( id > -1):
            self.write_pick ("Picked Point number:" + str(id))
            coord = pp.GetPickPosition()
            data = pp.GetMapper().GetInput().GetPointData()

            prn = format(coord, data, id)
            self.write_pick(prn)
            bounds = pp.GetMapper().GetInput().GetBounds()

            dx = 0.3*(bounds[1]-bounds[0])
            dy = 0.3*(bounds[3]-bounds[2])
            dz = 0.3*(bounds[5]-bounds[4])

            scale = max(dx,dy,dz)

            self.p_source.SetOrigin (coord)
            self.p_source.SetScaleFactor(scale)

            self.p_actor.VisibilityOn()
        else:
            self.write_pick("No valid point picked\n")
            self.p_actor.VisibilityOff()

        self.renwin.Render()
        self.write_pick("\n")

    def pick_cell (self, event=None):
        """ Picks the nearest cell."""
        debug ("In Picker::pick_cell ()")
        h = self.renwin.tkwidget.winfo_height() - 1 
        self.cellpicker.Pick( (float(event.x), float(h-event.y), \
                                    float(0)), self.renwin.get_renderer())

        cp = self.cellpicker
        id = cp.GetCellId()

        if ( id > -1):
            self.write_pick ("Picked Cell number:" + str(id))
            coord = cp.GetPickPosition()
            cell_data = cp.GetMapper().GetInput().GetCellData()

            prn = format(coord, cell_data, id)
            self.write_pick(prn)

            bounds = cp.GetMapper().GetInput().GetBounds()

            dx = 0.3*(bounds[1]-bounds[0])
            dy = 0.3*(bounds[3]-bounds[2])
            dz = 0.3*(bounds[5]-bounds[4])

            scale = max(dx, dy, dz)

            self.p_source.SetOrigin (cp.GetPickPosition())
            self.p_source.SetScaleFactor (scale)

            self.p_actor.VisibilityOn()
        else:
            self.write_pick ("No Cell was picked")
            self.p_actor.VisibilityOff()

        self.renwin.Render()
        self.write_pick("\n")

    def pick_world (self, event=None):
        """ Picks a world point and probes for data there."""
        debug ("In Picker::pick_world ()")
        h = self.renwin.tkwidget.winfo_height() - 1 
        self.worldpicker.Pick( (float(event.x), float(h-event.y), \
                                float(0)), self.renwin.get_renderer())

        # use the cell picker to get the data that needs to be probed.
        self.cellpicker.Pick( (float(event.x), float(h-event.y), \
                                float(0)), self.renwin.get_renderer())

        wp = self.worldpicker
        cp = self.cellpicker
        coord = wp.GetPickPosition()
        self.probe_point.SetPoint(0, coord)

        if (cp.GetMapper()):
            self.write_pick ("Picked generic point.")            
            data = get_last_input(cp.GetMapper().GetInput())
            # I need to create the probe each time because otherwise
            # it does not seem to work properly.            
            probe = vtk.vtkProbeFilter()
            probe.SetSource(data)
            probe.SetInput(self.probe_data)
            probe.Update()
            out = probe.GetOutput().GetPointData()
            prn = format(coord, out, 0)
            self.write_pick(prn)

            bounds = cp.GetMapper().GetInput().GetBounds()

            dx = 0.3*(bounds[1]-bounds[0])
            dy = 0.3*(bounds[3]-bounds[2])
            dz = 0.3*(bounds[5]-bounds[4])

            scale = max(dx, dy, dz)

            self.p_source.SetOrigin (coord)
            self.p_source.SetScaleFactor (scale)

            self.p_actor.VisibilityOn()
        else:
            self.write_pick ("No valid data near picked point.")
            self.p_actor.VisibilityOff()

        self.renwin.Render()
        self.write_pick("\n")

    def select_picking(self, event=None):        
        """ Called when the picker type is changed from the GUI."""
        pass

    def set_tolerance(self, event=None):
        """ Called by the GUI when the tolerance is changed."""
        debug ("In Picker::set_tolerance ()")
        if ( self.tol_var.get() > 0.5 ):
            self.tol_var.set(0.5)

        if ( self.tol_var.get() < 0. ):
            self.tol_var.set(0.)
        
        self.pointpicker.SetTolerance(self.tol_var.get())
        self.cellpicker.SetTolerance(self.tol_var.get())

    def _lift (self):
        """Lifts an already created configuration window to the
        top."""
        debug ("In Picker::_lift ()")
        self.root.deiconify ()
        self.root.lift ()
        
    def show (self): 
        """Create the GUI configuration controls for this object."""
        debug ("In Picker::show ()")
        if (self.root and self.root.winfo_exists ()):
            return self._lift ()
        self.root = Tkinter.Toplevel (self.master)
        main_win = self.root.master.winfo_toplevel ()
        self.root.geometry ("+%d+%d" % (main_win.winfo_rootx()+5,
                                        main_win.winfo_rooty()+5))
        #self.root.focus_set ()
        self.root.title ("Configure %s module"%self.__class__.__name__)
        self.root.protocol ("WM_DELETE_WINDOW", self.close_gui)

        self.make_custom_gui ()

    def make_custom_gui (self):
        """ This function is called by configure().  Use this to
        customize your own GUI."""
        debug ("In Picker::make_custom_gui ()")
        self.make_main_gui ()
        self.make_close_button ()

    def make_main_gui (self):
        debug ("In Picker::make_main_gui ()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', pady=2, fill='both', expand=1)

        rw = 0

        but = Tkinter.Radiobutton (frame,
                                   text="Nearest Point", 
                                   variable=self.pick_type_var,
                                   value=1,
                                   command=self.select_picking)
        but.grid (row=rw, column=0, columnspan=1,
                  pady=4, sticky='w')

        rw = rw + 1
        but = Tkinter.Radiobutton (frame,
                                   text="Nearest Cell", 
                                   variable=self.pick_type_var,
                                   value=2,
                                   command=self.select_picking)
        but.grid (row=rw, column=0, columnspan=1,
                  pady=4, sticky='w')

        rw = rw + 1
        but = Tkinter.Radiobutton (frame,
                                   text="Generic Point and Probe", 
                                   variable=self.pick_type_var,
                                   value=3,
                                   command=self.select_picking)
        but.grid (row=rw, column=0, columnspan=1,
                         pady=4, sticky='w')

        rw = rw + 1

        tol_label = Tkinter.Label( frame, text="Picking tolerance:")
        tol_label.grid (row=rw, column=0, sticky='ew')

        tol_entry = Tkinter.Entry (frame, width=10, relief='sunken',
                                   textvariable=self.tol_var)
        tol_entry.grid (row=rw, column=1, sticky='ew')
        tol_entry.bind ("<Return>", self.set_tolerance)

        rw = rw + 1
        
        sub_frame = Tkinter.Frame (self.root, relief='sunken', bd=2)
        sub_frame.pack (side='top', pady=2, fill='both', expand=1)
        sub_frame.rowconfigure (0, weight=1)
        sub_frame.columnconfigure (0, weight=1)
        scr1 = Tkinter.Scrollbar (sub_frame, orient='vertical')
        scr2 = Tkinter.Scrollbar (sub_frame, orient='horizontal')
        self.txt = Tkinter.Text (sub_frame, yscrollcommand=scr1.set,
                                 xscrollcommand=scr2.set,
                                 state='normal', wrap='none', width=60)
        scr1.config (command=self.txt.yview) 
        scr2.config (command=self.txt.xview) 
        self.txt.grid (row=0, column=0, sticky='ewns')
        scr1.grid (row=0, column=1, sticky='ns')
        scr2.grid (row=1, column=0, columnspan=2, sticky='ew')

    def make_close_button (self):
        """ Create a close button for the GUI control."""
        debug ("In Picker::make_close_button ()")
        but = Tkinter.Button (self.root, text="Close", underline=0,
                              command=self.close_gui)
        but.pack (side='bottom', fill='both', expand=1)
        self.root.bind ("<Alt-c>", self.close_gui)

    def close_gui(self, event=None):
        """Called when the 'close' button is clicked."""
        debug ("In Picker::close_gui ()")
        self.p_actor.VisibilityOff()
        self.root.master.focus_set ()
        self.root.withdraw()

