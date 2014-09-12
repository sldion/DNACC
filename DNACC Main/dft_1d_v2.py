# Solve two species phi fixed point equation.

from __future__ import division,print_function
from numpy import * #log, cos, pi, exp, linspace, piecewise, ones, roll, save, load
from numpy import zeros
from numpy.random import rand, seed
from numpy.fft import rfft, irfft
from numpy.linalg import solve
from pylab import plot, xlabel, ylabel, show, figure
from sys import exit

# Computational inputs
mj = 264   # Need an even value please (for convenience in defining potential).
smallmix = 0.0001  # Try using two orders of magnitude smaller than alpha (1/ialpha).
bigmix = 0.11        # Occasional big mixing step.
mix = smallmix
perc = 0.1          # Percent deviation for trying a big step.
maxit = 5000        # Maximum allowed iterations.
mindev = 1.0e-4     # Convergence criterion.
his = 5             # Number of past deviations to remember.
sd = 2            # Random seed.

# Physical inputs
lngth = 20.0
kappa = 1.0e4   # Try setting to two orders of magnitude larger than largest ialpha.
ialphaa = 1.0   # 1/alphaa and...
ialphab = 1.0  # ...1/alphab.
a1 = 10.0
a2 = 0.0
lmbda = 6.0
gmma = 0.5
fa = 0.5
fb = 1.0-fa

# Define potential form
dx = lngth/mj
x = linspace(0.0,lngth-dx,mj)
xx = x-0.5*lngth
Uab = 2.0*ialphaa*ialphab*piecewise(xx,[abs(xx)<=lmbda, abs(xx)>lmbda], [lambda r: 0.5*(a1+a2)*cos(pi*r/lmbda)+0.5*(a1-a2), lambda r: -a2*exp(-((abs(r)-lmbda)**2)/(2.0*gmma**2))])
#plot(xx,Uab,'.-')
#show()
Uab = roll(Uab,int(mj/2))
#plot(x,Uab,'.-')
#show()
iUab = rfft(Uab)/mj

# Set initial volume fraction profiles
seed(sd)
phia = rand(mj)
#phia = ones(mj)
#phia = load('phia.npy')

devtot = 100.0*ones(his)         # Initialize some variables.
count = 0
divergence = []
steps = []
i = 0
# Do the actual computation
for n in range(maxit): 

	lgaterm = -ialphaa*log(phia/fa)
	lgbterm = ialphab*log((1.0-phia)/fb)
	iphia = rfft(phia-fa)
	iftterm = iphia*iUab
	ftterm = lngth*irfft(iftterm)
	kpterm = kappa*(fa-sum(phia)/mj)
	phianew = phia+lgaterm+lgbterm+ftterm+kpterm
	phianew[phianew < 0] = 0.01
	phianew[phianew > 1] = 1.0
	dev = phianew-phia        # L2 norm deviation.
	phia = mix*phianew+(1.0-mix)*phia   # Picard iteration.
 
	dev2 = sum(dev**2)  
	norm = sum(phianew**2)
	devtot = roll(devtot,1)     # Remember previous deviations.
	devtot[0] = dev2/norm
	perdev = sum(abs(devtot))/his
	perdev = abs(100.0*(perdev-devtot[0])/perdev)   # % change in deviation.
	if (perdev<perc and count>100):
		mix = bigmix        # Try a big step
		count = 0
		print('Big!')
	else:
		mix = smallmix      # Stick with small step.
		count = count+1
	divergence.append(devtot[0])    
	steps.append(i)
	i = i + 1
	print(n, devtot[0], perdev)    # Iteration output.
	if (devtot[0]<mindev):
		break

phib = 1.0-phia
phiaave = sum(phia)/mj
phibave = sum(phib)/mj

# Outputs
#print(phiaave, phibave, phiaave+phibave)
print (phia)
save('phia',phia)
plot(x,phia,'.-')
plot(x,phib,'.-')

fig2 = figure(2)
plot(steps, divergence)
show()

# Tips:
#
# Averaging over the unstable box solutions seems to give the same answer as
# many stable steps! So, use the unstable convergence followed by fewer
# slow stable small mixing steps. Speed the slow part by taking occasional large
# steps when the percentage deviation change becomes low, then burn off the
# rounding error to (hopefully) get faster convergence.
#
# Comparisons:
# Using just small steps (0.0001) converges below only 0.3 in 5500 iterations.
# Adding occasional big steps (0.1) to this is unstable (loses solution).
# Box averaging for 500 steps followed by just small steps converges below
# 10^-3 in 5000 (+500) steps.
# Box averaging for 500 steps followed by small with occasional big steps converges 
# to below 10^-4 in under 4000 (+500) iterations.
#
# For larger mj (4096 or bigger), iterate with smaller mix for a while until stable, then switch
# back to 0.01 for a few hundred iterations more.

