"""This creates matlab like one liners that make it easy to visualize
data from the Python interpreter.

Right now this provides the following useful functions.

 1. surf(x, y, f) -- samples f along x, y and plots a surface.

 2. view(arr) -- Views array as structured points.

 3. viewi(arr) -- Views array as an image.

 4. sampler(xa, ya, func) -- Samples func along array of ordered
 points (xa, ya).

Author:
  Prabhu Ramachandran <prabhu_r@users.sf.net>

License:
  BSD --  http://www.opensource.org/licenses/bsd-license.html
"""

import mayavi
import vtk
import Numeric

try:
    from vtk.util import vtkConstants
except ImportError:
    class vtkConstants:
        pass
    vtkConstants.VTK_CHAR=2
    vtkConstants.VTK_UNSIGNED_CHAR = 3
    vtkConstants.VTK_SHORT           = 4
    vtkConstants.VTK_UNSIGNED_SHORT  = 5
    vtkConstants.VTK_INT             = 6
    vtkConstants.VTK_UNSIGNED_INT    = 7
    vtkConstants.VTK_LONG            = 8
    vtkConstants.VTK_UNSIGNED_LONG   = 9
    vtkConstants.VTK_FLOAT           =10
    vtkConstants.VTK_DOUBLE          =11

def array2vtk(z):    
    """Converts a Numeric Array to a VTK array object directly. The
    resulting array copies the data in the passed Numeric array.  The
    array can therefore be deleted safely.  This works for real arrays.

    XXX what should be done for complex arrays?
    """
    
    arr_vtk = {'c':vtkConstants.VTK_UNSIGNED_CHAR,
               'b':vtkConstants.VTK_UNSIGNED_CHAR,
               '1':vtkConstants.VTK_CHAR,
               's':vtkConstants.VTK_SHORT,
               'i':vtkConstants.VTK_INT,
               'l':vtkConstants.VTK_LONG,
               'f':vtkConstants.VTK_FLOAT,
               'd':vtkConstants.VTK_DOUBLE,
               'F':vtkConstants.VTK_FLOAT,
               'D':vtkConstants.VTK_DOUBLE }

    # A dummy array used to create others.
    f = vtk.vtkFloatArray()
    # First create an array of the right type by using the typecode.
    tmp = f.CreateDataArray(arr_vtk[z.typecode()])
    tmp.SetReferenceCount(2) # Prevents memory leak.
    zf = Numeric.ravel(z)
    tmp.SetNumberOfTuples(len(zf))
    tmp.SetNumberOfComponents(1)
    tmp.SetVoidArray(zf, len(zf), 1)

    # Now create a new array that is a DeepCopy of tmp.  This is
    # required because tmp does not copy the data from the NumPy array
    # and will point to garbage if the NumPy array is deleted.
    arr = f.CreateDataArray(arr_vtk[z.typecode()])
    arr.SetReferenceCount(2) # Prevents memory leak.
    arr.DeepCopy(tmp)

    return arr


def _create_structured_points_pyvtk(x, y, z):
    
    """Creates a vtkStructuredPoints object given input data in the
    form of arrays.  This uses pyvtk to do the job and generates a
    temporary file in the process.

    Input Arguments:
       x -- Array of x-coordinates.  These should be regularly spaced.

       y -- Array of y-coordinates.  These should be regularly spaced.

       z -- Array of z values for the x, y values given.  The values
       should be computed such that the z values are computed as x
       varies fastest and y next.

    """

    import pyvtk
    import tempfile, os
    
    nx = len(x)
    ny = len(y)
    nz = len(z)
    assert nx*ny == nz, "len(x)*len(y) != len(z).  "\
           "You passed nx=%d, ny=%d,  nz=%d"%(nx, ny, nz)

    xmin, ymin = x[0], y[0]
    dx, dy= (x[1] - x[0]), (y[1] - y[0])

    # create a vtk data file
    sp = pyvtk.StructuredPoints ((nx, ny, 1), (xmin, ymin, 0), (dx, dy, 1))
    pd = pyvtk.PointData(pyvtk.Scalars(z, name='Scalars',
                                       lookup_table="default"))
    d = pyvtk.VtkData(sp, pd, "Surf data")
    file_name = tempfile.mktemp(suffix='.vtk')
    d.tofile(file_name, format='ascii')

    # read the created file - yes this is circuitous but works for now.
    reader = vtk.vtkStructuredPointsReader()
    reader.SetFileName(file_name)
    reader.Update()
    # cleanup.
    os.remove(file_name)
    return reader.GetOutput()


