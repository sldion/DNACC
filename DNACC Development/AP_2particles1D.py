
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
alphaA          = 1.0
alphaB          = 1.0
perc            = 0.01          # Percent deviation for trying a big step.
smallmix        = 0.001
bigmix          = 0.1
mixParameter    = smallmix

#[0.01 0.005 0.0005]

number_of_iterations 			= 50000 	# Default 30000
tolerence 						= 10**(-4) 	# the tolerance 
number_of_lattice_pointsX 		= 256      	# number of lattice points for the j direction
half_number_of_lattice_pointsX 	= number_of_lattice_pointsX/2 # the halfway point in the lattice
xsize 							= 20.0    								#  
dx 								= xsize/float(number_of_lattice_pointsX)
xxs 							= [i*dx - xsize/2.0 for i in range(0,number_of_lattice_pointsX)]


flag  = 0

PotentialAB = np.zeros((number_of_lattice_pointsX))

# These variables are what define the form of the potential
A1 = 100.0 #4
A2 = 0.0 #0.30
length = 2.0 #0.001
halfWidthHalfMinimum = 0.50 #0.45
gamma = 0.5#halfWidthHalfMinimum/(m.sqrt(2.0*m.log(2.0)))



#Create the interaction potential
for j in range(0,number_of_lattice_pointsX):
    r = m.sqrt(xxs[j]**2)
    if r <= length:
        PotentialAB[j] = (A1+A2)*(m.cos(3.14*r/length))/2.0 + (A1 - A2)/2.0
    else:
        PotentialAB[j] = -A2*(m.exp(-((r-length)**2.0)/(2.0*gamma**2.0)))

	
# This function moves the origin of the particles to line the origin of the potential axis
# to the computational axis shifts the center of the potential to one of the corners


PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsX, axis = 0)



#fft the potential for later use
Vkab = (np.fft.rfft(PotentialAB))/(float(number_of_lattice_pointsX))

#Randomize the density of particle A using a Gaussian distribution
std = 0.15;
phia = volumeFractionA  + std*np.random.randn(number_of_lattice_pointsX)

print phia

g = 0

divergence = []
step = []
percentDeviation = []

count  = 0
devtot = 100.0*np.ones(5)         # Initialize some variables.

for j in xrange(number_of_iterations):
    iphia       = np.fft.rfft(phia - volumeFractionA)
    lgaterm     = -(1/alphaA)*np.log(phia/volumeFractionA)
    lgbterm     = (1/alphaB)*np.log((1.0 - phia)/volumeFractionB)
    cnvab       = iphia*Vkab
    convolution_Phia_PotentialAb =  xsize*np.fft.irfft(cnvab)
    kpterm      = 10000*(volumeFractionA - (np.sum(phia)/(number_of_lattice_pointsX)))
    
    # if statements to threshold the values of phi, so no number is less than zero, greater than one
    phia[phia <= 0.0]   = 0.00000001
    phia[phia >= 1.0]  = 0.99999999

    #self consistent equations in reformulated form
    phianew     =  phia + lgaterm   + (2.0/(alphaA*alphaB))*convolution_Phia_PotentialAb + lgbterm + kpterm
    
    phianew[phianew <= 0.0]   = 0.00000001
    phianew[phianew >= 1.0]   = 0.99999999

    #check if phianew has obtained any incorrect values
    if np.isnan(np.sum(phianew)):
        flag = 1
        break

    #picard mixing to increase the convergence

    dev         = phianew - phia                                        #L2 norm deviation
    phia        = mixParameter*phianew + (1 - mixParameter)*phia
    
    # new mixing algorithm that combines the big mixing step with a small mixing step
 # Iteration output.
    dev2        = np.sum(dev**2)
    norm        = np.sum(phianew**2)
    phidev      = np.sum(dev2)/norm
    devtot      = np.roll(devtot,1)     # Remember previous deviations.
    devtot[0]   = dev2/norm
    perdev      = np.sum(abs(devtot))/5.0
    perdev      = abs(100.0*(perdev - devtot[0])/perdev)   # % change in deviation.

    if (perdev < perc and count > 100):
        mixParameter = bigmix        # Try a big step
        count   = 0
        print "Big" 
    else: 
        mixParameter = smallmix      # Stick with small step.
        count   = count+1
    print(g, devtot[0], perdev)   
    step.append(g)
    divergence.append(np.sum(dev * dev))
    g= g +1

    if devtot[0] < tolerence:
        break
	

#plot plot plot, we will plot

print phia


phib = 1.0-phia
phiaave = sum(phia)/number_of_lattice_pointsX
phibave = sum(phib)/number_of_lattice_pointsX

# Outputs
print(phiaave, phibave, phiaave+phibave)
print devtot[0]
fig1 = plt.figure(1)
phia_plt = plt.plot(xxs, phia, '.-')
phib_plt = plt.plot(xxs, 1.0 - phia, '.-')


#print length(step), length()
fig2 = plt.figure(2)
thing = plt.plot(step, divergence)


plt.show()

t2 = time.clock()


print t2 - t1
print g


if flag:
	print " Q was NaN"





