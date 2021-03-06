#!/usr/bin/env python

"""
This module defines a useful Tkinter based GUI editor for color
transfer functions.

Much of the original code was written by Gerard Gorman.  Prabhu
Ramachandran cleaned it up and incorporated it into the MayaVi
sources.

TODO:

  + Create a simple application like the Lut_Editor that can be used
    to edit and create LUTs.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2003, Prabhu Ramachandran.
"""

__author__ = "Gerard Gorman and Prabhu Ramachandran"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/08/02 18:26:25 $"

import Tkinter
import string
import vtk


def save_ctfs(volume_property):
    """Given a vtkVolumeProperty it saves the state of the RGB and
    opacity CTF to a dictionary and returns that."""
    vp = volume_property
    ctf = vp.GetRGBTransferFunction()
    otf = vp.GetScalarOpacity()
    s1, s2 = ctf.GetRange()
    nc = ctf.GetSize()
    ds = float(s2-s1)/(nc - 1)
    rgb, a = [], []
    for i in range(nc):
        rgb.append(ctf.GetColor(s1 + i*ds))
        a.append(otf.GetValue(s1 + i*ds))
    return {'range': (s1, s2), 'rgb':rgb, 'alpha':a}

def load_ctfs(saved_data, volume_property):
    """ Given the saved data produced via save_ctfs(), this member
    sets the state of the passed volume_property appropriately"""
    s1, s2 = saved_data['range']
    rgb = saved_data['rgb']
    a = saved_data['alpha']
    nc = len(a)
    ds = float(s2-s1)/(nc - 1)
    ctf = vtk.vtkColorTransferFunction ()
    otf = vtk.vtkPiecewiseFunction()
    for i in range(nc):
        v = s1 + i*ds
        ctf.AddRGBPoint(v, *(rgb[i]))
        otf.AddPoint(v, a[i])
    volume_property.SetColor(ctf)
    volume_property.SetScalarOpacity(otf)

def rescale_ctfs(volume_property, new_range):
    """ Given the volume_property with a new_range for the data while
    using the same transfer functions, this function rescales the
    CTF's so that everything work OK. """    
    ctf = volume_property.GetRGBTransferFunction()
    old_range = ctf.GetRange()
    if new_range != old_range:
        s_d = save_ctfs(volume_property)
        s1, s2 = new_range
        if s1 > s2:
            s_d['range'] = (s2, s1)
        else:
            s_d['range'] = (s1, s2)
        load_ctfs(s_d, volume_property)

def set_lut(lut, volume_property):
    """Given a vtkLookupTable and a vtkVolumeProperty it saves the
    state of the RGB and opacity CTF from the volume property to the
    LUT.  The number of colors to use is obtained from the LUT and not
    the CTF."""    
    vp = volume_property
    ctf = vp.GetRGBTransferFunction()
    otf = vp.GetScalarOpacity()
    s1, s2 = ctf.GetRange()
    nc = lut.GetNumberOfColors()
    ds = float(s2-s1)/(nc - 1)
    for i in range(nc):
        r, g, b = ctf.GetColor(s1 + i*ds)
        a = otf.GetValue(s1 + i*ds)
        lut.SetTableValue(i, r, g, b, a)

def set_ctf_from_lut(lut, volume_property):
    """Given a vtkLookupTable and a vtkVolumeProperty it loads the
    state of the RGB and opacity CTF from the lookup table to the CTF.
    The CTF range is obtained from the volume property and the number
    of colors to use is obtained from the LUT."""    
    vp = volume_property
    ctf = vp.GetRGBTransferFunction()
    s1, s2 = ctf.GetRange()
    nc = lut.GetNumberOfColors()
    ds = float(s2-s1)/(nc - 1)
    ctf = vtk.vtkColorTransferFunction ()
    otf = vtk.vtkPiecewiseFunction()
    for i in range(nc):
        v = s1 + i*ds
        r, g, b, a = lut.GetTableValue(i)
        ctf.AddRGBPoint(v, r, g, b)
        otf.AddPoint(v, a)
    volume_property.SetColor(ctf)
    volume_property.SetScalarOpacity(otf)

    
