"""Reproduce the illustrative calculations; no clinical parameter estimates."""
from pathlib import Path
import json,csv
import numpy as np
from scipy.optimize import brentq, minimize_scalar
ROOT=Path(__file__).resolve().parent

def baseline(s=0.,K=1.):
    q=lambda h:.2+np.sqrt(h)
    n=1. if s>=.5 else brentq(lambda n:(1-n)*q(K/n)-(.5-s),1e-12,1.)
    h=K/n; qp=.5/np.sqrt(h); H=q(h)+(1-n)*h*qp/n
    C=h*qp*(1-n/2); rho=C/.5; delta_F=n*H/.5
    return dict(N=n,h=h,rho=rho,delta_F=delta_F,
                eta_c=(rho+.1*delta_F)/(1-rho))

def group(s=(0.,0.),K=.3,wL=.2,need=(1.,1.),eta=.5,lam=.1,cx=.25):
    s=np.array(s); m=np.array([.5,.5]); w=np.array([wL,1.]); rneed=np.array(need,dtype=float)
    a=np.array([.8,.2]); b=np.array([.2,1.]); p=np.array([.5,.5])
    if np.any(rneed<=0): raise ValueError("support requirements must be positive")
    def at(h):
        q=a+b*(-np.expm1(-w*h/rneed)); t=np.clip((p-s)/q,0,1); n=m*(1-t)
        return q,t,n
    hi=1.
    while hi*np.dot(w,at(hi)[2])<K:hi*=2
    h=brentq(lambda z:z*np.dot(w,at(z)[2])-K,0,hi,xtol=1e-13)
    q,t,n=at(h); D=w@n; M=m*(1-t*t)/2; qp=b*(w/rneed)*np.exp(-w*h/rneed); S=M@qp
    # Local derivatives use only active interior groups. At a cutoff exactly
    # on the support endpoint derivatives are directional, not two-sided.
    raw_t=(p-s)/q
    active=(raw_t>0)&(raw_t<1)
    A=np.where(active,m/q,0.); B=A*t*qp; L=D+h*(w@B)
    dhds=-h*w*A/L; dns=np.diag(A)+np.outer(B,dhds); dnK=B/L
    C=w*h*S/D; J=(1+eta)*(t*q-C)-p-lam*s
    Ws=J@dns-lam*n
    Es=n+s@dns
    Vs=Ws+lam*Es
    Gamma=np.divide(Vs,Es,out=np.full_like(Vs,np.nan),where=Es>0)
    Wx=(1+eta)*S/D+J@dnK-(1+lam)*cx
    E=s@n+cx*(K-.3); W=(1+eta)*(M@q)-p@n-cx*(K-.3)-lam*E
    V=W+lam*E
    return dict(n=n,h=h,q=q,C=C,dns=dns,Es=Es,Vs=Vs,Gamma=Gamma,
                Ws=Ws,Wx=Wx,V=V,W=W,E=E,D=D)

def stock_flow(s=.05,K=.3,incumbent=.25,wA=1.,wL=.3,m=.5,p=.5,
               exit_rate=.1,persist=.8,incumbent_mean_value=.7):
    """One-group quasi-static stock-flow check; all values are illustrative."""
    if min(K,wA,m,p) <= 0 or min(incumbent,wL,exit_rate,persist) < 0:
        raise ValueError("stock-flow primitives outside the maintained domain")
    if exit_rate > 1 or persist > 1:
        raise ValueError("transition probabilities must not exceed one")
    def at(h):
        q=.4+.6*(-np.expm1(-h))
        t=np.clip((p-s)/q,0,1)
        adoption=m*(1-t)
        return q,t,adoption
    hi=1.
    while hi*(wA*at(hi)[2]+wL*incumbent)<K: hi*=2
    h=brentq(lambda z:z*(wA*at(z)[2]+wL*incumbent)-K,0,hi,xtol=1e-13)
    q,t,adoption=at(h); qp=.6*np.exp(-h)
    D=wA*adoption+wL*incumbent
    active=0 < (p-s)/q < 1
    direct=m/q if active else 0.; response=direct*t*qp
    denominator=D+h*wA*response
    dhds=-h*wA*direct/denominator
    dads=direct+response*dhds
    dhdK=1/denominator
    M_A=m*(1-t*t)/2
    M_L=incumbent*incumbent_mean_value
    S=(M_A+M_L)*qp
    C_A=h*wA*S/D
    next_incumbent=(1-exit_rate)*incumbent+persist*adoption
    return dict(A=adoption,L=incumbent,h=h,D=D,dhds=dhds,dAds=dads,
                dhdK=dhdK,C_A=C_A,L_next=next_incumbent,
                phase_weight_ratio=wA/wL if wL>0 else None)

