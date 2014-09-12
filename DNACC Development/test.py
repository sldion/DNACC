import numpy as np
import matplotlib.pyplot as plt
import scipy as sci
import math as m
import time
from decimal import *
import DNACCFunctions as p

std = 0.2
phia = 0.5 + std*np.random.randn(64,64)

#phia = np.loadtxt("dots.txt")
#x, y, z = p.AlgoirithmSCFT2D(phia, 100, 10, 4, 0.5, alpha = 0.000001)

equlibriumDensity, y, z, flag, = p.AlgorithmDFTLike2D(phia, 0.9, 0.5, 4, 0.5, alpha = 1)

#print equlibriumDensity


equlibriumDensity2, y, z, flag, = p.AlgoirithmSCFT2D(phia, 0.9, 0.5, 4, 0.5, alpha = 1)

F1 = p.FreeEnergy(equlibriumDensity,  0.5)
F2 = p.FreeEnergy(equlibriumDensity2, 0.5)


print F1,F2
phianew = np.sum(np.sum(equlibriumDensity))/(64*64)
phibnew = np.sum(np.sum(1- equlibriumDensity))/(64*64)

print phianew, phibnew



fig1 = plt.figure(1)
phia_plt = plt.contourf(y, z, equlibriumDensity)
plt.contour(y,z,equlibriumDensity)
fig1.colorbar(phia_plt)

plt.show()
