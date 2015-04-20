import numpy as np
import matplotlib.pyplot as plt
import scipy as sci
import math as m
import time
from decimal import *




#parameters = np.loadtxt('try.txt')

def Particles3SCFT(intialDensityA,intialDensityB,Height, Depth, Length, Width, volumeFraction = [0.33,0.33], AlphaA = 1,AlphaB = 1):

	np.set_printoptions(precision = 4)
	t1              = time.clock()
	volumeFractionA = volumeFraction[0]
	volumeFractionB = volumeFraction[1]
	volumeFractionC = 1 - volumeFraction[0] - volumeFraction[1]
	alphaA          = AlphaA
	alphaB          = AlphaB
	alphaC	        = 1.0
	perc            = 0.1          # Percent deviation for trying a big step.
	bigmix          = 0.1

	kappa 	 = [10, 100,1000]
	smallmix = [0.01 ,0.005, 0.0005]

	number_of_iterations 			= 10000	# Default 30000
	tolerence 						= 10**(-7) 	# the tolerance
	number_of_lattice_pointsX 	    = len(intialDensityA)      	# number of lattice points for the j direction
	number_of_lattice_pointsY       = len(intialDensityA)
	number_of_lattice_pointsZ       = len(intialDensityA)

	half_number_of_lattice_pointsX 	= number_of_lattice_pointsX/2 # the halfway point in the lattice
	half_number_of_lattice_pointsY  = number_of_lattice_pointsY/2
	half_number_of_lattice_pointsZ  = number_of_lattice_pointsY/2


	#define box demsions and grid spacing
	xsize 							= 8.0    								#
	ysize                           = 8.0
	zsize							= 8.0
	dx 								= xsize/float(number_of_lattice_pointsX)
	dy                              = ysize/float(number_of_lattice_pointsY)
	dz                          	= zsize/float(number_of_lattice_pointsZ)
	xxs 			         		= [i*dx - xsize/2.0 for i in range(0,number_of_lattice_pointsX)]
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
	Vkab = np.fft.rfftn(PotentialAB)/((float(number_of_lattice_pointsY)*float(number_of_lattice_pointsX)*float(number_of_lattice_pointsZ)))

	#Randomize the density of particle A using a Gaussian distribution
	#phia = volumeFractionA + std*np.random.randn(number_of_lattice_pointsY,number_of_lattice_pointsX)

	phia = intialDensityA

	phib = intialDensityB

	phic = 1 - intialDensityA - intialDensityB



	divergence          = []
	step                = []
	percentDeviation    = []
	devtot = 100.0*np.ones(5)
	count  = 0
	g = 0
	for b in xrange(3):
		for j in xrange(number_of_iterations):

			#SCFT.
			iphia = np.fft.rfftn(phia);
			iphib = np.fft.rfftn(phib);
			iphic = np.fft.rfftn(phic);

			cnva  = iphia*Vkab;
			cnvb  = iphib*Vkab;
			cnvc  = iphic*Vkab;


			icnva = xsize*ysize*zsize*np.fft.irfftn(cnva);
			icnvb = xsize*ysize*zsize*np.fft.irfftn(cnvb);
			icnvc = xsize*ysize*zsize*np.fft.irfftn(cnvc)


			wa = icnvb + icnvc - kappa[b]*(1 - phia - phib - phic);
			wb = icnva + icnvc - kappa[b]*(1 - phia - phib - phic);
			wc = icnvb + icnva - kappa[b]*(1 - phia - phib - phic)
			

			ewa = np.exp(-alphaA*wa)
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

			phiaave = volumeFractionA - dx*dy*dz*np.sum(phiatemp)/(xsize*ysize*zsize)
			phibave = volumeFractionB - dx*dy*dz*np.sum(phibtemp)/(xsize*ysize*zsize)
			phicave = volumeFractionC - dx*dy*dz*np.sum(phictemp)/(xsize*ysize*zsize)

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



	#will return the density if the code converges to a certain tolerance, otherwise will return an array of zeros.
	
	if (phidev <= tolerence):
		return phia, phib, xxs, yys, zzs, flag
	else:
		return phia, phib, xxs, yys, zzs, flag
