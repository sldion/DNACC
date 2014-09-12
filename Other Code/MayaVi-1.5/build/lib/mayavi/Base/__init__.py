# This file makes this directory a Python package.
# Base

import sys, os, string

# print __path__
my_name = os.path.basename (__path__[0])

# hacks to allow local names and prevents unnecessary reloading of
# modules.

# First make Common accessible.
for mod_name in ('mayavi.Common', ):
    if sys.modules.has_key (mod_name):
        local = string.replace (mod_name, 'mayavi', 'mayavi.' + my_name)
        sys.modules[local] = sys.modules[mod_name]

# needed by the LutHandler
import Objects

# now import Misc.LutHandler since we need it here.
if sys.modules.has_key ('mayavi') and not \
   sys.modules.has_key ('mayavi.Misc.LutHandler'):
    import mayavi.Misc.LutHandler

# Make Misc names local.
for mod_name in ('mayavi.Misc.LutHandler', 'mayavi.Misc'):
    if sys.modules.has_key (mod_name):
        local = string.replace (mod_name, 'mayavi', 'mayavi.' + my_name)
        sys.modules[local] = sys.modules[mod_name]
