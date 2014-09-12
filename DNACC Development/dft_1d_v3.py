# Solve two species phi fixed point equation.

from __future__ import division,print_function
from numpy import log, cos, pi, exp, linspace, piecewise, ones, roll, save, load
from numpy.random import rand, seed
from numpy.fft import rfft, irfft
from pylab import plot, xlabel, ylabel, show, legend
from sys import exit

# Computational inputs
mj = 2048   # Need an even value please (for convenience in defining potential).
smallmix = 0.01  # Try using two orders of magnitude smaller than alpha (1/ialpha).
bigmix = 0.1        # Occasional big mixing step.
mix = smallmix
maxcount = 5 #5               # Minimum frequency for trying a big step.
perc = 0.1          # Percent deviation for trying a big step.
maxit = 100000        # Maximum allowed iterations.
mindev = 1.0e-4     # Convergence criterion.
his = 5             # Number of past deviations to remember.
sd = 2            # Random seed.

# Physical inputs
lngth = 15.0
kappa = 1.0e2 # Try setting to two orders of magnitude larger than largest ialpha.
kneg = 0.0
ialphaa = 1.0     # 1/alphaa and...
ialphab = 1.0e6     # ...1/alphab.
a1 = 0.350
a2 = 0.350
lmbda = 2.0
gmma = 0.5
fa = 0.5
fb = 1.0-fa

# Define potential form
dx  = lngth/mj
x   = linspace(0.0,lngth-dx,mj)
xx  = x-0.5*lngth


Uab = piecewise(xx,[abs(xx)<=lmbda, abs(xx)>lmbda], [lambda r: 0.5*(a1+a2)*cos(pi*r/lmbda) + 0.5*(a1-a2), lambda r: -a2*exp(-((abs(r)-lmbda)**2.0)/(2.0*gmma**2.0))])


#plot(xx,Uab,'.-')
#show()
Uab = roll(Uab,int(mj/2))
#plot(x,Uab,'.-')
#show()
iUab = rfft(Uab)/mj
# Set initial volume fraction profiles
seed(sd)
phia = fa-0.1*rand(mj)+0.1
#phia = 0.01*ones(mj)
#phia = load('phia.npy')

devtot = 100.0*ones(his)         # Initialize some variables.
count = 0

# Do the actual computation
for n in range(maxit):
    lgaterm = -ialphaa*log(phia/fa)
    lgbterm = ialphab*log((1.0-phia)/fb)
    iphia = rfft(phia-fa)
    iftterm = iphia*iUab
    ftterm = lngth*irfft(iftterm)
    kpterm = kappa*(fa-sum(phia)/mj)
    phianew = (lgaterm+lgbterm+2.0*ialphaa*ialphab*ftterm+kpterm)

    dev = phianew            # L2 norm deviation.
    dev2 = sum(phianew**2)
    norm = sum(phia**2)
    devtot = roll(devtot,1)
    devtot[0] = dev2/norm
    perdev = sum(abs(devtot))/his
    perdev = abs(100.0*(perdev-devtot[0])/perdev)   # % change in deviation.
    
    if (perdev<perc and count>maxcount):
        mix = bigmix        # Try a big step
        count = 0
        print('Big!')
    else:
        mix = smallmix      # Stick with small step.
        count = count+1
        
    #print(n+1, devtot[0], perdev)    # Iteration output.
    if (devtot[0] < mindev):
        break
    phia = phia+mix*phianew/ialphab
    phia[phia<0.0] = 1.0e-12    # Set negative densities to (near) zero.
    phia[phia>1.0] = 0.999999999999   # Set too big densities to (near) one.

phib = 1.0-phia
phiaave = sum(phia)/mj
phibave = sum(phib)/mj

# Outputs
#print(phiaave, phibave, phiaave+phibave)
save('phia',phia)
plot(x,phia,'.-')
plot(x,phib,'.-')

show()

# Issues:

# It works! I can converge ialpha=1e6 to less than 1e-8, with no end in sight.
# Perhaps Anderson mixing would be effective at this stage?
# Perhaps the old SCFT method would also work for limited Uab?
#
# I can get higher segregations, where phib hits 1.0, for ialpha = 1.0.
# I manage it by reducing mix to 0.001 when phib starts to touch 1.0.
# But for ialpha = 1e6, I'm having trouble with higher segregations.
#
# The technique that I used was: I chose a1,a2 such that the system converged at
# mix=0.01 quickly. The result was that it was very close to uniform. Then, I
# increased a1,a1 so the system would uncoverge. I varied a1,a2 until the
# convergence was near 0 change. Then, I increased a1,a2 and unconverged to get
# a well segregated structure, and changed a1,a2 to the 0 converging values.
# Then I used bigmixing of 0.1-1.0 with smallmix = 0.01 to power converge
# to the solution.

