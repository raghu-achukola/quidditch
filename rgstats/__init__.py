import random as rand
import numpy 
import scipy
import pandas as pd
import matplotlib.pyplot as plt
from itertools import compress

def lsrNormalEquations(x,y):
    if(x.ndim==1):
        n =1
        m = len(x)
        x = x.reshape((m,1))
    else:
        m = len(x)
        n = len(x.T)
    xprime = numpy.hstack((numpy.ones((m,1)),x))
    return (numpy.linalg.pinv(xprime.T.dot(xprime)).dot(xprime.T).dot(y))

def kmeans(x,y,k,iter):
	centers = [(rand.uniform(min(x),max(x)),rand.uniform(min(y),max(y))) for _ in range(k)]

	for _ in range(iter):
		closest = [nearest_euclidean((x[i],y[i]),centers) for i in range(len(y))]
		for i in range(k):
			fil = closest == [i]*len(y)
			xval = list(compress(x,fil))
			yval = list(compress(y,fil))
			centers[i]  = (average(xval),average(yval))
	return (closest,centers)

def nearest_euclidean(point, cts):
	m = float('inf')
	index_m = -1
	for i in range(len(cts)): 
		c = euclidean_metric(point,cts[i])
		if m > c: 
			index_m = i
			m = c
	return index_m
	
def euclidean_metric(p1,p2):
	return (p2[0]-p1[0])**2 + (p2[1]-p1[1])**2

def velocity_verlet(x0,v0,h,func,val,t0,tmax):
	t=numpy.arange(t0,tmax,h)
	x = [x0]
	v = [v0]
	for _ in t:
		a = func(x[-1])
		x.append(x[-1]+v[-1]*h+h*h*a/2)
		v.append(v[-1]+(a+func(x[-1]))*h/2)
	return (t,x,v)
def moods_median(vecs):
	num = len(vecs)
	pooled = numpy.concatenate(vecs)
	pooled_median = numpy.median(pooled)
	# len([d for d in ])
	#maces = []
	#for vec in vecs:
	#	maces.append(numpy.array((sum(1 for d in vec if d>=pooled_median),sum(1 for d in vec if d<=pooled_median))).reshape(2,1))
	maces = [numpy.array((sum(1 for d in vec if d>pooled_median),sum(1 for d in vec if d<=pooled_median))).reshape(2,1) for vec in vecs]
	table = numpy.hstack(maces)
	chisq,p,df,arr = scipy.stats.chi2_contingency(table.tolist(),correction=False)
	return (chisq,p,df,table.tolist())
def normalize(df):
	rows, cols  = df.shape
	for num in range(cols):
		col = df[num]
		df[num] = (col - numpy.mean(col))/numpy.std(col)
	return df