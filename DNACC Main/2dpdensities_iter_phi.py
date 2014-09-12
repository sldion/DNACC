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
from decimal import *

#------------------------------------------------------------
# Initialize the Variables
#------------------------------------------------------------
np.set_printoptions(precision = 4)
getcontext().prec = 7
t1 = time.clock()
fa = 0.5
alpha = 1
fb = 0.5
fc  = 1 - fb - fa

incompresibilityFactor 	= [10.0,100.0 ,1000.0]# Default 1850, 2050 [10 100 1000]
mixParameter 			= [0.01, 0.005, 0.0005] #[0.01 0.005 0.0005]

number_of_iterations 			= 100000 	# Default 30000
tolerence 						= 10**(-7) 	# the tolerence 
number_of_lattice_pointsX 		= 64      	# number of latice points for the j direction
number_of_lattice_pointsY       = 64

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
Vac = np.zeros((number_of_lattice_pointsX, number_of_lattice_pointsY))
Vbc = np.zeros((number_of_lattice_pointsX, number_of_lattice_pointsY))


A1 = 0.0 #4
A2 = 2.0#0.30

length = 6.0 #0.001

halfWidthHalfMinimum = 0.95 #0.45
gamma = halfWidthHalfMinimum/(m.sqrt(2.0*m.log(2.0)))

for j in range(0,number_of_lattice_pointsX):
    for i in range(0, number_of_lattice_pointsY):
		r = m.sqrt(xxs[j]**2 + yys[i]**2)
		if r <= length:
			Vab[j][i] = (A1+A2)*(m.cos(3.14*r/length))/2.0 + (A1 - A2)/2.0
			Vac[j][i] = (A1+A2)*(m.cos(3.14*r/length))/2.0 + (A1 - A2)/2.0
			Vbc[j][i] = (A1+A2)*(m.cos(3.14*r/length))/2.0 + (A1 - A2)/2.0
		else:
		    Vab[j][i] = -A2*(m.exp(-((r-length)**2.0)/(2.0*gamma**2.0)))
		    Vac[j][i] = -A2*(m.exp(-((r-length)**2.0)/(2.0*gamma**2.0)))
		    Vbc[j][i] = -A2*(m.exp(-((r-length)**2.0)/(2.0*gamma**2.0)))
	
Vac = np.roll(Vac, half_number_of_lattice_pointsX, axis = 0)
Vac = np.roll(Vac, half_number_of_lattice_pointsY, axis = 1)
Vab = np.roll(Vab, half_number_of_lattice_pointsX, axis = 0)
Vab = np.roll(Vab, half_number_of_lattice_pointsY, axis = 1)
Vbc = np.roll(Vbc, half_number_of_lattice_pointsX, axis = 0)
Vbc = np.roll(Vbc, half_number_of_lattice_pointsY, axis = 1)


Vkab = (np.fft.rfft2(Vab))/((float(number_of_lattice_pointsY)*float(number_of_lattice_pointsX)))
Vkac = (np.fft.rfft2(Vac))/((float(number_of_lattice_pointsY)*float(number_of_lattice_pointsX)))
Vkbc = (np.fft.rfft2(Vbc))/((float(number_of_lattice_pointsY)*float(number_of_lattice_pointsX)))

# Vkab = np.abs(Vkab)
# Vkac = np.abs(Vkac)
# Vkbc = np.abs(Vkbc)
#print Vkab

std = 0.15;
phia = fa  + std*np.random.randn(number_of_lattice_pointsX, number_of_lattice_pointsY)# np.random.random((number_of_lattice_pointsX, number_of_lattice_pointsY))#

phib = fb  +  std*np.random.randn(number_of_lattice_pointsX, number_of_lattice_pointsY)#np.random.random((number_of_lattice_pointsX, number_of_lattice_pointsY)) #

phic = 1 - phia - phib 

phia1 = phia
phib1 = phib
phic1 = phic

g = 0
for i in range(0,3):
    for j in range(0, number_of_iterations):
        
		iphia = np.fft.rfft2(phia)
		iphib = np.fft.rfft2(phib)
		iphic = np.fft.rfft2(phic)
		
		cnva  = iphia*Vkac
		cnvac = iphic*Vkac
		
		cnvb  = iphib*Vkab
		cnvba = iphia*Vkab
		
		cnvc  = iphic*Vkbc
		cnvcb = iphib*Vkbc

		icnva =  ysize*xsize*np.fft.irfft2(cnva)
		icnvb =  ysize*xsize*np.fft.irfft2(cnvb)
		icnvc =  ysize*xsize*np.fft.irfft2(cnvc)
		
		icnvba =  ysize*xsize*np.fft.irfft2(cnvba)
		icnvac =  ysize*xsize*np.fft.irfft2(cnvac)
		icnvcb =  ysize*xsize*np.fft.irfft2(cnvcb)
		
        #self conistent equations
		wa =  icnvac + icnvb - incompresibilityFactor[i]*(  1  - phia - phib - phic)
		wb =  icnvba + icnvc - incompresibilityFactor[i]*(  1  - phia - phib - phic)
		wc =  icnva  + icnvcb - incompresibilityFactor[i]*(  1  - phia - phib - phic)
		
		
		ewa = np.exp(-wa)
		
		ewb = np.exp(-wb)
		ewc = np.exp(-wc)
		QA = dx*dy*np.sum(ewa)
		if m.isnan(QA):
			flag = 1
			break
			
			
		QB = dx*dy*np.sum(np.sum(ewb))
		QC = dx*dy*np.sum(np.sum(ewc))
		
		
		phiatemp = fa*xsize*ysize*ewa/QA
		phibtemp = fb*xsize*ysize*ewb/QB
		phictemp = fc*xsize*ysize*ewc/QC
		
		phiaave = fa - dy*dx*np.sum(phiatemp)/(xsize*ysize)
		phibave = fb - dy*dx*np.sum(phibtemp)/(xsize*ysize)
		phicave = fc - dy*dx*np.sum(phictemp)/(xsize*ysize)
		
		phianew = phiatemp + phiaave
		phibnew = phibtemp + phibave
		phicnew = phictemp + phicave
		
		phia = mixParameter[i]*phianew + (1 - mixParameter[i])*phia
		phib = mixParameter[i]*phibnew + (1 - mixParameter[i])*phib
		phic = mixParameter[i]*phicnew + (1 - mixParameter[i])*phic
		
		dev = phianew - phia
		dev2 = dev * dev
		norm = np.sum(phianew * phianew)
		phidev = np.sum(dev2)/norm
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


fig2 = plt.figure(2)
phib_plt = plt.contourf(xxs,yys,phib)
plt.contour(xxs,yys,phib)
fig2.colorbar(phib_plt)

fig3 = plt.figure(3)
phic_plt = plt.contourf(xxs,yys, phic)
plt.contour(xxs,yys,phic)
fig3.colorbar(phic_plt)


fig4 = plt.figure(4)
Vac_plt = plt.contourf(xxs,yys, Vac)
fig4.colorbar(Vac_plt)

plt.show()