def _create_structured_points_direct(x, y, z=None):
    """Creates a vtkStructuredPoints object given input data in the
    form of Numeric arrays.

    Input Arguments:
       x -- Array of x-coordinates.  These should be regularly spaced.

       y -- Array of y-coordinates.  These should be regularly spaced.

       z -- Array of z values for the x, y values given.  The values
       should be computed such that the z values are computed as x
       varies fastest and y next.  If z is None then no scalars are
       associated with the structured points.  Only the structured
       points data set is created.
    """

    nx = len(x)
    ny = len(y)
    if z:
        nz = Numeric.size(z)
        assert nx*ny == nz, "len(x)*len(y) != len(z)"\
               "You passed nx=%d, ny=%d,  nz=%d"%(nx, ny, nz)

    xmin, ymin = x[0], y[0]
    dx, dy= (x[1] - x[0]), (y[1] - y[0])

    sp = vtk.vtkStructuredPoints()
    sp.SetDimensions(nx, ny, 1)
    sp.SetOrigin(xmin, ymin, 0)
    sp.SetSpacing(dx, dy, 1)
    if z:
        sc = array2vtk(z)
        sp.GetPointData().SetScalars(sc)
    return sp


def sampler(xa, ya, func,f_args=(),f_keyw=None):
    """Samples a function at an array of ordered points (with equal
    spacing) and returns an array of scalars as per VTK's requirements
    for a structured points data set, i.e. x varying fastest and y
    varying next.
    
    Input Arguments:
        xa -- Array of x points.

        ya -- Array if y points.

        func -- function of x, and y to sample.

        f_args -- a tuple of additional positional arguments for func()
        (default is empty)

        f_keyw -- a dict of additional keyword arguments for func()
        (default is empty)
    """
    if f_keyw is None:
        f_keyw = {}
    ret = func(xa[:,Numeric.NewAxis] +
               Numeric.zeros(len(ya), ya.typecode()),
               Numeric.transpose(ya[:,Numeric.NewAxis] +
               Numeric.zeros(len(xa), xa.typecode()) ),
               *f_args, **f_keyw
               )
    return Numeric.transpose(ret)


def _check_sanity(x, y, z):
    """Checks the given arrays to see if they are suitable for
    surf."""
    msg = "Only ravelled or 2D arrays can be viewed! "\
          "This array has shape %s" % str(z.shape)
    assert len(z.shape) <= 2, msg
    
    if len( z.shape ) == 2:
        msg = "len(x)*len(y) != len(z.flat).  You passed "\
              "nx=%d, ny=%d, shape of z=%s"%(len(x), len(y), z.shape)
        assert z.shape[0]*z.shape[1] == len(x)*len(y), msg

        msg = "length of y(%d) and x(%d) must match shape of z "\
              "%s. (Maybe you need to swap x and y?)"%(len(y), len(x),
                                                        str(z.shape))
        assert z.shape == (len(y), len(x)), msg 


def squeeze(a):
    "Returns a with any ones from the shape of a removed"
    a = Numeric.asarray(a)
    b = Numeric.asarray(a.shape)
    val = Numeric.reshape(a,
                          tuple(Numeric.compress(Numeric.not_equal(b, 1), b)))
    return val


