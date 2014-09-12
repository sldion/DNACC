# This file makes this directory into a Python package.

# Hacks to make local name lookups work.  Order is important and
# Common must be imported first.
import Common, Base.Objects

import Main

# This is a function that will return a MayaViTkGUI instance.
mayavi = Main.mayavi
MayaVi = mayavi
