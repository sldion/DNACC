"""

Defines a simple wrapper for the vtkRenderWindow.  This the class
which is responsible for all the actual rendering. It is also
responsible for saving the scene to a image.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2001-2003, Prabhu Ramachandran.
 
"""

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.28 $"
__date__ = "$Date: 2005/08/02 18:26:25 $"

import Tkinter, tkFileDialog, tkMessageBox, tkSimpleDialog
import vtk
from vtk.tk import vtkTkRenderWidget
import Common, Base.Objects
import types, os
import vtkPipeline.ConfigVtkObj
import vtkPipeline.vtkMethodParser
import Picker, Lights

tk_fsave = tkFileDialog.asksaveasfilename
debug = Common.debug


class JPEGDialog(tkSimpleDialog.Dialog):
    def __init__ (self, parent, values):
        debug ("In JPEGDialog ::__init__ ()")
        self.values = values
        tkSimpleDialog.Dialog.__init__ (self, parent,
                                        "Set JPEG parameters.")

    def body (self, master):
        debug ("In JPEGDialog ::body ()")
        self.prog_var = Tkinter.IntVar ()
        self.prog_var.set (self.values[1])
        cb = Tkinter.Checkbutton (master, text="Progressive JPEG",
                                  variable=self.prog_var, onvalue=1,
                                  offvalue=0)
        cb.pack(side='top', fill='both', expand=1)

        sl = Tkinter.Scale (master, label="JPEG Quality", from_=0, to=100,
                            length="8c", orient='horizontal')
        sl.set (self.values[0])
        sl.pack (side='top')
        sl.bind ("<ButtonRelease>", self.set_quality)
        self.quality_scale = sl
        return sl

    def set_quality (self, event=None):
        debug ("In JPEGDialog ::set_quality ()")
        self.values[0] = self.quality_scale.get ()

    def set_progressive (self, event=None):
        debug ("In JPEGDialog ::set_progressive ()")
        self.values[1] = self.prog_var.get()

    def ok (self, event=None):
        debug ("In JPEGDialog ::ok ()")
        self.result = self.values
        tkSimpleDialog.Dialog.ok (self, event)



