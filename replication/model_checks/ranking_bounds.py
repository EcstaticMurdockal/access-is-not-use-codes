"""Welfare bounds at the paper's equal-outlay, zero-subsidy reference equilibrium."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

from policy_incidence import CAPACITY, CAPACITY_COST, EXTERNAL_BENEFIT, FINANCING_COST, equilibrium

OUT = Path(__file__).resolve().parent


def welfare_gap_bounds(external_benefit, entry_benefit, benefit_changes, lower_mass, upper_mass):
    """Equal-outlay welfare gap at fixed adoption and service responses."""
    fixed_part = external_benefit * entry_benefit - 1
    low = (1 + external_benefit) * benefit_changes * lower_mass
    high = (1 + external_benefit) * benefit_changes * upper_mass
    return [float(fixed_part + np.minimum(low, high).sum()),
            float(fixed_part + np.maximum(low, high).sum())]


def density(t, concentrated):
    """Piecewise linear density on [0,1], equal to one near the original cutoff."""
    if not concentrated:
        return np.array([0., 1.]), np.ones(2)
    e = 0.001
    x = np.array([0., e, 2*e, 1-3*e, 1-2*e, 1-e, 1.])
    y = np.array([1., 1., e, e, e, e, e])
    area = np.diff(x) @ ((y[:-1] + y[1:]) / 2)
    # A triangle of base 2e places the remaining mass near the upper endpoint.
    y[4] += (1 - area) / e
    return np.r_[0., t + (1-t)*x], np.r_[1., y]


def tail_moments(grid, heights, cutoff):
    """Integrate mass and first moment exactly on each linear density segment."""
    if cutoff >= grid[-1]:
        return 0., 0.
    lower = max(cutoff, grid[0])
    points = np.r_[lower, grid[grid > lower]]
    values = np.interp(points, grid, heights)
    a, b = points[:-1], points[1:]
    left, right = values[:-1], values[1:]
    mass = (b-a) @ ((left+right)/2)
    moment = (b-a) @ (((2*a+b)*left + (a+2*b)*right)/6)
    return mass, moment


def witness_returns(base, group_mass, tail_grid):
    """Re-solve levels with original prices, technology and a different valuation tail."""
    weights, price = base['weights'], base['prices']
    def solve(spending, target):
        capacity = CAPACITY + (spending/CAPACITY_COST if target is None else 0.)
        def levels(subsidies):
            def patients(h):
                # These are the benefit intercepts and responses in verify_models.group.
                q = np.array([.8, .2]) + np.array([.2, 1.]) * (-np.expm1(-weights*h))
                cutoffs = (price - subsidies)/q
                moments = np.array([tail_moments(x, y, t)
                                    for (x, y), t in zip(tail_grid, cutoffs)])
                n, M = (group_mass[:, None] * moments).T
                return q, n, M
            h = brentq(lambda h: h*(weights @ patients(h)[1])-capacity, 0., 5.,
                       xtol=1e-14)
            q, n, M = patients(h)
            public = subsidies @ n + CAPACITY_COST*(capacity-CAPACITY)
            welfare = ((1 + EXTERNAL_BENEFIT)*(M @ q) - price @ n
                       - CAPACITY_COST*(capacity-CAPACITY) - FINANCING_COST*public)
            return n, h, public, welfare
        subsidies = np.zeros(2)
        if target is not None and spending > 0:
            unit = np.eye(2)[target]
            rate = brentq(lambda s: levels(unit*s)[2]-spending, 0.,
                          2*spending/base['n'][target], xtol=1e-16)
            subsidies[target] = rate
        n, h, public, welfare = levels(subsidies)
        np.testing.assert_allclose(public, spending, atol=1e-15, rtol=0)
        return np.r_[n, h, welfare]

    origin = solve(0., None)
    np.testing.assert_allclose(origin[:3], np.r_[base['n'], base['h']], atol=5e-13, rtol=0)
    answers = []
    for target in (None, 0, 1):
        step = 1e-6
        near = (solve(step, target) - origin)/step
        far = (solve(2*step, target) - origin)/(2*step)
        answers.append(2*near-far)
    return np.stack(answers)


def analyze():
    base = equilibrium(np.zeros(2), 0.)
    n, price, qp = base['n'], base['prices'], base['qp']
    t = price/base['q']
    # The published reference has uniform [0,1] valuations and two equal-size groups.
    group_mass = np.full(len(n), .5)
    np.testing.assert_allclose(group_mass*(1-t), n, atol=1e-12, rtol=0)
    upper = np.ones_like(n)
    bid = (t+upper)/2
    yes = np.full(len(n), .5)  # A hypothetical completed elicitation, not survey data.
    lower_after_bid = n*((1-yes)*t + yes*bid)
    upper_after_bid = n*((1-yes)*bid + yes*upper)

    results = {}
    for j, label in enumerate(('L', 'H')):
        change_n = base['dn_dK']/CAPACITY_COST - base['dns'][:,j]/n[j]
        change_h = base['dh_dK']/CAPACITY_COST - base['dh_ds'][j]/n[j]
        change_q = qp*change_h
        entry_benefit = float(price @ change_n)
        fixed_part = EXTERNAL_BENEFIT * entry_benefit - 1
        baseline = fixed_part+(1+EXTERNAL_BENEFIT)*(base['M'] @ change_q)
        np.testing.assert_allclose(baseline, base['Wx']/CAPACITY_COST-base['Ws'][j]/n[j],
                                   atol=2e-13, rtol=0)
        def support_bounds(eta):
            return welfare_gap_bounds(eta, entry_benefit, change_q, n*t, n*upper)

        results[label] = dict(baseline_gap=float(baseline),
                              support_only=support_bounds(EXTERNAL_BENEFIT),
                              with_midpoint_bid=welfare_gap_bounds(
                                  EXTERNAL_BENEFIT, entry_benefit, change_q, lower_after_bid, upper_after_bid),
                              support_only_eta_040=support_bounds(0.40),
                              break_even_S=float(-fixed_part/((1+EXTERNAL_BENEFIT)*change_h)))
        if label == 'H':
            # For eta >= 0 the active endpoints are unchanged. The worst-case
            # gap is -1 + C + eta*(entry_benefit + C).
            incumbent_lower = float(np.minimum(change_q*n*t, change_q*n*upper).sum())
            slope = entry_benefit + incumbent_lower
            assert slope > 0
            tie = (1 - incumbent_lower) / slope
            assert 0.40 < tie < EXTERNAL_BENEFIT
            np.testing.assert_allclose(support_bounds(tie)[0], 0., atol=3e-14, rtol=0)
            np.testing.assert_allclose(tie, brentq(lambda eta: support_bounds(eta)[0],
                                                   0.40, EXTERNAL_BENEFIT), atol=1e-12, rtol=0)
            results[label]['lower_bound_zero_eta'] = float(tie)
        # Changing the purchase price of an extra unit leaves the baseline,
        # with no expansion yet, unchanged. Only the affordable scale varies.
        cost_ties = []
        for S in ((n*t) @ qp, n @ qp):
            unit_benefit = (EXTERNAL_BENEFIT * (price @ base['dn_dK'])
                            + (1 + EXTERNAL_BENEFIT) * S * base['dh_dK'])
            subsidy_benefit = (EXTERNAL_BENEFIT * (price @ base['dns'][:, j])
                               + (1 + EXTERNAL_BENEFIT) * S * base['dh_ds'][j]) / n[j]
            assert unit_benefit > 0 and 1 + subsidy_benefit > 0
            cost = unit_benefit / (1 + subsidy_benefit)
            dn = base['dn_dK'] / cost - base['dns'][:, j] / n[j]
            dh = base['dh_dK'] / cost - base['dh_ds'][j] / n[j]
            gap = EXTERNAL_BENEFIT * (price @ dn) + (1 + EXTERNAL_BENEFIT) * S * dh - 1
            np.testing.assert_allclose(gap, 0., atol=1e-12, rtol=0)
            cost_ties.append(float(cost))
        results[label]['break_even_unit_cost_at_lower_and_upper_S'] = cost_ties

    witnesses = {}
    for name, concentrated in [('uniform',False), ('upper_tail',True)]:
        distributions = [density(x, concentrated) for x in t]
        moments = np.array([tail_moments(x,y,cut) for (x,y),cut in zip(distributions,t)])
        for (grid, values), cut in zip(distributions, t):
            np.testing.assert_allclose(tail_moments(grid,values,0)[0], 1, atol=6e-13, rtol=0)
            np.testing.assert_allclose(np.interp(cut,grid,values), 1, atol=1e-14, rtol=0)
        np.testing.assert_allclose(group_mass*moments[:,0], n, atol=6e-13, rtol=0)
        S = (group_mass*moments[:,1]) @ qp
        responses = witness_returns(base, group_mass, distributions)
        gaps = responses[0,-1]-responses[1:,-1]
        for j, label in enumerate(('L','H')):
            delta_h = base['dh_dK']/CAPACITY_COST - base['dh_ds'][j]/n[j]
            prediction = (1+EXTERNAL_BENEFIT)*delta_h*(S-results[label]['break_even_S'])
            np.testing.assert_allclose(prediction, gaps[j], atol=2e-7, rtol=0)
            lower, upper_gap = results[label]['support_only']
            assert lower < prediction < upper_gap
        witnesses[name] = dict(S=float(S), capacity_minus_subsidy=gaps.tolist(),
                               adoption_and_intensity_responses=responses[:,:3].tolist())
    left, right = witnesses.values()
    np.testing.assert_allclose(left['adoption_and_intensity_responses'],
                               right['adoption_and_intensity_responses'], atol=3e-7, rtol=0)
    assert left['capacity_minus_subsidy'][0] < 0 < right['capacity_minus_subsidy'][0]
    assert results['H']['support_only'][0] > 0 and results['L']['with_midpoint_bid'][1] < 0
    return dict(groups=['L','H'], units='model money per marginal public dollar',
                cutoff=t.tolist(), support_S=[float((n*t)@qp),float(n@qp)],
                uniform_S=float(base['M']@qp), hypothetical_bid=bid.tolist(),
                hypothetical_yes_given_adoption=yes.tolist(), gaps=results, witnesses=witnesses)


def write_table(results):
    def interval(pair):
        return '$['+f'{pair[0]:.3f},\\ {pair[1]:.3f}'+']$'
    lines = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lccc@{}}\toprule',
             r'Incumbent valuations & $\eta$ & Capacity vs.\ subsidy $L$ & Capacity vs.\ subsidy $H$\\',
             r'\midrule']
    gaps = results['gaps']
    for label, eta, field in [('Cutoff and upper support', EXTERNAL_BENEFIT, 'support_only'),
                              ('Cutoff and upper support', 0.40, 'support_only_eta_040'),
                              ('Also a midpoint bid', EXTERNAL_BENEFIT, 'with_midpoint_bid')]:
        cells = [interval(gaps[g][field]) for g in ('L', 'H')]
        lines.append(' & '.join([label, f'${eta:.2f}$', *cells])+r'\\')
    cells = [f"${gaps[g]['baseline_gap']:.3f}$" for g in ('L','H')]
    lines += [' & '.join(['Uniform reference', f'${EXTERNAL_BENEFIT:.2f}$', *cells])+r'\\',
              r'\bottomrule',r'\end{tabular*}']
    (OUT/'ranking_bounds_table.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__ == '__main__':
    result = analyze()
    (OUT/'ranking_bounds.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    write_table(result)
    print(json.dumps(result['gaps'],indent=2))
