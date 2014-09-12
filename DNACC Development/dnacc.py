#------------------------------------------------------------
# Name: dnacc.py
#
# Description: Contains functions used to create multi particle DNA covered colloid(dnacc) 
#              Which are solutions to a set of self consistent equations 
#
#------------------------------------------------------------

import numpy as np
import matplotlib.pyplot as plt
import scipy as sci
import math as m
import time
from decimal import *

class dnacc:
    # The member variables that our functions need to run properly
    incompresibilityFactor 	        = [10.0,100.0 ,1000.0]# Default 1850, 2050 [10 100 1000]
    mixParameter 			        = [0.01, 0.005, 0.0005] 
    number_of_lattice_points        = 32
    size 							= 15.0    								#  

    # These values can be calculated from the user inputed values
    half_number_of_lattice_points 	= number_of_lattice_points/2 # the halfway point in the lattice
    dx 								= xsize/float(number_of_lattice_points)
    xxs 							= [i*dx - size/2.0 for i in range(0,number_of_lattice_points)]

    m_volumeFractions               = np.array([])
    m_NumberOfDimensions            = 1
    m_NumberOfParticles             = 3
    m_InitalDensities               = np.array([])
    m_FinalDensities                = np.array([])
    m_Potentials                    = np.array([])
    flag  = 0



#----------------------------------------------------------------------------------------
#Name: _init_
#
#Description: Takes in the number of dimensions and number of Particles. Will also set the
#             the volume fractions so that each particle takes up an equal space in the box
#----------------------------------------------------------------------------------------
    def _init_(self,dimensions, numberOfParticles):
        self.m_NumberOfDimensions = dimensions
        self.m_NumberOfParticles  = numberOfParticles
        self.m_volumeFractions    = np.array([float(1/numberOfParticles) for i in range(0,numberOfParticles)])



#----------------------------------------------------------------------------------------
#Name: setVolumeFractions
#
#Description: Sets the number of volume fractions based on the user input.
#
#
#Returns: 0 if user input is not valid
#----------------------------------------------------------------------------------------

    def setVolumeFractions(self, listOfVolumeFractions):

        if np.ceil(np.sum(listOfVolumeFractions)) == 1 and len(listOfVolumeFractions) == self.m_NumberOfParticles:
            self.m_volumeFractions = listOfVolumeFractions
        else:
            return 0






#----------------------------------------------------------------------------------------
# Generates Random initial densites for the number of particles using a gaussian distribution.
# Normalizes the densities so the sum equals one.
#----------------------------------------------------------------------------------------
    def generateRandomIntialDensities(self):
        std = 0.15
        if self.m_NumberOfDimensions == 1:
            for i in range(0,len(self.m_volumeFractions)):
               
                if i != len(self.m_volumeFractions) - 1:
                    np.append(self.m_InitalDensities,volumeFraction[i] + std*np.random.randn(number_of_lattice_points))
                else:
                    np.append(self.m_InitalDensities,1 - np.sum(self.m_InitalDensities))






#----------------------------------------------------------------------------------------
# Generates potentials based on user specified values. If no values given it defaults to 
# chosen values.
#----------------------------------------------------------------------------------------
    def generatePotential(self,A1 = 3.0, A2 = 1.0, length = 6.0, halfWidthHalfMaximum = 0.65):
        gamma = halfWidthHalfMinimum/(m.sqrt(2*m.log(2)))
        for potential in range(0,nCr(self.m_NumberOfParticles,2)):
            tempPotential = np.zeros(self.number_of_lattice_points,1)
            for i in range(0,self.number_of_lattice_points):
                r = abs(xxs[i])
                if r <= length:
                    tempPotential[i] = (A1+A2)*(m.cos((sci.pi)*r/length))/2.0 + (A1 - A2)/2.0
                else:
                    tempPotential[i] -A2*(m.exp(-(r-length)))**2.0/(2.0*gamma**2.0)
            np.append(self.m_Potentials,tempPotential)

#----------------------------------------------------------------------------------------
# Generates potentials based on user specified values. If no values given it defaults to 
# chosen values.
#----------------------------------------------------------------------------------------

    def _fourierTransform(self, ListOfArrays):
        fourierList = np.array([])
        for things in ListOfArrays
              np.append(fourierList, np.fft.fft(things))
        return fourierList

    def _inverseFourierTransform(self,ListOfFourierArrays
        inverseFourierList = np.array([])
        for things in ListOfArrays
              np.append(fourierList, np.fft.fft(things))
        return fourierList



#----------------------------------------------------------------------------------------
# Takes the intial densites and the potential that was specified by the user and
# calculates the final densities using a real space FFT method.
#----------------------------------------------------------------------------------------
    def findFinalDensities(self):
        
        for i in range(0,3):
            for j in range(0, 100000):


    def nCr(n,r):
        f = math.factorial
        return f(n) / f(r) / f(n-r)
