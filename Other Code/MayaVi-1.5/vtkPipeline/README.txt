		Instructions for the VTK pipeline browser
		-----------------------------------------

The vtkPipeline browser home page is here:

    http://mayavi.sourceforge.net/vtkPipeline/

This Python module provides a VTK pipeline browser similar to Paul
Rajlich's.  Also provided is a simple VTK object "pickler".  Using
this one can save the state of a VTK object to a file and reload it
later.  Not every method is dumped but most of the useful ones are.


Requirements:
^^^^^^^^^^^^^

*  You will need to have VTK along with the python bindings installed.

*  You will also need to have Tkinter installed.

*  Python version 1.5.2 seems to work fine.  Older versions may have
   problems but I recommend Python-2.x.

*  The VTK method parser and pickler will work without Tkinter too.

Installation:
^^^^^^^^^^^^^

  The vtkPipeline module ships as part of MayaVi.  When you install
  MayaVi using distutils, the vtkPipeline module is also installed in
  a site-packages directory.  Once this is done you should be all set
  to use it.


Usage:
^^^^^^

  To use the vtkPipeline do the following.  In your VTK application
  just add the following lines.

       from vtkPipeline import vtkPipelineBrowser
       # or 
       from vtkPipeline import *

       # Only if you haven't already started Tk you will you need the next
       # two lines
       root = Tk ()
       root.withdraw ()

       # renwin refers to your vtkRenderWindow.
       pipe = vtkPipelineBrowser (root, renwin)
       pipe.browse ()

       # If not done already.
       root.mainloop ()

  For a more detailed example read the vtkPipeline.py file.  There is
  a working example.  To see it working you can just run
  vtkPipeline.py like so:

      $ python vtkPipeline.py

  The configuration options that require a color will have a button
  associated with them at the left side.  Click on the button to
  choose a color from a GUI.  Hit the apply botton (or the key
  combination Alt+A) to apply the changes.

  You can use the VtkPickler class to dump/reload the state of any VTK
  object to/from a file.  This can be done like so.

      from vtkMethodParser import VtkPickler
      # or
      from vtkMethodParser import *

      p = VtkPickler ()
      out_file = open ("test.sav", 'w')
      # to dump the state do 
      p.dump (vtk_object, out_file)
      out_file.close ()
      # to reload the dumped state from a file
      in_file = open ("test.sav", 'r')
      p.load (vtk_object, in_file)
      in_file.close ()

  The dumped data is simple text.  Any of the methods that have been
  parsed will be saved to the file.  More than one object can be
  dumped into the same file.  The order in which they are dumped is
  important.


Notes:
^^^^^^

  The pipeline browser is similar to Paul Rajlich's tcl vtkPipeline.
  The structure of the pipeline is a little different though.  The GUI
  configuration of the various objects is IMHO much cleaner than the
  one used by him.

  Only the Get/Set, On/Off, Set<State>To<Value> methods are
  configurable.  I believe this is sufficient.  The methods are
  obtained by parsing the output of repr(vtk_obj) together with the
  output of a dir(vtk_obj).


Feedback, suggestions and bug fixes are always welcome.

Have fun.

Prabhu Ramachandran <prabhu_r@users.sf.net>
http://www.aero.iitm.ernet.in/~prabhu/
