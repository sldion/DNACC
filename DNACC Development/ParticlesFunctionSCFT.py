import numpy as np
import matplotlib.pyplot as plt
import scipy as sci
import math as m
import time
from decimal import *




#parameters = np.loadtxt('try.txt')

def Particles2SCFT(intialDensity,Height, Depth, Length, Width, volumeFraction = 0.5, alpha = 1):

	np.set_printoptions(precision = 4)
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

	kappa 	 = [10 ,100 ,900]
	smallmix = [0.01 ,0.005, 0.0005]

	number_of_iterations 			= 30000	# Default 30000
	tolerence 						= 10**(-4) 	# the tolerance 
	number_of_lattice_pointsX 		= 64      	# number of lattice points for the j direction
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
	Vkab = np.fft.rfft2(PotentialAB)/((float(number_of_lattice_pointsY)*float(number_of_lattice_pointsX)))

	#Randomize the density of particle A using a Gaussian distribution
	std = 0.1;
	#phia = volumeFractionA + std*np.random.randn(number_of_lattice_pointsY,number_of_lattice_pointsX)

	phia = intialDensity

	phib = 1 - phia
	

	
	divergence          = []
	step                = []
	percentDeviation    = []
	devtot = 100.0*np.ones(5)
	count  = 0
	g = 0
	for b in xrange(3):
		for j in xrange(number_of_iterations):

			#SCFT.
			iphia = np.fft.rfft2(phia);
			iphib = np.fft.rfft2(phib);

			cnva  = iphia*Vkab;
			cnvb  = iphib*Vkab;

			icnva = xsize*ysize*np.fft.irfft2(cnva);
			icnvb = xsize*ysize*np.fft.irfft2(cnvb);
			cnvab = iphia*Vkab


			wa = icnvb - kappa[b]*(1-phia-phib);
			wb = icnva - kappa[b]*(1-phia-phib);

			ewa = np.exp(-wa)
			ewb = np.exp(-alpha*wb)

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
		return phia
	else:
		return np.zeros((64,64))

