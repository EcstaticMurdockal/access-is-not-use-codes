"""Targeted visual additions: policy denominators, outcome channels, sample selection."""
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from verify_models import group, use_benefit

def generate(b):
    root=Path(__file__).resolve().parent
    weights=np.linspace(0,1,161)
    gross=[];net=[];den=[];maxerr=0.
    eps=1e-6
    for w in weights:
        z=group(wL=w)
        # At zero subsidies, E_sj=n_j and E_x=c_x.
        e=np.r_[z['Es'],.25]
        n=np.r_[z['Ws'],z['Wx']]/e
        assert np.all(e>0)
        net.append(n);gross.append(n+.1);den.append(e)
        if w in (0.,.5,1.):
            for j in range(2):
                step=np.zeros(2);step[j]=eps
                plus=group(s=step,wL=w);minus=group(s=-step,wL=w)
                maxerr=max(maxerr,abs((plus['W']-minus['W'])/(2*eps)-z['Ws'][j]))
            plus=group(K=.3+eps,wL=w);minus=group(K=.3-eps,wL=w)
            maxerr=max(maxerr,abs((plus['W']-minus['W'])/(2*eps)-z['Wx']))
    assert maxerr<1e-7
    net=np.asarray(net);gross=np.asarray(gross);den=np.asarray(den)
    fig,ax=plt.subplots(figsize=(7.8,3.2),layout='constrained')
    for k,col,ls,label in [(0,b.BLUE,'-',r'Group $L$: $W_{s_L}/\mathcal{E}_{s_L}$'),
                           (1,b.ORANGE,'--',r'Group $H$: $W_{s_H}/\mathcal{E}_{s_H}$'),
                           (2,b.TEAL,'-.',r'Capacity: $W_x/\mathcal{E}_x$')]:
        ax.plot(weights,net[:,k],color=col,ls=ls,lw=2.0,label=label)
    ax.axhline(0,color=b.NAVY,lw=.7)
    ax.set(xlabel=r'Group-$L$ allocation weight $w_L$',ylabel='Net welfare per marginal public dollar',
           title='Illustrative local policy comparison on a common fiscal denominator',xlim=(0,1))
    ax.legend(frameon=False,loc='upper right',fontsize=8.5)
    ax.grid(axis='y',color='#E6EDF5',lw=.6)
    b.save(fig,'policy_returns_per_dollar')
    np.savetxt(root/'policy_returns_per_dollar.csv',np.column_stack([weights,den,net,gross]),delimiter=',',
        header='w_L,E_sL,E_sH,E_x,W_sL_per_dollar,W_sH_per_dollar,W_x_per_dollar,Gamma_L,Gamma_H,Gamma_x',comments='')

    u=np.linspace(0,3,200);z=[use_benefit(v) for v in u]
    ar=lambda key:np.array([v[key] for v in z])
    fig,axes=plt.subplots(1,3,figsize=(8.5,3.0),layout='constrained')
    axes[0].plot(u,ar('chi'),color=b.BLUE,lw=2.0)
    axes[0].set(title='(a) Effective-use probability',ylabel=r'$\chi(\upsilon)$',ylim=(0,1))
    axes[1].plot(u,ar('nu'),color=b.ORANGE,ls='--',label=r'Conditional benefit $\nu$')
    axes[1].plot(u,ar('q'),color=b.TEAL,label=r'Expected benefit $q=\chi\nu$')
    axes[1].set(title='(b) Benefit levels',ylabel='Benefit units',ylim=(0,1.25))
    axes[1].legend(frameon=False,fontsize=8,loc='lower right')
    axes[2].plot(u,ar('use_component'),color=b.BLUE,ls='--',label=r'Use channel $\chi^{\prime}\nu$')
    axes[2].plot(u,ar('conditional_benefit_component'),color=b.ORANGE,ls=':',label=r'Benefit channel $\chi\nu^{\prime}$')
    axes[2].plot(u,ar('analytical_derivative'),color=b.PURPLE,label=r'Total $q^{\prime}$')
    axes[2].set(title='(c) Marginal support response',ylabel='Benefit per unit of adequacy',ylim=(0,.5))
    axes[2].legend(frameon=False,fontsize=8,loc='upper right')
    for ax in axes:
        ax.set_xlabel(r'Support adequacy $\upsilon$');ax.set_xlim(0,3);ax.grid(axis='y',color='#E6EDF5',lw=.6)
    b.save(fig,'use_benefit_channels')
    derivative=np.array([(use_benefit(v+eps)['q']-use_benefit(v-eps)['q'])/(2*eps) for v in u])
    err=float(np.max(np.abs(derivative-ar('analytical_derivative'))));assert err<1e-8

    record=json.loads((root/'nhanes_reproduction_results.json').read_text())
    sample=record['sample_flow'];keys=list(sample)
    counts=[sample[k] for k in keys]
    assert counts==[1493,1230,205,199,197]
    labels=['Examined, age 70+','Bilateral audiometry','Current hearing device',
            'Hearing aid + valid wearing','Known test recency']
    fig,ax=plt.subplots(figsize=(9.3,2.25));ax.set(xlim=(0,10),ylim=(0,2.5));ax.axis('off')
    # Colors distinguish sequential steps, not clinical or statistical classes.
    step_fills=['#E8F2FC','#FFF0DF','#F0E9FA','#E9F6E9','#FBEAF0']
    step_edges=['#397EBA','#BD8548','#9473B7','#55925F','#B77591']
    for i,(label,n) in enumerate(zip(labels,counts)):
        x=.05+2*i
        ax.add_patch(FancyBboxPatch((x,.95),1.7,.9,boxstyle='round,pad=.02,rounding_size=.06',
            facecolor=step_fills[i],edgecolor=step_edges[i],lw=.9))
        # Wrap on deliberate word boundaries, not automatic hyphenation.
        texts=['Examined, age 70+','Complete bilateral\naudiometry','Current hearing\ndevice','Hearing aid +\nvalid wearing','Known specialist-\ntest recency']
        ax.text(x+.85,1.56,texts[i],ha='center',va='center',fontsize=9)
        ax.text(x+.85,1.15,f'n = {n:,}',ha='center',fontsize=10)
        if i<4:
            ax.annotate('',xy=(x+1.98,1.4),xytext=(x+1.74,1.4),arrowprops=dict(arrowstyle='-|>',color=b.NAVY,lw=2.0,mutation_scale=14))
            ax.text(x+1.85,.68,f'{n-counts[i+1]:,} excluded',ha='center',fontsize=9)
    ax.text(5,2.2,'NHANES analytic sample: sequential restrictions, not causal transitions',ha='center',fontsize=11)
    ax.text(5,.18,'Unweighted counts; survey weights are used for prevalence and regression estimates.',ha='center',fontsize=9)
    b.save(fig,'nhanes_sample_flow')
    (root/'visual_additions_validation.json').write_text(json.dumps(dict(
        max_policy_derivative_error=maxerr,max_use_benefit_derivative_error=err,
        minimum_fiscal_denominator=float(den.min()),sample_counts=counts,
        policy_parameters=dict(K=.3,s=[0,0],eta=.5,lam=.1,cx=.25,need=[1,1]),
        interpretation='Illustrative policies and outcome functions; NHANES counts are descriptive.'),indent=2))