def device_age_aggregation(first_entry=.08,stock=(.24,.20,.16,.12),
                           refit=(.01,.03,.08,.35),exit_rate=(.03,.04,.05,.08),
                           w_first=1.15,w_refit=1.25,w_maint=(.45,.35,.28,.22),
                           retain_first=.85,retain_refit=.90):
    """Check exact aggregation of first fitting, refitting, and device-age stock.

    Values are illustrative accounting inputs, not estimated transition hazards.
    Refitted users are assigned to the refitting flow and are not simultaneously
    counted in routine maintenance during the policy period.
    """
    stock=np.asarray(stock,dtype=float); refit=np.asarray(refit,dtype=float)
    exit_rate=np.asarray(exit_rate,dtype=float); w_maint=np.asarray(w_maint,dtype=float)
    if not (stock.shape==refit.shape==exit_rate.shape==w_maint.shape):
        raise ValueError("device-age vectors must have the same shape")
    if first_entry<0 or min(w_first,w_refit,retain_first,retain_refit)<0:
        raise ValueError("device-age primitives must be nonnegative")
    if np.any(stock<0) or np.any(refit<0) or np.any(exit_rate<0) or np.any(w_maint<0):
        raise ValueError("device-age vectors must be nonnegative")
    if np.any(refit+exit_rate>1) or retain_first>1 or retain_refit>1:
        raise ValueError("transition probabilities lie outside the maintained domain")
    replacement=float(refit@stock)
    maintenance_stock=(1-refit)*stock
    direct_load=(w_first*first_entry+w_refit*replacement+
                 float(w_maint@maintenance_stock))
    current_fittings=first_entry+replacement
    active_maintenance=float(maintenance_stock.sum())
    wA=(w_first*first_entry+w_refit*replacement)/current_fittings if current_fittings else None
    wL=float(w_maint@maintenance_stock)/active_maintenance if active_maintenance else None
    aggregate_load=((wA*current_fittings if wA is not None else 0.)+
                    (wL*active_maintenance if wL is not None else 0.))
    next_by_age=np.zeros_like(stock)
    next_by_age[0]=retain_first*first_entry+retain_refit*replacement
    next_by_age[1:]=(1-exit_rate[:-1]-refit[:-1])*stock[:-1]
    identity_error=abs(direct_load-aggregate_load)
    return dict(first_entry=first_entry,replacement_flow=replacement,
                maintenance_stock=active_maintenance,w_first=w_first,w_refit=w_refit,
                aggregate_wA=wA,aggregate_wL=wL,direct_load=direct_load,
                aggregate_load=aggregate_load,aggregation_identity_error=identity_error,
                next_stock_by_age=next_by_age)

def policy_tools(sR=.2,IR=0.,capacity0=.30,n=(.30,.25),
                 request0=(1.0,.50),elasticity=(.60,.60)):
    """Requested versus delivered support under proportional fulfilment.

    All primitives are illustrative.  sR lowers a normalized service price;
    exp(elasticity*sR) is used only to obtain a smooth positive request curve.
    """
    n=np.asarray(n,dtype=float); request0=np.asarray(request0,dtype=float)
    elasticity=np.asarray(elasticity,dtype=float)
    if np.any(n<0) or np.any(request0<0) or np.any(elasticity<0):
        raise ValueError("policy-tool primitives must be nonnegative")
    d=request0*np.exp(elasticity*sR)
    R=float(n@d); K=capacity0+IR  # linear normalization x_R=Phi(I_R)=I_R
    mu=min(1.,K/R) if R>0 else 1.
    y=mu*d; Y=float(n@y)
    return dict(d=d,R=R,K=K,mu=mu,y=y,Y=Y,unmet=R-Y,
                service_subsidy_spending=sR*Y)

