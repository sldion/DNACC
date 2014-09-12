"""

This filter wraps around a user specified filter and lets one
experiment with VTK filters that are not yet part of MayaVi.  By
default if the class is instantiated it will ask the user for the VTK
class to wrap around.  If passed a valid VTK class name it will try to
use that particular class.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__= "$Revision: 1.4 $"
__date__   = "$Date: 2005/08/02 18:26:25 $"

import Base.Objects, Common
import Tkinter
import vtk
import vtkPipeline.ConfigVtkObj
import tkSimpleDialog
import sys

debug = Common.debug


def get_class_name():
    if sys.version_info[1] == 3:
        # Bug in Python 2.3 prevents the dialog from opening.
        r = Tkinter.Tk()
    else:
        r = Tkinter._default_root
    name = tkSimpleDialog.askstring("Enter VTK class name",
                                    "Enter VTK class name to use as filter",
                                    parent=r)
    return name


def get_valid_class(name):
    if not name:
        name = get_class_name()
    if not name:
        msg = "No class chosen, cannot create filter!"
        raise Base.Objects.ModuleException, msg
        
    if not hasattr(vtk, name):
        msg = "Unable to find VTK class named: '%s'"%name
        raise Base.Objects.ModuleException, msg
    klass = getattr(vtk, name)
    try:
        obj = klass()
    except TypeError:
        msg = "Class '%s' is abstract and cannot be instantiated."%name
        raise Base.Objects.ModuleException, msg        
    if not hasattr(klass, 'SetInput'):
        msg = "Class '%s' has no SetInput method and cannot be used."%name
        raise Base.Objects.ModuleException, msg
    if not hasattr(klass, 'GetOutput'):
        msg = "Class '%s' has no GetOutput method and cannot be used"%name
        raise Base.Objects.ModuleException, msg
    return klass


class UserDefined(Base.Objects.Filter):

    """ This filter wraps around a user specified filter and lets one
    experiment with VTK filters that are not yet part of MayaVi.  By
    default if the class is instantiated it will ask the user for the
    VTK class to wrap around.  If passed a valid VTK class name it
    will try to use that particular class.  """

    def __init__ (self, mod_m, vtk_fil_name=""):
        debug("In UserDefined::__init__()")
        Base.Objects.Filter.__init__(self, mod_m)
        klass = get_valid_class(vtk_fil_name)
        self.fil = klass()        
        self.fil.SetInput(self.prev_fil.GetOutput())
        self.fil.Update()

    def set_input_source(self, source):
        debug("In UserDefined::set_input_source ()")
        Common.state.busy()
        self.fil.SetInput(source.GetOutput ())
        self.prev_filter = source
        self.fil.Update()
        Common.state.idle()
        
    def configure(self, master=None):
        debug("In UserDefined::configure ()")
        c = vtkPipeline.ConfigVtkObj.ConfigVtkObj(self.renwin)
        c.configure(self.root, self.fil, get=[], toggle=['!AbortExecuteOn'],
                    one_frame=1, auto_update=1)
        c.root.transient(master)

    def save_config(self, file):
        debug("In UserDefined::save_config ()")
        # writing an extra class name so that when the mayavi
        # visualization is loaded it can instantiate this class
        # correctly without the user having to re-enter the vtk class.
        file.write("%s\n"%self.fil.GetClassName())
        Base.Objects.Filter.save_config(self, file)
        
