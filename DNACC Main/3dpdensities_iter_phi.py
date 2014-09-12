#------------------------------------------------------------
# Name: 2dpdensities_iter_phi.py
#
# Description: This code generates potentials for interactions between different species and solves a 
#              set of self consitent equations for 3 particles. Then the results are plotted and the free
#               is calculated 
#------------------------------------------------------------




import numpy as np
import matplotlib.pyplot as plt
import scipy as sci
import math as m
import time
from mpl_toolkits.mplot3d import Axes3D
from mayavi import mlab

##------------------------------------------------------------
# Name: createIsosurface
#
# Description:  Takes in a function and creates an isosurface of the function based on the value
#               threshold and returns the x y coordinates and function's isosurface that can be plotted
#               using numpys surface plot function.
#------------------------------------------------------------
def createIsosurface(Xcoordinates, Ycoordinates, function, threshold):
    
    X, Y = np.meshgrid(Xcoordinates, Ycoordinates)
    


    return (X,Y,Z)

#------------------------------------------------------------
# Initialize the Variables
#------------------------------------------------------------
t1 = time.clock()
fa = 0.333
alpha = 1
fb = 0.333
fc  = 1 - fb - fa

incompresibilityFactor 	= [10,100 ,1000]# Default 1850, 2050 [10 100 1000]
mixParameter 			= [0.01, 0.005, 0.0005] #[0.01 0.005 0.0005]

number_of_iterations 			= 100000 	# Default 30000
tolerence 						= 10**(-7) 	# the tolerence 
number_of_lattice_pointsX 		= 32       	# number of latice points for the j direction
number_of_lattice_pointsY       = 32
number_of_lattice_pointsZ       = 32
half_number_of_lattice_pointsX 	= number_of_lattice_pointsX/2 # the halfway point in the lattice
half_number_of_lattice_pointsY  = number_of_lattice_pointsY/2
half_number_of_lattice_pointsZ  = number_of_lattice_pointsZ/2
xsize 							= 4.0    								#  
ysize                           = 4.0
zsize                           = 4.0
dx 								= xsize/number_of_lattice_pointsX
dy                              = ysize/number_of_lattice_pointsY
dz                              = zsize/number_of_lattice_pointsZ
xxs 							= [i*dx - xsize/2.0 for i in range(0,number_of_lattice_pointsX)]
yys                             = [i*dy - ysize/2.0 for i in range(0,number_of_lattice_pointsY)]
zzs                             = [i*dz - zsize/2.0 for i in range(0,number_of_lattice_pointsZ)]

Vab = np.zeros((number_of_lattice_pointsX, number_of_lattice_pointsY, number_of_lattice_pointsZ))
Vac = np.zeros((number_of_lattice_pointsX, number_of_lattice_pointsY, number_of_lattice_pointsZ))
Vbc = np.zeros((number_of_lattice_pointsX, number_of_lattice_pointsY, number_of_lattice_pointsZ))


A1 = 5.0 #4
A2 = 1.0 #0.30
length = 2.0#0.001

halfWidthHalfMinimum = 0.65 #0.45
gamma = halfWidthHalfMinimum/(m.sqrt(2*m.log(2)))

for j in range(0,number_of_lattice_pointsX):
    for i in range(0, number_of_lattice_pointsY):
        for k in range(0, number_of_lattice_pointsZ):
            r = m.sqrt(xxs[j]**2 + yys[i]**2 + zzs[k]**2)
            if r <= length:
                Vab[j][i][k] = (A1+A2)*(m.cos(sci.pi*r/length))/2.0 + (A1 - A2)/2.0
                Vac[j][i][k] = (A1+A2)*(m.cos(sci.pi*r/length))/2.0 + (A1 - A2)/2.0
                Vbc[j][i][k] = (A1+A2)*(m.cos(sci.pi*r/length))/2.0 + (A1 - A2)/2.0
            else:
                Vab[j][i][k] = -A2*(m.exp(-(r-length)**2.0/(2.0*gamma**2.0)))
                Vac[j][i][k] = -A2*(m.exp(-(r-length)**2.0/(2.0*gamma**2.0)))
                Vbc[j][i][k] = -A2*(m.exp(-(r-length)**2.0/(2.0*gamma**2.0)))


Vac = np.roll(Vac, half_number_of_lattice_pointsX, axis = 0)
Vac = np.roll(Vac, half_number_of_lattice_pointsY, axis = 1)
Vab = np.roll(Vab, half_number_of_lattice_pointsX, axis = 0)
Vab = np.roll(Vab, half_number_of_lattice_pointsY, axis = 1)
Vbc = np.roll(Vbc, half_number_of_lattice_pointsX, axis = 0)
Vbc = np.roll(Vbc, half_number_of_lattice_pointsY, axis = 1)