def surf(x, y, z, warp=1, scale=[1.0, 1.0, 1.0], viewer=None,
         f_args=(), f_keyw=None):
    """Creates a surface given regularly spaced values of x, y and the
    corresponding z as arrays.  Also works if z is a function.
    Currently works only for regular data - can be enhanced later.

    Input Arguments:
        x -- Array of x points (regularly spaced)

        y -- Array if y points (regularly spaced)

        z -- A 2D array for the x and y points with x varying fastest
        and y next.  Also will work if z is a callable which supports
        x and y arrays as the arguments.

        warp -- If true, warp the data to show a 3D surface
        (default = 1).        

        scale -- Scale the x, y and z axis as per passed values.
        Defaults to [1.0, 1.0, 1.0].

        viewer -- An optional viewer (defaults to None).  If provided
        it will use this viewer instead of creating a new MayaVi
        window each time.

        f_args -- a tuple of additional positional arguments for func()
        (default is empty)

        f_keyw -- a dict of additional keyword arguments for func()
        (default is empty)
    """

    if f_keyw is None:
        f_keyw = {}

    if callable(z):
        zval = Numeric.ravel(sampler(x, y, z, f_args=f_args, f_keyw=f_keyw))
        x, y = squeeze(x), squeeze(y)
    else:
        x, y = squeeze(x), squeeze(y)
        _check_sanity(x, y, z)
        zval = Numeric.ravel(z)
        assert len(zval) > 0, "z is empty - nothing to plot!"

    xs = x*scale[0]
    ys = y*scale[1]
    data = _create_structured_points_direct(xs, ys, zval)
    # do the mayavi stuff.
    if not viewer:
        v = mayavi.mayavi()
    else:
        v = viewer
    v.open_vtk_data(data)
    if warp:
        f = v.load_filter('WarpScalar', 0)
        f.fil.SetScaleFactor(scale[2])
        n = v.load_filter('PolyDataNormals', 0)
        n.fil.SetFeatureAngle(45)
    m = v.load_module('SurfaceMap', 0)
    if not viewer:
        a = v.load_module('Axes', 0)
        a.axes.SetCornerOffset(0.0)
        if (min(scale) != max(scale)) or (scale[0] != 1.0):
            a.axes.UseRangesOn()
            a.axes.SetRanges(x[0], x[-1], y[0], y[-1], min(zval), max(zval))
        o = v.load_module('Outline', 0)
    v.Render()
    return v


def view(arr, smooth=0, warp=0, scale=[1.0, 1.0, 1.0]):

    """Allows one to view a 2D Numeric array.  Note that the view will
    be set to the way we normally think of matrices with with 0, 0 at
    the top left of the screen.

    Input Arguments:
       arr -- Array to be viewed.
       
       smooth -- If true, view the array as VTK point data i.e. the
       matrix entries will be treated as scalar data at the integral
       values along the axes and between these points the colours will
       be interpolated providing a smooth appearance for the data.  If
       set to false the data is viewed as cells with no interpolation
       and each cell of the matrix is viewed in a separate color with
       no interpolation.  Note that if smooth is set to true you will
       be able to do more fancy things with the visualization (like
       contouring the data, warping it to get a 3d surface etc.) than
       when smooth is off.  If warp is set to true then this option is
       set to true.  (default=false)

       warp -- If true, warp the data to show a 3D surface (default =
       0).  If set the smooth option has no effect.  Note that this is
       an expensive operation so use it sparingly for large arrays.

       scale -- Scale the x, y and z axis as per passed values.
       Defaults to [1.0, 1.0, 1.0].
    """

    assert len(arr.shape) == 2, "Only 2D arrays can be viewed!"
    ny, nx = arr.shape
    if warp:
        smooth=1
    if not smooth:
        nx += 1
        ny += 1

    dx, dy, junk = Numeric.array(scale)*1.0
    xa = Numeric.arange(0, nx*scale[0] - 0.1*dx, dx, 'f')
    ya = Numeric.arange(0, ny*scale[1] - 0.1*dy, dy, 'f')
    
    if smooth:
        data = _create_structured_points_direct(xa, ya, arr)
    else:
        data = _create_structured_points_direct(xa, ya)
        sc = array2vtk(arr)
        data.GetCellData().SetScalars(sc)
    
    # do the mayavi stuff.
    v = mayavi.mayavi()
    v.open_vtk_data(data)
    if warp:
        f = v.load_filter('WarpScalar', 0)
        f.fil.SetScaleFactor(scale[2])
        n = v.load_filter('PolyDataNormals', 0)
        n.fil.SetFeatureAngle(45)
    m = v.load_module('SurfaceMap', 0)
    a = v.load_module('Axes', 0)
    a.axes.SetCornerOffset(0.0)
    a.axes.YAxisVisibilityOff()
    a.axes.UseRangesOn()
    arr_flat = Numeric.ravel(arr)
    a.axes.SetRanges(0, nx, 0, ny, min(arr_flat), max(arr_flat))
    o = v.load_module('Outline', 0)
    v.renwin.update_view(0, 0, -1, 0, -1, 0)
    v.Render()
    return v


