import numpy as np
import matplotlib as plt
import scipy.ndimage.filters as snf

def majorityPlot(phia, phib ,phic, volumeFractions = []):
	temp1 = phia
	temp2 = phib
	temp3 = phic

	temp1[temp1 > volumeFractions[0]] 							= 0
	temp1[temp1 < volumeFractions[0]] 							= 0
	temp2[temp2 > volumeFractions[1]] 							= 1
	temp2[temp2 < volumeFractions[1]] 						   	= 0
	temp3[temp3 > (1 - volumeFractions[0] - volumeFractions[1])] 	= 2
	temp3[temp3 < (1 - volumeFractions[0] - volumeFractions[1])] 	= 0

	majorityPlot = temp1 + temp2 + temp3

	majorityPlot[majorityPlot == 6] = 1
	majorityPlot[majorityPlot == 5] = 2
	majorityPlot[majorityPlot == 3] = 1.5

	majorityPlot = snf.uniform_filter(majorityPlot, mode = "wrap")

	majorityPlot[majorityPlot < 0] = 0

	return majorityPlot
