import numpy as np
import matplotlib.pyplot as plt
import scipy as sci
import math as m
import time
from decimal import *




#parameters = np.loadtxt('try.txt')

def Particles3SCFT(intialDensityA,intialDensityB,Height, Depth, Length, Width, volumeFraction = [0.33,0.33], alpha = 1):

	np.set_printoptions(precision = 4)
	t1              = time.clock()
	volumeFractionA = volumeFraction[0]
	volumeFractionB = volumeFraction[1] 
	volumeFractionC = 1 - volumeFraction[0] - volumeFraction[1]
	alphaA          = alpha
	alphaB          = 1.0
	alphaC			= 1.0
	perc            = 0.1          # Percent deviation for trying a big step.
	smallmix        = 0.01
	bigmix          = 0.1
	mixParameter    = smallmix
	incompresiblity = 100/alphaA        # Defines the stregnth of the global energy penalty 

	kappa 	 = [10 ,100 ,900]
	smallmix = [0.01 ,0.005, 0.0005]

	number_of_iterations 			= 100000	# Default 30000
	tolerence 						= 10**(-4) 	# the tolerance 
	number_of_lattice_pointsX 		= 64      	# number of lattice points for the j direction
	number_of_lattice_pointsY       = 64
	number_of_lattice_pointsZ       = 64

	half_number_of_lattice_pointsX 	= number_of_lattice_pointsX/2 # the halfway point in the lattice
	half_number_of_lattice_pointsY  = number_of_lattice_pointsY/2
	half_number_of_lattice_pointsZ  = number_of_lattice_pointsY/2

	
	#define box demsions and grid spacing
	xsize 							= 15.0    								#  
	ysize                           = 15.0
	zsize							= 15.0
	dx 								= xsize/float(number_of_lattice_pointsX)
	dy                              = ysize/float(number_of_lattice_pointsY)
	dz                          	= zsize/float(number_of_lattice_pointsZ)
	xxs 							= [i*dx - xsize/2.0 for i in range(0,number_of_lattice_pointsX)]
	yys                             = [i*dy - ysize/2.0 for i in range(0,number_of_lattice_pointsY)]
	zzs                         	= [i*dz - zsize/2.0 for i in range(0,number_of_lattice_pointsZ)]


	flag  = 0

	PotentialAB = np.ones((number_of_lattice_pointsX, number_of_lattice_pointsY, number_of_lattice_pointsZ))
	
	A1 = Height
	A2 = Depth
	length = Length
	gamma = Width

	#Create the piecewise interaction potential
	for j in range(0,number_of_lattice_pointsX):
		for i in range(0, number_of_lattice_pointsY):
			for k in range(0, number_of_lattice_pointsZ):
				r = m.sqrt(yys[i]**2 + xxs[j]**2 + zzs[k]**2)
				if r <= length:
					PotentialAB[j][i][k] = ((A1+A2)*(m.cos(3.14*r/length))/2.0 + (A1 - A2)/2.0)
				else:
					PotentialAB[j][i][k] = (-A2*(m.exp(-((r-length)**2.0)/(2.0*(gamma**2.0)))))




	PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsX, axis = 0)
	PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsY, axis = 1)
	PotentialAB = np.roll(PotentialAB, half_number_of_lattice_pointsZ, axis = 2)

	#fft the potential for later use
	Vkab = np.fft.rfft2(PotentialAB)/((float(number_of_lattice_pointsY)*float(number_of_lattice_pointsX)))

	#Randomize the density of particle A using a Gaussian distribution
	std = 0.1;
	#phia = volumeFractionA + std*np.random.randn(number_of_lattice_pointsY,number_of_lattice_pointsX)

	phia = intialDensityA

	phib = intialDensityB

	phic = 1 -intialDensityA - intialDensityB
	

	
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
			iphic = np.fft.rfft2(phic);

			cnva  = iphia*Vkab;
			cnvb  = iphib*Vkab;
			cnvb  = iphic*Vkab;


			icnva = xsize*ysize*zsize*np.fft.irfft2(cnva);
			icnvb = xsize*ysize*zsize*np.fft.irfft2(cnvb);
			icnvc = xsize*ysize*zsize*np.fft.irfft2(cnvc)


			wa = icnvb + icnvc - kappa[b]*(1 - phia - phib - phic);
			wb = icnva + icnvc - kappa[b]*(1 - phia - phib - phic);
			wc = icnvc + icnva - kappa[b]*(1 - phia - phib - phic)

			ewa = np.exp(-alpha*wa)
			ewb = np.exp(-alphaB*wb)
			ewc = np.exp(-alphaC*wc)
			#print phianew


			#print phianew


			QA = dx*dy*dz*np.sum(np.sum(np.sum(ewa)))
			QB = dx*dy*dz*np.sum(np.sum(np.sum(ewb)))
			QC = dx*dy*dz*np.sum(np.sum(np.sum(ewc)))

			#picard mixing to increase the convergence
			phiatemp = volumeFractionA*xsize*ysize*zsize*ewa/QA;
			phibtemp = volumeFractionB*xsize*ysize*zsize*ewb/QB;
			phictemp = volumeFractionC*xsize*ysize*zsize*ewc/QC;

			phiaave = volumeFractionA -dx*dy*dz*np.sum(phiatemp)/(xsize*ysize*zsize)
			phibave = volumeFractionB -dx*dy*dz*np.sum(phibtemp)/(xsize*ysize*zsize)
			phicave = volumeFractionC -dx*dy*dz*np.sum(phictemp)/(xsize*ysize*zsize)

			phianew = phiatemp+phiaave
			phibnew = phibtemp+phibave
			phicnew = phictemp+phicave

			    #print phia
			#print(g, devtot[0], perdev)   
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



	#will return the density if the code converges to a certain tolerance, otherwise will return an array of zeros.
	if (phidev <= tolerence):
		return phia
	else:
		return np.zeros((64,64))