def device_policy_episode_flows(s_first=.10,s_replace=.12,capacity=.30,
                                first_mass=.24,first_index=-.8,first_slope=2.0,
                                stock=(.24,.20,.16,.12),
                                base_refit=(.01,.03,.08,.35),refit_slope=1.4,
                                request_first=1.15,request_refit=1.25,
                                request_maint=(.45,.35,.28,.22)):
    """First-entry and replacement subsidy accounting.

    Smooth response curves are illustrative only.  The check verifies that a
    refitting subsidy moves an incumbent from maintenance into refitting, so
    the incremental requested load is d_R-d_L rather than the full d_R.
    """
    stock=np.asarray(stock,dtype=float)
    base_refit=np.asarray(base_refit,dtype=float)
    request_maint=np.asarray(request_maint,dtype=float)
    if not (stock.shape==base_refit.shape==request_maint.shape):
        raise ValueError("episode vectors must have the same shape")
    if np.any(stock<0) or np.any(base_refit<=0) or np.any(base_refit>=1):
        raise ValueError("stock must be nonnegative and baseline hazards interior")
    logistic=lambda z:1/(1+np.exp(-z))
    first_rate=logistic(first_index+first_slope*s_first)
    first_entry=first_mass*first_rate
    dfirst=first_mass*first_slope*first_rate*(1-first_rate)
    refit_logit=np.log(base_refit/(1-base_refit))+refit_slope*s_replace
    rho=logistic(refit_logit)
    drho=refit_slope*rho*(1-rho)
    replacement=float(stock@rho)
    maintenance=(1-rho)*stock
    requested=(request_first*first_entry+request_refit*replacement+
               float(request_maint@maintenance))
    drequested_first=request_first*dfirst
    drequested_replace=float(((request_refit-request_maint)*stock)@drho)
    delivered=min(requested,capacity)
    spending=s_first*first_entry+s_replace*replacement
    dspending_first=first_entry+s_first*dfirst
    dspending_replace=replacement+s_replace*float(stock@drho)
    return dict(first_entry=first_entry,replacement_flow=replacement,
                maintenance_stock=float(maintenance.sum()),requested=requested,
                delivered=delivered,device_spending=spending,
                drequested_first=drequested_first,
                drequested_replace=drequested_replace,
                dspending_first=dspending_first,
                dspending_replace=dspending_replace,
                refit_hazards=rho)

def use_benefit(upsilon=.8):
    """Illustrative decomposition q=chi*nu; not a clinical calibration."""
    chi=lambda z:.35+.55*(-np.expm1(-.8*z))
    nu=lambda z:.45+.75*(-np.expm1(-.6*z))
    chip=lambda z:.44*np.exp(-.8*z)
    nup=lambda z:.45*np.exp(-.6*z)
    use_component=chip(upsilon)*nu(upsilon)
    benefit_component=chi(upsilon)*nup(upsilon)
    return dict(upsilon=upsilon,chi=chi(upsilon),nu=nu(upsilon),q=chi(upsilon)*nu(upsilon),
                use_component=use_component,
                conditional_benefit_component=benefit_component,
                analytical_derivative=use_component+benefit_component)

def use_benefit_externality(h=.8,entrant_weight=.6,D=.5):
    """Two-group channel identity for C_j; illustrative, not calibrated."""
    M=np.array([.28,.19])
    c0=np.array([.35,.28]); c1=np.array([.55,.62]); a=np.array([.8,.55])
    v0=np.array([.45,.38]); v1=np.array([.75,.82]); b=np.array([.6,.72])
    chi=lambda z:c0+c1*(-np.expm1(-a*z))
    nu=lambda z:v0+v1*(-np.expm1(-b*z))
    chip=lambda z:c1*a*np.exp(-a*z)
    nup=lambda z:v1*b*np.exp(-b*z)
    scale=h*entrant_weight/D
    use_channel=scale*float(M@(chip(h)*nu(h)))
    benefit_channel=scale*float(M@(chi(h)*nup(h)))
    return dict(h=h,entrant_weight=entrant_weight,D=D,
                use_channel=use_channel,
                conditional_benefit_channel=benefit_channel,
                total_externality=use_channel+benefit_channel,
                aggregate_value=float(M@(chi(h)*nu(h))))

