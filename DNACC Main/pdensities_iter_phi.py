import numpy as np
import matplotlib.pyplot as plt
import scipy as sci
import math as m
import time

#------------------------------------------------------------
# Initialize the Variables
#------------------------------------------------------------
t1 = time.clock()
fa = 0.333
alpha = 1
fb = 0.333
fc  = 1 - fb - fa

incompresibilityFactor 	= [10,100 ,1000]# Default 1850, 2050 [10 100 1000]
mixParameter 			= [0.01, 0.005, 0.0005] #[0.01 0.005 0.0005]

number_of_iterations 			= 100000 	# Default 30000
tolerence 						= 10**(-7) 	# the tolerence 
number_of_lattice_points 		= 64       	# number of latice points for the j direction
half_number_of_lattice_points 	= number_of_lattice_points/2    	# the halfway point in the lattice
xsize 							= 15.0    								#  
dx 								= xsize/number_of_lattice_points
xxs 							= [i*dx - xsize/2.0 for i in range(0,number_of_lattice_points)]


Vab = np.zeros(number_of_lattice_points )
Vac = np.zeros( number_of_lattice_points )
Vbc = np.zeros( number_of_lattice_points )


A1 = 110.0 #4
A2 = 0.0 #0.30
length = 0.001

halfWidthHalfMinimum = 0.65 #0.45
gamma = halfWidthHalfMinimum/(m.sqrt(2*m.log(2)))

for j in range(0,number_of_lattice_points):
	r = abs(xxs[j])
	if r <= length:
		Vab[j]= (A1+A2)*(m.cos((sci.pi)*r/length))/2.0 + (A1 - A2)/2.0
		Vac[j]= (A1+A2)*(m.cos(sci.pi*r/length))/2.0 + (A1 - A2)/2.0
		Vbc[j]= (A1+A2)*(m.cos(sci.pi*r/length))/2.0 + (A1 - A2)/2.0

	else:
		Vab[j] = -A2*(m.exp(-(r-length)))**2.0/(2.0*gamma**2.0)
		Vac[j] = -A2*(m.exp(-(r-length)))**2.0/(2.0*gamma**2.0)
		Vbc[j] = -A2*(m.exp(-(r-length)))**2.0/(2.0*gamma**2.0)
	


#Vac = np.roll(Vac, half_number_of_lattice_points)
#Vab = np.roll(Vab, half_number_of_lattice_points)
#Vbc = np.roll(Vbc, half_number_of_lattice_points)


Vkab = (np.fft.rfft(Vab))/float(number_of_lattice_points)
Vkac = (np.fft.rfft(Vac))/float(number_of_lattice_points)
Vkbc = (np.fft.rfft(Vbc))/float(number_of_lattice_points)


std = 0.15;
phia = fa + std*np.random.randn(number_of_lattice_points)

phib = fb + std*np.random.randn(number_of_lattice_points)

phic = 1 - phia - phib

phia1 = phia;
phib1 = phib;
phic1 = phic; 

g = 0
for i in range(0,3):
    for j in range(0, number_of_iterations):
        iphia = np.fft.rfft(phia)
        iphib = np.fft.rfft(phib)
        iphic = np.fft.rfft(phic)

        cnva  = iphia*Vkac
        cnvac = iphic*Vkac

        cnvb  = iphib*Vkab
        cnvba = iphia*Vkab

        cnvc  = iphic*Vkbc
        cnvcb = iphib*Vkbc

        icnva = xsize*np.fft.irfft(cnva)
        icnvb = xsize*np.fft.irfft(cnvb)
        icnvc = xsize*np.fft.irfft(cnvc)

        icnvba = xsize*np.fft.irfft(cnvba)
        icnvac = xsize*np.fft.irfft(cnvac)
        icnvcb = xsize*np.fft.irfft(cnvcb)

        #self conistent equations
        wa =  icnvba + icnva - incompresibilityFactor[i]*(  1  - phia - phib - phic)
        wb =  icnvcb + icnvb - incompresibilityFactor[i]*(  1  - phia - phib - phic)
        wc =  icnvac + icnvc - incompresibilityFactor[i]*(  1  - phia - phib - phic)

        ewa = np.exp(-wa)
        ewb = np.exp(-wb)
        ewc = np.exp(-wc)

        QA = dx*np.sum(ewa)

        if m.isnan(QA):
            print "this is bad"

        QB = dx*np.sum(ewb)
        QC = dx*np.sum(ewc)

        phiatemp = fa*xsize*ewa/QA
        phibtemp = fb*xsize*ewb/QB
        phictemp = fc*xsize*ewc/QC

        phiaave = fa - dx*np.sum(phiatemp)/xsize
        phibave = fb - dx*np.sum(phibtemp)/xsize
        phicave = fc - dx*np.sum(phictemp)/xsize

        phianew = phiatemp + phiaave
        phibnew = phibtemp + phibave
        phicnew = phictemp + phicave

        phia = mixParameter[i]*phianew + (1 - mixParameter[i])*phia
        phib = mixParameter[i]*phibnew + (1 - mixParameter[i])*phib
        phic = mixParameter[i]*phicnew + (1 - mixParameter[i])*phic

        dev = phianew - phia
        dev2 = dev * dev
        norm = np.sum(phianew * phianew)
        phidev = np.sum(dev2)/norm
        g = g + 1

        if phidev < tolerence:
            break


t2 = time.clock()


print t2 - t1

plt.plot(xxs,phia)
plt.plot(xxs,phib,'r')
plt.plot(xxs,phic,'g')
plt.plot(xxs, phia + phib+ phic,'k--')
#plt.axis([-8 ,8 , 1.0])

plt.show()



			

