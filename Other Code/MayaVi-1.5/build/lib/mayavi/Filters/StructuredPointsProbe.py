"""

A useful filter that can be used to probe any dataset using a
Structured Points dataset.  The filter also allows one to convert the
scalar data to an unsigned short array so that the scalars can be used
for volume visualization.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2003, Prabhu Ramachandran.
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.6 $"
__date__ = "$Date: 2005/08/23 17:02:48 $"

import Base.Objects, Common
import vtk
import Tkinter
import vtkPipeline.ConfigVtkObj

debug = Common.debug


class StructuredPointsProbe (Base.Objects.Filter):

    """ A useful filter that can be used to probe any dataset using a
    Structured Points dataset.  The filter also allows one to convert
    the scalar data to an unsigned short array so that the scalars can
    be used for volume visualization."""

    def initialize (self):
        debug ("In StructuredPointsProbe::__init__ ()")
        self.spacing_var = Tkinter.StringVar()
        self.dimension_var = Tkinter.StringVar()
        self.conv_scalar_var = Tkinter.IntVar()
        self.conv_scalar_var.set(1)
        self.p_data = vtk.vtkStructuredPoints()
        self.p_data_gui = None        
        self.init_p_data()
        self.fil = vtk.vtkProbeFilter ()
        self.fil.SetSource (self.prev_fil.GetOutput ())
        self.fil.SetInput(self.p_data)
        self.fil.Update ()
        self.set_scaled_scalars()
        self.pipe_objs = self.fil

    def init_p_data(self):
        debug ("In StructuredPointsProbe::init_p_data ()")
        pd = self.p_data
        out = self.prev_fil.GetOutput()
        if out.IsA('vtkStructuredPoints') or out.IsA('vtkImageData'):
            pd.SetOrigin(out.GetOrigin())
            pd.SetDimensions(out.GetDimensions())
            pd.SetSpacing(out.GetSpacing())
        else:
            b = out.GetBounds()
            pd.SetOrigin(b[0], b[2], b[4])
            l = [b[1] - b[0], b[3] - b[2], b[5] - b[4]]
            tot_len = float(l[0] + l[1] + l[2])
            npnt = pow(out.GetNumberOfPoints(), 1./3.) + 0.5
            fac = 3.0*npnt/tot_len
            dims = [int(l[0]*fac) + 1, int(l[1]*fac) + 1, int(l[2]*fac) + 1]
            pd.SetExtent(0, dims[0]-1, 0, dims[1] -1, 0, dims[2] -1)
            pd.SetUpdateExtent(0, dims[0]-1, 0, dims[1] -1, 0, dims[2] -1)
            pd.SetWholeExtent(0, dims[0]-1, 0, dims[1] -1, 0, dims[2] -1)
            pd.SetDimensions(dims)
            dims = [max(1, x-1) for x in dims]
            l = [max(1e-3, x) for x in l]
            sp = [l[0]/dims[0], l[1]/dims[1], l[2]/dims[2]]
            pd.SetSpacing(sp)
        pd.Update()

        sp = pd.GetSpacing()
        txt = "Point Spacing: [%.3g, %.3g, %.3g]"%(sp[0], sp[1], sp[2])
        self.spacing_var.set(txt)
        self.dimension_var.set(str(self.p_data.GetDimensions()))

    def set_input_source (self, source):
        debug ("In StructuredPointsProbe::set_input_source ()")
        Common.state.busy ()
        self.fil.SetSource (source.GetOutput ())
        self.prev_fil = source
        self.fil.Update ()
        self.set_scaled_scalars()
        Common.state.idle ()

    def set_scaled_scalars(self):
        debug ("In StructuredPointsProbe::set_scaled_scalars ()")
        out = self.fil.GetOutput()
        pd = out.GetPointData()
        
        sc = pd.GetScalars()
        if not sc: # no input scalars
            return

        if self.conv_scalar_var.get() == 0:            
            orig_sc = self.prev_fil.GetOutput().GetPointData().GetScalars()
            if sc.IsA('vtkUnsignedShortArray') and \
               sc.GetName() == 'sp_probe_us_data':
                pd.SetActiveScalars(orig_sc.GetName())
            return

        calc = vtk.vtkArrayCalculator()
        calc.SetAttributeModeToUsePointData()
        
        s_min, s_max = sc.GetRange()
        # checking to see if input array is constant.
        avg = (s_max + s_min)*0.5
        diff = 1
        if (s_max > avg) and (avg > s_min):
            diff = s_max - s_min
        
        base = sc.CreateDataArray(sc.GetDataType())
        base.SetNumberOfTuples(sc.GetNumberOfTuples())
        base.SetNumberOfComponents(1)
        base.SetName('sp_probe_us_base')
        base.FillComponent(0, s_min)
        pd.AddArray(base)
        
        calc.SetInput(out)
        calc.AddScalarVariable("s", sc.GetName(), 0)
        calc.AddScalarVariable("sb", base.GetName(), 0)
        calc.SetFunction("(s - sb)*%f"%(65535.0/diff))
        calc.SetResultArrayName('sp_probe_us_data')
        calc.Update()

        sc = calc.GetOutput().GetPointData().GetScalars()
        uca = vtk.vtkUnsignedShortArray()
        uca.SetName(sc.GetName())
        uca.DeepCopy(sc)
        pd.AddArray(uca)
        pd.SetActiveScalars('sp_probe_us_data')

    def save_config(self, file):
        debug ("In StructuredPointsProbe::save_config()")
        s = {}
        s['conv_scalar'] = self.conv_scalar_var.get()
        cfg = {}
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        p.dump(self.p_data, cfg)
        s['probe_config'] = cfg
        file.write("%s\n"%s)        
        # Somehow pickling the object turns off the scalars!?  The
        # following fixes that.
        self.fil.Update()
        self.set_scaled_scalars()

    def load_config(self, file):
        debug ("In StructuredPointsProbe::load_config()")
        s = eval(file.readline())
        self.conv_scalar_var.set(s['conv_scalar'])
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        p.load(self.p_data, s['probe_config'])
        self.fil.GlobalWarningDisplayOff()
        self.fil.SetInput(None)
        self.fil.SetInput(self.p_data)
        self.fil.Update()
        self.set_scaled_scalars()
        self.fil.GlobalWarningDisplayOn()
        
    def make_main_gui (self):
        debug ("In StructuredPointsProbe::make_main_gui()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)

        out = self.prev_fil.GetOutput()
        rw = 0
        b = out.GetBounds()
        txt = "Input bounds: [%.3g, %.3g, %.3g, %.3g, %.3g, %.3g]"%b
        lab = Tkinter.Label(frame, text=txt)
        lab.grid(row=rw, column=0, columnspan=2, sticky='ew')
        rw += 1
        lab = Tkinter.Label(frame, textvariable=self.spacing_var)
        lab.grid(row=rw, column=0, columnspan=2, sticky='ew')
        rw += 1

        lab = Tkinter.Label(frame, text='SetDimensions')        
        lab.grid(row=rw, column=0, sticky='ew')
        self.dimension_var.set(str(self.p_data.GetDimensions()))
        entr = Tkinter.Entry(frame, width=20, relief='sunken',
                             textvariable=self.dimension_var)
        entr.grid(row=rw, column=1, sticky='ew')
        entr.bind('<Return>', self.change_dimensions_gui)
        if out.IsA('vtkStructuredPoints') or out.IsA('vtkImageData'):
            entr.config(state='disabled')
        rw += 1
        
        but = Tkinter.Button(frame, text="Reset probe defaults",
                             underline=0,
                             command=self.reset_probe_defaults_gui)
        self.root.bind('<Alt-r>', self.reset_probe_defaults_gui)
        but.grid(row=rw, column=0, columnspan=2, sticky='ew')
        rw += 1
        cb = Tkinter.Checkbutton (frame, text="Scalars to UnsignedShort", 
                                  variable=self.conv_scalar_var,
                                  onvalue=1, offvalue=0,
                                  command=self.conv_scalar_gui)
        cb.grid (row=rw, column=0, columnspan=2, sticky='ew')
        rw += 1

    def reset_probe_defaults_gui(self, event=None):
        debug ("In StructuredPointsProbe::reset_probe_defaults_gui ()")
        Common.state.busy ()
        self.init_p_data()
        self.fil.GlobalWarningDisplayOff()
        self.fil.SetInput(None)
        self.fil.SetInput(self.p_data)
        self.fil.Update()
        self.set_scaled_scalars()
        self.fil.GlobalWarningDisplayOn()
        self.mod_m.Update()  
        self.renwin.Render()
        Common.state.idle ()

    def conv_scalar_gui(self, event=None):
        debug ("In StructuredPointsProbe::conv_scalar_gui ()")
        Common.state.busy ()
        self.set_scaled_scalars()
        self.fil.Update()
        self.mod_m.Update()
        self.renwin.Render()
        Common.state.idle ()        

    def change_dimensions_gui(self, event=None):
        debug ("In StructuredPointsProbe::change_dimensions_gui ()")
        Common.state.busy()
        pd = self.p_data
        out = self.prev_fil.GetOutput()
        b = out.GetBounds()
        l = [b[1] - b[0], b[3] - b[2], b[5] - b[4]]
        dims = eval(self.dimension_var.get())
        pd.SetDimensions(dims)
        pd.SetExtent(0, dims[0]-1, 0, dims[1] -1, 0, dims[2] -1)
        pd.SetUpdateExtent(0, dims[0]-1, 0, dims[1] -1, 0, dims[2] -1)
        pd.SetWholeExtent(0, dims[0]-1, 0, dims[1] -1, 0, dims[2] -1)
        pd.Update()        
        dims = [max(1, x-1) for x in dims]
        l = [max(1e-3, x) for x in l]
        sp = [l[0]/dims[0], l[1]/dims[1], l[2]/dims[2]]
        txt = "Point Spacing: [%.3g, %.3g, %.3g]"%(sp[0], sp[1], sp[2])
        self.spacing_var.set(txt)
        pd.SetSpacing(sp)
        self.fil.GlobalWarningDisplayOff()
        self.fil.SetInput(None)
        self.fil.SetInput(pd)
        self.fil.Update()
        self.fil.GlobalWarningDisplayOn()
        self.set_scaled_scalars()
        self.mod_m.Update()
        self.renwin.Render()
        Common.state.idle ()
        