def capped_benchmark(s=0.,K=.8,hbar=1.,p=.5):
    """Homogeneous slack/binding bridge; all values are illustrative."""
    q=lambda h:.2+np.sqrt(h)
    def at(n):
        h=min(hbar,K/n)
        return h,q(h)
    if s>=p:
        n=1.
    else:
        n=brentq(lambda z:(1-z)*at(z)[1]-(p-s),1e-12,1.,xtol=1e-14)
    h,qv=at(n); requested=n*hbar; delivered=min(requested,K)
    regime='slack' if requested<K-1e-10 else ('binding' if requested>K+1e-10 else 'boundary')
    return dict(N=n,K=K,hbar=hbar,h=h,q=qv,R=requested,Y=delivered,
                utilization=delivered/K,regime=regime)

def group_random_stress_check(attempts=1000,seed=20261123,eps=1e-6):
    """Stress-test Proposition 3 only where both group cutoffs are interior.

    Corner solutions are intentionally skipped because the displayed analytical
    derivatives are interior comparative statics.  The seed makes the audit
    exactly reproducible.
    """
    rng=np.random.default_rng(seed); tested=0; skipped=0; failures=0; worst=0.
    for _ in range(attempts):
        wL=float(rng.uniform(.01,2.5))
        need=tuple(rng.uniform(.25,3.,2))
        K=float(rng.uniform(.08,.7))
        s=np.asarray(rng.uniform(0,.18,2))
        try:
            z=group(s=s,K=K,wL=wL,need=need)
            if np.any(z['n']<1e-5) or np.any(z['n']>.5-1e-5):
                skipped+=1; continue
            tested+=1
            for j in range(2):
                plus=s.copy(); minus=s.copy(); plus[j]+=eps; minus[j]-=eps
                gp=group(s=plus,K=K,wL=wL,need=need)
                gm=group(s=minus,K=K,wL=wL,need=need)
                fd=(gp['n']-gm['n'])/(2*eps)
                err=float(np.max(np.abs(fd-z['dns'][:,j])))
                worst=max(worst,err)
                failures+=int(err>2e-6)
        except ValueError:
            skipped+=1
    assert failures==0
    return dict(seed=seed,attempts=attempts,interior_cases=tested,
                skipped_corner_or_infeasible=skipped,failures=failures,
                worst_absolute_error=worst)

