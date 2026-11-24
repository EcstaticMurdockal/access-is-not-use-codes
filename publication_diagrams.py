"""Exact vector diagrams and additional illustrative plots; no empirical fitting."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from scipy.optimize import brentq

def generate(b):
    navy,blue,green,orange,purple=b.NAVY,b.BLUE,b.TEAL,b.ORANGE,b.PURPLE
    # Two reproducible additions using the manuscript's illustrative benchmark.
    fig,axes=plt.subplots(1,2,figsize=(7.8,3.1),layout='constrained')
    n=np.linspace(.15,.999,400)
    for K,c,ls in [(1,blue,'-'),(1.3,green,'--')]:
        axes[0].plot(n,(1-n)*(.2+np.sqrt(K/n)),color=c,ls=ls,label=fr'$K={K:g}$')
    axes[0].axhline(.5,color=orange,lw=1,ls=':',label=r'$p-s=0.5$')
    for K,c in [(1,blue),(1.3,green)]:
        root=brentq(lambda z:(1-z)*(.2+np.sqrt(K/z))-.5,.01,.999)
        assert abs((1-root)*(.2+np.sqrt(K/root))-.5)<1e-10
        axes[0].scatter(root,.5,s=22,color=c,zorder=3)
    axes[0].set(xlabel=r'Adopter mass $N$',ylabel='Marginal willingness to pay',title='(a) Equilibrium intersection',ylim=(0,1.8))
    axes[0].legend(frameon=False,fontsize=9)
    ks=np.linspace(1,1.6,100);ns=np.array([brentq(lambda z:(1-z)*(.2+np.sqrt(k/z))-.5,.01,.999) for k in ks]);n0=ns[0]
    axes[1].plot(ks,ks/ns,color=green,label='With induced adoption')
    axes[1].plot(ks,ks/n0,color=blue,ls='--',label='Holding adoption fixed')
    axes[1].set(xlabel=r'Capacity $K$',ylabel=r'Support intensity $h$',title='(b) Entry absorbs part of expansion')
    axes[1].legend(frameon=False,fontsize=9)
    for ax in axes:ax.grid(axis='y',color='#E6EDF5',lw=.6)
    b.save(fig,'equilibrium_capacity_feedback')

    fig,axes=plt.subplots(1,2,figsize=(7.8,3.1),layout='constrained')
    requests=np.linspace(0,2,301)
    axes[0].plot(requests,requests,color=blue,ls='--',label='Requested')
    axes[0].plot(requests,np.minimum(requests,1),color=green,label='Delivered: '+r'$K=1$')
    axes[0].axvline(1,color=b.GREY,ls=':',lw=.8)
    axes[0].set(xlabel=r'Requested service $\mathcal{R}$',ylabel='Effective service units',title='(a) Requests at fixed capacity')
    k=np.linspace(.2,2,300)
    axes[1].plot(k,np.minimum(1.5,k),color=green,label=r'$Y=\min\{1.5,K\}$')
    axes[1].plot(k,np.maximum(1.5-k,0),color=orange,ls='--',label='Unmet requests')
    axes[1].set(xlabel=r'Capacity $K$',ylabel='Effective service units',title='(b) Capacity at fixed requests')
    for ax in axes:ax.grid(axis='y',color='#E6EDF5',lw=.6);ax.legend(frameon=False,fontsize=9)
    b.save(fig,'requested_delivered_capacity')
