

#------------------------------------------------------------
# This code is indending to address the asymetry of the solution
# with the colloids through the use of a psudo asymptotic preserving
# method. It now adds a large step when possible to speed up convergence
#
# 
# Author: Shawn Dion 
# Date: Feb 13, 2014
#
# 
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

t1              = time.clock()
volumeFractionA = 0.5
volumeFractionB = 1 - volumeFractionA
alphaA          = 0.000001
alphaB          = 1.0
perc            = 0.1          # Percent deviation for trying a big step.
smallmix        = 0.01
bigmix          = 0.1
mixParameter    = smallmix
incompresiblity = 100/alphaA        # Defines the stregnth of the global energy penalty 

number_of_iterations 			= 1000000	# Default 30000
tolerence 						= 10**(-4) 	# the tolerance 
number_of_lattice_pointsX 		= 32      	# number of lattice points for the j direction
number_of_lattice_pointsY       = 32

half_number_of_lattice_pointsX 	= number_of_lattice_pointsX/2 # the halfway point in the lattice
half_number_of_lattice_pointsY  = number_of_lattice_pointsY/2
xsize 							= 15.0    								#  
ysize                           = 15.0
dx 								= xsize/float(number_of_lattice_pointsX)
dy                              = ysize/float(number_of_lattice_pointsY)
xxs 							= [i*dx - xsize/2.0 for i in range(0,number_of_lattice_pointsX)]
yys                             = [i*dy - ysize/2.0 for i in range(0,number_of_lattice_pointsY)]

flag  = 0

PotentialAB = np.zeros((number_of_lattice_pointsX, number_of_lattice_pointsY))

print PotentialAB
# These variables are what define the form of the potential
A1 = 0.1#0.0195510 #4
A2 = 0.1

#0.0195510 #0.30
length =  2.0 #0.001
gamma = 0.5 #0.45



#Create the piecewise interaction potential
for j in range(0,number_of_lattice_pointsX):
    for i in range(0, number_of_lattice_pointsY):
        r = m.sqrt(yys[i]**2 + xxs[j]**2)

        if r <= length:
            PotentialAB[j][i] = ((A1+A2)*(m.cos(3.14*r/length))/2.0 + (A1 - A2)/2.0)

        else:
            PotentialAB[j][i] = (-A2*(m.exp(-((r-length)**2.0)/(2.0*(gamma**2.0)))))




# This importfunction moves the origin of the particles to line the origin of the potential axis
# to the computational axis shifts the center of the potential to one of the corners


PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsX, axis = 0)
PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsY, axis = 1)


# fig3 =plt.figure(3)
# plot3 =plt.contourf(xxs,yys,PotentialAB)
# fig3.colorbar(plot3)
# plt.show()


#fft the potential for later use
Vkab = np.fft.rfft2(PotentialAB)/((float(number_of_lattice_pointsY)*float(number_of_lattice_pointsX)))

#Randomize the density of particle A using a Gaussian distribution
std = 0.1;
phia = volumeFractionA + std*np.random.randn(number_of_lattice_pointsX, number_of_lattice_pointsY)

phib = 1 - phia

g = 0

divergence          = []
step                = []
percentDeviation    = []
count  = 0
devtot = 100.0*np.ones(5)         # Initialize some variables.

for j in xrange(number_of_iterations):

    iphia       = np.fft.rfft2(phia - volumeFractionA)
    iphib       = np.fft.rfft2(phib - volumeFractionB)

    lgaterm     = -(1/alphaA)*np.log(phia/volumeFractionA)
    lgbterm     = (1/alphaB)*np.log((phib)/volumeFractionB)

    cnvab       = iphia*Vkab
    cnvba       = iphib*Vkab

    convolution_Phia_PotentialAb =  ysize*xsize*np.fft.irfft2(cnvab)
    convolution_Phia_PotentialBa =  ysize*xsize*np.fft.irfft2(cnvba)

    kpterm      = incompresiblity*(volumeFractionA - (np.sum(phia)/(number_of_lattice_pointsY*number_of_lattice_pointsX)))
    kptermb     = incompresiblity*(volumeFractionB - (np.sum(phib)/(number_of_lattice_pointsY*number_of_lattice_pointsX)))
    
    #self consistent equations in reformulated form
    phianew     =  (lgaterm  + (2.0/(alphaA*alphaB))*convolution_Phia_PotentialAb + kpterm) - 100*(phia + phib - 1)
    phibnew     =  (lgbterm + (2.0/(alphaA*alphaB))*convolution_Phia_PotentialBa + kptermb) - 100*(phia + phib - 1)




    #print phianew
    #check if phianew has obtained any incorrect values
    if np.isnan(np.sum(phianew)):
        flag = 1
        break

    #picard mixing to increase the convergence
    dev         = phianew                                 #L2 norm deviation
    dev2        = np.sum(dev**2)
    norm        = np.sum(phia**2)
    devtot      = np.roll(devtot,1)     # Remember previous deviations.
    devtot[0]   = dev2/norm
    perdev      = np.sum(abs(devtot))/5.0
    perdev      = abs(100.0*(perdev - devtot[0])/perdev)   # % change in deviation.

    if (perdev < perc and count > 5):
        mixParameter = bigmix        # Try a big step
        count   = 0
        print "Big" 
    else: 
        mixParameter = smallmix      # Stick with small step.
        count   = count+1
    #print(g, devtot[0], perdev)   
    step.append(g)
    divergence.append(np.sum(dev * dev))
    g= g +1

    if abs(devtot[0]) < tolerence:
        break

    phia  = phia + alphaA*mixParameter*phianew
    
    phib = phib  + alphaB*mixParameter*phibnew

    # if statements to threshold the values of phi, so no number is less than zero, greater than one
    phia[phia >= 1.0]  = 0.99999999
    phia[phia <= 0.0]  = 1e-15
    
    phib[phib >= 1.0] = 0.999999999
    phib[phib <= 0.0] = 1e-15

#plot plot plot, we will plot

print phia
phib = 1.0 - phia

phianew = np.sum(np.sum(phia))/(number_of_lattice_pointsY*number_of_lattice_pointsX)
phibnew = np.sum(np.sum(phib))/(number_of_lattice_pointsY*number_of_lattice_pointsX)


print devtot[0], phianew, phibnew



fig1 = plt.figure(1)
phia_plt = plt.contourf(xxs, yys, phia)
plt.contour(xxs,yys,phia)
fig1.colorbar(phia_plt)

#print length(step), length()
fig2 = plt.figure(2)
thing = plt.plot(step, divergence)


fig3 = plt.figure(3)
phib_plt = plt.contourf(xxs, yys, phib)
plt.contour(xxs,yys,phib)
fig3.colorbar(phib_plt)
plt.show()

t2 = time.clock()


print t2 - t1
print g


if flag:
	print " Q was NaN"





