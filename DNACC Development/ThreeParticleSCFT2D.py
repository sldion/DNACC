import numpy as np

import matplotlib.pyplot as plt

import scipy as sci

import math as m

import time

from decimal import *

def Particles3SCFT2D(intialDensityA,intialDensityB,
                     Height, Depth, Length, Width, 
                     volumeFraction = [0.33,0.33], 
                     alpha = 1):

        # set the necessasary variables from the function call, while also 
        # creating other variables from the inputed variables
	np.set_printoptions(precision = 4)
	volumeFractionA = volumeFraction[0]
	volumeFractionB = volumeFraction[1]
	volumeFractionC = 1 - volumeFractionA - volumeFractionB
	alphaA          = alpha
	alphaB          = 1.0
	alphaC          = 1.0
	perc            = 0.1          # Percent deviation for trying a big step.
	smallmix        = 0.01
	bigmix          = 0.1
	mixParameter    = smallmix
	incompresiblity = 100/alphaA        # Defines the stregnth of the global energy penalty 
	kappa 	 = [10 ,100 ,1000]
	smallmix = [0.01 ,0.005, 0.0005]
	number_of_iterations 			  = 30000	# Default 30000
	tolerence 						= 10**(-7) 	
	number_of_lattice_pointsX 		  = len(intialDensityA)        	# number of lattice points for the j direction
	number_of_lattice_pointsY                 = len(intialDensityA)  
	half_number_of_lattice_pointsX 	= number_of_lattice_pointsX/2 # the halfway point in the lattice
	half_number_of_lattice_pointsY  = number_of_lattice_pointsY/2
	xsize 							= 15.0    								#  
	ysize                           = 15.0
	dx 				= xsize/float(number_of_lattice_pointsX)
	dy                              = ysize/float(number_of_lattice_pointsY)
	xxs 			        = [i*dx - xsize/2.0 for i in range(0,number_of_lattice_pointsX)]
	yys                             = [i*dy - ysize/2.0 for i in range(0,number_of_lattice_pointsY)]
	flag  = 0
        A1 = Height
	A2 = Depth
	length = Length
	gamma = Width
	
        #Create the piecewise interaction potential that will be used to determine
        #the interaction between the particles. Currently the same potential is 
        #used between the different particles, this behaviour is hard coded in and
        #needs to be changed
	PotentialAB = np.ones((number_of_lattice_pointsX, number_of_lattice_pointsY))
	for j in range(0,number_of_lattice_pointsX):
		for i in range(0, number_of_lattice_pointsY):
		      r = m.sqrt(yys[i]**2 + xxs[j]**2 )
		      if r <= length:
                            PotentialAB[j][i] = ((A1+A2)*(m.cos(3.14*r/length))/2.0 + (A1 - A2)/2.0)
		      else:
                            PotentialAB[j][i] = (-A2*(m.exp(-((r-length)**2.0)/(2.0*(gamma**2.0)))))
        
        
        #The pontential needs to be rotated  in order to line up the zero of the potential
        #with the zero of the the physical zero of the densities
        PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsX, axis = 0)
	PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsY, axis = 1)
        
        #The potential needs to be fourier transformed
        Vkab = np.fft.rfftn(PotentialAB)/((float(number_of_lattice_pointsY)*float(number_of_lattice_pointsX)))

	#Randomize the density of particle A using a Gaussian distribution
	#phia = volumeFractionA + std*np.random.randn(number_of_lattice_pointsY,number_of_lattice_pointsX)

	phia = intialDensityA
	phib = intialDensityB
	phic = 1 - intialDensityA - intialDensityB

        for b in xrange(3):
		for j in xrange(number_of_iterations):

			#SCFT.
			iphia = np.fft.rfftn(phia)
			iphib = np.fft.rfftn(phib)
			iphic = np.fft.rfftn(phic)
			cnva  = iphia*Vkab
			cnvb  = iphib*Vkab
			cnvc  = iphic*Vkab
			icnva = xsize*ysize*np.fft.irfft2(cnva)
			icnvb = xsize*ysize*np.fft.irfft2(cnvb)
			icnvc = xsize*ysize*np.fft.irfft2(cnvc)

			wa = icnvb + icnvc - kappa[b]*(1 - phia - phib - phic);
			wb = icnva + icnvc - kappa[b]*(1 - phia - phib - phic);
			wc = icnvb + icnva - kappa[b]*(1 - phia - phib - phic)
		
			ewa = np.exp(-alphaA*wa)
			ewb = np.exp(-alphaB*wb)
			ewc = np.exp(-alphaC*wc)

			QA = dx*dy*np.sum(np.sum(np.sum(ewa)))
			QB = dx*dy*np.sum(np.sum(np.sum(ewb)))
			QC = dx*dy*np.sum(np.sum(np.sum(ewc)))

			#picard mixing to increase the convergence
			phiatemp = volumeFractionA*xsize*ysize*ewa/QA;
			phibtemp = volumeFractionB*xsize*ysize*ewb/QB;
			phictemp = volumeFractionC*xsize*ysize*ewc/QC;

			phiaave = volumeFractionA - dx*dy*np.sum(phiatemp)/(xsize*ysize)
			phibave = volumeFractionB - dx*dy*np.sum(phibtemp)/(xsize*ysize)
			phicave = volumeFractionC - dx*dy*np.sum(phictemp)/(xsize*ysize)

			phianew = phiatemp+phiaave
			phibnew = phibtemp+phibave
			phicnew = phictemp+phicave

			#print phia

			phia = smallmix[b]*phianew + (1 - smallmix[b])*phia
			phib = smallmix[b]*phibnew + (1 - smallmix[b])*phib
			phic = smallmix[b]*phicnew + (1 - smallmix[b])*phic

			dev = phianew-phia;
			dev2 = dev*dev;
			norm = np.sum(phianew*phianew)
			phidev = np.sum(dev2)/norm
			if abs(phidev) < tolerence:
			    flag = 1
			    break

	#will return the density if the code converges to a certain tolerance, otherwise will retrn an array of zeros.
	
	F = -fa*log(QA)-(fb/alpha)*log(QB)+dx*dy*sum(sum(icnva))/(2*xsize*ysize)+dx*dy*np.sum(icnvb)/(xsize*ysize)+dx*dy*np.sum(icnvc)/(2*xsize*ysize)-dx*dy*sum(waphia)/(xsize*ysize)-dx*dy*sum(sum(wbphib))/(xsize*ysize)+(kappa(end)/2)*dx*dy*sum(sum(comprss2))

	if (phidev <= tolerence):
		return phia, phib, xxs, yys, flag
	else:
		return phia, phib, xxs, yys, flag

