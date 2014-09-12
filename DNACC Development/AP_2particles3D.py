

#----------------------------------------------------------------------------------------------
# This code is indending to address the asymetry of the solution
# with the colloids through the use of a psudo asymptotic preserving
# method. It now adds a large step when possible to speed up convergence
#
# 
# Author: Shawn Dion 
# Date: Feb 13, 2014
#
# 
#----------------------------------------------------------------------------------------------


import numpy as np
import matplotlib.pyplot as plt
import scipy as sci
import math as m
import time
from decimal import *
from mpl_toolkits.mplot3d import Axes3D
from mayavi import mlab


#------------------------------------------------------------
# Initialize the Variables
#------------------------------------------------------------

t1              = time.clock()
volumeFractionA = 0.5
volumeFractionB = 1 - volumeFractionA
alphaA          = 0.0000001
alphaB          = 1.0
perc            = 0.1          # Percent deviation for trying a big step.
smallmix        = 0.0001
bigmix          = 0.1
mixParameter    = smallmix
incompresiblity = 100/alphaA        # Defines the stregnth of the global energy penalty 

number_of_iterations 			= 300000	# Default 30000
tolerence 						= 10**(-4) 	# the tolerance 
number_of_lattice_pointsX 		= 16      	# number of lattice points for the j direction
number_of_lattice_pointsY       = 16
number_of_lattice_pointsZ       = 16

half_number_of_lattice_pointsX 	= number_of_lattice_pointsX/2 # the halfway point in the lattice
half_number_of_lattice_pointsY  = number_of_lattice_pointsY/2
half_number_of_lattice_pointsZ  = number_of_lattice_pointsY/2
xsize 							= 15.0    								#  
ysize                           = 15.0
zsize                           = 15.0
dx 								= xsize/float(number_of_lattice_pointsX)
dy                              = ysize/float(number_of_lattice_pointsY)
dz                              = zsize/float(number_of_lattice_pointsZ)
xxs 							= [i*dx - xsize/2.0 for i in range(0,number_of_lattice_pointsX)]
yys                             = [i*dy - ysize/2.0 for i in range(0,number_of_lattice_pointsY)]
zzs                             = [i*dz - zsize/2.0 for i in range(0,number_of_lattice_pointsZ)]


flag  = 0

PotentialAB = np.zeros((number_of_lattice_pointsX, number_of_lattice_pointsY, number_of_lattice_pointsZ))

# These variables are what define the form of the potential
A1 = 0.23 #0.0195510 #4
A2 = 0.05

#0.0195510 #0.30
length =  4.0 #0.001
gamma = 0.502 


#Create the piecewise interaction potential
for i in range(0,number_of_lattice_pointsX):
    for j in range(0, number_of_lattice_pointsY):
            for k in range(0,number_of_lattice_pointsZ):

                r = m.sqrt(yys[j]**2 + xxs[i]**2 + zzs[k]**2)

                if r <= length:
                    PotentialAB[i][j][k] = (0.5*(A1+A2)*(np.cos((np.pi*r)/length)) + 0.5*(A1 - A2))
                else:
                    PotentialAB[i][j][k] = -(A2*(np.exp((-(abs(r)-length)**2.0)/(2.0*(gamma**2.0)))))


# This importfunction moves the origin of the particles to line the origin of the potential axis
# to the computational axis shifts the center of the potential to one of the corners


PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsX, axis = 0)
PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsY, axis = 1)
PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsZ, axis = 2)

# print PotentialAB
# fig3 =plt.figure(3)
# plot3 =plt.contourf(xxs,yys,PotentialAB)
# fig3.colorbar(plot3)
# plt.show()


#fft the potential for later use
Vkab = np.fft.rfftn(PotentialAB)/(number_of_lattice_pointsY*number_of_lattice_pointsX*number_of_lattice_pointsZ)




phia = np.ones((number_of_lattice_pointsX, number_of_lattice_pointsY, number_of_lattice_pointsZ))
#Randomize the density of particle A using a Gaussian distribution
std = 0.01;
#phia = volumeFractionA + std*np.random.randn(number_of_lattice_pointsX, number_of_lattice_pointsY, number_of_lattice_pointsZ) 



#LAMERLAR PHASE 
phia[0:half_number_of_lattice_pointsX/2] = 0.99
phia[(half_number_of_lattice_pointsX/2):half_number_of_lattice_pointsX] = 0.01
phia[number_of_lattice_pointsX:number_of_lattice_pointsX*(0.75)] = 0.99
phia[number_of_lattice_pointsX*(0.75):number_of_lattice_pointsX] = 0.01

g = 0

divergence          = []
step                = []
percentDeviation    = []
count  = 0
devtot = 100.0*np.zeros(5)         # Initialize some variables.
phianew2 = np.zeros((number_of_lattice_pointsY, number_of_lattice_pointsY))
for j in xrange(number_of_iterations):
    phia2 = phia  - volumeFractionA

    
    iphia       = np.fft.rfftn(phia2)
    lgaterm     = -(1/alphaA)*np.log(phia/volumeFractionA)
    lgbterm     = (1/alphaB)*np.log((1.0 - phia)/volumeFractionB)
    cnvab       = iphia*Vkab
    convolution_Phia_PotentialAb =  ysize*xsize*zsize*np.fft.irfftn(cnvab)

    #print (2.0/(alphaA*alphaB))*convolution_Phia_PotentialAb
    kpterm      = incompresiblity*(volumeFractionA - (np.sum(phia)/(number_of_lattice_pointsY*number_of_lattice_pointsX*number_of_lattice_pointsZ)))

    #self consistent equations in reformulated 
    phianew = lgaterm + lgbterm  +  kpterm + (2.0/(alphaA*alphaB))*convolution_Phia_PotentialAb
    

    #check if phianew has obtained any incorrect values

    if np.isnan(np.sum(phianew)):
        flag = 1
        break

    #picard mixing to increase the convergence
    dev         = phianew                                #L2 norm deviation
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

    phia  = phia + (alphaA*mixParameter)*phianew
    
    # if statements to threshold the values of phi, so no number is less than zero, greater than one

    phia[phia >= 1.0]  = 0.999999
    phia[phia <= 0.0]  = 0.000001


#plot plot plot, we will plot


phib = 1.0 - phia

phianew = np.sum(np.sum(phia))/(number_of_lattice_pointsY*number_of_lattice_pointsX*number_of_lattice_pointsZ)
phibnew = np.sum(np.sum(phib))/(number_of_lattice_pointsY*number_of_lattice_pointsX*number_of_lattice_pointsZ)

#np.savetxt('3DResult.txt',phia)
print devtot[0], phianew, phibnew

print phia
s = mlab.contour3d( phia)
mlab.show()
a = mlab.contour3d(phib)
mlab.show()


#print length(step), length()

t2 = time.clock()


print t2 - t1
print g


if flag:
	print " Q was NaN"