def main():
    b=baseline(); end=baseline(.49)
    rows=[]; maxerr=0.
    for w in [0.,.2,1.]:
        r=group(wL=w)
        for j in range(2):
            s=np.array([.05,.07]); eps=1e-6
            z=group(s=s,wL=w)
            plus=s.copy();minus=s.copy();plus[j]+=eps;minus[j]-=eps
            rp=group(plus,wL=w);rm=group(minus,wL=w)
            maxerr=max(maxerr,abs((rp['W']-rm['W'])/(2*eps)-z['Ws'][j]),np.max(abs((rp['n']-rm['n'])/(2*eps)-z['dns'][:,j])))
        z=group(s=[.05,.07],wL=w)
        maxerr=max(maxerr,abs((group([.05,.07],K=.300001,wL=w)['W']-group([.05,.07],K=.299999,wL=w)['W'])/.000002-z['Wx']))
        rows.append(dict(w_L=w,n_L=r['n'][0],n_H=r['n'][1],h=r['h'],C_L=r['C'][0],C_H=r['C'][1],W_sL=r['Ws'][0],W_sH=r['Ws'][1],W_x=r['Wx'],dnH_dsL=r['dns'][1,0]))
    # The same analytical derivatives must remain valid when requirement and
    # allocation weights are not proportional. These values are illustrative.
    unequal_need=(.6,1.4)
    need_allocation_ratio_checks=[]
    for w in [.2,1.]:
        s=np.array([.05,.07]); eps=1e-6; z=group(s=s,wL=w,need=unequal_need)
        for j in range(2):
            plus=s.copy();minus=s.copy();plus[j]+=eps;minus[j]-=eps
            rp=group(plus,wL=w,need=unequal_need);rm=group(minus,wL=w,need=unequal_need)
            maxerr=max(maxerr,abs((rp['W']-rm['W'])/(2*eps)-z['Ws'][j]),np.max(abs((rp['n']-rm['n'])/(2*eps)-z['dns'][:,j])))
        maxerr=max(maxerr,abs((group(s,K=.300001,wL=w,need=unequal_need)['W']-group(s,K=.299999,wL=w,need=unequal_need)['W'])/.000002-z['Wx']))
        ratio=z['C'][0]/z['C'][1]
        ratio_error=abs(ratio-w)
        assert ratio_error<1e-12
        need_allocation_ratio_checks.append(dict(w_L=w,C_L_over_C_H=ratio,
                                                  absolute_error=ratio_error))
    # A predetermined active incumbent stock changes the load denominator but
    # preserves the scalar implicit-function derivatives for current adoption.
    sf=stock_flow(); eps=1e-6
    sfp=stock_flow(s=.05+eps); sfm=stock_flow(s=.05-eps)
    sfkp=stock_flow(K=.3+eps); sfkm=stock_flow(K=.3-eps)
    stockerr=max(abs((sfp['h']-sfm['h'])/(2*eps)-sf['dhds']),
                 abs((sfp['A']-sfm['A'])/(2*eps)-sf['dAds']),
                 abs((sfkp['h']-sfkm['h'])/(2*eps)-sf['dhdK']))
    maxerr=max(maxerr,stockerr)
    # The richer device-age/refitting accounting must collapse exactly to the
    # two-phase denominator when phase composition is held fixed.
    ageflow=device_age_aggregation()
    ageflow_reverse=device_age_aggregation(w_refit=.80)
    assert ageflow['aggregation_identity_error']<1e-12
    assert ageflow_reverse['aggregation_identity_error']<1e-12
    assert ageflow['replacement_flow']>0 and ageflow['maintenance_stock']>0
    # Both phase-weight orderings are admissible; neither is hard-coded.
    assert ageflow['w_refit']>ageflow['w_first']
    assert ageflow_reverse['w_refit']<ageflow_reverse['w_first']
    # Three-instrument audit.  With binding capacity and a common proportional
    # request response, a higher service subsidy raises requested load but not
    # delivered units.  Capacity investment raises delivered units one-for-one.
    pt=policy_tools(); ptp=policy_tools(sR=.2+eps); ptm=policy_tools(sR=.2-eps)
    ptxp=policy_tools(IR=eps); ptxm=policy_tools(IR=-eps)
    dR_dsR=(ptp['R']-ptm['R'])/(2*eps)
    dY_dsR=(ptp['Y']-ptm['Y'])/(2*eps)
    dy_dsR=(ptp['y']-ptm['y'])/(2*eps)
    dY_dIR=(ptxp['Y']-ptxm['Y'])/(2*eps)
    assert pt['R']>pt['K'] and dR_dsR>0
    assert abs(dY_dsR)<1e-9 and np.max(np.abs(dy_dsR))<1e-9
    assert abs(dY_dIR-1.)<1e-9
    # With slack capacity, the same price change increases delivered support.
    pt_slack=policy_tools(capacity0=1.0)
    pt_slack_p=policy_tools(sR=.2+eps,capacity0=1.0)
    pt_slack_m=policy_tools(sR=.2-eps,capacity0=1.0)
    dY_dsR_slack=(pt_slack_p['Y']-pt_slack_m['Y'])/(2*eps)
    assert pt_slack['R']<pt_slack['K'] and dY_dsR_slack>0
    # Device subsidies can move two different episode margins.  First-entry
    # subsidies add recipients; replacement subsidies move installed-base
    # users from maintenance to refitting.  Verify the exact load and fiscal
    # derivatives, including inframarginal device payments.
    dep=device_policy_episode_flows()
    dep_f_p=device_policy_episode_flows(s_first=.10+eps)
    dep_f_m=device_policy_episode_flows(s_first=.10-eps)
    dep_r_p=device_policy_episode_flows(s_replace=.12+eps)
    dep_r_m=device_policy_episode_flows(s_replace=.12-eps)
    dep_fd=dict(
        drequested_first=(dep_f_p['requested']-dep_f_m['requested'])/(2*eps),
        drequested_replace=(dep_r_p['requested']-dep_r_m['requested'])/(2*eps),
        dspending_first=(dep_f_p['device_spending']-dep_f_m['device_spending'])/(2*eps),
        dspending_replace=(dep_r_p['device_spending']-dep_r_m['device_spending'])/(2*eps),
        ddelivered_first=(dep_f_p['delivered']-dep_f_m['delivered'])/(2*eps),
        ddelivered_replace=(dep_r_p['delivered']-dep_r_m['delivered'])/(2*eps))
    dep_error=max(abs(dep_fd[k]-dep[k]) for k in
                  ['drequested_first','drequested_replace',
                   'dspending_first','dspending_replace'])
    assert dep_error<1e-9
    assert dep['requested']>0.30
    assert abs(dep_fd['ddelivered_first'])<1e-9
    assert abs(dep_fd['ddelivered_replace'])<1e-9
    assert dep['dspending_first']>dep['first_entry']
    assert dep['dspending_replace']>dep['replacement_flow']
    ub=use_benefit(); ubp=use_benefit(ub['upsilon']+eps); ubm=use_benefit(ub['upsilon']-eps)
    ub_fd=(ubp['q']-ubm['q'])/(2*eps)
    ub_error=abs(ub_fd-ub['analytical_derivative'])
    assert ub_error<1e-9 and ub['use_component']>0 and ub['conditional_benefit_component']>0
    ubx=use_benefit_externality(); ubxp=use_benefit_externality(h=ubx['h']+eps); ubxm=use_benefit_externality(h=ubx['h']-eps)
    aggregate_derivative=(ubxp['aggregate_value']-ubxm['aggregate_value'])/(2*eps)
    ubx_fd=ubx['h']*ubx['entrant_weight']/ubx['D']*aggregate_derivative
    ubx_error=abs(ubx_fd-ubx['total_externality'])
    assert ubx_error<1e-9 and ubx['use_channel']>0 and ubx['conditional_benefit_channel']>0
    # Slack, boundary, and binding regimes of h=min(hbar,K/N).
    cap_slack=capped_benchmark(); cap_bind=capped_benchmark(K=.3)
    cap_sp=capped_benchmark(s=eps); cap_sm=capped_benchmark(s=-eps)
    slack_dN_ds=(cap_sp['N']-cap_sm['N'])/(2*eps)
    slack_dh_ds=(cap_sp['h']-cap_sm['h'])/(2*eps)
    cap_kp=capped_benchmark(K=.8+eps); cap_km=capped_benchmark(K=.8-eps)
    slack_dN_dK=(cap_kp['N']-cap_km['N'])/(2*eps)
    assert cap_slack['regime']=='slack' and cap_bind['regime']=='binding'
    assert abs(slack_dN_ds-1/(.2+np.sqrt(1.)))<1e-8
    assert abs(slack_dh_ds)<1e-9 and abs(slack_dN_dK)<1e-9
    boundary_K=cap_slack['N']*cap_slack['hbar']
    cap_boundary=capped_benchmark(K=boundary_K)
    b_sp=capped_benchmark(s=eps,K=boundary_K); b_sm=capped_benchmark(s=-eps,K=boundary_K)
    b_kp=capped_benchmark(K=boundary_K+eps); b_km=capped_benchmark(K=boundary_K-eps)
    boundary_directional=dict(
        dh_ds_left=(cap_boundary['h']-b_sm['h'])/eps,
        dh_ds_right=(b_sp['h']-cap_boundary['h'])/eps,
        dh_dK_left=(cap_boundary['h']-b_km['h'])/eps,
        dh_dK_right=(b_kp['h']-cap_boundary['h'])/eps)
    assert abs(boundary_directional['dh_ds_left'])<1e-8
    assert boundary_directional['dh_ds_right']<0
    assert boundary_directional['dh_dK_left']>0
    assert abs(boundary_directional['dh_dK_right'])<1e-8
    assert maxerr<1e-7,maxerr
    assert abs(group(wL=0.)['dns'][1,0])<1e-12
    assert group(wL=.2)['dns'][1,0]<0
    assert all(group(wL=w)['dns'][j,j]>0 for w in [0.,.2,1.] for j in range(2))
    # Targeted-subsidy fiscal accounting.  The finite-difference expenditure
    # derivative must include inframarginal payments and cross-group feedback.
    target=group(s=[.05,.07],wL=.2)
    target_fd_E=[]; target_fd_V=[]
    for j in range(2):
        plus=np.array([.05,.07]); minus=plus.copy()
        plus[j]+=eps; minus[j]-=eps
        gp=group(s=plus,wL=.2); gm=group(s=minus,wL=.2)
        target_fd_E.append((gp['E']-gm['E'])/(2*eps))
        target_fd_V.append((gp['V']-gm['V'])/(2*eps))
    target_fd_E=np.array(target_fd_E); target_fd_V=np.array(target_fd_V)
    target_error=max(np.max(np.abs(target_fd_E-target['Es'])),
                     np.max(np.abs(target_fd_V-target['Vs'])))
    assert target_error<1e-8
    assert np.all(target['Es']>0)
    # Exact first-order budget-neutral reallocation identity from H to L.
    dsL=1.
    dsH=-target['Es'][0]/target['Es'][1]
    dV_direct=target['Vs'][0]*dsL+target['Vs'][1]*dsH
    dV_ratio=target['Es'][0]*(target['Gamma'][0]-target['Gamma'][1])*dsL
    reallocation_error=abs(dV_direct-dV_ratio)
    assert reallocation_error<1e-12
    with (ROOT/'heterogeneity_results.csv').open('w') as f:
        wr=csv.DictWriter(f,fieldnames=rows[0]);wr.writeheader();wr.writerows(rows)
    clean=lambda z:{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in z.items()}
    stress=group_random_stress_check()
    result=dict(baseline=b,adoption_change=end['N']/b['N']-1,intensity_change=end['h']/b['h']-1,max_finite_difference_error=maxerr,unequal_requirement_check=list(unequal_need),need_allocation_ratio_checks=need_allocation_ratio_checks,group_random_stress_check=stress,stock_flow_check=sf,stock_flow_finite_difference_error=stockerr,device_age_aggregation_checks=dict(refit_weight_above_first=clean(ageflow),refit_weight_below_first=clean(ageflow_reverse)),policy_tools_check=dict(binding=clean(pt),dR_dsR=dR_dsR,dY_dsR=dY_dsR,dy_dsR=dy_dsR.tolist(),dY_dIR=dY_dIR,slack=clean(pt_slack),dY_dsR_slack=dY_dsR_slack),device_policy_episode_check=dict(levels=clean(dep),finite_difference=dep_fd,finite_difference_error=dep_error),use_benefit_decomposition_check=dict(**ub,finite_difference_derivative=ub_fd,absolute_error=ub_error),use_benefit_externality_check=dict(**ubx,finite_difference_externality=ubx_fd,absolute_error=ubx_error),capacity_regime_check=dict(slack=cap_slack,binding=cap_bind,slack_dN_ds=slack_dN_ds,slack_dh_ds=slack_dh_ds,slack_dN_dK=slack_dN_dK,boundary=cap_boundary,boundary_directional=boundary_directional),targeted_subsidy_check=dict(s=[.05,.07],w_L=.2,n=target['n'].tolist(),Es=target['Es'].tolist(),Vs=target['Vs'].tolist(),Ws=target['Ws'].tolist(),Gamma=target['Gamma'].tolist(),net_ratio=(target['Ws']/target['Es']).tolist(),finite_difference_E=target_fd_E.tolist(),finite_difference_V=target_fd_V.tolist(),finite_difference_error=float(target_error),budget_neutral_direction=[dsL,float(dsH)],reallocation_direct=float(dV_direct),reallocation_ratio=float(dV_ratio),reallocation_identity_error=float(reallocation_error)),group_results=rows)
    (ROOT/'verification_results.json').write_text(json.dumps(result,indent=2))
    lines=[r'\begin{tabular}{rrrrrrr}',r'\toprule',r'$w_L$ & $n_L$ & $n_H$ & $C_L$ & $C_H$ & $W_{s_L}$ & $W_{s_H}$\\',r'\midrule']
    for r in rows:lines.append(' & '.join(f'{r[k]:.4f}' for k in ['w_L','n_L','n_H','C_L','C_H','W_sL','W_sH'])+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}']
    (ROOT/'heterogeneity_table.tex').write_text('\n'.join(lines))
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
