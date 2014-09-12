#!/usr/bin/env python

import sys, traceback, re

__HAS_TK = 0

def print_msg(msg):
    if __HAS_TK:
        tkMessageBox.showinfo("Information", re.sub('\s+', ' ', msg))
        print msg
    else:
        print msg

def print_err(msg):
    if __HAS_TK:
        tkMessageBox.showerror("ERROR", re.sub('\s+', ' ', msg))
        print msg
    else:
        print msg    
    
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


print_msg("Testing if Tkinter is available... ")
try:
    import Tkinter
except ImportError:
    msg = "Sorry Tkinter does not appear to be available.\n"\
          "Please check your Python installation. "\
          "It is possible that you have not installed Tcl/Tk and Tkinter."\
          "Please visit http://www.python.org for more details."    
    print_err(msg)
    sys.exit(1)
else:
    import tkMessageBox
    print_msg("OK - you have Tkinter")
    print_msg("TclVersion = %s, TkVersion = %s"%(Tkinter.TclVersion,
                                                 Tkinter.TkVersion))
    __HAS_TK = 1


def test_vtk_cone():
    import vtk

    msg = """Testing a sample vtk program.  You should see a 300x300
    pixel window with a black background and with a magenta coloured
    Cone.  You can interact with the cone using the mouse.  To quit
    the test press q on the window.  If this test is successful then
    the basic vtk installation is OK."""

    print_msg (msg)
    # create a rendering window and renderer
    ren = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(ren)
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)

    # create an actor and give it cone geometry
    cone = vtk.vtkConeSource()
    cone.SetResolution(40)
    coneMapper = vtk.vtkPolyDataMapper()
    coneMapper.SetInput(cone.GetOutput())
    coneActor = vtk.vtkActor()
    coneActor.SetMapper(coneMapper)
    coneActor.GetProperty ().SetColor (0.5, 0.5, 1.0)    

    ren.AddActor(coneActor)
    # enable user interface interactor
    iren.Initialize()
    iren.Start()

def test_vtk_tk_render_widget(root):
    import vtk
    from vtk.tk.vtkTkRenderWidget import vtkTkRenderWidget
    
    msg = """Testing a sample vtk program that uses the
    vtkTkRenderWidget.  You should see a 300x300 pixel window with a
    black background and with a magenta coloured Cone.  You can
    interact with the cone using the mouse.  To quit the test press q
    on the window.  If this test is successful then the vtk
    installation is OK.  You should be able to use Tkinter and VTK
    properly."""
    
    print_msg (msg)
    
    # create vtkTkRenderWidget
    t = Tkinter.Toplevel(root)
    pane = vtkTkRenderWidget(t,width=300,height=300)
    pane.bind("<KeyPress-q>",
              lambda e=None: e.widget.winfo_toplevel().master.destroy())
    
    ren = vtk.vtkRenderer()
    pane.GetRenderWindow().AddRenderer(ren)
    pane.pack(expand=1, fill='both')
    

    cone = vtk.vtkConeSource()
    cone.SetResolution(40)    
    coneMapper = vtk.vtkPolyDataMapper()
    coneMapper.SetInput(cone.GetOutput())    
    coneActor = vtk.vtkActor()
    coneActor.SetMapper(coneMapper)
    coneActor.GetProperty ().SetColor (0.5, 0.5, 1.0)

    ren.AddActor(coneActor)


def test_vtk(root):
    print_msg ("Testing if VTK can be imported ...")
    try:
        import vtk
    except ImportError:
        msg = "Sorry, vtk cannot be found by your Python "\
              "installation."
        print_err(msg)
        sys.exit(1)
    else:
        print_msg("OK, vtk found.")

    test_kits()

    test_vtk_cone()

    print_msg ("Testing if vtkTkRenderWidget can be imported...")
    try:
        from vtk.tk import vtkTkRenderWidget
    except ImportError:
        
        msg = """Sorry, module vtk.tk.vtkTkRenderWidget cannot be found
        by your Python installation.  First check if you have the file
        called vtkRenderWidget.py somewhere.  If you do then most
        probably Python doesn't have this directory in its search
        path.  The way to fix this would be to create a file called
        'vtk.pth' containing a single line which is the path to the
        directory that contains vtkRenderWidget.py.  Put this file in
        your Python directory's 'site-packages' directory."""
        
        print_err (msg)
        sys.exit(1)
    else:
        print_msg("OK, vtkTkRenderWidget found.")

    test_vtk_tk_render_widget(root)


def test_kits():
    import vtk
    print_msg ("Testing if vtkCubeAxesActor2D can be instantiated ...")
    try:
        a = vtk.vtkCubeAxesActor2D()
    except AttributeError:

        msg = """Warning: Unable to create a vtkCubeAxesActor2D
        object.  You will not be able to use all the MayaVi modules
        especially the Axes module.  Under VTK 3.x you need to also
        compile the 'contrib' classes.  Under 4.x you need to also
        compile the 'Hybrid' classes."""

        print_err (msg)
    else:
        print_msg("OK, vtkCubeAxesActor2D can be instantiated.")
    
def test_value_error():
    import vtk
    print_msg("Testing if your overall installation is OK ...")
    try:
        p = vtk.vtkPolyData()
        m = vtk.vtkPolyDataMapper()
        m.SetInput(p)
    except ValueError, msg:
        
        msg = """ERROR:
        Looks like your installation has a problem.  It appears that
        you have two copies of your VTK libraries.  This can happen if
        you built VTK from sources and have then installed VTK-Python.

        To fix the error either move your build directory (usually
        called 'bin') to a different directory (like 'bin1') or delete
        the libraries in the build directory.

        Alternatively use the 'vtkpython' interpreter ditributed with
        VTK instead of the usual Python interpreter i.e. run VTK
        scripts like so:
          vtkpython some_vtk_script.py"""

        print_err (msg)
        sys.exit(1)
    else:
        print_msg("OK, your installation seems fine!")
        


if __name__ == "__main__":
    root = Tkinter.Tk()
    root.withdraw()
    test_value_error()
    test_vtk(root)
    root.mainloop()
    
