"""

This file provides a highly general VTK data file reader.  Currently
this class handles the various types of VTK data as per the old
(non-XML) format.  Unstructured grids, structured grids, rectilinear
grids, structured points and polydata are supported.  Scalar, vector
and tensor data are supported.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.12 $"
__date__ = "$Date: 2005/08/02 18:30:14 $"
__credits__ = """Many thanks to Jose Paulo <moitinho@civil.ist.utl.pt> 
for adding tensor data support."""


import string, re, os
import Base.Objects, Common
import Tkinter, tkFileDialog
import vtk
import vtkPipeline.vtkMethodParser
import vtkPipeline.ConfigVtkObj

debug = Common.debug

def find_data_type (file_name):
    "Parses the named file to see what type of data there is."
    debug ("In find_data_type ()")
    f = open (file_name, "rb")
    ## somewhere in the first 10 lines the strings should be present
    ## Bug here.  s_grid will match uns_grid, so we need to put it first. :(
    supported = ["UNSTRUCTURED_GRID", "STRUCTURED_GRID", 
                 "STRUCTURED_POINTS", "RECTILINEAR_GRID", "POLYDATA" ]
    for i in range (0, 10):
        line = f.readline ()
        for data_type in supported:
            if string.find (line, data_type) > -1:
                return data_type

    raise Base.Objects.ParseException, \
          "Unknown data type: Known data types are: %s, %s, "\
          "%s, %s and %s. Quitting!"% (supported[0], supported[1], 
                                       supported[2], supported[3], 
                                       supported[4])


def get_attribute_list (reader, type='Scalars'):
    n = eval ("reader.GetNumberOf%sInFile ()"%type)
    lst = []
    for i in range (n):
        lst.append (eval ("reader.Get%sNameInFile (i)"%type))

    return lst

def get_attribute_lists (file_name):    
    """
    Parses the named file for a list of attribute data and returns the
    list of attributes available, should work for both VECTORS,
    SCALARS and TENSORS. """

    debug ("In get_attribute_lists ()")
    tmp = r'^(SCALARS|VECTORS|TENSORS)\s+(\S+)'
    patn = re.compile (tmp, re.M)
    f = open (file_name, "rb")
    match = patn.findall (f.read ())
    f.close ()
    sc_list = []
    vec_list = []
    ten_list = []
    for m in match:
        if string.lower (m[0]) == 'scalars':
            sc_list.append (m[1])
        elif string.lower (m[0]) == 'vectors':
            vec_list.append (m[1])
        elif string.lower (m[0]) == 'tensors':
            ten_list.append (m[1]) 
    return sc_list, vec_list, ten_list


def get_file_name (f_name):
    debug ("In get_file_name ()")
    msg = "Unable to open file: " + f_name
    msg = msg + "\n\nPlease try selecting the file manually."
    Common.print_err (msg)
    tk_fopen = tkFileDialog.askopenfilename
    file_name = tk_fopen (title="Open VTK data file", 
                          filetypes=[("VTK files", "*.vtk"), 
                                     ("All files", "*")])
    if not file_name:
        msg = "Unable to load VtkDataReader configuration since "\
              "no data file has been specified.  Cannot proceed!"
        raise IOError, msg
    else:
        return file_name


class VtkDataReader (Base.Objects.DataSource):

    """This class is a general VTK data file reader.  Currently this
    class handles the various types of VTK data as per the old
    (non-XML) format.  Unstructured grids, structured grids,
    rectilinear grids, structured points and polydata are supported.
    Scalar, vector and tensor data are supported.  """

    def __init__ (self, renwin=None): 
        debug ("In VtkDataReader::__init__ ()")
        Base.Objects.DataSource.__init__ (self)
        self.scalar_lst = [] # avaliable scalars
        self.vector_lst = []
        self.tensor_lst = []
        self.reader = None
        self.renwin = renwin
        self.scalar_var = Tkinter.StringVar ()
        self.vector_var = Tkinter.StringVar ()
        self.tensor_var = Tkinter.StringVar ()

    def __del__ (self): 
        debug ("In VtkDataReader::__del__ ()")
    
    def initialize (self, file_name): 
        "Overload this if reqd. Use the existing functions if possible."    
        debug ("In VtkDataReader::initialize ()")
        Base.Objects.DataSource.initialize (self, file_name)
        Common.state.busy ()
        self.file_name = file_name
        self.create_reader ()
        self.set_file_name(self.file_name)
        self.reader.Update ()
        self.setup_defaults ()
        self.reader.Update ()
        self.update_references ()
        Common.state.idle ()
        
    def setup_defaults (self): 
        debug ("In VtkDataReader::setup_defaults ()")
        self.scalar_lst, self.vector_lst, self.tensor_lst = \
                         get_attribute_lists (self.file_name)
        if self.scalar_lst:
            self.reader.SetScalarsName (self.scalar_lst[0])
        if self.vector_lst:
            self.reader.SetVectorsName (self.vector_lst[0])
        if self.tensor_lst:
            self.reader.SetTensorsName (self.tensor_lst[0])
        self.setup_names ()

    def setup_names (self): 
        debug ("In VtkDataReader::setup_names ()")
        name = self.reader.GetScalarsName ()
        if not name:
            name = ""
        self.scalar_var.set (name)
        self.scalar_data_name = name
        name = self.reader.GetVectorsName ()
        if not name:
            name = ""
        self.vector_var.set (name)
        self.vector_data_name = name        
        name = self.reader.GetTensorsName ()
        if not name:
            name = ""
        self.tensor_var.set (name)
        self.tensor_data_name = name

    def create_reader (self): 
        "Create the corresponding reader."
        debug ("In VtkDataReader::create_reader ()")
        # set up the reader     
        if self.file_name == "":
            raise IOError, "No filename specifed for the data handler!"

        self.grid_type = find_data_type (self.file_name)
        if self.grid_type == "STRUCTURED_GRID":
            self.reader = vtk.vtkStructuredGridReader ()
        elif self.grid_type == "STRUCTURED_POINTS":
            self.reader = vtk.vtkStructuredPointsReader ()
        elif self.grid_type == "RECTILINEAR_GRID":
            self.reader = vtk.vtkRectilinearGridReader ()
        elif self.grid_type == "POLYDATA":
            self.reader = vtk.vtkPolyDataReader ()
        elif self.grid_type == "UNSTRUCTURED_GRID":
            self.reader = vtk.vtkUnstructuredGridReader () 

    def set_file_name(self, file_name):
        """Abstracts the call to self.reader.Set*FileName(). Useful
        when using this class as a base for other classes.  Override
        this if needed."""
        debug ("In VtkDataReader::set_file_name ()")
        self.file_name = file_name
        self.reader.SetFileName(file_name)

    def set_scalar_name (self, scalar): 
        debug ("In VtkDataReader::set_scalar_name ()")
        self.scalar_data_name = scalar
        self.reader.SetScalarsName (scalar)
        self.reader.Update ()
        self.update_references ()

    def set_vector_name (self, vector): 
        debug ("In VtkDataReader::set_vector_name ()")
        self.vector_data_name = vector
        self.reader.SetVectorsName (vector)
        self.reader.Update ()
        self.update_references ()

    def set_tensor_name (self, tensor): 
        debug ("In VtkDataReader::set_tensor_name ()")
        self.tensor_data_name = tensor
        self.reader.SetTensorsName (tensor)
        self.reader.Update ()
        self.update_references ()
        
    def get_scalar_list (self): 
        debug ("In VtkDataReader::get_scalar_list ()")
        return self.scalar_lst

    def get_vector_list (self): 
        debug ("In VtkDataReader::get_vector_list ()")
        return self.vector_lst

    def get_tensor_list (self): 
        debug ("In VtkDataReader::get_tensor_list ()")
        return self.tensor_lst
            
    def GetOutput (self): 
        "Get the reader's output. "
        debug ("In VtkDataReader::GetOutput ()")
        return self.reader.GetOutput ()

    def get_output (self): 
        debug ("In VtkDataReader::get_output ()")
        return self.reader.GetOutput ()

    def Update (self): 
        debug ("In VtkDataReader::Update ()")
        self.reader.Update ()

    def get_reader (self): 
        debug ("In VtkDataReader::get_reader ()")
        return self.reader

    def get_render_window (self): 
        debug ("In VtkDataReader::get_render_window ()")
        return self.renwin

    def save_config (self, file): 
        debug ("In VtkDataReader::save_config ()")
        rel_file_name = Common.get_relative_file_name (file.name,
                                                       self.file_name)
        file.write ("%s\n"%rel_file_name)
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        p.dump (self.reader, file)

    def load_config (self, file): 
        debug ("In VtkDataReader::load_config ()")
        f_name = Common.get_abs_file_name (file.name,
                                           file.readline ()[:-1])
        if os.path.isfile (f_name):
            self.file_name = f_name
        else:
            self.file_name = get_file_name (f_name)
            
        Base.Objects.DataSource.initialize (self, self.file_name)
        # create the DataReader
        self.create_reader ()
        # load the settings.
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        p.load (self.reader, file)
        # Correct the filename because the stored filename uses an
        # absolute path.
        self.set_file_name (self.file_name)
        self.reader.Update ()
        self.scalar_lst, self.vector_lst, self.tensor_lst = \
                         get_attribute_lists (self.file_name)
        self.setup_names ()
        self.update_references ()

    def scalar_gui (self, master): 
        debug ("In VtkDataReader::scalar_gui ()")
        if not self.scalar_lst:
            return
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top')
        Tkinter.Label (frame, text="Select Scalar").grid (row=0,
                                                          column=0,
                                                          sticky='ew')
        rw = 1
        for sc in self.scalar_lst:
            rb = Tkinter.Radiobutton (frame, text=sc,
                                      variable=self.scalar_var, value=sc,
                                      command=self.set_scalar_gui)
            rb.grid (row=rw, column=0, sticky='w')
            rw = rw + 1
            
    def vector_gui (self, master): 
        debug ("In VtkDataReader::vector_gui ()")
        if not self.vector_lst:
            return
        
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top')
        Tkinter.Label (frame, text="Select Vector").grid (row=0,
                                                          column=0,
                                                          sticky='ew')
        rw = 1
        for vec in self.vector_lst:
            rb = Tkinter.Radiobutton (frame, text=vec,
                                      variable=self.vector_var, value=vec,
                                      command=self.set_vector_gui)
            rb.grid (row=rw, column=0, sticky='w')
            rw = rw + 1

    def tensor_gui (self, master): 
        debug ("In VtkDataReader::tensor_gui ()")
        if not self.tensor_lst:
            return
        
        frame = Tkinter.Frame (master, relief='ridge', bd=2)
        frame.pack (side='top')
        Tkinter.Label (frame, text="Select Tensor").grid (row=0,
                                                          column=0,
                                                          sticky='ew')
        rw = 1
        for ten in self.tensor_lst:
            rb = Tkinter.Radiobutton (frame, text=ten,
                                      variable=self.tensor_var, value=ten,
                                      command=self.set_tensor_gui)
            rb.grid (row=rw, column=0, sticky='w')
            rw = rw + 1

    def make_custom_gui (self):
        debug ("In VtkDataReader::make_custom_gui ()")
        self.make_main_gui ()
        self.make_close_button ()

    def make_main_gui (self): 
        debug ("In VtkDataReader::make_main_gui ()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top')
        lab = Tkinter.Label (frame, text="File Name: "+
                             os.path.basename (self.file_name))
        lab.pack (side='top', fill='both', expand=1)
        self.file_name_label = lab

        self.make_timestep_gui(frame)
        self.scalar_gui (frame)
        self.vector_gui (frame)
        self.tensor_gui (frame)
        but1 = Tkinter.Button (frame, text="More Config options",
                               command=self.config_reader, underline=1)
        but1.pack (side='top', fill='both', expand=1)
        b = Tkinter.Button (frame, text="Re-read data file", underline=0,
                            command=self.reread_file)
        b.pack (side='top', fill='both', expand=1)
        b = Tkinter.Button (frame, text="Update", underline=0,
                            command=self.update_gui)
        b.pack (side='top', fill='both', expand=1)
        self.root.bind ("<Alt-o>", self.config_reader)
        self.root.bind ("<Alt-r>", self.reread_file)
        self.root.bind ("<Alt-u>", self.update_gui)

    def set_scalar_gui (self, event=None): 
        debug ("In VtkDataReader::set_scalar_gui ()")
        Common.state.busy ()
        self.set_scalar_name (self.scalar_var.get ())
        self.renwin.Render ()
        Common.state.idle ()

    def set_vector_gui (self, event=None): 
        debug ("In VtkDataReader::set_vector_gui ()")
        Common.state.busy ()
        self.set_vector_name (self.vector_var.get ())
        self.renwin.Render ()
        Common.state.idle ()

    def set_tensor_gui (self, event=None): 
        debug ("In VtkDataReader::set_tensor_gui ()")
        Common.state.busy ()
        self.set_tensor_name (self.tensor_var.get ())
        self.renwin.Render ()
        Common.state.idle ()
        
    def config_reader (self, event=None): 
        debug ("In VtkDataReader::config_reader ()")
        c = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        c.set_update_method (self.update_gui)
        c.configure (self.root, self.reader)

    def update_gui (self, event=None):
        debug ("In VtkDataReader::update_gui ()")
        self.reader.Update ()
        self.update_references ()

    def reread_file (self, event=None):        
        """ This re-reads the data file. Useful when you have changed
        the data and want the visualization to take notice.  Warning:
        this will not work properly if you change the file format or
        the dataset type."""
        debug ("In VtkDataReader::reread_file ()")
        Common.state.busy ()
        sc_lst, vec_lst, ten_lst = get_attribute_lists (self.file_name)
        change_in_attr = (self.scalar_lst != sc_lst) or \
                         (self.vector_lst != vec_lst) or \
                         (self.tensor_lst != ten_lst)
        self.scalar_lst, self.vector_lst, self.tensor_lst = \
                         sc_lst, vec_lst, ten_lst
        if (self.scalar_data_name and \
            (self.scalar_data_name not in sc_lst)) or \
            (self.vector_data_name and \
             (self.vector_data_name not in vec_lst)) or \
             (self.tensor_data_name and \
              (self.tensor_data_name not in ten_lst)):
            msg = "Warning: currently used data names:\n"\
                  "scalar name: %s\nvector name: %s\ntensor name: %s\n"\
                  "do not exist in file %s \n"\
                  "Setting to defaults!"%(self.scalar_data_name,
                                          self.vector_data_name,
                                          self.tensor_data_name,
                                          self.file_name)
            Common.print_err (msg)
            if self.scalar_lst:
                self.reader.SetScalarsName (self.scalar_lst[0])
            if self.vector_lst:
                self.reader.SetVectorsName (self.vector_lst[0])
            if self.tensor_lst:
                self.reader.SetTensorsName (self.tensor_lst[0])
            self.setup_names ()

        self.reader.Modified ()
        self.reader.Update ()
        self.update_references ()
        
        # the following changes the gui so that any changes in the
        # data are reflected in the gui.
        if self.root and self.root.winfo_exists() and change_in_attr:
            geom = self.root.geometry () # save old geometry
            master = self.root.master
            self.close_gui ()
            self.configure (master)
            self.root.geometry(geom[string.find(geom, '+'):])
        Common.state.idle ()
