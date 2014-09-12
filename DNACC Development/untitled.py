import ParticlesFunction as p
import numpy as np
import os 

parameters = np.loadtxt('try.txt')

intialCondtion = np.loadtxt('dots.txt')


for i in range(parameters.shape[1]):
	for j in range(parameters.shape[1]):
		for k in range(parameters.shape[1]):
			for l in range(parameters.shape[1]):
				x = p.Particles2D(intialCondtion, parameters[0][i],parameters[1][j],parameters[2][k],parameters[3][l])
				x_max = np.max(x)
				x_min = np.min(x)
				diff = abs(x_max - x_min)
				if np.sum(x) != 0 and diff > 0.0001:
					newFileName ="/Output/" + str(i) + "_" + str(j) + "_" + str(k) + "_" + str(l) +".txt"
					z = os.getcwd()
					if not os.path.exists(os.path.dirname(z + newFileName)):
    						os.makedirs(os.path.dirname(z + newFileName))
					 	
					np.savetxt(z + newFileName, x)
					
				 
		
