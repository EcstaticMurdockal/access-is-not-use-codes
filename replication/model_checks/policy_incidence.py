"""Rebuild the paper's marginal policy comparison at its published two-group baseline."""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT.parents[1]))
from verify_models import group

CAPACITY = 0.3
CAPACITY_COST = 0.25
EXTERNAL_BENEFIT = 0.5
FINANCING_COST = 0.1
ROWS = ("adoption_L", "adoption_H", "consumer_surplus_L", "consumer_surplus_H",
        "external_benefit", "net_welfare")


def equilibrium(subsidies, expansion, cost=CAPACITY_COST):
    return group(s=subsidies, K=CAPACITY + expansion, wL=0.2,
                 need=(1., 1.), eta=EXTERNAL_BENEFIT, lam=FINANCING_COST, cx=cost)


def outcome_levels(z, subsidies):
    benefit = z['M'] * z['q']
    consumer_surplus = benefit - (z['prices'] - subsidies) * z['n']
    return np.r_[z['n'], consumer_surplus, EXTERNAL_BENEFIT * benefit.sum(), z['W']]


def incidence(base, subsidies, expansion, cost=CAPACITY_COST):
    """Directional responses per unit of public outlay at zero device subsidies."""
    spending = base['n'] @ subsidies + cost * expansion
    dh = base['dh_ds'] @ subsidies + base['dh_dK'] * expansion
    dn = base['dns'] @ subsidies + base['dn_dK'] * expansion
    incumbent_slopes = base['M'] * base['qp']
    cs = base['n'] * subsidies + incumbent_slopes * dh
    dq = base['prices'] @ dn + incumbent_slopes.sum() * dh
    external = EXTERNAL_BENEFIT * dq
    welfare = cs.sum() + external - (1 + FINANCING_COST) * spending
    np.testing.assert_allclose(welfare, base['Ws'] @ subsidies + base['Wx'] * expansion, atol=2e-14)
    return np.r_[dn, cs, external, welfare] / spending


def equal_budget_response(subsidies, expansion, budget):
    """Re-solve in levels for a strictly feasible common budget increment."""
    def at(scale):
        return equilibrium(scale * subsidies, scale * expansion)

    upper = 1e-3
    while at(upper)['E'] < budget:
        upper *= 2
    scale = brentq(lambda t: at(t)['E'] - budget, 0, upper, xtol=1e-15)
    z = at(scale)
    np.testing.assert_allclose(z['E'], budget, rtol=2e-9, atol=1e-16)
    return outcome_levels(z, scale * subsidies)


def matched_reservation(base):
    """Value a marginal entrant's displacement at the same initial allocation."""
    n, w, M, h = (base[k] for k in ('n', 'weights', 'M', 'h'))
    service = w * h
    value_per_unit = M * base['qp'] / (n * w)
    pooled = service * ((n * service / CAPACITY) @ value_per_unit)
    reserved = service * value_per_unit
    incumbent_slopes = M * base['qp']
    share = incumbent_slopes / incumbent_slopes.sum()
    np.testing.assert_allclose(pooled, base['C'], rtol=2e-12)
    # Hold the original adopters fixed. Value their changes in delivered service
    # under each rule directly using the paper's benefit functions.
    def benefit(per_adopter):
        return M * (np.array([.8, .2]) + np.array([.2, 1.]) * (-np.expm1(-per_adopter)))

    for j, unit in enumerate(np.eye(2)):
        def losses(extra):
            added = n + extra * unit
            after_pooled = w * CAPACITY / (w @ added)
            after_reserved = n * service / added
            return np.array([benefit(service) - benefit(after_pooled),
                             benefit(service) - benefit(after_reserved)]) / extra
        observed = 2 * losses(1e-6) - losses(2e-6)
        np.testing.assert_allclose(observed[0], pooled[j] * share, atol=2e-9, rtol=0)
        np.testing.assert_allclose(observed[1], reserved[j] * unit, atol=2e-9, rtol=0)
    return dict(value_per_service_unit=value_per_unit.tolist(),
                pooled_loss=pooled.tolist(), reserved_loss=reserved.tolist(),
                recipient_share_of_pooled_loss=share.tolist())


def value_lost_follow_up(base, reservation, subsidy_H):
    """Trace time lost by the original patients through to welfare at zero subsidies."""
    minutes_per_unit = 10.0  # Illustrative unit conversion for one kind of service.
    n, weights = base['n'], base['weights']
    per_person = weights * base['h']
    shares = n * per_person / CAPACITY
    lost_minutes = minutes_per_unit * per_person[1] * shares
    money_per_minute = np.asarray(reservation['value_per_service_unit']) / minutes_per_unit
    losses = lost_minutes * money_per_minute

    # Independently recompute service for the original cohort after H entry.
    # The perturbation is in adopter mass; the original recipients stay fixed.
    initial_load = weights @ n
    before = weights * CAPACITY / initial_load
    np.testing.assert_allclose(before, per_person, rtol=1e-12)

    def minutes_given_up(extra):
        after = weights * CAPACITY / (initial_load + weights[1] * extra)
        return minutes_per_unit * n * (before - after) / extra

    observed = 2 * minutes_given_up(1e-6) - minutes_given_up(2e-6)
    np.testing.assert_allclose(observed, lost_minutes, rtol=0, atol=2e-8)
    np.testing.assert_allclose(lost_minutes.sum(), minutes_per_unit * per_person[1], rtol=0, atol=1e-12)
    np.testing.assert_allclose(losses.sum(), base['C'][1], rtol=0, atol=1e-12)

    # At zero subsidy a marginal buyer values the device at its resource price.
    # Include the change in L adoption when valuing a dollar of extra H subsidy.
    dn = np.array([subsidy_H['adoption_L'], subsidy_H['adoption_H']])
    entrant_external = EXTERNAL_BENEFIT * (base['prices'] @ dn)
    social_incumbent = (1 + EXTERNAL_BENEFIT) * (base['C'] @ dn)
    net = entrant_external - social_incumbent - FINANCING_COST
    np.testing.assert_allclose(net, subsidy_H['net_welfare'], rtol=0, atol=2e-14)
    return dict(illustrative_minutes_per_service_unit=minutes_per_unit,
                recipient_groups=['L', 'H'], minutes_lost_per_H_entrant=lost_minutes.tolist(),
                model_money_per_minute=money_per_minute.tolist(),
                private_loss_by_incumbent_group=losses.tolist(),
                private_loss_per_H_entrant=float(losses.sum()),
                social_incumbent_loss_per_H_entrant=float((1 + EXTERNAL_BENEFIT) * losses.sum()),
                per_dollar_of_H_subsidy=dict(entrant_external_benefit=float(entrant_external),
                                             social_incumbent_loss=float(social_incumbent),
                                             excess_financing_cost=FINANCING_COST,
                                             net_welfare=float(net)))


