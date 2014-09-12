import ParticlesFunctionSCFT as p
import numpy as np
import os 



alphaA = [1, 0.1, 0.01, 0.001, 0.0001, 0.00001, 0.000001]
intialCondtion = np.loadtxt('dots.txt')


A1		= [0.9 , 0.4, 0.2, 0.15, 0.1, 0.08]
A2		= [0.2, 0.17, 0.13, 0.09, 0.07,0.03] 

length  = 1.9
gamma 	= 0.4

dA1		= [0.1, 0.01, 0.01, 0.01, 0.01, 0.01]
dA2		= [0.1, 0.01, 0.01, 0.01, 0.01, 0.01]
dlength = 0.1
dgamma  = 0.1


for t in range(0,6):


	number_of_parameters = 3
	parameters   = np.zeros((4,number_of_parameters))

	A1List     = [i*dA1[t] + A1[t]  for i in range(0,number_of_parameters)]
	A2List     = [i*dA2[t] + A2[t]  for i in range(0,number_of_parameters)]
	lengthList = [i*dlength + length  for i in range(0,number_of_parameters)]
	gammaList  = [i*dgamma + gamma  for i in range(0,number_of_parameters)]

	parameters[0][0:number_of_parameters] = A1List
	parameters[1][0:number_of_parameters] = A2List
	parameters[2][0:number_of_parameters] = lengthList
	parameters[3][0:number_of_parameters] = gammaList

	np.transpose(parameters)




	for i in range(parameters.shape[1]):
		for j in range(parameters.shape[1]):
			for k in range(parameters.shape[1]):
				for l in range(parameters.shape[1]):
					x = p.Particles2DSCFT(intialCondtion, parameters[0][i],parameters[1][j],parameters[2][k],parameters[3][l], 0.5,  alpha)
					x_max = np.max(x)
					x_min = np.min(x)
					diff = abs(x_max - x_min)
					if np.sum(x) != 0 and diff > 0.01:
						newFileName ="/OutputSCFT" + str(t) +"/" + str(i) + "_" + str(j) + "_" + str(k) + "_" + str(l) +".txt"
						z = os.getcwd()
						if not os.path.exists(os.path.dirname(z + newFileName)):
	    						os.makedirs(os.path.dirname(z + newFileName))
						
						np.savetxt(z + newFileName, x)
						
					 
			
