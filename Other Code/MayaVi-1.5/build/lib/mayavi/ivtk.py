"""
ivtk - Interactive VTK.

A simple utility module that makes VTK easier to use from the Python
interpreter.  It requires that MayaVi be installed.  It provides the
following:

  (1) An easy to use VTK actor viewer that has menus to save the
  scene, change background, help browser, pipeline browser etc.

  (2) A simple class documentation search tool that lets you search
  for arbitrary strings in the VTK class documentation and lets you
  browse the VTK class documentation.

  (3) Easy GUI to configure VTK objects using the
  vtkPipeline.ConfigVtkObj module.

All of this makes using VTK from Python much easier and much more fun.

Example session:

  >>> import ivtk
  >>> from vtk import *
  >>> c = vtkConeSource()
  >>> m = vtkPolyDataMapper()
  >>> m.SetInput(c.GetOutput())
  >>> a = vtkActor()
  >>> a.SetMapper(m)
  >>> v = ivtk.create_viewer() # or ivtk.viewer()
  # this creates the easy to use render window that can be used from
  # the interpreter.  It has several useful menus.

  >>> v.AddActors(a)    # add actor(s) to viewer
  >>> v.config(c)       # pops up a GUI configuration for object.
  >>> v.doc(c)          # pops up class documentation for object.
  >>> v.help_browser()  # pops up a help browser where you can search!
  >>> v.RemoveActors(a) # remove actor(s) from viewer.

  Even without the viewer you can do the following:

  >>> import ivtk
  >>> d = ivtk.doc_browser()
  # pops up a standalone searcheable VTK class help browser.
  >>> from vtk import *
  >>> c = vtkConeSource()
  >>> ivtk.doc(c)            # pops up class documentation for c
  >>> ivtk.doc('vtkObject')  # class documentation for vtkObject.
  >>> ivtk.config(c)         # configure object with GUI.

Read the code for more details - most things are reasonably
documented.

License:

  This code is distributed under the conditions of the BSD license.
  See LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.13 $"
__date__ = "$Date: 2005/08/02 18:26:22 $"


import types, string, re
import vtk
import Tkinter, tkColorChooser
from vtkPipeline.ConfigVtkObj import ConfigVtkObj, VtkShowDoc, print_err
import vtkPipeline.vtkPipeline
import Misc.RenderWindow

def check_tk ():
    r = Tkinter._default_root
    if not r:
        r = Tkinter.Tk ()
        r.withdraw ()

def tk_2_vtk_color (tk_col):
    "Converts a Tk RGB color to a VTK RGB color."
    ONE_255 = 1.0/255.0
    return (tk_col[0]*ONE_255, tk_col[1]*ONE_255, tk_col[2]*ONE_255)


def doc (obj):
    """Shows the class documentation for passed VTK object or
    classname.

    Input arguments:

        obj -- this is either a VTK object or the class name of a VTK
        object that you want documentation for.
    """
    if type (obj) is types.StringType:
        o = eval ('vtk.%s()'%obj)
    else:
        o = obj

    check_tk ()
    d = VtkShowDoc ()
    d.show_doc (o)


def config (obj, renwin=None):
    """Provides a Tkinter based GUI that can be used to configure the
    passed VTK object.

    Input arguments:

      obj -- this is a VTK object that you want to configure.

      renwin -- An optional argument that points to the renderwindow
      being used.  Using this will force the window to be Rendered
      when the changes made to the window are applied.
      """
    check_tk ()
    c = ConfigVtkObj (renwin)
    c.configure (None, obj)


class Viewer:

    """ A simple actor viewer.  That allows one to easily add/remove
    actors and also allows one to save the rendered scene to an image.
    It also is capable of createing a VTK pipeline browser."""
    
    def __init__ (self, master):
        self.root = Tkinter.Toplevel (master)
        self.root.title ("VTK Actor Viewer")
        self.root.protocol ("WM_DELETE_WINDOW", self.Quit)
        self.root.minsize (450, 450)
	#self.root.geometry ("600x600+0+0")
        self.renwin_frame = Tkinter.Frame (self.root)
        self.renwin_frame.pack (side='left', fill='both', expand=1)
        self.renwin = Misc.RenderWindow.RenderWindow (self.renwin_frame)
        self.renwin.set_background ((0., 0., 0.))
        self.renwin.Render ()
        self.actors = []
        self.make_menus ()
        self.helper = VtkHelp (self.renwin)

    def make_menus (self): 
        self.menu = Tkinter.Menu (self.root, tearoff=0)
        self.root.config (menu=self.menu)

        self.file_menu = Tkinter.Menu (self.menu, tearoff=0)
        self.menu.add_cascade (label="File", menu=self.file_menu, 
			       underline=0)
        self.viz_menu = Tkinter.Menu (self.menu, tearoff=0)
        self.menu.add_cascade (label="Visualize", menu=self.viz_menu,
                               underline=0)

        self.option_menu = Tkinter.Menu (self.menu, tearoff=0)
        self.menu.add_cascade (label="Options", menu=self.option_menu,
                               underline=0)

        self.help_menu = Tkinter.Menu (self.menu, name='help', tearoff=0)
        self.menu.add_cascade (label="Help", menu=self.help_menu,
                               underline=0)        

        self.sshot_menu = Tkinter.Menu (self.file_menu, tearoff=0)
        self.file_menu.add_cascade (label="Save As", underline=1, 
                                    menu=self.sshot_menu)

        self.file_menu.add_command (label="Exit", underline=1, 
                                    command=self.Quit)
        
        ## Save As menus
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
        self.viz_menu.add_command (label="Pipeline browser", underline=0,
                                   command=self.PipelineBrowse)

        ## Option menus
        self.option_menu.add_command (label="Configure RenderWindow",
                                      underline=16,
                                      command=self.ConfigRenWin)
        self.option_menu.add_command (label="Change Background",
                                      underline=7,
                                      command=self.SetBackground)
        self.option_menu.add_command (label="Configure Lights",
                                      underline=10,
                                      command=self.renwin.config_lights)
        ## Help menu
        self.help_menu.add_command (label="Search VTK docs",
                                    underline=0, 
                                    command=self.help_browser)
        
    def SetBackground (self):
        """Choose and set a color from a GUI color chooser and change
        the colors of the background."""
        rw_col = self.renwin.get_renderer ().GetBackground ()
        col = rw_col
        cur_col = "#%02x%02x%02x"% (col[0]*255, col[1]*255, col[2]*255)
        new_color = tkColorChooser.askcolor (title="Background color",
                                             initialcolor=cur_col)
        if new_color[1] != None:
            col = tk_2_vtk_color (new_color[0])
            self.renwin.set_background (col)
            self.renwin.Render ()

    def PipelineBrowse (self, event=None):
        "Creates a graphical VTK pipeline browser."
        rw = self.renwin.get_vtk_render_window ()
        pipe_b = vtkPipeline.vtkPipeline.vtkPipelineBrowser (self.root, rw)
        pipe_b.browse ()

    def ConfigRenWin (self, event=None):
        "Creates a configuration window for the render window."
        self.renwin.configure (self.root)
        
    def Quit (self, event=None):
        "Closes the window."
        self.renwin.remove_actors (self.actors)
        self.actors = []
        self.renwin.quit ()
        self.root.destroy ()

    def AddActors (self, actors):
        """ Adds a single actor or a tuple or list of actors to the
        renderer.

        Input arguments:

           actors -- A single actor or a tuple/list of actors that are
           to be added.
        """        
        self.renwin.add_actors (actors)
        if len (self.actors) == 0:
            self.renwin.tkwidget.Reset (0, 0)
        try:
            actors[0]
        except TypeError:
            self.actors.append (actors)
        else:
            self.actors.extend (list(actors))
        self.renwin.Render ()

    def RemoveActors (self, actors):  
        """ Removes a single actor or a tuple or list of actors to the
        renderer.

        Input arguments:

           actors -- A single actor or a tuple/list of actors that are
           to be removed.
        """
        self.renwin.remove_actors (actors)
        try:
            actors[0]
        except TypeError:
            self.actors.remove (actors)
        else:
            for a in actors:
                self.actors.remove (a)
        self.renwin.Render ()

    def GetActors (self):
        """Returns a list of actors currently being rendered."""
        return self.actors

    def Render (self):
        """Renderers the scene."""
        self.renwin.Render ()

    def GetRenWin (self):
        "Returns the vtkTkRenderWindow being used."
        return self.renwin

    def GetActiveCamera (self):
        "Returns the active VTK camera being used."
        return self.renwin.GetActiveCamera ()
        
    def GetRenderer (self):
        "Returns the vtkRenderer being used."
        return self.ren

    def GetRenderWindow (self): 
        "Returns the vtkRenderWindow being used."
        return self.renwin.get_render_window ()

    def get_helper (self):
        """Returns an instance of VtkHelp that can be used to show
        documentation, search through the classes etc."""
        return self.helper

    def config (self, obj):
        """Configure the object using the helper."""
        self.helper.config (obj)

    def doc (self, obj):
        """Get docs for the object using the helper."""
        self.helper.doc (obj)

    def help_browser (self, event=None):
        """Popup the search/help browser."""
        h = HelpBrowser (self.root)
        

class VtkHelp:

    """A simple class that is provides methods to show class
    documentation, configure VTK objects, search for classes and
    search through class documentation."""

    def __init__(self, renwin=None):
        self.renwin = renwin
        self.root = Tkinter._default_root
        if not self.root:
            self.root = Tkinter.Tk ()
            self.root.withdraw ()

        self.vtk_classes = dir (vtk)

        n = len (self.vtk_classes)
        self.vtk_c_name = ['']*n
        self.vtk_c_doc = ['']*n

        # setup the data.
        for i in range (n):
            c = self.vtk_classes[i]
            self.vtk_c_name[i] = string.lower (c)
            if c[:3] == 'vtk':
                try:
                    doc = string.lower (getattr(vtk, c).__doc__)
                    self.vtk_c_doc[i] = doc
                except AttributeError:
                    pass

    def doc (self, obj):
        """Shows the class documentation for passed VTK object or
        classname.

        Input arguments:

           obj -- this is either a VTK object or the class name of a
           VTK object that you want documentation for."""

        if type (obj) is types.StringType:
            try:
                o = eval ('vtk.%s()'%obj)
            except AttributeError:
                print "Sorry vtk does not have the class %s"%obj
                return
        else:
            o = obj
        d = VtkShowDoc (self.root)
        d.show_doc (o)

    def config (self, obj, renwin=None):
        """Provides a Tkinter based GUI that can be used to configure
        the passed VTK object.

        Input arguments:

            obj -- this is a VTK object that you want to configure.

            renwin -- An optional argument that points to the
            renderwindow being used.  Using this will force the window
            to be Rendered when the changes made to the window are
            applied.  If not passed the default will be used
        """
        c = ConfigVtkObj (self.renwin)
        c.configure (self.root, obj)

    def search_class (self, name):    
        """ Search for classes which contain part of name.  The search
        is case insensitive.

        Input Arguments:

            name -- name to search for.
        """
        assert type (name) is types.StringType, \
               "Sorry, passed argument, %s is not a string."%name

        ret = []
        lname = string.lower (name)
        i = 0
        N = len (self.vtk_classes)
        while i < N:
            if string.find (self.vtk_c_name[i], lname) > -1:
                ret.append (self.vtk_classes[i])
            i = i + 1

        return ret

    def search_class_doc (self, word):
        
        """ Search for word in class documentation and return matching
        classes.  This is also case insensitive.  The searching
        supports the 'and' and 'or' keywords that allow for fairly
        complex searches.  A space between words assumes that the two
        words appear one after the other.

        Input Arguments:
        
            word -- name to search for.
        """
        assert type (word) is types.StringType, \
               "Sorry, passed argument, %s is not a string."%word
        if not string.strip (word):
            return []

        lword = string.lower (string.strip (word))
        tmp_list = string.split (lword)
        wlist = []
        prev = ""
        for w in tmp_list:
            z = string.strip (w)
            if z in ('and', 'or'):
                if prev and prev not in ('and', 'or'):
                    wlist.append (prev)
                    wlist.append (z)
                    prev = z
            else:
                if prev and prev not in ('and', 'or'):
                    prev = prev + ' ' + z
                else:
                    prev = z

        if prev in ('and', 'or'):
            del wlist[-1]
        elif prev:
            wlist.append (prev)
            
        ret = []
        i = 0
        N = len (self.vtk_classes)
        while i < N:
            stored_test = 0
            do_test = ''
            for w in wlist:
                if w == 'and':
                    do_test = 'and'
                elif w == 'or':
                    do_test = 'or'
                else:
                    test = (string.find (self.vtk_c_doc[i], w) > -1)
                    if do_test == 'and':
                        stored_test = stored_test and test
                    elif do_test == 'or':
                        stored_test = stored_test or test
                    elif do_test == '':              
                        stored_test = test
            if stored_test:
                ret.append (self.vtk_classes[i])
            i = i + 1

        return ret 

    def SetRenderWindow (self, rw):
        self.renwin = rw


class HelpBrowser:
    """ A VTK help browser!"""
    
    def __init__ (self, master=None):
        self.master = master
        self.root = Tkinter.Toplevel (self.master)
        self.root.geometry ("500x500")
        self.helper = VtkHelp (self.root)
        self.root.title ("VTK documentation browser")
        self.root.protocol ("WM_DELETE_WINDOW", self.quit)        

        frame = Tkinter.Frame (self.root)
        frame.pack (side='top', fill='both', expand=1)
        
        s_frame = Tkinter.Frame (frame)
        s_frame.pack (side='top', fill='both', expand=1)

        self.s_name_var = Tkinter.StringVar ()
        self.s_doc_var = Tkinter.StringVar ()
        l = Tkinter.Button (s_frame, text="Search class names:",
                            command=self.search_name)
        l.grid (row=0, column=0, sticky='w')
        e = Tkinter.Entry (s_frame, width=45, relief='sunken',
                           textvariable=self.s_name_var)
        e.grid (row=0, column=1, sticky='ew')
        e.bind ("<Return>", self.search_name)
        
        l = Tkinter.Button (s_frame, text="Search class docs:",
                            command=self.search_doc)
        l.grid (row=1, column=0, sticky='w')
        e = Tkinter.Entry (s_frame, width=45, relief='sunken',
                           textvariable=self.s_doc_var)
        e.grid (row=1, column=1, sticky='ew')
        e.bind ("<Return>", self.search_doc)

        f = Tkinter.Frame (frame)
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

        self.help_but = Tkinter.Button (self.root, text="Help",
                                         underline=0, command=self.help)
        self.help_but.pack (side='top')
        self.root.bind ("<Alt-h>", self.help)
        self.close_but = Tkinter.Button (self.root, text="Close", fg="red",
                                         underline=0, command=self.quit)
        self.close_but.pack (side='top')
        self.root.bind ("<Alt-c>", self.quit)
        
        self.txt.tag_config ("heading", foreground="red",
                             underline=1, justify='center')
        self.txt.tag_config ("link", foreground="blue",
                             underline=1, justify='left')
    
        self.txt.tag_bind ("link", "<Enter>", self.show_hand_cursor)
        self.txt.tag_bind ("link", "<Leave>", self.show_arrow_cursor)
        self.txt.tag_bind ("link", "<Button-1>", self.click)
        self.txt.config (cursor='')

        self.help ()

    def help (self, event=None):        
        self.txt.delete ('0.0', 'end')

        msg = """This browser supports searching the VTK classes and
        their documentation for arbitrary strings.  The searches are
        all case insensitive.  There are two types of searches.  (1)
        Search for a class name, and (2) search in the class
        documentation.  Type text in the field and hit enter or click
        the button.  The lower panel will show you the results.
        Clicking on any of the classes will show you the class
        documentation.

        Searching the class documentation supports the
        'and' and 'or' keywords.  Using these you can make pretty
        complex searches. """

        msg = re.sub('\n\s+', '\n', msg)
        self.txt.insert ('end', "Help on searching:\n\n", 'heading')
        self.txt.insert ('end', msg)

    def show_hand_cursor (self, event=None):
        self.txt.config (cursor='hand2')

    def show_arrow_cursor (self, event=None):
        self.txt.config (cursor='')

    def click (self, event=None):
        val = self.txt.get ('current wordstart', 'current wordend')
        self.helper.doc (val)

    def search_name (self, event=None):
        name = self.s_name_var.get ()
        self.txt.delete ('0.0', 'end')
        try:
            res = self.helper.search_class (name)
        except Exception, msg:
            print_err (msg)
            return
        self.txt.insert ('end', "Search Results:\n\n", 'heading')
        for i in res:
            self.txt.insert ('end', i, 'link')
            self.txt.insert ('end', "\n")

    def search_doc (self, event=None):
        name = self.s_doc_var.get ()
        self.txt.delete ('0.0', 'end')
        try:
            res = self.helper.search_class_doc (name)
        except Exception, msg:
            print_err (msg)
            return
        self.txt.insert ('end', "Search Results:\n\n", 'heading')
        for i in res:
            self.txt.insert ('end', i, 'link')
            self.txt.insert ('end', "\n")
        
    def quit (self, event=None):
        self.root.destroy ()       


def get_tk_root ():
    """Returns a Tkapp instance."""
    r = Tkinter._default_root
    if not r:
        r = Tkinter.Tk ()
        r.withdraw ()
    return r

def create_helper ():
    """Creates a VtkHelp instance."""
    r = get_tk_root ()
    v = VtkHelp (r)
    return v

def doc_browser ():
    """Creates a HelpBrowser instance."""
    r = get_tk_root ()
    v = HelpBrowser (r)
    return v    

def create_viewer ():
    """Simply creates a VTK actor viewer by instantiating Viewer."""
    r = get_tk_root ()
    v = Viewer (r)
    return v

viewer = create_viewer
