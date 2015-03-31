import numpy as np
import matplotlib.pyplot as plt  
import ThreeParticleSCFT3D as p
import mayavi.mlab as mlab

volumeFraction = [0.18,0.18]

phia = volumeFraction[0] + 0.1*np.random.randn(32,32,32)
phib = volumeFraction[1] + 0.1*np.random.randn(32,32,32)



#phia = volumeFractionA + std*
x ,x2 ,y, z , l, flag = p.Particles3SCFT(phia, phib, 3.50, 0.3 ,1.20,0.65,volumeFraction,AlphaA = 1,AlphaB = 1 )
x3 = 1 - x - x2
print flag
#print x
#print x2
fig1 = plt.figure(1)
thing = plt.contourf(y,z,x[16][:][:])
fig1.colorbar(thing)


fig2 = plt.figure(2)
thing2 = plt.contourf(y,z,x2[16][:][:])
fig2.colorbar(thing2)


fig3 = plt.figure(3)
thing3 = plt.contourf(y,z,x3[16][:][:])
fig3.colorbar(thing3)


plt.show()
print x + x2 + x3
print x[8][:][:]
print x2[8][:][:]
print x3[8][:][:]

mlab.contour3d(x3, contours =  [0.5])
#mlab.show()

#mlab.contour3d(x2, contours = [0.33]) #[0.1,0.33, 0.7, 0.9])
#mlab.show()
#mlab.contour3d(x, contours = [0.5])#[0.1,0.33, 0.7, 0.9])

mlab.show()
