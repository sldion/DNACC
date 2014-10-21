import numpy as np 
import matplotlib.pyplot as plt  
import ThreeParticleSCFT3D as p
import mayavi.mlab as mlab

volumeFraction = [0.33,0.33]

phia = volumeFraction[0] + 0.1*np.random.randn(64,64,64)
phib = volumeFraction[1] + 0.1*np.random.randn(64,64,64)

#phia = volumeFractionA + std*
x ,x2 ,y, z , l, flag = p.Particles3SCFT(phia, phib,1.6,0.7 ,1,0.5,volumeFraction)
x3 = 1 - x - x2

mlab.contour3d(x2, contours = [0.5])
#print x
mlab.show()


