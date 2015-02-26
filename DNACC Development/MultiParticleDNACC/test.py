import MultiDNACCFunctions as MF
import numpy as np
#import matplotlib.pyplot as plt

volumeFraction = [0.33,0.33,0.33]
Alphas         = [1,1,1]
phia = volumeFraction[0] + 0.1*np.random.randn(32,32,32)
phib = volumeFraction[1] + 0.1*np.random.randn(32,32,32)
phic = 1 - phia - phib
initialDensities = [phia, phib, phic]
xsize = 6
xxs = [i*(xsize/32.0) - xsize/2.0 for i in range(0,32)]

segments =[xxs,xxs,xxs]

x = MF.createPotential3D(0.0, 0.0, 1.5,0.65, segments = segments )
Potentials = [x,x,x]



MF.solveSystemSCFT3D(initialDensities,Potentials,volumeFraction, Alphas)