Vkab = (np.fft.rfftn(Vab))/((float(number_of_lattice_pointsY)*float(number_of_lattice_pointsX)*float(number_of_lattice_pointsZ)))
Vkac = (np.fft.rfftn(Vac))/((float(number_of_lattice_pointsY)*float(number_of_lattice_pointsX)*float(number_of_lattice_pointsZ)))
Vkbc = (np.fft.rfftn(Vbc))/((float(number_of_lattice_pointsY)*float(number_of_lattice_pointsX)*float(number_of_lattice_pointsZ)))


std = 0.15;
phia = fa + std*np.random.randn(number_of_lattice_pointsX, number_of_lattice_pointsY, number_of_lattice_pointsZ)

phib = fb + std*np.random.randn(number_of_lattice_pointsX, number_of_lattice_pointsY, number_of_lattice_pointsZ)

phic = 1 - phia - phib

phia1 = phia
phib1 = phib
phic1 = phic

g = 0
for i in range(0,3):
    for j in range(0, number_of_iterations):
        iphia = np.fft.rfftn(phia)
        iphib = np.fft.rfftn(phib)
        iphic = np.fft.rfftn(phic)

        cnva  = iphia*Vkac
        cnvac = iphic*Vkac

        cnvb  = iphib*Vkab
        cnvba = iphia*Vkab

        cnvc  = iphic*Vkbc
        cnvcb = iphib*Vkbc

        icnva =  zsize*ysize*xsize*np.fft.irfftn(cnva)
        icnvb =  zsize*ysize*xsize*np.fft.irfftn(cnvb)
        icnvc =  zsize*ysize*xsize*np.fft.irfftn(cnvc)

        icnvba =  zsize*ysize*xsize*np.fft.irfftn(cnvba)
        icnvac =  zsize*ysize*xsize*np.fft.irfftn(cnvac)
        icnvcb =  zsize*ysize*xsize*np.fft.irfftn(cnvcb)

        #self conistent equations
        wa =  icnvac + icnvb - incompresibilityFactor[i]*(  1  - phia - phib - phic)
        wb =  icnvba + icnvc - incompresibilityFactor[i]*(  1  - phia - phib - phic)
        wc =  icnvcb + icnva - incompresibilityFactor[i]*(  1  - phia - phib - phic)

        ewa = np.exp(-wa)
        ewb = np.exp(-wb)
        ewc = np.exp(-wc)

        QA = dx*dy*dz*np.sum(np.sum(np.sum(ewa)))

        if m.isnan(QA):
            print "this is bad"

        QB = dx*dy*dz*np.sum(np.sum(np.sum(ewb)))
        QC = dx*dy*dz*np.sum(np.sum(np.sum(ewc)))

        phiatemp = fa*zsize*xsize*ysize*ewa/QA
        phibtemp = fb*zsize*xsize*ysize*ewb/QB
        phictemp = fc*zsize*xsize*ysize*ewc/QC

        phiaave = fa - dy*dx*dz*np.sum(np.sum(np.sum(phiatemp)))/(xsize*ysize*zsize)
        phibave = fb - dy*dx*dz*np.sum(np.sum(np.sum(phibtemp)))/(xsize*ysize*zsize)
        phicave = fc - dy*dx*dz*np.sum(np.sum(np.sum(phictemp)))/(xsize*ysize*zsize)

        phianew = phiatemp + phiaave
        phibnew = phibtemp + phibave
        phicnew = phictemp + phicave

        phia = mixParameter[i]*phianew + (1 - mixParameter[i])*phia
        phib = mixParameter[i]*phibnew + (1 - mixParameter[i])*phib
        phic = mixParameter[i]*phicnew + (1 - mixParameter[i])*phic

        dev = phianew - phia
        dev2 = dev * dev
        norm =np.sum(np.sum(np.sum(phianew * phianew)))
        phidev = np.sum(np.sum(np.sum(dev2)))/norm
        g = g + 1

        if phidev < tolerence:
            break

print g
t2 = time.clock()
print t2 - t1

x , y ,z = np.mgrid[-2:dx:2j, -2:dx:2j ,-2:dx:2j]

s = mlab.contour3d( phia)
mlab.show()
a = mlab.contour3d(phib)
mlab.show()
b = mlab.contour3d(phic)
mlab.show()

#plot plot plot
#Axes3D.plot_surface()
