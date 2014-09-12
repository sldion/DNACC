"""

This file provides access to a vtkPLOT3DReader.  Currently the
vtkPLOT3DReader only suports binary structured grid files.  Vector and
scalar data are supported.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2002, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.8 $"
__date__ = "$Date: 2005/08/02 18:30:14 $"

import os
import Base.Objects, Common
import Tkinter, tkFileDialog
import vtk
import vtkPipeline.vtkMethodParser
import vtkPipeline.ConfigVtkObj

debug = Common.debug

def get_number_of_blocks (file_name, reader):
    """Finds the number of blocks in the multiblock file.  Thanks to
    Dr. M. Fatica."""
    if hasattr(reader, 'GetBinaryFile'):
        # This is the new reader which does the job just fine.
        return reader.GetNumberOfOutputs()
    else:
        # Older version of reader which only supports binary files so
        # the following should work.
        import struct
        file = open (file_name, 'rb')
        (num_blocks,) = struct.unpack ('l', file.read (4))
        file.close ()
        return num_blocks

def get_file_name (f_name, type="xyz"):
    debug ("In get_file_name ()")
    msg = "Unable to open file: " + f_name
    msg = msg + "\n\nPlease try selecting the file manually."
    Common.print_err (msg)
    tk_fopen = tkFileDialog.askopenfilename
    file_name = ""
    if type == "xyz":
        file_name = tk_fopen (title="Open XYZ Co-ordinate file.", 
                              filetypes=[("All files", "*")])
    else:
        file_name = tk_fopen (title="Open Q Solution file.", 
                              filetypes=[("All files", "*")])
    if not file_name:
        msg = "Unable to load PLOT3DReader configuration since "\
              "no data file has been specified.  Cannot proceed!"
        raise IOError, msg
    else:
        return file_name


class PLOT3DReader (Base.Objects.DataSource):

    """This class provides access to a vtkPLOT3DReader.  Currently the
    vtkPLOT3DReader only suports binary structured grid files.  Vector
    and scalar data are supported."""

    def __init__ (self, renwin=None):
        debug ("In PLOT3DReader::__init__ ()")
        Base.Objects.DataSource.__init__ (self)
        self.xyz_file = ""
        self.q_file = ""
        self.grid_type = "STRUCTURED_GRID"
        self.scalars = {'density': 100, 'pressure': 110, 'temperature': 120,
                        'enthalpy': 130, 'internal energy': 140, 
                        'kinetic energy': 144, 'velocity magnitude': 153,
                        'stagnation energy': 163, 'entropy': 170, 
                        'swirl': 184}
        self.vectors = {'velocity': 200, 'vorticity': 201, 'momentum': 202,
                        'pressure gradient': 210}
        self.reader = None
        self.renwin = renwin
        self.scalar_var = Tkinter.StringVar ()
        self.vector_var = Tkinter.StringVar ()
        self.reader = vtk.vtkPLOT3DReader ()
        self.cur_block = 0
    
    def initialize (self, xyz_name, q_name, multi=0):
        debug ("In PLOT3DReader::initialize ()")
        Common.state.busy ()
        self.xyz_file = xyz_name
        self.q_file = q_name
        self.file_name = os.path.basename (xyz_name) + ', ' \
                         + os.path.basename (q_name)
        self.multi = multi
        self.init_reader ()
        self.update_references ()
        Common.state.idle ()

    def init_reader (self):
        "Set up the PLOT3D reader."
        debug ("In PLOT3DReader::init_reader ()")
        # set up the reader 
        if self.xyz_file == "":
            raise IOError, "No Co-ordinate filename specifed for the "\
                  "Plot3d data handler!"
        else:
            self.reader.SetXYZFileName (self.xyz_file)
            if self.q_file:
                self.reader.SetQFileName (self.q_file)
                self.scalars = {'density': 100, 'pressure': 110,
                                'temperature': 120, 'enthalpy': 130,
                                'internal energy': 140,
                                'kinetic energy': 144,
                                'velocity magnitude': 153,
                                'stagnation energy': 163, 'entropy': 170, 
                                'swirl': 184}
                self.vectors = {'velocity': 200, 'vorticity': 201,
                                'momentum': 202, 'pressure gradient': 210}
            else:
                self.scalars = {}
                self.vectors = {}

        if self.multi:
            try:
                self.reader.SetFileFormat (2)
            except AttributeError:
                self.reader.MultiGridOn()
        else:
            try:
                self.reader.SetFileFormat (0)
            except AttributeError:
                self.reader.MultiGridOff()

        # Try reading the file.
        self.reader.Update ()
        if not self.reader.GetOutput().GetPoints():
            # No output so the file might have IBlanking.
            try:
                self.reader.IBlankingOn()
            except AttributeError:
                pass

        # Try again.
        self.reader.Update ()
        if not self.reader.GetOutput().GetPoints():
            # No output so the file might be an ASCII file.
            try:
                # Turn off IBlanking.
                self.reader.IBlankingOff()
                self.reader.BinaryFileOff()
            except AttributeError:
                pass

        # Try again this time as ascii and with blanking.
        self.reader.Update ()
        if not self.reader.GetOutput().GetPoints():
            # No output so the file might be an ASCII file.
            try:
                # Turn on IBlanking.
                self.reader.IBlankingOn()
            except AttributeError:
                pass

        if self.multi:
            self.n_blocks = get_number_of_blocks (self.xyz_file, self.reader)

        self.reader.Update ()

    def set_scalar_name (self, scalar):
        debug ("In PLOT3DReader::set_scalar_name ()")
        self.scalar_data_name = scalar
        self.reader.SetScalarFunctionNumber (self.scalars[scalar])
        self.reader.Update ()
        self.update_references ()

    def set_vector_name (self, vector):
        debug ("In PLOT3DReader::set_vector_name ()")
        self.vector_data_name = vector
        self.reader.SetVectorFunctionNumber (self.vectors[vector])
        self.reader.Update ()
        self.update_references ()

    def get_scalar_list (self):
        debug ("In PLOT3DReader::get_scalar_list ()")
        return self.scalars.keys ()

    def get_vector_list (self):
        debug ("In PLOT3DReader::get_vector_list ()")
        return self.vectors.keys ()
            
    def GetOutput (self):
        "Get the reader's output. "
        debug ("In PLOT3DReader::GetOutput ()")
        if hasattr(self.reader, 'GetNumberOfOutputs'):
            return self.reader.GetOutput (self.cur_block)
        else:
            return self.reader.GetOutput ()

    def get_output (self):
        debug ("In PLOT3DReader::get_output ()")
        return self.GetOutput ()

    def get_reader (self):
        debug ("In PLOT3DReader::get_reader ()")
        return self.reader

    def Update (self): 
        debug ("In PLOT3DReader::Update ()")
        self.reader.Update ()

    def save_config (self, file): 
        debug ("In PLOT3DReader::save_config ()")
        file.write ("%d\n"%self.multi)
        rel_file_name = Common.get_relative_file_name (file.name,
                                                       self.xyz_file)
        file.write ("%s\n"%rel_file_name)
        rel_file_name = ""
        if self.q_file:
            rel_file_name = Common.get_relative_file_name (file.name,
                                                           self.q_file)
        file.write ("%s\n"%rel_file_name)

        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        p.dump (self.reader, file)

    def load_config (self, file): 
        debug ("In PLOT3DReader::load_config ()")
        self.multi = eval (file.readline ())
        f_name = Common.get_abs_file_name (file.name,
                                           file.readline ()[:-1])
        if os.path.isfile (f_name):
            self.xyz_file = f_name
        else:
            self.xyz_file = get_file_name (f_name, "xyz")

        rel_name = file.readline ()[:-1]
        if rel_name:
            f_name = Common.get_abs_file_name (file.name, rel_name)
            if os.path.isfile (f_name):
                self.q_file = f_name
            else:
                self.q_file = get_file_name (f_name, "q")
        else:
            self.q_file = ""
            
        # load the settings.
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        p.load (self.reader, file)
        # Correct the filename because the stored filename uses an
        # absolute path.
        self.initialize (self.xyz_file, self.q_file, self.multi)
        val = self.reader.GetScalarFunctionNumber ()
        for i in self.scalars.keys ():
            if self.scalars[i] == val:
                self.scalar_var.set (i)
                self.scalar_data_name = i
        val = self.reader.GetVectorFunctionNumber ()
        for i in self.vectors.keys ():
            if self.vectors[i] == val:
                self.vector_var.set (i)
                self.vector_data_name = i

    def make_custom_gui (self):
        debug ("In PLOT3DReader::make_custom_gui ()")
        self.make_main_gui ()
        self.make_close_button ()

    def make_main_gui (self, master=None):
        "Configure the data handler."
        debug ("In PLOT3DReader::make_main_gui ()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top')
        lab = Tkinter.Label (frame, text="XYZ File Name: "+
                             os.path.basename (self.xyz_file))
        lab.pack (side='top', fill='both', expand=1)
        lab = Tkinter.Label (frame, text="Q File Name: "+
                             os.path.basename (self.q_file))
        lab.pack (side='top', fill='both', expand=1)
        self.scalar_gui (frame)
        self.vector_gui (frame)        

        frame = Tkinter.Frame (self.root)
        frame.pack (side='top', expand=1, fill='both')
        rw = 0
        if self.multi:
            self.slider = Tkinter.Scale (frame,
                                         label="Set Block Number", 
                                         orient='horizontal', from_=1, 
                                         to=self.n_blocks, 
                                         command=self.change_block)
            self.slider.grid (row=rw, column=0, columnspan=2, padx=2, 
                              pady=2,sticky='ew')
            self.slider.bind ("<ButtonRelease>", self.change_block )
            rw = rw + 1

        self.gamma_var = Tkinter.DoubleVar ()
        self.gamma_var.set (self.reader.GetGamma ())
        self.r_var = Tkinter.DoubleVar ()
        self.r_var.set (self.reader.GetR ())
        lab = Tkinter.Label (frame, text="SetGamma: ")
        lab.grid (row=rw, column=0, padx=2, pady=2, sticky='w')
        entr = Tkinter.Entry (frame, width=10, relief='sunken', 
                              textvariable=self.gamma_var)
        entr.grid (row=rw, column=1, padx=2, pady=2, sticky='w')
        entr.bind ("<Return>", self.set_constants)
        rw = rw+1
        lab = Tkinter.Label (frame, text="SetR: ")
        lab.grid (row=rw, column=0, sticky='w')
        entr = Tkinter.Entry (frame, width=10, relief='sunken', 
                              textvariable=self.r_var)
        entr.grid (row=rw, column=1, padx=2, pady=2, sticky='w')
        entr.bind ("<Return>", self.set_constants)
        rw = rw+1
        
        b = Tkinter.Button (frame, text="More Options", underline=5,
                            command=self.more_cfg)
        b.grid (row=rw, column=0, columnspan=2, padx=2, pady=2,
                sticky='ew')
        rw = rw + 1
        b = Tkinter.Button (frame, text="Re-read data file", underline=0,
                            command=self.reread_file)
        b.grid (row=rw, column=0, columnspan=2, padx=2, pady=2,
                sticky='ew')
        rw = rw + 1
        b = Tkinter.Button (frame, text="Update", underline=0,
                            command=self.update_gui)
        b.grid (row=rw, column=0, columnspan=2, padx=2, pady=2,
                sticky='ew')
        self.root.bind ("<Alt-o>", self.more_cfg)
        self.root.bind ("<Alt-r>", self.reread_file)
        self.root.bind ("<Alt-u>", self.update_gui)

    def scalar_gui (self, master): 
        debug ("In PLOT3DReader::scalar_gui ()")
        if not self.scalars:
            return
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top')
        Tkinter.Label (frame, text="Select Scalar").grid (row=0,
                                                          column=0,
                                                          sticky='ew')
        rw = 1
        for sc in self.scalars.keys ():
            rb = Tkinter.Radiobutton (frame, text=sc,
                                      variable=self.scalar_var, value=sc,
                                      command=self.set_scalar_gui)
            rb.grid (row=rw, column=0, sticky='w')
            rw = rw + 1
            
    def vector_gui (self, master): 
        debug ("In PLOT3DReader::vector_gui ()")
        if not self.vectors:
            return
        
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top')
        Tkinter.Label (frame, text="Select Vector").grid (row=0,
                                                          column=0,
                                                          sticky='ew')
        rw = 1
        for vec in self.vectors.keys ():
            rb = Tkinter.Radiobutton (frame, text=vec,
                                      variable=self.vector_var, value=vec,
                                      command=self.set_vector_gui)
            rb.grid (row=rw, column=0, sticky='w')
            rw = rw + 1

    def set_scalar_gui (self, event=None): 
        debug ("In PLOT3DReader::set_scalar_gui ()")
        Common.state.busy ()
        self.set_scalar_name (self.scalar_var.get ())
        self.renwin.Render ()
        Common.state.idle ()

    def set_vector_gui (self, event=None): 
        debug ("In PLOT3DReader::set_vector_gui ()")
        Common.state.busy ()
        self.set_vector_name (self.vector_var.get ())
        self.renwin.Render ()
        Common.state.idle ()
        
    def change_block (self, event=None):
        debug ("In PLOT3DReader::change_block ()")
        n = self.slider.get ()
        self.cur_block = n - 1
        try:
            self.reader.SetGridNumber (n)
        except AttributeError:
            pass
        self.reader.Update ()
        self.update_references ()

    def set_constants (self, event=None):
        debug ("In PLOT3DReader::set_constants ()")
        g = self.gamma_var.get ()
        r = self.r_var.get ()
        self.reader.SetGamma (g)
        self.reader.SetR (r)
        self.reader.Update ()
        self.update_references ()
        
    def more_cfg (self, event=None):
        debug ("In PLOT3DReader::more_cfg ()")
        c = vtkPipeline.ConfigVtkObj.ConfigVtkObj ()
        c.set_update_method (self.update_gui)
        c.configure (self.root, self.reader)
    
    def update_gui (self, event=None):
        debug ("In PLOT3DReader::update_gui ()")
        self.reader.Update ()
        self.update_references ()

    def reread_file (self, event=None):        
        """ This re-reads the data file. Useful when you have changed
        the data and want the visualization to take notice.  Warning:
        this will not work properly if you change the file format or
        the dataset type.  You cannot also change the number of
        blocks."""
        debug ("In PLOT3DReader::reread_file ()")
        Common.state.busy ()
        self.reader.Modified ()
        self.reader.Update ()
        self.update_references ()
        Common.state.idle ()
