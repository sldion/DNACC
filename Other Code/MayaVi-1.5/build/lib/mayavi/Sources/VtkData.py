"""

This Source object allows one to create a vtkData object
vtkStructuredGrid, vtkStructuredPoints, vtkRectilinearGrid,
vtkPolyData, vtkUnstructuredGrid or a corresponding reader object and
use MayaVi to visualize it.  This makes it easy to create data on the
fly and then use MayaVi for visualization.  The class handles
save_visualization requests intelligently by dumping the used data to
a file that can be used subsequently.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.10 $"
__date__ = "$Date: 2005/08/02 18:30:14 $"

import string
import Tkinter
import Base.Objects, Common
import vtk, string
import vtkPipeline.vtkMethodParser
import vtkPipeline.ConfigVtkObj
from VtkXMLDataReader import get_array_type

debug = Common.debug


def _get_attribute_list(data):
    """ Gets scalar, vector and tensor information from the given data
    (either cell or point data). """    
    debug ("In _get_attribute_list ()")    
    attr = {'scalars':[], 'vectors':[], 'tensors':[]}
    if data:
        n = data.GetNumberOfArrays()
        for i in range(n):
            arr = data.GetArray(i)
            type = get_array_type(arr)
            name = arr.GetName()
            if not name:
                name = "%s%d"%(type[:-1], len(attr[type]))
                arr.SetName(name)
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


class VtkData (Base.Objects.DataSource):

    """ This Source object allows one to create a vtkData object
    vtkStructuredGrid, vtkStructuredPoints, vtkRectilinearGrid,
    vtkPolyData, vtkUnstructuredGrid or a corresponding reader object
    and use MayaVi to visualize it.  This makes it easy to create data
    on the fly and then use MayaVi for visualization.  The class
    handles save_visualization requests intelligently by dumping the
    used data to a file that can be used subsequently."""

    def __init__ (self, renwin=None): 
        debug ("In VtkData::__init__ ()")
        Base.Objects.DataSource.__init__ (self)
        self.renwin = renwin
        self.data = None
        self.scalar_lst = [] # avaliable scalars
        self.vector_lst = []
        self.tensor_lst = []
        self.point_attr = None
        self.cell_attr = None
        self.file_name = "No file"
        self.scalar_var = Tkinter.StringVar ()
        self.vector_var = Tkinter.StringVar ()
        self.tensor_var = Tkinter.StringVar ()
        self.data_types = {'vtkStructuredGrid': 'STRUCTURED_GRID',
                           'vtkStructuredPoints': 'STRUCTURED_POINTS',
                           'vtkImageData': 'IMAGE_DATA',
                           'vtkRectilinearGrid': 'RECTILINEAR_GRID',
                           'vtkPolyData': 'POLYDATA',
                           'vtkUnstructuredGrid': 'UNSTRUCTURED_GRID'}
        self.writers = {}
        self.readers = {}
        for x in self.data_types:
            if x == 'vtkImageData':
                self.writers[x] = vtk.vtkStructuredPointsWriter
                self.readers[x] = vtk.vtkStructuredPointsReader
            else:
                self.writers[x] = getattr(vtk, x + 'Writer')
                self.readers[x] = getattr(vtk, x + 'Reader')
        self.current_type = ''

    def _get_type (self, obj):
        debug ("In VtkData::_get_type ()")
        self.grid_type = ''
        for i in self.data_types.keys ():
            if obj.IsA (i):
                self.grid_type = self.data_types[i]
                self.current_type = i
                break
        if not self.grid_type:
            raise Base.Objects.ParseException, \
                  "Unknown data type: Known data types are one of: %s."\
                  %(self.data_types.keys ())
    
    def initialize (self, obj): 
        """Initialize the object given a valid object."""
        debug ("In VtkData::initialize ()")
        Common.state.busy ()
        if obj.IsA ('vtkDataReader'):
            self.data = obj.GetOutput ()
        else:
            self.data = obj            
        self._get_type (self.data)
        self.setup_defaults()
        self.update_references ()
        Common.state.idle ()

    def setup_defaults (self): 
        debug ("In VtkData::setup_defaults ()")
        pa, ca = get_attribute_lists(self.data)
        self.point_attr, self.cell_attr = pa, ca
        self.scalar_lst = pa['scalars'] + ca['scalars']
        self.vector_lst = pa['vectors'] + ca['vectors']
        self.tensor_lst = pa['tensors'] + ca['tensors']

        out = self.data
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
        debug ("In VtkData::setup_names ()")
        out = self.data
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

    def set_scalar_name (self, scalar): 
        debug ("In VtkData::set_scalar_name ()")
        assert (scalar in self.scalar_lst), \
               "Sorry, no scalar called %s available"%scalar
        self.scalar_data_name = scalar
        out = self.data
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
        debug ("In VtkData::set_vector_name ()")
        assert (vector in self.vector_lst), \
               "Sorry, no vector called %s available"%vector
        self.vector_data_name = vector
        out = self.data
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
        debug ("In VtkData::set_tensor_name ()")
        assert (tensor in self.tensor_lst), \
               "Sorry, no tensor called %s available"%tensor
        self.tensor_data_name = tensor
        out = self.data
        pd = out.GetPointData()
        cd = out.GetCellData()
        if tensor in self.point_attr['tensors']:
            pd.SetActiveTensors(tensor)
        else:
            cd.SetActiveTensors(tensor)
        self.Update ()
        self.force_update()
        self.update_references ()
        
    def GetOutput (self): 
        """Get the Data reader's output. """
        debug ("In VtkData::GetOutput ()")
        return self.data

    def get_output (self): 
        debug ("In VtkData::get_output ()")
        return self.data

    def get_scalar_list (self): 
        debug ("In VtkData::get_scalar_list ()")
        return self.scalar_lst

    def get_vector_list (self): 
        debug ("In VtkData::get_vector_list ()")
        return self.vector_lst

    def get_tensor_list (self): 
        debug ("In VtkData::get_tensor_list ()")
        return self.tensor_lst      

    def force_update(self):
        """Used to force the pipeline to update. This is necessary
        since the consumers do not update when the output is
        modified."""
        debug ("In VtkData::force_update ()")
        out = self.GetOutput()
        for i in range(out.GetNumberOfConsumers()):
            out.GetConsumer(i).Modified()

    def Update (self): 
        debug ("In VtkData::Update ()")
        self.data.Update ()
        out = self.GetOutput()
        out.Modified()
        out.Update()

    def get_render_window (self): 
        debug ("In VtkData::get_render_window ()")
        return self.renwin

    def save_config (self, file): 
        """Save the configuration to file."""
        debug ("In VtkData::save_config ()")
        # write the data to a vtk file.
        filename = file.name + '.vtk'
        writer = self.writers[self.current_type]()
        writer.SetFileName (filename)
        writer.SetInput (self.data)
        writer.Write ()        
        # now save the necessary data to the mayavi file.
        file.write ("%s, %s\n"%(self.current_type, filename))
        file.write ("%s, %s, %s\n"%(self.scalar_data_name,
                                    self.vector_data_name,
                                    self.tensor_data_name))
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        p.dump (self.data, file)

    def load_config (self, file): 
        """Load the saved objects configuration from a file."""
        debug ("In VtkData::load_config ()")
        val = string.replace (file.readline ()[:-1], ' ', '')
        val = string.split (val, ',')
        typ, filename = val
        val = string.replace (file.readline ()[:-1], ' ', '')
        val = string.split (val, ',')
        s_n, v_n, t_n = val
        self.scalar_data_name = s_n
        self.vector_data_name, self.tensor_data_name = v_n, t_n
        # set type info.
        self.current_type = typ
        self.grid_type = self.data_types[typ]
        # read data from vtk file.
        reader = self.readers[self.current_type]()
        reader.SetFileName (filename)
        reader.Update ()
        if self.current_type == 'vtkImageData':
            self.data = vtk.vtkImageData()
            self.data.DeepCopy(reader.GetOutput())
        else:
            self.data = reader.GetOutput ()
        # now read the config for the object
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        p.load (self.data, file)

        pa, ca = get_attribute_lists(self.data)
        self.point_attr, self.cell_attr = pa, ca
        self.scalar_lst = pa['scalars'] + ca['scalars']
        self.vector_lst = pa['vectors'] + ca['vectors']
        self.tensor_lst = pa['tensors'] + ca['tensors']

        if s_n:
            self.set_scalar_name(s_n)
        if v_n:
            self.set_vector_name(v_n)
        if t_n:
            self.set_tensor_name(t_n)
        
        self.setup_names ()
        self.update_references ()
        

    def scalar_gui (self, master): 
        debug ("In VtkData::scalar_gui ()")
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
        debug ("In VtkData::vector_gui ()")
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
        debug ("In VtkData::tensor_gui ()")
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
        debug ("In VtkData::make_custom_gui ()")
        self.make_main_gui ()
        self.make_close_button ()

    def make_main_gui (self): 
        debug ("In VtkData::make_main_gui ()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top')
        lab = Tkinter.Label (frame,
                             text="VTK Data object: %s"%self.current_type)
        lab.pack (side='top', fill='both', expand=1)
        self.scalar_gui (frame)
        self.vector_gui (frame)
        self.tensor_gui (frame)
        but1 = Tkinter.Button (frame, text="More Config options",
                               command=self.config_data, underline=1)
        but1.pack (side='top', fill='both', expand=1)
        b = Tkinter.Button (frame, text="Update", underline=0,
                            command=self.update_data)
        b.pack (side='top', fill='both', expand=1)
        self.root.bind ("<Alt-o>", self.config_data)
        self.root.bind ("<Alt-u>", self.update_data)

    def set_scalar_gui (self, event=None): 
        debug ("In VtkData::set_scalar_gui ()")
        scalar = self.scalar_var.get()
        if scalar == self.scalar_data_name:
            return
        Common.state.busy ()
        self.set_scalar_name (scalar)
        self.renwin.Render ()
        Common.state.idle ()

    def set_vector_gui (self, event=None): 
        debug ("In VtkData::set_vector_gui ()")
        vector = self.vector_var.get()
        if vector == self.vector_data_name:
            return
        Common.state.busy ()
        self.set_vector_name (vector)
        self.renwin.Render ()
        Common.state.idle ()

    def set_tensor_gui (self, event=None): 
        debug ("In VtkData::set_tensor_gui ()")
        tensor = self.tensor_var.get()
        if tensor == self.tensor_data_name:
            return
        Common.state.busy ()
        self.set_tensor_name (tensor)
        self.renwin.Render ()
        Common.state.idle ()
        
    def config_data (self, event=None): 
        debug ("In VtkData::config_data()")
        c = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        c.configure (self.root, self.data)

    def update_data(self, event=None):
        """ This looks at the input data again. Useful when you have changed
        the data and want the visualization to take notice.  Warning:
        this will not work properly if you change the file format or
        the dataset type."""
        debug ("In VtkData::update_data ()")
        Common.state.busy()
        pa, ca = get_attribute_lists(self.data)
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
            Common.print_err(msg)
            self.setup_defaults()
            self.force_update()
            self.update_references()
        else:
            sd, vd, td = self.scalar_data_name, self.vector_data_name, \
                         self.tensor_data_name,        
            if sd:
                self.set_scalar_name(sd)
            if vd:
                self.set_vector_name(vd)
            if td:
                self.set_tensor_name(td)

        self.renwin.Render()
        # the following changes the gui so that any changes in the
        # data are reflected in the gui.
        geom = self.root.geometry()
        master = self.root.master
        self.close_gui ()
        self.configure (master)
        self.root.geometry(geom[string.find(geom, '+'):])
        Common.state.idle ()
        
