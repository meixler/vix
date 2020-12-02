## vix.py
## vix.py is a python script that calculates the CBOE Volatility Index (VIX) (https://markets.cboe.com/tradable_products/vix/) according to the method described in the 
## CBOE VIX White Paper (https://cdn.cboe.com/resources/futures/vixwhite.pdf).
## This script reproduces the example in the whitepaper.
## To run, copy vixnearterm.dat and vixnextterm.dat to the same directory as vix.py, then run python3 vix.py
##
##inputs
rates=[0.000305, 0.000286] 				#risk-free interest rates (whitepaper, p5)
datafiles=['./vixnearterm.dat', './vixnextterm.dat']	#SPX Option Data Used in Sample VIX Index Calculation (whitepaper, appendix A)
verbose=0						#0 for just the result, 1 for some output, 2 for more output

import math

#get option data from vixnearterm.dat and vixnextterm.dat for options expiring on near term and next term expiration dates
quotedata=[[], []]
for j in (0,1):
	f=open(datafiles[j])
	for line in f:
		ar=[]
		for v in line.strip().split("\t"):
			ar.append(float(v))
		quotedata[j].append(ar)
	f.close()

#get minutes and years to near term and next term expiration dates (p5)
Nt=[854+510+34560, 854+900+44640]		#minutes
T=[Nt[0]/(60*24*365), Nt[1]/(60*24*365)]	#years

if(verbose>=1): 
	print('Nt:', Nt)
	print('T:', T)

#Step 1: Select the options to be used in the VIX Index calculation
#Compute F for near term and next term (p6)
F=[None, None]
for j in (0,1):
	mindiff=None
	diff=None
	mindiff=None
	Fstrike=None
	Fcall=None
	Fput=None
	for d in quotedata[j]:
		diff=abs( ((d[1]+d[2])/2) - ((d[3]+d[4])/2) )
		if(mindiff is None or diff<mindiff):
			mindiff=diff
			Fstrike=d[0]
			Fcall=(d[1]+d[2])/2
			Fput=(d[3]+d[4])/2
	F[j]=Fstrike + math.exp(rates[j]*T[j]) * (Fcall - Fput)

if(verbose>=1): print('F:', F)


#select the options to be used in the VIX Index calculation (p6,7)
selectedoptions=[[], []]
k0=[None, None]
for j in (0,1):
	i=0
	for d in quotedata[j]:
		if(d[0]<F[j]): 
			k0[j]=d[0]
			k0i=i
		i+=1

	d=quotedata[j][k0i]
	ar=[d[0], 'put/call average', (((d[1]+d[2])/2)+((d[3]+d[4])/2))/2]
	selectedoptions[j].append(ar)

	i=k0i-1
	b=True
	previousbid=None
	while(b and i>=0):
		d=quotedata[j][i]
		if(d[3]>0):
			ar=[d[0], 'put', (d[3]+d[4])/2]
			selectedoptions[j].insert(0,ar)
		else:
			if(previousbid==0): b=False
		previousbid=d[3]
		i-=1

	i=k0i+1
	b=True
	previousbid=None
	while(b and i<len(quotedata[j])):
		d=quotedata[j][i]
		if(d[1]>0):
			ar=[d[0], 'call', (d[1]+d[2])/2]
			selectedoptions[j].append(ar)
		else:
			if(previousbid==0): b=False
		previousbid=d[1]
		i+=1

if(verbose==2): 
	print('selectedoptions (near term):')
	for e in selectedoptions[0]: print('', e)
	print('selectedoptions (next term):')
	for e in selectedoptions[1]: print('', e)

#Step 2: Calculate volatility for both near-term and next-term options (p8)
for j in (0,1):
	i=0
	for d in selectedoptions[j]:
		if(i==0): 
			deltak=selectedoptions[j][1][0]-selectedoptions[j][0][0]
		elif(i==len(selectedoptions[j])-1):
			deltak=selectedoptions[j][i][0]-selectedoptions[j][i-1][0]
		else:
			deltak=(selectedoptions[j][i+1][0]-selectedoptions[j][i-1][0])/2
		contributionbystrike=(deltak/(d[0]*d[0])) * math.exp(rates[j]*T[j]) * d[2]
		selectedoptions[j][i].append(contributionbystrike)
		i+=1
if(verbose==2): 
	print('contributions by strike (near term):')
	for e in selectedoptions[0]: print('', e)
	print('contributions by strike (next term):')
	for e in selectedoptions[1]: print('', e)


aggregatedcontributionbystrike=[None, None]
for j in (0,1):
	aggregatedcontributionbystrike[j]=0
	for d in selectedoptions[j]:
		aggregatedcontributionbystrike[j]+=d[3]
	aggregatedcontributionbystrike[j]=(2/T[j])*aggregatedcontributionbystrike[j]


sigmasquared=[None, None]
for j in (0,1):
	sigmasquared[j]=aggregatedcontributionbystrike[j] - (1/T[j])*(F[j]/k0[j] -1)*(F[j]/k0[j] -1)

if(verbose): print('sigmasquared:', sigmasquared)

#Step 3: Calculate the 30-day weighted average of sigmasquared[0] and sigmasquared[1] (p9)
N30=30*1440
N365=365*1440
VIX=100 * math.sqrt( ((T[0]*sigmasquared[0])*(Nt[1]-N30)/(Nt[1]-Nt[0]) + (T[1]*sigmasquared[1])*(N30-Nt[0])/(Nt[1]-Nt[0]))*N365/N30 )

print('VIX:', VIX)

