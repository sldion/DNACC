#!/usr/bin/env python

""" setup.py for building and installing MayaVi """

__author__ = "Prabhu Ramachandran <prabhu_r@users.sf.net>"
__version__ = "$Revision: 1.11 $"
__date__ = "$Date: 2005/08/25 10:32:10 $"
__credits__ = """Many thanks to Pearu Peterson <pearu@cens.ioc.ee> 
for helping with this setup.py and helping with packaging MayaVi."""

from __version__ import version
import glob, sys, os
import os.path
from distutils.core import setup
from distutils.command.install_data import install_data
from distutils.command.install_scripts import install_scripts

try:
    import py2exe
except ImportError:
    pass

# This class has been copied from scipy's setup.py and is useful to
# install the data files inside the project directory rather than some
# arbitrary place.
class my_install_data (install_data):
    def finalize_options (self):
        self.set_undefined_options ('install',
                                    ('install_lib', 'install_dir'),
                                    ('root', 'root'),
                                    ('force', 'force'),
                                    )


# This renames the mayavi script to a MayaVi.pyw script on win32.
class my_install_scripts (install_scripts):
    def run (self):
        install_scripts.run (self)
        if os.name != 'posix':
            # Rename <script> to <script>.pyw. Executable bits
            # are already set in install_scripts.run().
            for file in self.get_outputs ():
                if file[-4:] != '.pyw':
                    if file == 'mayavi':
                        new_file = file[:-6] + 'MayaVi.pyw'
                    else:
                        new_file = os.path.splitext(file)[0] + '.pyw'
                    self.announce("renaming %s to %s" % (file, new_file))
                    if not self.dry_run:
                        if os.path.exists(new_file):
                            os.remove (new_file)
                        os.rename (file, new_file)

# make docs if necessary.  This will most probably work only for Prabhu.
if 'sdist' in sys.argv:
    os.system ('cd doc/guide && make all')
    

setup (name              = "MayaVi",
       version           = version,
       description       = "The MayaVi Data Visualizer",
       author            = "Prabhu Ramachandran",
       author_email      = "prabhu_r@users.sf.net",
       license           = "BSD",
       long_description  = "A powerful scientific data visualizer for "\
                           "Python",
       keywords          = "scientific data visualization, VTK, graphics",
       url               = "http://mayavi.sourceforge.net",
       platforms         = ['Any'],

       cmdclass          = {'install_data': my_install_data,
                            'install_scripts': my_install_scripts},

       packages          = ['mayavi', 'mayavi.Base', 'mayavi.Filters',
                            'mayavi.Misc', 'mayavi.Modules',
                            'mayavi.Sources', 'mayavi.tools',
                            'vtkPipeline' ],
       package_dir       = {'mayavi': '.'},
       scripts           = ['mayavi', 'doc/vtk_doc.py'],
       data_files        = [('vtkPipeline/Icons',
                             glob.glob('vtkPipeline/Icons/*.gif'))]
       )
