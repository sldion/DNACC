"""
This wraps the vtkExtractTensorComponents filter and allows one to
select any of the nine components or the effective stress or the
determinant from an input tensor data set.  This will work for any
dataset.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.4 $"
__date__ = "$Date: 2005/08/02 18:26:24 $"
__credits__ = """Many thanks to Jose Paulo <moitinho@civil.ist.utl.pt>
for contributing this Filter.  This Filter is almost entirely his
work."""

import Base.Objects, Common
import Tkinter
import vtk
import vtkPipeline.vtkMethodParser

debug = Common.debug

class ExtractTensorComponents (Base.Objects.Filter):

    """ This wraps the vtkExtractTensorComponents filter and allows
    one to select any of the nine components or the effective stress
    or the determinant from an input tensor data set.  This will work
    for any dataset. """

    def initialize (self):
        debug ("In ExtractTensorComponents::initialize ()")
        self.fil = vtk.vtkExtractTensorComponents ()
        self.fil.SetInput (self.prev_fil.GetOutput ())
        self.comp_var = Tkinter.IntVar ()
        self.comp_var.set (9)
        # 0..8 tensor components, 9 effective stress, 10 determinant

        self.fil.ScalarIsEffectiveStress ()
        self.fil.PassTensorsToOutputOn ()
        self.fil.ExtractScalarsOn ()

        self.fil.Update ()

    def GetOutput (self):
        debug ("In ExtractTensorComponents::GetOutput ()")
        # There is no need to select the component here. All the
        # work is done in change_component
        return self.fil.GetOutput ()

    def _gui_vars_init (self):
        """Initializes the GUI variables."""
        debug ("In ExtractTensorComponents::_gui_vars_init ()")
        mode = self.fil.GetScalarMode ()
        comp = self.fil.GetScalarComponents ()
        if mode == 0: # component mode
            self.comp_var.set (comp[0]*3 + comp[1])
        elif mode == 1: # effective stress
            self.comp_var.set (9)
        elif mode == 2: # determinant
            self.comp_var.set (10)     

    def set_input_source (self, source):
        debug ("In ExtractTensorComponents::set_input_source ()")
        Common.state.busy ()
        self.fil.SetInput (source.GetOutput ())
        self.prev_filter = source
        self.fil.Update ()
        Common.state.idle ()

    def get_scalar_data_name (self):
        debug ("In ExtractTensorComponents::get_scalar_data_name ()")
        name = self.prev_fil.get_tensor_data_name ()
        self._gui_vars_init ()
        val = self.comp_var.get ()
        if val == 10:
            name = name + ' (determinant)'            
        elif val == 9:
            name = name + ' (effective)'
        else:
            comp = ['X', 'Y', 'Z']
            name = name + '(' + comp[val/3] + ',' + comp[val%3] + ')'
        return name

    def make_custom_gui (self):
        debug ("In ExtractVectorComponents::make_custom_gui()")
        self.make_main_gui ()
        self.make_close_button ()

    def make_main_gui (self):
        debug ("In ExtractVectorComponents::make_main_gui()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)
        txt = ("X", "Y", "Z")
        self._gui_vars_init ()
        # This grid is for the 3x3 components
        grid = Tkinter.Frame (frame, relief="flat", bd=0)
        rw = 0
        grid.grid (row=rw, column=0, sticky='w')
        for i in range( 0, 3):
            for j in range( 0, 3):
                text = "%s,%s"%(txt[i], txt[j])
                rb = Tkinter.Radiobutton (grid, text=text,
                                          variable=self.comp_var,
                                          value=i*3+j,
                                          command=self.change_component)
                rb.grid (row=i, column=j, sticky='w')

        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text="Effective Stress",
                                  variable=self.comp_var, value=9,
                                  command=self.change_component)
        rb.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        rb = Tkinter.Radiobutton (frame, text="Determinant",
                                  variable=self.comp_var, value=10,
                                  command=self.change_component)
        rb.grid (row=rw, column=0, sticky='w')

    def change_component (self, event=None):
        debug ("In ExtractTensorComponents::change_component ()")
        Common.state.busy ()
        new_component = self.comp_var.get ()
        if (new_component >= 0) and (new_component <= 8):
            self.fil.ScalarIsComponent ()
            self.fil.SetScalarComponents ( new_component/3, \
                                           new_component%3)
        elif new_component == 9:
            self.fil.ScalarIsEffectiveStress ()
        elif new_component == 10:
            self.fil.ScalarIsDeterminant ()
        self.mod_m.Update ()
        Common.state.idle ()