class PiecewiseFunction:
    def __init__(self, canv, line_color, ctf=None, color=None):
        """ Constructor.

          Input Arguments:

            canv -- The parent Tkinter canvas.
            line_color -- Line color to use for the piecewise function.

            ctf -- A vtkColorTransferFunction or a
            vtkPiecewiseFunction.  Defaults to None where the
            piecewise function is set to a sane default.
            
            color -- The color to be used from the
            vtkColorTransferFunction this has to be one of ['red',
            'green', 'blue'].  If the color is None (default), then
            the ctf is treated as a vtkPiecewiseFunction.
        """
        self.xLast   = -1.0
        self.yLast   = -1.0
        self.npoints = 101
        self.dt = 1.0/(self.npoints - 1)
        self.canv    = canv
        self.line_color   = line_color

        self.Fxn = vtk.vtkCardinalSpline ()
        self.initialize_ctf()
        if ctf:
            if color:
                self.load_vtkColorTransferFunction (ctf, color)
            else:
                self.load_vtkPiecewiseFunction (ctf)

    def initialize_ctf(self):
        # Initalize the piecewise function - 101 points from 0 to 1
        line = []
        for i in range(self.npoints):
            t = self.dt*i
            x = 0.5
            
            line.append (t)
            line.append (x)
            
            self.Fxn.AddPoint (t, x)
        self.lineHandle = self.canv.create_line (line, fill=self.line_color)
    
    def redraw_fxn(self):
        line = []
        for i in range(self.npoints):
            t = i*self.dt
            x,y = self.parametric2global (t, self.get_value(t))
            line.append (x)
            line.append (y)
            
        self.canv.coords(self.lineHandle, *line)
        return

    def global2parametric(self, x, y):
        # The values of t must be in integral multiples of self.dt
        # This is essential since the returned value of t must
        # correspond to an already added point in the
        # vtkCardinalSpline (self.Fxn).
        t = self.dt*int(self.npoints*x/(self.width () - 1.0))
        f = float(self.height() - 1.0 - y)/(self.height () - 1.0)
        return t, f

    def parametric2global(self, t, f):
        x = t*(self.width() - 1.0)
        y = self.height() - 1.0 - f*(self.height() - 1.0)
        return x, y
    
    def width(self):
        return self.canv.winfo_width ()
    
    def height(self):
        return self.canv.winfo_height ()
    
    def withinCanvas(self, event):
        return (self.withinXBounds(event) and self.withinYBounds(event))
    
    def withinXBounds(self, event):
        return (event.x >= 0) and (event.x <= self.width())

    def withinYBounds(self, event):
        return (event.y >= 0) and (event.y <= self.height())
    
    def resetXYLast(self, event):
        self.xLast = -1
        self.yLast = -1
                
    def _getY(self, event):
        y = event.y
        if y < 0:
            return 0
        elif y >= self.height():
            return self.height() - 1
        else:
            return y

    def setXYLast(self, event):
        self.xLast = event.x
        self.yLast = self._getY(event)
            
    def onModifyFxn(self, event):
        if self.withinXBounds(event):
            x = float(event.x)
            y = float(self._getY(event))
            
            if self.xLast < 0:
                t, f = self.global2parametric(x, y)
                self.Fxn.RemovePoint(t)
                self.Fxn.AddPoint(t, f)
            else:
                cnt = abs(x - self.xLast)
                if cnt > 0:
                    if self.xLast < x:
                        x0 = self.xLast
                        y0 = self.yLast
                        x1 = x
                        dy = (y - self.yLast)/float(cnt)
                    else:
                        x0 = x
                        y0 = y
                        x1 = self.xLast
                        dy = (self.yLast - y)/float(cnt)
                        
                    for i in range(int(cnt) + 1):
                        t, f = self.global2parametric (x0 + i, y0 + dy*i)
                        self.Fxn.RemovePoint (t)
                        self.Fxn.AddPoint (t, f)

            self.setXYLast(event)
        else:
            self.resetXYLast(event)
        self.Fxn.Compute()
        self.redraw_fxn ()

    def load_vtkPiecewiseFunction(self, vtk_fxn):
        s0, s1 = vtk_fxn.GetRange()
        self.Fxn.RemoveAllPoints ()
        ds = float(s1-s0)/(self.npoints - 1.0)
        for i in range(self.npoints):
            self.Fxn.AddPoint (i*self.dt, vtk_fxn.GetValue (s0 + i*ds))
        self.Fxn.Compute()
        self.redraw_fxn ()

    def load_vtkColorTransferFunction(self, vtk_fxn, color):
        s0, s1 = vtk_fxn.GetRange()
        self.Fxn.RemoveAllPoints ()
        ds = float(s1-s0)/(self.npoints - 1.0)
        for i in range(self.npoints):
            if string.lower(color) == "red":
                self.Fxn.AddPoint(i*self.dt, vtk_fxn.GetRedValue(s0 + i*ds))
            elif string.lower(color) == "green":
                self.Fxn.AddPoint(i*self.dt,
                                  vtk_fxn.GetGreenValue(s0 + i*ds))
            else:
                self.Fxn.AddPoint(i*self.dt,
                                  vtk_fxn.GetBlueValue(s0 + i*ds))
        self.Fxn.Compute()
        self.redraw_fxn()
                
    def get_function(self):
        f = vtk.vtkPiecewiseFunction ()
        for i in range(self.npoints):
            f.AddPoint(i*self.dt, self.get_value(i*self.dt))
        return f    

    def get_value(self, t):
        return max(min(self.Fxn.Evaluate(t), 1.0), 0.0)


