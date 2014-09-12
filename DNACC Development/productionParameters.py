
#----------------------------------------------------------------------
# Creates a list of the paramers that can be used for the calculations
#
# 
# Author: Shawn Dion 
# Date: Feb 13, 2014
#
# 
#----------------------------------------------------------------------

import numpy as np

xsize   = 5.0
mj  	= 64

A1		= 0.4
A2		= 0.05

length  = 1.9
gamma 	= 0.4

dA1		= 0.1
dA2		= 0.2
dlength = 0.1
dgamma  = 0.1

number_of_parameters = 3
parameters   = np.zeros((4,number_of_parameters))



A1List     = [i*dA1 + A1  for i in range(0,number_of_parameters)]
A2List     = [i*dA2 + A2  for i in range(0,number_of_parameters)]
lengthList = [i*dlength + length  for i in range(0,number_of_parameters)]
gammaList  = [i*dgamma + gamma  for i in range(0,number_of_parameters)]

parameters[0][0:number_of_parameters] = A1List
parameters[1][0:number_of_parameters] = A2List
parameters[2][0:number_of_parameters] = lengthList
parameters[3][0:number_of_parameters] = gammaList

np.transpose(parameters)

np.savetxt('FirstSetAlpha-2.txt',parameters)
# for i in A1List:
# 	for j in A2List:
# 		for k in lengthList:
# 			for l in gammaList:



