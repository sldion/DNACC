"""
This file provides a wrapper for VTK's EnSight reader.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.3 $"
__date__ = "$Date: 2005/08/02 18:30:14 $"

import os
import Base.Objects, Common
import vtk
import VtkXMLDataReader
import vtkPipeline.vtkMethodParser

debug = Common.debug

class VtkEnSightReader (VtkXMLDataReader.VtkXMLDataReader):

    """This class is a wrapper for VTK's EnSight reader. """

    def __init__ (self, renwin=None): 
        debug ("In VtkEnSightReader::__init__ ()")
        VtkXMLDataReader.VtkXMLDataReader.__init__ (self, renwin)
        
    def set_file_name(self, file_name):
        debug ("In VtkEnSightReader::set_file_name ()")
        self.file_name = file_name
        self.reader.SetCaseFileName(file_name)
        
    def create_reader (self): 
        "Create the corresponding reader."
        debug ("In VtkEnSightReader::create_reader ()")
        # set up the reader     
        if self.file_name == "":
            raise IOError, "No filename specifed for the data handler!"
        self.reader = vtk.vtkGenericEnSightReader()