def viewi(arr, smooth=0, lut='br', scale=[1.0, 1.0, 1.0]):
    
    """Allows one to view a 2D Numeric array as an image.  This works
    best for very large arrays (like 1024x1024 arrays).  The
    implementation of this function is a bit of a hack and many of
    MayaVi's features cannot be used.  For instance you cannot change
    the lookup table color and expect the color of the image to
    change.

    Note that the view will be set to the way we normally think of
    matrices with with 0, 0 at the top left of the screen.

    Input Arguments:
       arr -- Array to be viewed.
       
       smooth -- If true, perform interpolation on the image.  If
       false do not perform interpolation.  (default=0)

       lut -- Specifies the lookuptable to map the data with.  This
       should be on of ['br', 'rb', 'bw', 'wb'] 'br' refers to
       blue-to-red, 'rb' to red-to-blue, 'bw' to black-to-white and
       'wb' to white-black.  (default='br')

       scale -- Scale the x, y and z axis as per passed values.
       Defaults to [1.0, 1.0, 1.0].
    """

    valid_lut = {'br': 1, 'rb':2, 'bw':3, 'wb':4}
    
    assert len(arr.shape) == 2, "Only 2D arrays can be viewed!"
    assert lut in valid_lut.keys(), \
           "lut must be one of %s!"%(valid_lut.keys())
    
    ny, nx = arr.shape
    dx, dy, junk = Numeric.array(scale)*1.0
    xa = Numeric.arange(0, nx*scale[0] - 0.1*dx, dx, 'f')
    ya = Numeric.arange(0, ny*scale[1] - 0.1*dy, dy, 'f')

    arr_flat = Numeric.ravel(arr)
    min_val = min(arr_flat)
    max_val = max(arr_flat)
    
    sp = _create_structured_points_direct(xa, ya)
    v = mayavi.mayavi()
    v.open_vtk_data(sp)

    mm = v.get_current_dvm().get_current_module_mgr()
    luth = mm.get_scalar_lut_handler()
    
    luth.lut_var.set(valid_lut[lut])
    luth.change_lut()

    l = luth.get_lut()
    l.SetRange(min_val, max_val)
    za = array2vtk(arr_flat)
    a = l.MapScalars(za, 0, 0)
    sp.GetPointData().SetScalars(a)
    sp.SetScalarTypeToUnsignedChar()
    sp.SetNumberOfScalarComponents(4)
    
    luth.legend_on.set(1)
    luth.legend_on_off()    
    luth.set_data_range([min_val, max_val])
    luth.range_on_var.set(1)
    luth.set_range_on()
    
    ia = vtk.vtkImageActor()
    if smooth:
        ia.InterpolateOn()
    else:
        ia.InterpolateOff()        
    ia.SetInput(sp)

    v.renwin.add_actors(ia)

    a = v.load_module('Axes', 0)
    a.axes.SetCornerOffset(0.0)
    a.axes.YAxisVisibilityOff()
    a.axes.UseRangesOn()
    a.axes.SetRanges(0, nx, 0, ny, min_val, max_val)
    o = v.load_module('Outline', 0)
    v.renwin.update_view(0, 0, -1, 0, -1, 0)
    t = v.renwin.tkwidget
    t.UpdateRenderer(0,0)
    t.Pan(0,-25)
    v.Render()
    return v



def main():
    
    """ A simple example.  Note that the Tkinter lines are there only
    because this code will be run standalone.  On the interpreter,
    simply invoking surf and view would do the job."""
    
    import Tkinter
    r = Tkinter.Tk()
    r.withdraw()

    def f(x, y):
        return Numeric.sin(x*y)/(x*y)

    x = Numeric.arange(-7., 7.05, 0.1)
    y = Numeric.arange(-5., 5.05, 0.05)
    v = surf(x, y, f)

    import RandomArray
    z = RandomArray.random((50, 25))
    v1 = view(z)
    v2 = view(z, warp=1)
    z_large = RandomArray.random((1024, 512))
    v3 = viewi(z_large)

    # A hack for stopping Python when all windows are closed.
    v.master = r 
    v1.master = r
    v2.master = r
    #v3.master = r
    
    r.mainloop()
    

if __name__ == "__main__":
    main()