class TransferFunctionEditor(Tkinter.Frame):
    
    """ A powerful and easy to use color transfer function editor.
    This is most useful with the volume module and is used to
    edit/create the vtkColorTransferFunction. """
    
    def __init__(self, parent, volume_property, width=250,
                 height=100):
        """Constructor.

        Input Arguments:
          parent -- parent Tk widget.
          volume_property -- a vtkVolumeProperty object that needs to
          be configured.
          width -- default, initial width of editor (250).
          height -- default, initial height of editor (100).
        """          
          
        Tkinter.Frame.__init__(self, parent)
        vp = volume_property
        ctf = vp.GetRGBTransferFunction()
        otf = vp.GetScalarOpacity()
        self.xLast = -1
        self.yLast = -1
        self.min_x, self.max_x = ctf.GetRange()
        
        self.canv = canv = Tkinter.Canvas(self, width=width,
                                          height=height,
                                          highlightthickness=0, border = 0,
                                          background='black')
        
        # Initalize the opacity/color transfer functions
        self.redFxn = PiecewiseFunction(self.canv, 'red', ctf, 'red')
        self.greenFxn = PiecewiseFunction(self.canv, 'green', ctf, 'green')
        self.blueFxn = PiecewiseFunction(self.canv, 'blue', ctf, 'blue')
        self.alphaFxn = PiecewiseFunction(self.canv, 'white', otf)
        
        canv.bind('<Shift-B1-Motion>',self.alphaFxn.onModifyFxn)
        canv.bind('<B1-Motion>',self.redFxn.onModifyFxn)
        canv.bind('<B2-Motion>',self.greenFxn.onModifyFxn)
        canv.bind('<Control-B1-Motion>',self.greenFxn.onModifyFxn)
        canv.bind('<B3-Motion>',self.blueFxn.onModifyFxn)
        canv.bind('<Control-B2-Motion>',self.greenFxn.onModifyFxn)
        canv.bind('<Leave>',self.resetXYLast)
        canv.bind('<ButtonRelease>',self.resetXYLast)
        canv.bind('<Motion>',self.UpdateInfo)
        canv.bind('<Configure>', self.redraw)

        canv.pack(side="top", fill="both", expand=1)

        self.color_bar = Tkinter.Canvas(self, width=width, height=10,
                                        highlightthickness=0, border=0,
                                        background='black')
        cb = self.color_bar
        cb.pack(side="top", fill="x", expand=1)
        self.create_color_bar()
        
        l1 = Tkinter.Label(self, text='Scalar:')
        l1.pack(side="left")
        self.s = s = Tkinter.Label(self, text='0.0', relief=Tkinter.RIDGE)
        s.pack(side="left")
        
        self.w = w = Tkinter.Label(self, text='0.0', relief=Tkinter.RIDGE)
        w.pack(side="right")
        l2 = Tkinter.Label(self, text='Weight:')
        l2.pack(side="right")

    def reset_ctfs(self, volume_property):
        """Updates the CTF's given a vtkVolumeProperty object."""
        vp = volume_property
        ctf = vp.GetRGBTransferFunction()
        otf = vp.GetScalarOpacity()
        self.min_x, self.max_x = ctf.GetRange()

        self.redFxn.load_vtkColorTransferFunction(ctf, 'red')
        self.greenFxn.load_vtkColorTransferFunction(ctf, 'green')
        self.blueFxn.load_vtkColorTransferFunction(ctf, 'blue')
        self.alphaFxn.load_vtkPiecewiseFunction(otf)
        self.redraw()        

    def get_tk_color(self, t):
        r = min(self.redFxn.get_value(t)*255, 255)
        g = min(self.greenFxn.get_value(t)*255, 255)
        b = min(self.blueFxn.get_value(t)*255, 255)
        return "#%02x%02x%02x"%(r, g, b)        

    def create_color_bar(self):
        cb = self.color_bar
        w = 250
        npnt = self.redFxn.npoints
        self.cb_boxes = box = []
        h = 10
        dx = float(w)/(npnt - 1)
        x1 = 0
        dt = 1.0/(npnt - 1.0)
        for i in range(npnt):
            col = self.get_tk_color(dt*i)
            box.append(cb.create_rectangle(x1, 0, x1 + dx, h, outline="",
                                           fill=col))
            x1 += dx
        self.update()

    def update_color_bar(self):
        cb = self.color_bar
        w = self.winfo_width()
        npnt = self.redFxn.npoints
        h = cb.winfo_height()
        dx = float(w)/(npnt - 1)
        x1 = 0
        dt = 1.0/(npnt - 1)
        box = self.cb_boxes
        for i in range(npnt):
            col = self.get_tk_color(dt*i)
            cb.coords(box[i], x1, 0, x1+dx, h)
            cb.itemconfig(box[i], fill=col)
            x1 += dx

    def width(self):
        return self.canv.winfo_width ()
    
    def height(self):
        return self.canv.winfo_height ()
    
    def bind(self, a, b):
        self.canv.bind(a, b)
        
    def UpdateInfo(self, event):
        val = self.min_x + (self.max_x - self.min_x)*(float(event.x)/(self.width() - 1.0))
        self.s.config(text='%f'%val)
        
        weight = float(self.height() - 1.0 - event.y)/(self.height() - 1.0)
        self.w.config(text='%f'%weight)
                
    def resetXYLast(self, event):
        self.alphaFxn.resetXYLast(event)
        self.redFxn.resetXYLast(event)
        self.greenFxn.resetXYLast(event)
        self.blueFxn.resetXYLast(event)
        self.redraw ()
        
    def redraw(self, event=None):
        self.alphaFxn.redraw_fxn()
        self.redFxn.redraw_fxn()
        self.greenFxn.redraw_fxn()
        self.blueFxn.redraw_fxn()
        self.update_color_bar()
        
    def getTFxn(self):
        a = self.alphaFxn.get_function ()
        f = vtk.vtkPiecewiseFunction ()
        npnt = self.alphaFxn.npoints
        dt = 1.0/(npnt - 1.0)
        ds = (self.max_x - self.min_x)/(npnt - 1.0)
        
        for i in range(npnt):
            f.AddPoint(self.min_x + i*ds, a.GetValue(i*dt))
        return f

    def getCTFxn(self):
        ctfun = vtk.vtkColorTransferFunction ()
        r = self.redFxn.get_function ()
        g = self.greenFxn.get_function ()
        b = self.blueFxn.get_function ()
        npnt = self.redFxn.npoints
        dt = 1.0/(npnt - 1.0)
        ds = (self.max_x - self.min_x)/(npnt - 1.0)
        
        for i in range(npnt):
            ctfun.AddRGBPoint(self.min_x + i*ds,
                              r.GetValue(i*dt),
                              g.GetValue(i*dt), b.GetValue(i*dt))
        return ctfun


