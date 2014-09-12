 

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





#------------------------------------------------------------
# Initialize the Variables
#------------------------------------------------------------

t1              = time.clock()
volumeFractionA = 0.5
volumeFractionB = 1 - volumeFractionA
alphaA          = 0.0000001
alphaB          = 1.0
perc            = 0.1          # Percent deviation for trying a big step.
smallmix        = 0.001
bigmix          = 0.1
mixParameter    = smallmix
incompresiblity = 100/alphaA        # Defines the stregnth of the global energy penalty 

number_of_iterations 			= 100000	# Default 30000
tolerence 						= 10**(-4) 	# the tolerance 
number_of_lattice_pointsX 		= 16      	# number of lattice points for the j direction
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

PotentialAB = np.zeros((number_of_lattice_pointsX, number_of_lattice_pointsY))

# These variables are what define the form of the potential
A1 = 10.0 #0.0195510 #4
A2 = 0.0

#0.0195510 #0.30
length =  2.0 #0.001
gamma = 0.52 


#Create the piecewise interaction potential
for i in range(0,number_of_lattice_pointsX):
    for j in range(0, number_of_lattice_pointsY):
        r = m.sqrt(yys[j]**2 + xxs[i]**2)

        if r <= length:
            PotentialAB[i][j] = (0.5*(A1+A2)*(np.cos((np.pi*r)/length)) + 0.5*(A1 - A2))
        else:
            PotentialAB[i][j] = -(A2*(np.exp((-(abs(r)-length)**2.0)/(2.0*(gamma**2.0)))))

# This importfunction moves the origin of the particles to line the origin of the potential axis
# to the computational axis shifts the center of the potential to one of the corners


PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsX, axis = 0)
PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsY, axis = 1)

# print PotentialAB
# fig3 =plt.figure(3)
# plot3 =plt.contourf(xxs,yys,PotentialAB)
# fig3.colorbar(plot3)
# plt.show()


#fft the potential for later use
Vkab = np.fft.rfft2(PotentialAB)/(number_of_lattice_pointsY*number_of_lattice_pointsX)


def BisectionMethod(lowerLimitPhia, upperLimitPhia):
    phiA      = lowerLimitPhia
    phiB       = upperLimitPhia
    middle      = 0
    hugeNumbers = 100000
    devtot = 100.0*np.zeros(5)   

    functionC = np.ones((number_of_lattice_pointsX,number_of_lattice_pointsY))

    loopNumber = 1
    while loopNumber <= number_of_iterations:
        phiC = (phiA + phiB)/2.0

        iphia       = np.fft.rfft2(phiA)
        lgaterm     = -(1/alphaA)*np.log(phiA/volumeFractionA)
        lgbterm     = (1/alphaB)*np.log((1.0 - phiA)/volumeFractionB)
        cnvab       = iphia*Vkab
        convolution_Phia_PotentialAb =  ysize*xsize*np.fft.irfft2(cnvab)
        kpterm      = incompresiblity*(volumeFractionA - (np.sum(phiA)/(number_of_lattice_pointsY*number_of_lattice_pointsX)))

        FunctionA   = lgaterm + lgbterm  +  kpterm + (2.0/(alphaA*alphaB))*convolution_Phia_PotentialAb 

        iphib      = np.fft.rfft2(phiB)
        lgatermb     = -(1/alphaA)*np.log(phiB/volumeFractionA)
        lgbtermb     = (1/alphaB)*np.log((1.0 - phiB)/volumeFractionB)
        cnvabB       = iphia*Vkab
        convolution_Phia_PotentialAb =  ysize*xsize*np.fft.irfft2(cnvabB)
        kptermb      = incompresiblity*(volumeFractionA - (np.sum(phiB)/(number_of_lattice_pointsY*number_of_lattice_pointsX))) 
    
        FunctionB   = lgatermb + lgbtermb  +  kptermb+ (2.0/(alphaA*alphaB))*convolution_Phia_PotentialAb
        

        iphic       = np.fft.rfft2(phiC)
        lgatermc     = -(1/alphaA)*np.log(phiC/volumeFractionA)
        lgbtermc     = (1/alphaB)*np.log((1.0 - phiC)/volumeFractionB)
        cnvabC       = iphia*Vkab
        convolution_Phia_PotentialAb =  ysize*xsize*np.fft.irfft2(cnvabC)
        kptermc      = incompresiblity*(volumeFractionA - (np.sum(phiC)/(number_of_lattice_pointsY*number_of_lattice_pointsX))) 
    
        FunctionC   = lgatermc + lgbtermc  +  kptermc + (2.0/(alphaA*alphaB))*convolution_Phia_PotentialAb
        
        dev         = FunctionC                                #L2 norm deviation
        dev2        = np.sum(dev**2)
        devtot      = np.roll(devtot,1)     # Remember previous deviations.
        devtot[0]   = dev2
        perdev      = np.sum(abs(devtot))/5.0
        perdev      = abs(100.0*(perdev - devtot[0])/perdev)   # % change in deviation.
        
        if devtot[0] < tolerence:
            return phiC


        loopNumber = loopNumber + 1 

        signOfA = np.sign(FunctionA)
        signOfB = np.sign(FunctionB)
        signOfC = np.sign(FunctionC)

        for k in range(0,number_of_lattice_pointsX):
            for l in range(0, number_of_lattice_pointsX):
                if signOfC[k][l] == signOfA[k][l]:

                    phiA[k][l]  = phiC[k][l]
                
                else:
                    phiB[k][l]   = phiC[k][l]

        
        
 
    return phiC


std = 0.1
upperLimit = 0.8*np.ones((number_of_lattice_pointsX,number_of_lattice_pointsY))
lowerLimit = 0.0001*np.ones((number_of_lattice_pointsX, number_of_lattice_pointsY))


phia = BisectionMethod(lowerLimit,upperLimit)

print phia 
phib = 1.0 - phia

phianew = np.sum(np.sum(phia))/(number_of_lattice_pointsY*number_of_lattice_pointsX)
phibnew = np.sum(np.sum(phib))/(number_of_lattice_pointsY*number_of_lattice_pointsX)




fig1 = plt.figure(1)
phia_plt = plt.contourf(xxs, yys, phia)
plt.contour(xxs,yys,phia)
fig1.colorbar(phia_plt)



fig4 = plt.figure(4)
thing2 = plt.plot(xxs, phia[0:number_of_lattice_pointsX][half_number_of_lattice_pointsX])

plt.show()

plt.show()

t2 = time.clock()


print t2 - t1


if flag:
	print " Q was NaN"





