"""
This filter computes the vorticity of an input vector field.  For
convenience, the filter allows one to optionally pass-through the
given input vector field.  The filter also allows the user to show the
component of the vorticity along a particular cartesian co-ordinate
axes.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2005, Gareth Clay and Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__= "$Revision: 1.1 $"
__date__   = "$Date: 2005/08/23 14:33:25 $"
__credits__ = """Thanks to Gareth Clay <gareth.clay@imperial.ac.uk> for contributing this filter."""


import Common
from Base import Objects
import Tkinter
import vtk
from vtkPipeline.vtkMethodParser import VtkPickler

debug = Common.debug

class Vorticity (Objects.Filter):
    """This filter computes the vorticity of an input vector field.
    For convenience, the filter allows one to optionally pass-through
    the given input vector field.  The filter also allows the user to
    show the component of the vorticity along a particular cartesian
    co-ordinate axes.
    """
    def initialize (self):
        debug ("In Vorticity::initialize()")
        self.fil = vtk.vtkCellDerivatives ()
        self.fil.SetVectorModeToComputeVorticity ()
        self.fil.SetInput(self.prev_fil.GetOutput ())        
        self.fil.Update ()
        self.dimension_to_allow = Tkinter.IntVar ()
        self.dimension_to_allow.set (-1)
        self.vector_name = Tkinter.StringVar ()
        self.vector_name.set ("Vorticity")

    def generate_arrays (self, outputGrid):    
        if (self.vector_name.get () == "Source vector"):
            return outputGrid
            
        # Calculate vorticity
        debug ("Calculating vorticity...")
        self.fil.SetInput (outputGrid)
        self.fil.Update ()
        outputGrid = self.fil.GetOutput ()
        outputGrid.Update ()
        
        # Convert vorticity to point data
        cellToPoint = vtk.vtkCellDataToPointData ()    
        cellToPoint.SetInput (outputGrid)
        cellToPoint.PassCellDataOff ()
        cellToPoint.Update ()
        outputGrid = cellToPoint.GetOutput ()

        # Allow the user to constrain vorticity to one dimension (this
        # has the same effect as flattening the source array
        # (e.g. velocity) onto a plane).
        desiredDimensionIndex = self.dimension_to_allow.get ()
        if desiredDimensionIndex != -1:
            vorticity = outputGrid.GetPointData ().GetArray ("Vorticity")
            for i in range(3):
                if i != desiredDimensionIndex:
                    vorticity.FillComponent(i, 0.0)
            outputGrid.Update ()
                
        # Extract vector norm
        vectorNorm = vtk.vtkVectorNorm ()
        vectorNorm.SetAttributeModeToUsePointData ()
        vectorNorm.SetInput (outputGrid)
        vectorNorm.Update ()    
        outputGrid = vectorNorm.GetOutput()        
        
        return outputGrid

    def GetOutput (self):
        debug ("In Vorticity::GetOutput()")        
        return self.generate_arrays (self.prev_fil.GetOutput ())
      
    def set_input_source (self, source):
        debug ("In Vorticity::set_input_source")
        Common.state.busy ()
        self.prev_filter = source
        Common.state.idle ()    
  
    def save_config (self, file):
        debug ("In Vorticity::save_config")
        on = int(self.vector_name.get () == "Vorticity")
        file.write ("%d, %d\n"%(on, self.dimension_to_allow.get()))
        p = VtkPickler ()
        for obj in (self.fil, ):
            p.dump (obj, file)
  
    def load_config (self, file):
        debug ("In Vorticity::load_config")
        on, val = eval (file.readline ())
        if on:
            self.vector_name.set('Vorticity')
        else:
            self.vector_name.set('Source vector')
        self.dimension_to_allow.set (val)
        p = VtkPickler ()
        for obj in (self.fil, ):
            p.load (obj, file)
            
        self.fil.Update ()

    def make_custom_gui (self):
        debug ("In Vorticity::make_custom_gui")
        self.make_main_gui ()
        self.make_close_button ()

    def make_main_gui (self):
        debug ("In Vorticity::make_main_gui")
            
        vectorFrame = Tkinter.Frame (self.root, relief='ridge', bd = 2)
        vectorFrame.pack (side = 'top', fill = 'both', expand = 1)
        vectorLabel = Tkinter.Label (vectorFrame, text="Vector to display")
        vectorLabel.grid (row = 0, column = 0)
         
        vectorNames = ("Source vector", "Vorticity")
        for i in range ( len(vectorNames) ):
            radio = Tkinter.Radiobutton (vectorFrame,
                                         text = vectorNames[i],
                                         variable = self.vector_name,
                                         value = vectorNames[i],
                                         command = self.rebuild_array)
            radio.grid (row = i + 1, column = 0, sticky='w')
            
        planeFrame = Tkinter.Frame (self.root, relief='ridge', bd = 2)
        planeFrame.pack (side = 'top', fill = 'both', expand = 1)            
        planeLabel = Tkinter.Label (planeFrame,
                                    text="Make source vector \n"\
                                    "non-zero only on a plane?")
        planeLabel.grid (row = 0, column = 0)
        
        # The value of each of these radio buttons corresponds to the number
        # of the dimension that is allowed to be non-zero in the vorticity,
        # e.g. if velocity only is 0 in the Z component then:
        #      value = 2 - i,  == 2 - 0,  == 2 which is the index of Z in
        #      a tuple/list containing (X, Y, Z)
        planeNames = ("XY", "XZ", "YZ", "No constraint")
        for i in range ( len(planeNames) ):
            radio = Tkinter.Radiobutton (planeFrame,
                                         text = planeNames[i],
                                         variable = self.dimension_to_allow,
                                         value = 2 - i,
                                         command = self.rebuild_array)
            radio.grid (row = i + 1, column = 0,  sticky='w')

    def rebuild_array (self, event = None):
        debug ("In Vorticity::change_array")
        Common.state.busy ()
        self.mod_m.Update ()
        Common.state.idle ()

    def get_vector_data_name (self):
        debug ("In Vorticity::get_vector_data_name ()")
        return "Vorticity"

    def get_scalar_data_name (self):
        debug ("In Vorticity::get_scalar_data_name ()")
        return "Vorticity magnitude"