class RenderWindow (Base.Objects.VizObject):
    
    """ Defines a simple wrapper for the vtkRenderWindow.  This the
    class which is responsible for all the actual rendering. It is
    also responsible for saving the scene to a image. """

    def __init__ (self, master): 
        debug ("In RenderWindow::__init__ ()")
        Base.Objects.VizObject.__init__ (self)
        self.frame = Tkinter.Frame (master)
        self.frame.pack (side='top', fill='both', expand=1)
        tkw = None
        self._do_render = 1
        stereo = Common.config.stereo
        if stereo:
            tkw = vtkTkRenderWidget.vtkTkRenderWidget (self.frame, width=600,
                                                       height=505, stereo=1)
        else:
            tkw = vtkTkRenderWidget.vtkTkRenderWidget (self.frame, width=600,
                                                       height=505)
        self.tkwidget = tkw
        self.tkwidget.pack (expand='true',fill='both')
        #self.tkwidget.bind ("<KeyPress-q>", self.quit)
        # disabling surface and wireframe toggling.
        self.tkwidget.unbind ("<KeyPress-s>")
        self.tkwidget.unbind ("<KeyPress-w>")
        self.ren = vtk.vtkRenderer ()
        self.ren.TwoSidedLightingOn ()
        self.renwin = self.tkwidget.GetRenderWindow ()
        self.renwin.AddRenderer (self.ren)
        
        if stereo:
            self.renwin.SetStereoType(stereo[1])
            self.renwin.SetStereoRender(stereo[0])
            
        self.camera = self.ren.GetActiveCamera()        
        # this sets up the tkwidget and forces _CurrentRenderer
        # etc. to be updated
        self.tkwidget.UpdateRenderer (0.0, 0.0)

        buttonFrame=Tkinter.Frame (self.frame, relief='sunken', bd=2)
        buttonFrame.pack (side='bottom')
        Tkinter.Label (buttonFrame, text="View:").pack (side='left')
        Tkinter.Button(buttonFrame, text="+X",
                       command=self.x_plus_view).pack(side='left')
        Tkinter.Button(buttonFrame, text="-X",
                       command=self.x_minus_view).pack(side='left')
        Tkinter.Button(buttonFrame, text="+Y",
                       command=self.y_plus_view).pack(side='left')
        Tkinter.Button(buttonFrame, text="-Y",
                       command=self.y_minus_view).pack(side='left')
        Tkinter.Button(buttonFrame, text="+Z",
                       command=self.z_plus_view).pack(side='left')
        Tkinter.Button(buttonFrame, text="-Z",
                       command=self.z_minus_view).pack(side='left')
        #Tkinter.Button(buttonFrame, text="Default View",
        #               command=self.reset_zoom).pack(side='left')
        Tkinter.Button(buttonFrame, text="Isometric",
                       command=self.isometric_view).pack(side='left')

        self.set_background (Common.config.bg_color)

        # Create and bind the picker.
        self.picker = Picker.Picker(self.frame, self)
        self.tkwidget.bind ("<KeyPress-p>", self.picker.pick)
        self.tkwidget.bind ("<KeyPress-P>", self.picker.pick)
        
        # Create and bind the Light Manager.
        self.light_mgr = Lights.LightManager(self.frame, self, self.ren,
                                             mode='vtk')
        self.tkwidget.bind ("<KeyPress-l>", self.light_mgr.config)
        self.tkwidget.bind ("<KeyPress-L>", self.light_mgr.config)
        if Common.config.light_cfg:
            self.light_mgr.load_config(Common.config.light_cfg)

        self.def_pos = 1
        self.root = None
        self.pipe_objs = self.renwin

    def __del__ (self):
        debug ("In RenderWindow::__del__ ()")
        pass

    def disable_render(self):        
        """Use this to disable any rendering via Render() calls."""
        debug ("In RenderWindow::disable_render ()")
        self._do_render = 0

    def enable_render(self):
        """Use this to enable rendering via Render() calls."""
        debug ("In RenderWindow::enable_render ()")
        self._do_render = 1
        
    def update_view (self, x, y, z, vx, vy, vz):
        debug ("In RenderWindow::update_view ()")
        self.camera.SetFocalPoint (0.0, 0.0, 0.0)
        self.camera.SetPosition (x, y, z)
        self.camera.SetViewUp (vx, vy, vz)
        self.ren.ResetCamera()
        self.renwin.Render()

    def x_plus_view (self): 
        debug ("In RenderWindow::x_plus_view ()")
        self.update_view (self.def_pos, 0, 0, 0, 0, 1)
        
    def x_minus_view (self): 
        debug ("In RenderWindow::x_minus_view ()")
        self.update_view (-self.def_pos, 0, 0, 0, 0, 1)
        
    def z_plus_view (self): 
        debug ("In RenderWindow::z_plus_veiw ()")
        self.update_view (0, 0, self.def_pos, 0, 1, 0)

    def z_minus_view (self):
        debug ("In RenderWindow::z_minus_veiw ()")
        self.update_view (0, 0, -self.def_pos, 0, 1, 0)
        
    def y_plus_view (self): 
        debug ("In RenderWindow::y_plus_view ()")
        self.update_view (0, self.def_pos, 0, 1, 0, 0)
        
    def y_minus_view (self): 
        debug ("In RenderWindow::y_minus_view ()")
        self.update_view (0, -self.def_pos, 0, 1, 0, 0)

    def isometric_view (self): 
        debug ("In RenderWindow::isometric_view ()")
        self.update_view (self.def_pos, self.def_pos, self.def_pos,
                          0, 0, 1)

    def reset_zoom (self): 
        debug ("In RenderWindow::reset_zoom ()")
        self.ren.ResetCamera ()
        self.renwin.Render ()

    def add_actors (self, actors):
        """ Adds a single actor or a tuple or list of actors to the
        renderer."""
        debug ("In RenderWindow::add_actors ()")
        if type (actors) is types.ListType or \
           type (actors) is types.TupleType:            
            for actor in actors:
                self.add_actors (actor)
        else:
            # warning: I dont check if the type is valid.
            if actors:
                self.ren.AddActor (actors)

    def remove_actors (self, actors): 
        """ Renders a single actor or a tuple or list of actors to the
        renderer."""
        debug ("In RenderWindow::remove_actors ()")
        if type (actors) is types.ListType or \
           type (actors) is types.TupleType:
            for actor in actors:
                self.remove_actors (actor)
        else:
            # warning: I dont check if the type is valid.
            if actors:
                self.ren.RemoveActor (actors)

    def save_ps (self, file_name=""):        
        debug ("In RenderWindow::save_ps ()")
        if not file_name:
            file_name = tk_fsave (title="Export to PostScript",
                                  initialdir=Common.config.initial_dir,
                                  defaultextension=".ps",
                                  filetypes=[("PS files", "*.ps"),
                                             ("All files", "*")])
        if len (file_name) != 0:
            Common.state.busy ()
            w2if = vtk.vtkWindowToImageFilter ()
            w2if.SetMagnification (Common.config.magnification)
            self.lift ()
            w2if.SetInput (self.renwin)
            ex = vtk.vtkPostScriptWriter ()
            ex.SetFileName (file_name)
            ex.SetInput (w2if.GetOutput ())
            ex.Write ()
            Common.state.idle ()

    def save_ppm (self, file_name=""): 
        debug ("In RenderWindow::save_ppm ()")
        if not hasattr(self.renwin, 'SetFileName'):
            msg = "Saving to a PPM file is no longer supported under "\
                  "this VTK version please use another format. "
            Common.print_err (msg)
            return        
        if not file_name:
            file_name = tk_fsave (title="Save scene to PPM image file",
                                  initialdir=Common.config.initial_dir,
                                  defaultextension=".ppm",
                                  filetypes=[("PPM images", "*.ppm"), 
                                             ("All files", "*")])
        if len (file_name) != 0:
            Common.state.busy ()
            self.renwin.SetFileName (file_name)
            self.lift ()
            self.renwin.SaveImageAsPPM ()
            Common.state.idle ()

    def save_bmp (self, file_name=""): 
        debug ("In RenderWindow::save_bmp ()")
        if not file_name:
            file_name = tk_fsave (title="Export to BMP image",
                                  initialdir=Common.config.initial_dir,
                                  defaultextension=".bmp",
                                  filetypes=[("BMP images", "*.bmp"), 
                                             ("All files", "*")])
        if len (file_name) != 0:
            Common.state.busy ()
            w2if = vtk.vtkWindowToImageFilter ()
            w2if.SetMagnification (Common.config.magnification)
            self.lift ()
            w2if.SetInput (self.renwin)
            ex = vtk.vtkBMPWriter ()
            ex.SetFileName (file_name)
            ex.SetInput (w2if.GetOutput ())
            ex.Write () 
            Common.state.idle ()

    def save_tiff (self, file_name=""): 
        debug ("In RenderWindow::save_tiff ()")
        if not file_name:
            file_name = tk_fsave (title="Export to TIFF image",
                                  initialdir=Common.config.initial_dir,
                                  defaultextension=".tif",
                                  filetypes=[("TIFF images", "*.tiff"), 
                                             ("TIFF images", "*.tif"),
                                             ("All files", "*")])
        if len (file_name) != 0:
            Common.state.busy ()
            w2if = vtk.vtkWindowToImageFilter ()
            w2if.SetMagnification (Common.config.magnification)
            self.lift ()
            w2if.SetInput (self.renwin)
            ex = vtk.vtkTIFFWriter ()
            ex.SetFileName (file_name)
            ex.SetInput (w2if.GetOutput ())
            ex.Write () 
            Common.state.idle ()

    def save_png (self, file_name=""):
        """Requires VTK 4 to work."""
        debug ("In RenderWindow::save_png ()")
        try:
            ex = vtk.vtkPNGWriter ()
        except AttributeError:
            msg = "Saving to a PNG file is not supported by your "\
                  "version of VTK.  Versions 4.0 and above support this."
            Common.print_err (msg)
            return
        if not file_name:
            file_name = tk_fsave (title="Export to PNG image",
                                  initialdir=Common.config.initial_dir,
                                  defaultextension=".png",
                                  filetypes=[("PNG images", "*.png"),
                                             ("All files", "*")])
        if len (file_name) != 0:
            Common.state.busy ()
            w2if = vtk.vtkWindowToImageFilter ()
            w2if.SetMagnification (Common.config.magnification)
            self.lift ()
            w2if.SetInput (self.renwin)
            ex = vtk.vtkPNGWriter ()
            ex.SetFileName (file_name)
            ex.SetInput (w2if.GetOutput ())
            ex.Write () 
            Common.state.idle ()

    def save_jpg(self, file_name="", quality=None, progressive=None):
        """Requires VTK 4 to work.  Arguments: file_name if passed
        will be used, quality is the quality of the JPEG (10-100) are
        valid, the progressive arguments toggles progressive jpegs."""
        debug ("In RenderWindow::save_jpg ()")
        try:
            ex = vtk.vtkJPEGWriter()
        except AttributeError:
            msg = "Saving to a JPEG file is not supported by your "\
                  "version of VTK.  Versions 4.0 and above support this."
            Common.print_err (msg)
            return
        if not file_name:
            file_name = tk_fsave (title="Export to JPEG image",
                                  initialdir=Common.config.initial_dir,
                                  defaultextension=".jpg",
                                  filetypes=[("JPEG images", "*.jpg"), 
                                             ("JPEG images", "*.jpeg"),
                                             ("All files", "*")])
        if len (file_name) != 0:
            if not quality and not progressive:
                d = JPEGDialog (self.frame, [75, 1])
                if d.result:
                    quality, progressive = d.result
                else:
                    return
            Common.state.busy ()
            w2if = vtk.vtkWindowToImageFilter ()
            w2if.SetMagnification (Common.config.magnification)
            self.lift ()
            w2if.SetInput (self.renwin)
            ex = vtk.vtkJPEGWriter ()
            ex.SetQuality (quality)
            ex.SetProgressive (progressive)
            ex.SetFileName (file_name)
            ex.SetInput (w2if.GetOutput ())
            ex.Write ()
            Common.state.idle ()

    def save_iv (self, file_name=""): 
        debug ("In RenderWindow::save_iv ()")
        if not file_name:
            file_name = tk_fsave (title="Export to OpenInventor",
                                  initialdir=Common.config.initial_dir,
                                  defaultextension=".iv",
                                  filetypes=[("OpenInventor files",
                                              "*.iv"), 
                                             ("All files", "*")])
        if len (file_name) != 0:
            Common.state.busy ()
            ex = vtk.vtkIVExporter ()
            self.lift ()
            ex.SetInput (self.renwin)
            ex.SetFileName (file_name)
            ex.Write ()
            Common.state.idle ()

    def save_vrml (self, file_name=""): 
        debug ("In RenderWindow::save_vrml ()")
        if not file_name:
            file_name = tk_fsave (title="Export to VRML", 
                                  initialdir=Common.config.initial_dir,
                                  defaultextension=".wrl",
                                  filetypes=[("VRML files", "*.wrl"), 
                                             ("All files", "*")])
        if len (file_name) != 0:
            Common.state.busy ()
            ex = vtk.vtkVRMLExporter ()
            self.lift ()
            ex.SetInput (self.renwin)
            ex.SetFileName (file_name)
            ex.Write ()
            Common.state.idle ()

    def save_oogl (self, file_name=""):        
        """Saves the scene to a Geomview OOGL file. Requires VTK 4 to
        work."""        
        debug ("In RenderWindow::save_oogl ()")
        try:
            ex = vtk.vtkOOGLExporter ()
        except AttributeError:
            msg = "Saving to a Geomview OOGL file is not supported by "\
                  "your version of VTK.  Versions 4.0 and above "\
                  "support this."
            Common.print_err (msg)
            return
        if not file_name:
             file_name = tk_fsave (title="Export to Geomview OOGL",
                                   initialdir=Common.config.initial_dir,
                                   defaultextension=".oogl",
                                   filetypes=[("Geomview files",
                                               "*.oogl"),
                                              ("All files", "*")])
        if len (file_name) != 0:
            Common.state.busy ()
            ex = vtk.vtkOOGLExporter ()
            self.lift ()
            ex.SetInput (self.renwin)
            ex.SetFileName (file_name)
            ex.Write ()
            Common.state.idle ()

    def save_rib (self, file_name="", bg=None):
        """Save scene to a RenderMan RIB file.  

        Keyword Arguments:

        file_name -- Optional file name to save to.  (default '').  If
        no file name is given then a dialog will pop up asking for the
        file name.

        bg -- Optional background option.  If 0 then no background is
        saved.  If non-None then a background is saved.  If left alone
        (defaults to None) it will result in a pop-up window asking
        for yes/no.
        """        
        debug ("In RenderWindow::save_rib ()")
        if not file_name:
            file_name = tk_fsave (title="Export to RIB", 
                                  initialdir=Common.config.initial_dir,
                                  defaultextension=".rib",
                                  filetypes=[("RIB files", "*.rib"), 
                                             ("All files", "*")])
        
        if len (file_name) != 0:
            if bg is None:
                msg = "Do you want the image shader to use a background?\n"\
                      "If you are using Pixar's Renderman, say no. "\
                      "Otherwise say yes and see if you get the desired "\
                      "results."
                bg = tkMessageBox.askyesno ("Background On?", message=msg)
            Common.state.busy ()
            f_pref = os.path.splitext (file_name)[0]
            ex = vtk.vtkRIBExporter ()
            ex.SetFilePrefix (f_pref)
            ex.SetTexturePrefix (f_pref + "_tex")
            self.lift ()
            
            # The vtkRIBExporter is broken in respect to VTK light
            # types.  Therefore we need to convert all lights into
            # scene lights before the save and later convert them
            # back.

            ########################################
            # Internal functions
            def x3to4(x):
                # convert 3-vector to 4-vector (w=1 -> point in space)
                return (x[0], x[1], x[2], 1.0 )
            def x4to3(x):
                # convert 4-vector to 3-vector
                return (x[0], x[1], x[2])
            def for_each_light(renderer, callback):
                # invoke callback(light) for all lights belonging to renderer
                lightcollection = renderer.GetLights()
                lightcollection.InitTraversal()
                for i in range(lightcollection.GetNumberOfItems()):
                    light = lightcollection.GetNextItem()
                    callback(light, i)

            def cameralight_transform(light, xform, light_type):
                # transform light by 4x4 matrix xform
                origin = x3to4( light.GetPosition() )
                focus = x3to4( light.GetFocalPoint() )
                neworigin = xform.MultiplyPoint(origin)
                newfocus = xform.MultiplyPoint(focus)
                light.SetPosition(x4to3(neworigin))
                light.SetFocalPoint(x4to3(newfocus))
                light.SetLightType(light_type)
            ########################################

            # Save setting of existing lights.
            light_cfg = []
            def save_light(light, light_cfg=light_cfg):
                light_cfg.append(light.GetLightType())
            for_each_light(self.ren, lambda l, i: save_light(l))

            # Convert lights to scene lights.
            cam = self.ren.GetActiveCamera()
            xform = vtk.vtkMatrix4x4()
            xform.DeepCopy(cam.GetCameraLightTransformMatrix())
            for_each_light(self.ren, lambda l, i: \
                           cameralight_transform(l, xform, 3))

            # Write the RIB file.
            ex.SetRenderWindow (self.renwin)
            if bg:
                ex.BackgroundOn ()
            else:
                ex.BackgroundOff ()
            ex.Write ()

            # Now re-convert lights to camera lights.
            xform.Invert()
            for_each_light(self.ren, lambda l, i: \
                           cameralight_transform(l, xform, light_cfg[i]) )

            # Change the camera position. Otherwise VTK would render
            # one broken frame after the export.
            cam.Roll(0.5)
            cam.Roll(-0.5)
            
            Common.state.idle ()

    def save_wavefront (self, file_name=""):        
        """Save scene to a Wavefront OBJ file.  Two files are
        generated.  One with a .obj extension and another with a .mtl
        extension which contains the material proerties.

        Keyword Arguments:

        file_name -- Optional file name to save to (default '').  If
        no file name is given then a dialog will pop up asking for the
        file name.
        """
        debug ("In RenderWindow::save_wavefront ()")
        if not file_name:
            file_name = tk_fsave (title="Export to Wavefront OBJ",
                                  initialdir=Common.config.initial_dir,
                                  defaultextension=".obj",
                                  filetypes=[("Wavefront OBJ files",
                                              "*.obj"),
                                             ("All files", "*")])
        if len (file_name) != 0:
            Common.state.busy ()
            ex = vtk.vtkOBJExporter ()
            self.lift ()
            ex.SetInput (self.renwin)
            f_pref = os.path.splitext (file_name)[0]
            ex.SetFilePrefix(f_pref)
            ex.Write ()
            Common.state.idle ()

    def save_gl2ps (self, file_name="", exp=None):        
        """Save scene to a vector PostScript/EPS/PDF/TeX file using
        GL2PS.  If you choose to use a TeX file then note that only
        the text output is saved to the file.  You will need to save
        the graphics separately.

        Keyword Arguments:

        file_name -- Optional file name to save to.  (default '').  If
        no file name is given then a dialog will pop up asking for the
        file name.

        exp -- Optionally configured vtkGL2PSExporter object.
        Defaults to None and this will result in a pop-up window
        asking for configuration options.        
        """
        debug ("In RenderWindow::save_gl2ps ()")
        # Make sure the exporter is available.
        if not hasattr(vtk, 'vtkGL2PSExporter'):
            msg = "Saving as a vector PS/EPS/PDF/TeX file using GL2PS is "\
                  "either not supported by your version of VTK or "\
                  "you have not configured VTK to work with GL2PS -- read "\
                  "the documentation for the vtkGL2PSExporter class."
            Common.print_err (msg)
            return

        # Get a filename
        if not file_name:
            file_name = tk_fsave (title="Export to PS/EPS/PDF/TeX", 
                                  initialdir=Common.config.initial_dir,
                                  defaultextension=".eps",
                                  filetypes=[("All files", "*"),
                                             ("EPS files", "*.eps"),
                                             ("PS files", "*.ps"),
                                             ("PDF files", "*.pdf"),
                                             ("TeX files", "*.tex")])
        
        if len(file_name) != 0:
            f_prefix, f_ext = os.path.splitext(file_name)
            ex = None
            if exp:
                ex = exp
                if not isinstance(exp, vtk.vtkGL2PSExporter):
                    msg = "Need a vtkGL2PSExporter you passed a "\
                          "%s"%exp.__class__.__name__
                ex.SetFilePrefix(f_prefix)
            else:
                ex = vtk.vtkGL2PSExporter()
                # defaults
                ex.SetFilePrefix(f_prefix)
                if f_ext == ".ps":
                    ex.SetFileFormatToPS()
                elif f_ext == ".tex":
                    ex.SetFileFormatToTeX()
                elif f_ext == ".pdf":
                    ex.SetFileFormatToPDF()
                else:
                    ex.SetFileFormatToEPS()
                ex.SetSortToBSP()
                # configure the exporter.
                c = vtkPipeline.ConfigVtkObj.ConfigVtkObj(self.renwin)
                c.configure(self.frame, ex, get=[], auto_update=1,
                            one_frame=1, run_command=0)
                self.frame.update()
                c.root.transient(self.frame)
                self.frame.wait_window(c.root)
            
            self.lift()
            ex.SetRenderWindow(self.renwin)
            Common.state.busy()
            ex.Write()
            Common.state.idle()        

    def quit (self, event=None): 
        debug ("In RenderWindow::quit ()")
        del self.pipe_objs
        del self.root
        del self.renwin
        self.tkwidget.destroy()
        self.frame.destroy ()

    def no_quit (self, event=None):
        debug ("In RenderWindow::no_quit ()")
        msg = "Sorry! You cannot delete this window without exiting "\
              "the application."
        tkMessageBox.showerror ("ERROR", msg)

    def lift (self): 
        "Lift the window to the top. Useful for scene dumps."
        debug ("In RenderWindow::lift ()")
        top = self.frame.winfo_toplevel ()
        top.deiconify ()
        top.lift ()
        self.frame.update_idletasks ()
        self.Render ()

    def Render (self): 
        debug ("In RenderWindow::Render ()")
        if self._do_render:
            self.renwin.Render ()

    def GetActiveCamera (self):
        debug ("In RenderWindow::GetActiveCamera ()")
        return self.camera

    def get_active_camera (self):
        debug ("In RenderWindow::get_active_camera ()")
        return self.camera

    def get_renderer (self): 
        debug ("In RenderWindow::get_renderer ()")
        return self.ren

    def get_render_window (self): 
        debug ("In RenderWindow::get_render_window ()")
        return self.renwin

    def get_vtk_render_window (self): 
        debug ("In RenderWindow::get_vtk_render_window ()")
        return self.renwin

    def get_light_manager (self): 
        debug ("In RenderWindow::get_light_manager ()")
        return self.light_mgr

    def set_background (self, clr=Common.config.bg_color): 
        debug ("In RenderWindow::set_background ()")
        self.ren.SetBackground (*clr)
        #self.Render ()

    def save_config (self, file): 
        "Save the current configuration to file."
        debug ("In RenderWindow::save_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.ren, self.camera):
            p.dump (obj, file)
        self.light_mgr.save_config(file)

    def load_config (self, file): 
        "Load the saved configuration from a file."
        debug ("In RenderWindow::load_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        for obj in (self.ren, self.camera):
            p.load (obj, file)
        self.light_mgr.load_config(file)

    def config_changed (self): 
        debug ("In RenderWindow::config_changed ()")
        self.set_background (Common.config.bg_color)

    def make_custom_gui (self):
        debug ("In RenderWindow::configure ()")
        self.make_pipeline_gui ()
        self.make_main_gui ()
        self.make_close_button ()
        
    def make_main_gui (self):
        debug ("In RenderWindow::make_main_gui ()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)
        but = Tkinter.Button (frame, text="Configure RenderWindow",
                              command=self.config_renwin)
        but.pack (side='top')
        but = Tkinter.Button (frame, text="Configure Renderer",
                              command=self.config_ren)
        but.pack (side='top')
        but = Tkinter.Button (frame, text="Configure Camera",
                              command=self.config_camera)
        but.pack (side='top')
        
    def config_renwin (self, event=None):
        debug ("In RenderWindow::config_renwin ()")
        c = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        c.configure (self.root, self.renwin)

    def config_ren (self, event=None):
        debug ("In RenderWindow::config_ren ()")
        c = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        c.configure (self.root, self.ren)

    def config_camera (self, event=None):
        debug ("In RenderWindow::config_camera ()")
        c = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        c.configure (self.root, self.camera)

    def config_lights (self, event=None):
        debug ("In RenderWindow::config_lights ()")
        self.light_mgr.config(event)
