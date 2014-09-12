"""
This file provides a reader for VTK's new XML data format.  It should
support any of the standard VTK XML data files.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.12 $"
__date__ = "$Date: 2005/08/02 18:30:14 $"

import string, os
import Base.Objects, Common
import Tkinter, tkFileDialog
import vtk
import vtkPipeline.vtkMethodParser
import vtkPipeline.ConfigVtkObj

debug = Common.debug
vtk_version = float(vtk.vtkVersion().GetVTKVersion()[:3])

def find_data_type (file_name):
    "Parses the named file to see what type of data there is."
    debug ("In find_data_type ()")
    r = vtk.vtkXMLFileReadTester()
    r.SetFileName(file_name)
    if r.TestReadFile():
        return r.GetFileDataType()
    else:
        raise Base.Objects.ParseException, \
              "File %s is not a valid VTK XML file!"%(file_name)


def get_array_type(arr):    
    """Returns if the array is a scalar ('scalars'), vector
    ('vectors') or tensor ('tensors').  It looks at the number of
    components to decide.  If it has a wierd number of components it
    returns the empty string."""    
    n = arr.GetNumberOfComponents()
    if n == 1:
        return 'scalars'
    elif n == 3:
        return 'vectors'
    elif n == 9:
        return 'tensors'
    else:
        return ''


def _get_attribute_list(data):
    """ Gets scalar, vector and tensor information from the given data
    (either cell or point data). """    
    debug ("In _get_attribute_list ()")    
    attr = {'scalars':[], 'vectors':[], 'tensors':[]}
    if data:
        n = data.GetNumberOfArrays()
        for i in range(n):
            name = data.GetArrayName(i)
            type = get_array_type(data.GetArray(i))
            if type:
                attr[type].extend([name])
    return attr


def get_attribute_lists (obj):    
    """Gets the scalar, vector and tensor attributes that are
    available in the given VTK data object."""
    debug ("In get_attribute_lists ()")
    point_attr = _get_attribute_list(obj.GetPointData())
    cell_attr = _get_attribute_list(obj.GetCellData())
    return point_attr, cell_attr    
    


def get_file_name (f_name):
    debug ("In get_file_name ()")
    msg = "Unable to open file: " + f_name
    msg = msg + "\n\nPlease try selecting the file manually."
    Common.print_err (msg)
    tk_fopen = tkFileDialog.askopenfilename

    f_types = [("All files", "*"),
               ("XML files", "*.xml"), ("Image Data", "*.vti"),
               ("Poly Data", "*.vtp"), ("Rectilinear Grid", "*.vtr"),
               ("Structured Grid", "*.vts"),
               ("Unstructured Grid", "*.vtu"),
               ("Parallel Image Data", "*.pvti"),
               ("Parallel Poly Data", "*.pvtp"),
               ("Parallel Rectilinear Grid", "*.pvtr"),
               ("Parallel Structured Grid", "*.pvts"),
               ("Parallel Unstructured Grid", "*.pvtu")]

    file_name = tk_fopen (title="Open VTK data file", 
                          filetypes=f_types)
    if not file_name:
        msg = "Unable to load VtkDataReader configuration since "\
              "no data file has been specified.  Cannot proceed!"
        raise IOError, msg
    else:
        return file_name



class VtkXMLDataReader (Base.Objects.DataSource):

    """This class is a reader for VTK's new XML data format.  It
    should support any of the standard VTK XML data files.  """

    def __init__ (self, renwin=None): 
        debug ("In VtkXMLDataReader::__init__ ()")
        Base.Objects.DataSource.__init__ (self)
        self.scalar_lst = [] # avaliable scalars
        self.vector_lst = []
        self.tensor_lst = []
        self.point_attr = None
        self.cell_attr = None
        self.reader = None
        self.renwin = renwin
        self.scalar_var = Tkinter.StringVar ()
        self.vector_var = Tkinter.StringVar ()
        self.tensor_var = Tkinter.StringVar ()
        self.data_types = {'StructuredGrid': 'STRUCTURED_GRID',
                           'PStructuredGrid': 'STRUCTURED_GRID',
                           'StructuredPoints': 'STRUCTURED_POINTS',
                           'ImageData': 'IMAGE_DATA',
                           'PImageData': 'IMAGE_DATA',
                           'RectilinearGrid': 'RECTILINEAR_GRID',
                           'PRectilinearGrid': 'RECTILINEAR_GRID',
                           'PolyData': 'POLYDATA',
                           'PPolyData': 'POLYDATA',
                           'UnstructuredGrid': 'UNSTRUCTURED_GRID',
                           'PUnstructuredGrid': 'UNSTRUCTURED_GRID'}

    def __del__ (self): 
        debug ("In VtkXMLDataReader::__del__ ()")
    
    def initialize (self, file_name): 
        "Overload this if reqd. Use the existing functions if possible."    
        debug ("In VtkXMLDataReader::initialize ()")
        Base.Objects.DataSource.initialize (self, file_name)
        Common.state.busy ()
        self.file_name = file_name
        self.create_reader ()
        self.set_file_name (file_name)
        self.reader.Update ()
        self.setup_defaults ()
        self.reader.GetOutput().Update ()
        self.update_references ()
        Common.state.idle ()
        
    def setup_defaults (self): 
        debug ("In VtkXMLDataReader::setup_defaults ()")
        pa, ca = get_attribute_lists(self.reader.GetOutput())
        self.point_attr, self.cell_attr = pa, ca
        self.scalar_lst = pa['scalars'] + ca['scalars']
        self.vector_lst = pa['vectors'] + ca['vectors']
        self.tensor_lst = pa['tensors'] + ca['tensors']

        out = self.reader.GetOutput()
        pd = out.GetPointData()
        cd = out.GetCellData()
        if pa['scalars']:
            pd.SetActiveScalars(self.scalar_lst[0])
        elif ca['scalars']:
            cd.SetActiveScalars(self.scalar_lst[0])
        if pa['vectors']:
            pd.SetActiveVectors(self.vector_lst[0])
        elif ca['vectors']:
            cd.SetActiveVectors(self.vector_lst[0])
        if pa['tensors']:
            pd.SetActiveTensors(self.tensor_lst[0])
        elif ca['tensors']:
            cd.SetActiveTensors(self.tensor_lst[0])

        self.setup_names ()

    def setup_names (self): 
        debug ("In VtkXMLDataReader::setup_names ()")
        out = self.reader.GetOutput()
        pd = out.GetPointData()
        cd = out.GetCellData()
        if not self.scalar_data_name:
            if pd:
                s = pd.GetScalars()
                if s:
                    self.scalar_data_name = s.GetName()
        if not self.scalar_data_name:
            if cd:
                s = cd.GetScalars()
                if s:
                    self.scalar_data_name = s.GetName()
        self.scalar_var.set(self.scalar_data_name)

        if not self.vector_data_name:
            if pd:
                v = pd.GetVectors()
                if v:
                    self.vector_data_name = v.GetName()
        if not self.vector_data_name:
            if cd:
                v = cd.GetVectors()
                if v:
                    self.vector_data_name = v.GetName()
        self.vector_var.set(self.vector_data_name)

        if not self.tensor_data_name:
            if pd:
                t = pd.GetTensors()
                if t:
                    self.tensor_data_name = t.GetName()
        if not self.tensor_data_name:
            if cd:
                t = cd.GetTensors()
                if t:
                    self.tensor_data_name = t.GetName()
        self.tensor_var.set(self.tensor_data_name)

    def create_reader (self): 
        "Create the corresponding reader."
        debug ("In VtkXMLDataReader::create_reader ()")
        # set up the reader     
        if self.file_name == "":
            raise IOError, "No filename specifed for the data handler!"

        gt = find_data_type (self.file_name)
        self.grid_type = self.data_types[gt]
        self.reader = eval('vtk.vtkXML%sReader()'%gt)

    def set_scalar_name (self, scalar): 
        debug ("In VtkXMLDataReader::set_scalar_name ()")
        assert (scalar in self.scalar_lst), \
               "Sorry, no scalar called %s available"%scalar
        self.scalar_data_name = scalar
        out = self.reader.GetOutput()
        pd = out.GetPointData()
        cd = out.GetCellData()
        if scalar in self.point_attr['scalars']:
            pd.SetActiveScalars(scalar)
        else:
            cd.SetActiveScalars(scalar)
        self.Update ()
        self.force_update()
        self.update_references ()

    def set_vector_name (self, vector): 
        debug ("In VtkXMLDataReader::set_vector_name ()")
        assert (vector in self.vector_lst), \
               "Sorry, no vector called %s available"%vector
        self.vector_data_name = vector
        out = self.reader.GetOutput()
        pd = out.GetPointData()
        cd = out.GetCellData()
        if vector in self.point_attr['vectors']:
            pd.SetActiveVectors(vector)
        else:
            cd.SetActiveVectors(vector)
        self.Update ()
        self.force_update()
        self.update_references ()

    def set_tensor_name (self, tensor): 
        debug ("In VtkXMLDataReader::set_tensor_name ()")
        assert (tensor in self.tensor_lst), \
               "Sorry, no tensor called %s available"%tensor
        self.tensor_data_name = tensor
        out = self.reader.GetOutput()
        pd = out.GetPointData()
        cd = out.GetCellData()
        if tensor in self.point_attr['tensors']:
            pd.SetActiveTensors(tensor)
        else:
            cd.SetActiveTensors(tensor)
        self.Update ()
        self.force_update()
        self.update_references ()

    def set_file_name(self, file_name):
        """Abstracts the call to self.reader.Set*FileName(). Useful
        when using this class as a base for other classes.  Override
        this if needed."""
        debug ("In VtkXMLDataReader::set_file_name ()")
        self.file_name = file_name
        self.reader.SetFileName(file_name)
        
    def get_scalar_list (self): 
        debug ("In VtkXMLDataReader::get_scalar_list ()")
        return self.scalar_lst

    def get_vector_list (self): 
        debug ("In VtkXMLDataReader::get_vector_list ()")
        return self.vector_lst

    def get_tensor_list (self): 
        debug ("In VtkXMLDataReader::get_tensor_list ()")
        return self.tensor_lst
            
    def GetOutput (self): 
        "Get the reader's output. "
        debug ("In VtkXMLDataReader::GetOutput ()")
        return self.reader.GetOutput ()

    def get_output (self): 
        debug ("In VtkXMLDataReader::get_output ()")
        return self.reader.GetOutput ()

    def force_update(self):
        """Used to force the pipeline to update. This is necessary
        since the consumers do not update when the output is
        modified."""
        debug ("In VtkXMLDataReader::force_update ()")
        if vtk_version < 4.5:
            # This does not seem necessary with VTK-4.5 and above.
            out = self.GetOutput()
            for i in range(out.GetNumberOfConsumers()):
                out.GetConsumer(i).Modified()

    def Update (self): 
        debug ("In VtkXMLDataReader::Update ()")
        self.reader.Update ()
        out = self.GetOutput()
        out.Modified()
        out.Update()

    def get_reader (self): 
        debug ("In VtkXMLDataReader::get_reader ()")
        return self.reader

    def get_render_window (self): 
        debug ("In VtkXMLDataReader::get_render_window ()")
        return self.renwin

    def save_config (self, file): 
        debug ("In VtkXMLDataReader::save_config ()")
        rel_file_name = Common.get_relative_file_name (file.name,
                                                       self.file_name)
        file.write ("%s\n"%rel_file_name)        
        file.write("%s\n%s\n%s\n"%(self.scalar_data_name,
                                   self.vector_data_name,
                                   self.tensor_data_name))
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        p.dump (self.reader, file)

    def load_config (self, file): 
        debug ("In VtkXMLDataReader::load_config ()")
        f_name = Common.get_abs_file_name (file.name,
                                           file.readline ()[:-1])
        if os.path.isfile (f_name):
            self.file_name = f_name
        else:
            self.file_name = get_file_name (f_name)
        
        Base.Objects.DataSource.initialize (self, self.file_name)
        sd = file.readline()[:-1]
        vd = file.readline()[:-1]
        td = file.readline()[:-1]
        # create the DataReader
        self.create_reader ()
        # load the settings.
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        p.load (self.reader, file)
        # Correct the filename because the stored filename uses an
        # absolute path.
        self.set_file_name(self.file_name)
        self.reader.Update ()
        
        pa, ca = get_attribute_lists(self.reader.GetOutput())
        self.point_attr, self.cell_attr = pa, ca
        self.scalar_lst = pa['scalars'] + ca['scalars']
        self.vector_lst = pa['vectors'] + ca['vectors']
        self.tensor_lst = pa['tensors'] + ca['tensors']

        if sd:
            self.set_scalar_name(sd)
        if vd:
            self.set_vector_name(vd)
        if td:
            self.set_tensor_name(td)
        
        self.setup_names ()
        self.update_references ()

    def scalar_gui (self, master): 
        debug ("In VtkXMLDataReader::scalar_gui ()")
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
        debug ("In VtkXMLDataReader::vector_gui ()")
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
        debug ("In VtkXMLDataReader::tensor_gui ()")
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
        debug ("In VtkXMLDataReader::make_custom_gui ()")
        self.make_main_gui ()
        self.make_close_button ()

    def make_main_gui (self): 
        debug ("In VtkXMLDataReader::make_main_gui ()")
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
        debug ("In VtkXMLDataReader::set_scalar_gui ()")
        scalar = self.scalar_var.get()
        if scalar == self.scalar_data_name:
            return
        Common.state.busy ()
        self.set_scalar_name (scalar)
        self.renwin.Render ()
        Common.state.idle ()

    def set_vector_gui (self, event=None): 
        debug ("In VtkXMLDataReader::set_vector_gui ()")
        vector = self.vector_var.get()
        if vector == self.vector_data_name:
            return
        Common.state.busy ()
        self.set_vector_name (vector)
        self.renwin.Render ()
        Common.state.idle ()

    def set_tensor_gui (self, event=None): 
        debug ("In VtkXMLDataReader::set_tensor_gui ()")
        tensor = self.tensor_var.get()
        if tensor == self.tensor_data_name:
            return
        Common.state.busy ()
        self.set_tensor_name (tensor)
        self.renwin.Render ()
        Common.state.idle ()
        
    def config_reader (self, event=None): 
        debug ("In VtkXMLDataReader::config_reader ()")
        c = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        c.set_update_method (self.update_gui)
        c.configure (self.root, self.reader)

    def update_gui (self, event=None):
        debug ("In VtkXMLDataReader::update_gui ()")
        self.reader.Update ()
        self.update_references ()

    def reread_file (self, event=None):        
        """ This re-reads the data file. Useful when you have changed
        the data and want the visualization to take notice.  Warning:
        this will not work properly if you change the file format or
        the dataset type."""
        debug ("In VtkXMLDataReader::reread_file ()")
        Common.state.busy ()
        self.reader.Modified ()
        self.reader.Update ()
        pa, ca = get_attribute_lists(self.reader.GetOutput())
        change_in_attributes = (self.point_attr != pa) or \
                               (self.cell_attr != ca)
        self.point_attr, self.cell_attr = pa, ca
        self.scalar_lst = pa['scalars'] + ca['scalars']
        self.vector_lst = pa['vectors'] + ca['vectors']
        self.tensor_lst = pa['tensors'] + ca['tensors']

        sc_lst, vec_lst, ten_lst = self.scalar_lst, \
                                   self.vector_lst, self.tensor_lst
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
            self.setup_defaults()
        else:
            sd, vd, td = self.scalar_data_name, self.vector_data_name, \
                         self.tensor_data_name,
        
            if sd:
                self.set_scalar_name(sd)
            if vd:
                self.set_vector_name(vd)
            if td:
                self.set_tensor_name(td)

        self.update_references()
        self.renwin.Render()
        # the following changes the gui so that any changes in the
        # data are reflected in the gui.
        if self.root and self.root.winfo_exists() and change_in_attributes:
            geom = self.root.geometry()
            master = self.root.master
            self.close_gui ()
            self.configure (master)
            self.root.geometry(geom[string.find(geom, '+'):])
        Common.state.idle ()
