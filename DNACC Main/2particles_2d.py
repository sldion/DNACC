
#------------------------------------------------------------
# This is essentially the same as the other DNACC code for 3 particles.
# This code is for 2 particles and it is using the arbitrary precision
# library mpmath
#------------------------------------------------------------

import numpy as np
import matplotlib.pyplot as plt
import scipy as sci
import math as m
from mpmath import *
import time
from decimal import *
from mpmath_utils import *

#------------------------------------------------------------
# Initialize the Variables
#------------------------------------------------------------

mp.dps = 350
getcontext().prec = 7
t1 = time.clock()
fa = 0.5
alpha = 0.0001
fb = 1 - fa

incompresibilityFactor 	= [100.0,1000.0 ,10000.0]# Default 1850, 2050 [10 100 1000]
mixParameter 			= [0.01, 0.005, 0.0005] #[0.01 0.005 0.0005]

number_of_iterations 			= 100000 	# Default 30000
tolerence 						= 10**(-7) 	# the tolerence 
number_of_lattice_pointsX 		= 16      	# number of latice points for the j direction
number_of_lattice_pointsY       = 16

half_number_of_lattice_pointsX 	= number_of_lattice_pointsX/2 # the halfway point in the lattice
half_number_of_lattice_pointsY  = number_of_lattice_pointsY/2
xsize 							= 15.0    								#  
ysize                           = 15.0
dx 								= xsize/float(number_of_lattice_pointsX)
dy                              = ysize/float(number_of_lattice_pointsY)
xxs 							= [i*dx - xsize/2.0 for i in range(0,number_of_lattice_pointsX)]
yys                             = [i*dy - ysize/2.0 for i in range(0,number_of_lattice_pointsY)]

flag  = 0

Vab = np.zeros((number_of_lattice_pointsX, number_of_lattice_pointsY))


A1 = 9000.0 #4
A2 = 2000.0 #0.30

length = 2 #0.001

halfWidthHalfMinimum = 0.65 #0.45
gamma = halfWidthHalfMinimum/(m.sqrt(2.0*m.log(2.0)))

for j in range(0,number_of_lattice_pointsX):
    for i in range(0, number_of_lattice_pointsY):
		r = m.sqrt(xxs[j]**2 + yys[i]**2)
		if r <= length:
			Vab[j][i] = (A1+A2)*(m.cos(3.14*r/length))/2.0 + (A1 - A2)/2.0

		else:
		    Vab[j][i] = -A2*(m.exp(-((r-length)**2.0)/(2.0*gamma**2.0)))

	
#A function needs to be placed here to move the origin of the potentials

Vab = np.roll(Vab, half_number_of_lattice_pointsX, axis = 0)
Vab = np.roll(Vab, half_number_of_lattice_pointsY, axis = 1)


Vkab = (np.fft.rfft2(Vab))/((float(number_of_lattice_pointsY)*float(number_of_lattice_pointsX)))


std = 0.15;
phia = fa  + std*np.random.randn(number_of_lattice_pointsX, number_of_lattice_pointsY)# np.random.random((number_of_lattice_pointsX, number_of_lattice_pointsY))#

phib = 1 - phia
phib1 = phib

g = 0
for i in range(0,3):
    for j in range(0, number_of_iterations):
        iphia = np.fft.rfft2(phia)
        iphib = np.fft.rfft2(phib)
        cnvb  = iphib*Vkab
        cnvba = iphia*Vkab


        icnvb =  ysize*xsize*np.fft.irfft2(cnvb)
        icnvba =  ysize*xsize*np.fft.irfft2(cnvba)
        #self conistent equations
        wa =  icnvb   - incompresibilityFactor[i]*(  1  - phia - phib)
        wb =  icnvba  - incompresibilityFactor[i]*(  1  - phia - phib)
        
        wa_mp = array2mp(-wa)

        wb_mp = array2mp(-alpha*wb)
        
        wa_mp_exp = apply2mparray(wa_mp,exp)
        wb_mp_exp = apply2mparray(wb_mp,exp)

        QA = np.sum(wa_mp_exp)
        if m.isnan(QA):
			flag = 1
			break
        
        
        QB = np.sum(wb_mp_exp)
        phiatemp = mparray2npfloat( fa*xsize*ysize*wa_mp_exp/QA)
        phibtemp = mparray2npfloat(fb*xsize*ysize*wb_mp_exp/QB)
        
        phiaave = fa - dy*dx*np.sum(phiatemp)/(xsize*ysize)
        phibave = fb - dy*dx*np.sum(phibtemp)/(xsize*ysize)
        
        phianew = phiatemp + phiaave
        phibnew = phibtemp + phibave
        phia = mixParameter[i]*phianew + (1 - mixParameter[i])*phia
        phib = mixParameter[i]*phibnew + (1 - mixParameter[i])*phib
        dev = phianew - phia
        dev2 = dev * dev
        norm = np.sum( np.sum(phianew * phianew))
        phidev = np.sum(np.sum(dev2))/norm
        g = g + 1
        if phidev < tolerence:
            break
			

t2 = time.clock()
print t2 - t1
print g

if flag:
	print " Q was NaN"

#plot plot plot
fig1 = plt.figure(1)
phia_plt = plt.contourf(xxs, yys, phia)
plt.contour(xxs,yys,phia)
fig1.colorbar(phia_plt)

fig5 = plt.figure(5)
phia_slice = plt.plot(xxs, phia[15][:])








plt.show()