def compare():
    zero = np.zeros(2)
    L, H = np.eye(2)
    base = equilibrium(zero, 0)
    offset = -base['dh_ds'][1] / base['dh_dK']
    policies = {'subsidy_L': (L, 0), 'subsidy_H': (H, 0),
                'capacity': (zero, 1), 'subsidy_H_with_capacity': (H, offset)}
    answers = {}
    errors = []
    levels = outcome_levels(base, zero)
    for name, direction in policies.items():
        analytic = incidence(base, *direction)
        # Extrapolate two one-sided differences at zero outlay; both policies
        # being compared actually spend the same amount in each comparison.
        budget = 1e-6
        one = (equal_budget_response(*direction, budget) - levels) / budget
        two = (equal_budget_response(*direction, 2 * budget) - levels) / (2 * budget)
        errors.append(np.abs(2 * one - two - analytic).max())
        answers[name] = dict(zip(ROWS, map(float, analytic)))
    if max(errors) > 5e-8:
        raise ValueError(f"Equal-budget check failed: {max(errors):.3g}")
    protected = answers['subsidy_H_with_capacity']
    np.testing.assert_allclose([protected['adoption_L'], protected['consumer_surplus_L']], 0, atol=1e-13)
    L_return, capacity_return = answers['subsidy_L'], answers['capacity']
    benefit_per_capacity_unit = base['Wx'] + (1 + FINANCING_COST) * CAPACITY_COST
    cost_tie = benefit_per_capacity_unit / (1 + FINANCING_COST + L_return['net_welfare'])
    tie = equilibrium(zero, 0, cost=cost_tie)
    np.testing.assert_allclose(incidence(tie, zero, 1, cost_tie)[-1], L_return['net_welfare'], atol=2e-14)
    equity_tie = 1 + ((L_return['net_welfare'] - capacity_return['net_welfare']) /
                      (capacity_return['consumer_surplus_H'] - L_return['consumer_surplus_H']))
    weighted = [x['net_welfare'] + (equity_tie - 1) * x['consumer_surplus_H']
                for x in (L_return, capacity_return)]
    np.testing.assert_allclose(*weighted, atol=2e-14)
    reservation = matched_reservation(base)
    return dict(per_public_dollar=answers, reservation=reservation,
                lost_follow_up=value_lost_follow_up(base, reservation, answers['subsidy_H']),
                capacity_units_per_H_subsidy_unit_at_constant_support=float(offset),
                cost_threshold_capacity_vs_subsidy_L=float(cost_tie),
                H_welfare_weight_threshold_capacity_vs_subsidy_L=float(equity_tie),
                maximum_absolute_equal_budget_error=float(max(errors)))


def write_table(answers):
    labels = ("Adoption in $L$", "Adoption in $H$", "Consumer surplus in $L$",
              "Consumer surplus in $H$", "External benefit", "Net social welfare")
    lines = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrrr@{}}\toprule',
             r'& Subsidy $L$ & Subsidy $H$ & Capacity & \shortstack{Subsidy $H$\\plus capacity}\\',
             r'\midrule']
    for key, label in zip(ROWS, labels):
        if key in ('consumer_surplus_L', 'net_welfare'):
            lines.append(r'\addlinespace[2pt]')
        cells = [f'{p[key]:.3f}' if abs(p[key]) >= 0.0005 else '0.000' for p in answers.values()]
        lines.append(' & '.join([label, *cells]) + r'\\')
    lines.extend([r'\bottomrule', r'\end{tabular*}'])
    (OUT / 'policy_incidence_table.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_valuation_table(valuation):
    lines = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrr@{}}\toprule',
             r'Existing patients & Minutes displaced & Value per minute & Private loss\\',
             r'\midrule']
    rows = zip(valuation['recipient_groups'], valuation['minutes_lost_per_H_entrant'],
               valuation['model_money_per_minute'], valuation['private_loss_by_incumbent_group'])
    for label, minutes, unit_value, loss in rows:
        lines.append(f'Group ${label}$ & {minutes:.3f} & {unit_value:.6f} & {loss:.5f}' + r'\\')
    total_minutes = sum(valuation['minutes_lost_per_H_entrant'])
    total_loss = valuation['private_loss_per_H_entrant']
    lines.extend([r'\midrule', f'All incumbents & {total_minutes:.3f} & & {total_loss:.5f}' + r'\\',
                  r'\bottomrule', r'\end{tabular*}'])
    (OUT / 'incumbent_valuation_table.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    result = compare()
    (OUT / 'policy_incidence.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    write_table(result['per_public_dollar'])
    write_valuation_table(result['lost_follow_up'])
    print(json.dumps(result, indent=2))
