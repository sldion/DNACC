#!/Users/sldion/anaconda/bin/python

"""This script displays a simple VTK documentation search browser.  

This allows you to search for arbitrary strings in the VTK class
documentation and lets you browse the VTK class documentation

This script requires that MayaVi be installed as a Python module.

License:

  This code is distributed under the conditions of the BSD license.
  See LICENSE.txt for details.

Copyright (c) 2001-2005, Prabhu Ramachandran.

"""

import Tkinter
from mayavi import ivtk

if __name__ == "__main__":
    r = Tkinter.Tk()
    r.withdraw()
    d = ivtk.HelpBrowser(r)
    r.wait_window(d.root)
    r.destroy()
