################################################################################
# Functions useful for calculation of multi particle SCFT



################################################################################


import numpy as np
import math  as m

class MultiParticleSCFT:
	# member variables
	m_numberOfParticles = 2

	#Parameters for the potential
	length    = 2.0
	A1        = 1.0
	A2                  = 1.0
	width               = 0.5

	xsize                                    = 15
	number_of_lattice_pointsX                = 64

	xxs         = np.zeros((64))                
	yys         = np.zeros((64))
	zzs         = np.zeros((64))

	#Default parameters for the system
	volumeFraction        = 0.5
	alpha                 = 1.0 

	PotentialAB1D = zeros((number_of_lattice_pointsX))
	PotentialAB2D = zeros((number_of_lattice_pointsX, number_of_lattice_pointsY)

	#Intitlization
	def __init__(self,numberOfParticles):
	self.m_numberOfParticles = numberOfParticles



	#Functions for stuff
	def createPotential1D(self):
		for j in range(0,number_of_lattice_pointsX):
			r = xxs[j]

			if r <= length:
				PotentialAB1D[j] = ((A1+A2)*(m.cos(3.14*r/length))/2.0 + (A1 - A2)/2.0)
			else:
				PotentialAB1D[j] = (-A2*(m.exp(-((r-length)**2.0)/(2.0*(gamma**2.0)))))

	def createPotential2D(self):
		for i in range(0,number_of_lattice_pointsX):
			for  j in range(0,number_of_lattice_pointsX):
				r = sqrt(xxs[i]**2 + yys[j]**2)

				if r <= length:
					PotentialAB2D[i][j] = ((A1+A2)*(m.cos(3.14*r/length))/2.0 + (A1 - A2)/2.0)
				else:
					PotentialAB2D[i][j] = (-A2*(m.exp(-((r-length)**2.0)/(2.0*(gamma**2.0)))))




	def solveSystemSCFT(self):



	def DFTLikeAlgorithm(self):








