#############
# A set of functions to analyzse a system of particles with isotropic interactions
# Using two sets of algorithms, one for self consistent field theory and one for
#
#
################################################################################

import numpy as np
import matplotlib.pyplot as plt
import scipy as sci
import math as m
import time
from decimal import *

################################################################################
# A set of functions to analyzse a system of particles with isotropic interactions
# Using two sets of algorithms, one for self consistent field theory and one for
#
# Calculates the free energy for the DFT like algorithm(The free energy zero was
# moved so it needs to be a different function)
#
# It still needs work, the potential needs to be somehow passed to this function
# possible rework needed so that this code can be used in a object oriented like
# structure
################################################################################

def FreeEnergyDFTLike(phiaFree, volumeFractionA):

	volumeFractionB = 1 - volumeFractionA
	iphia       = np.fft.rfft2(phiaFree - volumeFractionA)

	iphiaVka    = iphia*Vkab

	phiaVphia   = (xsize*ysize)*np.fft.irfft2(iphiaVka)

	FreeEnergy  =  (1//(number_of_lattice_pointsY*number_of_lattice_pointsX*alphaA))*np.sum((phiaFree)*(np.log(phiaFree/volumeFractionA) - 1)) + \
	(1/(number_of_lattice_pointsY*number_of_lattice_pointsX*alphaB))*np.sum(((1.0 - phiaFree))*(np.log((1.0 - phiaFree)/volumeFractionB) - 1)) - \
	(1/(alphaA*alphaB*number_of_lattice_pointsY*number_of_lattice_pointsX))*np.sum(phiaVphia*(phiaFree - volumeFractionA)) + \
	(incompresiblity/2)*(volumeFractionA - (np.sum(phiaFree)/(number_of_lattice_pointsY*number_of_lattice_pointsX)))**2

	return FreeEnergy


def FreeEnergySCFT(phiaFree, volumeFractionA):

def AlgoirithmSCFT2D(intialDensity,Height, Depth, Length, Width, volumeFraction = 0.5, alpha = 1, numberOfLatticePoints = 64, SizeOfBox = 15.0):

	t1              = time.clock()
	volumeFractionA = volumeFraction
	volumeFractionB = 1 - volumeFractionA
	alphaA          = alpha
	alphaB          = 1.0
	perc            = 0.1          # Percent deviation for trying a big step.
	smallmix        = 0.0001
	bigmix          = 0.1
	mixParameter    = smallmix
	incompresiblity = 100/alphaA        # Defines the stregnth of the global energy penalty
	number_of_iterations 			= 100000	# Default 30000
	tolerence 						= 10**(-4) 	# the tolerance

	xsize							= SizeOfBox
	ysize							= SizeOfBox

	number_of_lattice_pointsX 		= numberOfLatticePoints
	number_of_lattice_pointsY 		= numberOfLatticePoints
	half_number_of_lattice_pointsX 	= numberOfLatticePoints/2 # the halfway point in the lattice
	half_number_of_lattice_pointsY  = numberOfLatticePoints/2

	dx 								= xsize/float(number_of_lattice_pointsX)
	dy                              = ysize/float(number_of_lattice_pointsY)
	xxs 							= [i*dx - xsize/2.0 for i in range(0,number_of_lattice_pointsX)]
	yys                             = [i*dy - ysize/2.0 for i in range(0,number_of_lattice_pointsY)]

	kappa 	 = [10 ,100 ,900]
	smallmix = [0.01 ,0.001, 0.0001]

	PotentialAB = np.ones((number_of_lattice_pointsX, number_of_lattice_pointsY))

	A1 = Height
	A2 = Depth
	length = Length
	gamma = Width

	#Create the piecewise interaction potential
	for j in range(0,number_of_lattice_pointsX):
		for i in range(0, number_of_lattice_pointsY):
			r = m.sqrt(yys[i]**2 + xxs[j]**2)
			if r <= length:
				PotentialAB[j][i] = ((A1+A2)*(m.cos(3.14*r/length))/2.0 + (A1 - A2)/2.0)
			else:
				PotentialAB[j][i] = (-A2*(m.exp(-((r-length)**2.0)/(2.0*(gamma**2.0)))))




	PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsX, axis = 0)
	PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsY, axis = 1)

	#fft the potential for later use
	Vkab = np.fft.rfft2(PotentialAB)/((float(number_of_lattice_pointsY)*float(number_of_lattice_pointsX))

	phia = intialDensity

	phib = 1 - phia

	divergence          = []
	step                = []
	percentDeviation    = []
	devtot = 100.0*np.ones(5)
	count  = 0
	g = 0
	flag = 0
	for b in xrange(3):
		for j in xrange(number_of_iterations):

			#SCFT.
			iphia = np.fft.rfft2(phia);
			iphib = np.fft.rfft2(phib);

			cnva  = iphia*Vkab;
			cnvb  = iphib*Vkab;

			icnva = (1/alpha)*xsize*ysize*np.fft.irfft2(cnva);
			icnvb = (1/alpha)*xsize*ysize*np.fft.irfft2(cnvb);
			cnvab = iphia*Vkab


			wa = icnvb - kappa[b]*(1-phia-phib);
			wb = icnva - kappa[b]*(1-phia-phib);

			ewa = np.exp(-alpha*wa)
			ewb = np.exp(-wb)

			#print phianew


			#print phianew


			QA = dx*dy*np.sum(np.sum(ewa))


			QB = dx*dy*np.sum(np.sum(ewb))
			#picard mixing to increase the convergence
			phiatemp = volumeFractionA*xsize*ysize*ewa/QA;
			phibtemp = volumeFractionB*xsize*ysize*ewb/QB;

			phiaave = volumeFractionA-dx*dy*sum(sum(phiatemp))/(xsize*ysize);
			phibave = volumeFractionB-dx*dy*sum(sum(phibtemp))/(xsize*ysize);

			phianew = phiatemp+phiaave;
			phibnew = phibtemp+phibave;

			    #print phia
			#print(g, devtot[0], perdev)
			phia = smallmix[b]*phianew+(1- smallmix[b])*phia;
			phib = smallmix[b]*phibnew+(1- smallmix[b])*phib;



			dev = phianew-phia;
			dev2 = dev*dev;
			norm = np.sum(np.sum(phianew*phianew));
			phidev = np.sum(np.sum(dev2))/norm;
			if abs(phidev) < tolerence:
			    flag = 1
			    break



	#will return the density if the code converges to a certain tolerance, otherwise will return an array of zeros.
	if (phidev <= tolerence):
		return phia, xxs ,yys, flag
	else:
		return np.zeros((64,64)), xxs, yys, flag

def AlgorithmDFTLike2D(intialDensity,Height, Depth, Length, Width, volumeFraction = 0.5, alpha = 1, numberOfLatticePoints = 64, SizeOfBox = 15.0):

	t1              = time.clock()
	volumeFractionA = volumeFraction
	volumeFractionB = 1 - volumeFractionA
	alphaA          = alpha
	alphaB          = 1.0
	perc            = 0.1          # Percent deviation for trying a big step.
	smallmix        = 0.01
	bigmix          = 0.1
	mixParameter    = smallmix
	incompresiblity = 100/alphaA        # Defines the stregnth of the global energy penalty
	number_of_iterations 			= 100000	# Default 30000
	tolerence 						= 10**(-4) 	# the tolerance

	xsize							= SizeOfBox
	ysize							= SizeOfBox

	number_of_lattice_pointsX 		= numberOfLatticePoints
	number_of_lattice_pointsY 		= numberOfLatticePoints
	half_number_of_lattice_pointsX 	= numberOfLatticePoints/2 # the halfway point in the lattice
	half_number_of_lattice_pointsY  = numberOfLatticePoints/2

	dx 								= xsize/float(number_of_lattice_pointsX)
	dy                              = ysize/float(number_of_lattice_pointsY)
	xxs 							= [i*dx - xsize/2.0 for i in range(0,number_of_lattice_pointsX)]
	yys                             = [i*dy - ysize/2.0 for i in range(0,number_of_lattice_pointsY)]


	PotentialAB = np.zeros((number_of_lattice_pointsX, number_of_lattice_pointsY))

	A1 = Height
	A2 = Depth
	length = Length
	gamma = Width


	#Create the piecewise interaction potential
	for j in range(0,number_of_lattice_pointsX):
		for i in range(0, number_of_lattice_pointsY):
			r = m.sqrt(yys[i]**2 + xxs[j]**2)
			if r <= length:
				PotentialAB[j][i] = ((A1+A2)*(m.cos(3.14*r/length))/2.0 + (A1 - A2)/2.0)
			else:
				PotentialAB[j][i] = (-A2*(m.exp(-((r-length)**2.0)/(2.0*(gamma**2.0)))))




	PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsX, axis = 0)
	PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsY, axis = 1)

	#fft the potential for later use
	Vkab = np.fft.rfft2(PotentialAB)/((float(number_of_lattice_pointsY)*float(number_of_lattice_pointsX)))

	#Randomize the density of particle A using a Gaussian distribution
	std = 0.1;
	#phia = volumeFractionA + std*np.random.randn(number_of_lattice_pointsY,number_of_lattice_pointsX)
	phia = np.ones((number_of_lattice_pointsX, number_of_lattice_pointsY))

	phia = np.loadtxt('dots.txt')




	phia[phia >= 1.0]  = 0.9999999
	phia[phia <= 0.0]  = 0.0000001



	divergence          = []
	step                = []
	percentDeviation    = []
	devtot = 100.0*np.ones(5)
	count  = 0
	g = 0
	flag = 0

	for j in xrange(number_of_iterations):
		phia2 = phia - volumeFractionA
		iphia       = np.fft.rfft2(phia2)

		lgaterm     = -(1/alphaA)*np.log(phia/volumeFractionA)
		lgbterm     = (1/alphaB)*np.log((1 - phia)/volumeFractionB)
		cnvab       = iphia*Vkab

		convolution_Phia_PotentialAb =  ysize*xsize*np.fft.irfft2(cnvab)

		kpterm      = incompresiblity*(volumeFractionA - (np.sum(phia)/(number_of_lattice_pointsY*number_of_lattice_pointsX)))

		#self consistent equations in reformulated form
		phianew     =  lgaterm  + lgbterm + (2/(alphaA*alphaB))*convolution_Phia_PotentialAb + kpterm

		#print phianew


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

		if (perdev < perc and count > 1000):
		    mixParameter = bigmix        # Try a big step
		    count   = 0
		else:
		    mixParameter = smallmix      # Stick with small step.
		    count   = count+1
		    #print phia
		#print(g, devtot[0], perdev)
		step.append(g)
		divergence.append(devtot[0])
		g= g +1

		if abs(devtot[0]) < tolerence:
		    flag = 1
		    print "convergences"
		    break

		phia  = phia + alphaA*mixParameter*phianew



		# if statements to threshold the values of phi, so no number is less than zero, greater than one
		phia[phia >= 0.99]  = 0.9999
		phia[phia <= 0.01]  = 0.0001


	#will return the density if the code converges to a certain tolerance, otherwise will return an array of zeros.
	if (devtot[0] <= tolerence):
		return phia, xxs, yys, flag
	else:
		return phia, xxs ,yys, flag
