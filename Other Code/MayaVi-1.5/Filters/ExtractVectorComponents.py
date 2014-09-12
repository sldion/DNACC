"""

This wraps the vtkExtractVectorComponents filter and allows one to
select any of the three components of an input vector data
attribute.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.6 $"
__date__ = "$Date: 2005/08/02 18:26:25 $"

import Base.Objects, Common
import Tkinter
import vtk
import vtkPipeline.vtkMethodParser

debug = Common.debug

class ExtractVectorComponents (Base.Objects.Filter):

    """ This wraps the vtkExtractVectorComponents filter and allows
    one to select any of the three components of an input vector data
    attribute. """

    def initialize (self):
        debug ("In ExtractVectorComponents::initialize ()")
        self.fil = vtk.vtkExtractVectorComponents ()
        self.fil.SetInput (self.prev_fil.GetOutput ())
        self.comp_var = Tkinter.IntVar ()
        self.comp_var.set (0)
        self.fil.Update ()

    def GetOutput (self):
        debug ("In ExtractVectorComponents::GetOutput ()")
        val = self.comp_var.get ()
        return self.fil.GetOutput (val)

    def set_input_source (self, source):
        debug ("In ExtractVectorComponents::set_input_source ()")
        Common.state.busy ()
        self.fil.SetInput (source.GetOutput ())
        self.prev_filter = source
        self.fil.Update ()
        Common.state.idle ()

    def get_scalar_data_name (self):
        debug ("In ExtractVectorComponents::get_scalar_data_name ()")
        name = self.prev_fil.get_vector_data_name ()
        comp = [' (X component)', ' (Y component)',' (Z component)']
        return name + comp[self.comp_var.get ()]

    def save_config (self, file):
        debug ("In ExtractVectorComponents::save_config ()")
        file.write ("%d\n"%(self.comp_var.get ()))
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.fil, ):
            p.dump (obj, file)

    def load_config (self, file):
        debug ("In ExtractVectorComponents::load_config ()")
        val = eval (file.readline ())
        self.comp_var.set (val)
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.fil, ):
            p.load (obj, file)

        self.fil.Update ()

    def make_custom_gui (self):
        debug ("In ExtractVectorComponents::make_custom_gui()")
        self.make_main_gui ()
        self.make_close_button ()

    def make_main_gui (self):
        debug ("In ExtractVectorComponents::make_main_gui()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)
        txt = ("X-Component", "Y-Component", "Z-Component")
        #self.axis_on_but = []
        for i in range (3):
            b = Tkinter.Radiobutton (frame, text=txt[i],
                                     variable=self.comp_var,
                                     value=i, command=self.change_component)
            b.grid (row=i, column=0)
            #self.axis_on_but.append (b)        

    def change_component (self, event=None):
        debug ("In ExtractVectorComponents::change_component()")
        Common.state.busy ()
        self.mod_m.Update ()
        Common.state.idle ()
