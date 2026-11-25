"""Check the analytical derivations and their boundary cases using only Python's standard library.

Run: python check_revision.py
The examples use illustrative primitives. No empirical data are read or written.
"""
import json
from fractions import Fraction as F
from math import exp, isclose, sqrt


def check(condition, message):
    if not condition:
        raise ValueError(message)


def root(function, low, high):
    """Bisect a continuous function that changes from negative to positive."""
    check(function(low) <= 0 <= function(high), "Root outside bracket")
    for _ in range(70):
        mid = (low + high) / 2
        if function(mid) > 0:
            high = mid
        else:
            low = mid
    return (low + high) / 2


def budget_boundary():
    # Uniform valuations, fixed K=1, x=0, a=.2, p=.5, eta=10, lambda=0.
    price = 0.5

    def subsidy(n):
        return price - (1 - n) * (0.2 + sqrt(1 / n))

    def surplus(n):
        return 11 * (n - n * n / 2) * (0.2 + sqrt(1 / n)) - price * n

    def marginal_surplus(n):
        q = 0.2 + sqrt(1 / n)
        derivative = -sqrt(1 / n) / (2 * n)
        return 11 * ((1 - n) * q + (n - n * n / 2) * derivative) - price

    lower = root(subsidy, 0.4, 1)
    interior = root(lambda n: -marginal_surplus(n), lower, 1)
    cap = 0.01
    upper = root(lambda n: subsidy(n) * n - cap, lower, 1)
    check(lower < upper < interior < 1, "Budget did not truncate the optimum")
    check(marginal_surplus(lower) > 0 and marginal_surplus(upper) > 0,
          "Budget-boundary derivative has wrong sign")
    for step in range(501):
        n = lower + (upper - lower) * step / 500
        check(surplus(n) <= surplus(upper) + 1e-12, "Feasible point beat boundary")
    check(isclose(upper * subsidy(upper), cap), "Binding outlay mismatch")
    return {"baseline_mass": lower, "budget_constrained_mass": upper,
            "unconstrained_mass": interior, "binding_outlay": cap}


def adequacy_derivative():
    # q=a+b*g(v), g(v)=1-exp(-v). Split q into probability chi and value nu=q/chi.
    # Variable chi lets nonzero component derivatives cancel even when b=0.
    h, requirement, step = 0.8, 2.5, 1e-5
    errors = []
    for weight in (0.0, 1.6):
        for response in (0.0, 1.5):
            v = weight * h / requirement
            chi = 0.6 + 0.1 * (1 - exp(-v))
            dchi = 0.1 * exp(-v)
            q = 1.0 + response * (1 - exp(-v))
            nu = q / chi
            dnu = (response * exp(-v) - dchi * nu) / chi
            analytical = (weight / requirement) * (dchi * nu + chi * dnu)

            def benefit(intensity):
                return 1.0 + response * (1 - exp(-weight * intensity / requirement))

            numerical = (benefit(h + step) - benefit(h - step)) / (2 * step)
            errors.append(abs(analytical - numerical))
            check(isclose(analytical, numerical, rel_tol=1e-8, abs_tol=1e-10),
                  "Shared-intensity derivative mismatch")
            if not weight or not response:
                check(abs(analytical) < 1e-14, "Flat branch did not vanish")
    return {"cases": len(errors), "max_absolute_error": max(errors)}


def age_bins(project=None):
    """Build an independent cohort ledger, optionally checking the shipped model."""
    tested = 0
    for stock in ([32], [32, 16], [32, 16, 24, 8], [0, 0, 0, 8], [0, 0]):
        size = len(stock)
        profiles = [
            ([F(0)] * size, [F(0)] * size),
            ([F(1, 8)] * size, [F(1, 4)] * size),
            ([F(0)] * size, [F(1)] * size),
            ([F(1)] * size, [F(0)] * size),
            ([F(age % 3, 8) for age in range(size)],
             [F(age + 1, 8) for age in range(size)]),
        ]
        for exits, refits in profiles:
            new_fits = 12
            replacements = sum(rate * n for rate, n in zip(refits, stock))
            entry = F(3, 4) * new_fits + F(1, 2) * replacements
            same_device = [(1 - death - refit) * n
                           for n, death, refit in zip(stock, exits, refits)]
            next_stock = [F(0)] * size
            next_stock[0] = entry
            for age, remaining in enumerate(same_device):
                next_stock[min(age + 1, size - 1)] += remaining
            exiting = sum(rate * n for rate, n in zip(exits, stock))
            expected = sum(stock) + F(3, 4) * new_fits - exiting - F(1, 2) * replacements
            check(sum(next_stock) == expected, "Total number of active people changed incorrectly")
            terminal = entry + same_device[0] if size == 1 else sum(same_device[-2:])
            check(next_stock[-1] == terminal, "Terminal survivors dropped or duplicated")
            if project is not None:
                actual = project(first_entry=new_fits, stock=stock, refit=refits,
                                 exit_rate=exits, w_maint=[0.5] * size,
                                 retain_first=0.75, retain_refit=0.5)
                check(len(actual["next_stock_by_age"]) == size and
                      all(isclose(value, float(reference), abs_tol=1e-12)
                          for value, reference in zip(actual["next_stock_by_age"], next_stock)),
                      "Model projection differs from the independent age-cohort ledger")
            tested += 1
    return {"exact_cases": tested}


def future_incumbent_load():
    # At h=1, D=2, both groups have unit claim weights and B=1/2.
    # The first group's direct adoption response A=1 implies Lambda=3.
    intensity_change = -F(1, 3)
    adoption_change = [1 + F(1, 2) * intensity_change, F(1, 2) * intensity_change]
    totals = []
    for retention in ([F(1, 10), F(1)], [F(1), F(1)]):
        total = sum(p * dn for p, dn in zip(retention, adoption_change))
        totals.append(total)
    check(adoption_change[0] > 0 and totals == [-F(1, 12), F(2, 3)],
          "Network load did not incorporate displaced entrants")
    return {"targeted_group_adoption_derivative": str(adoption_change[0]),
            "low_targeted_retention_load_derivative": str(totals[0]),
            "equal_retention_load_derivative": str(totals[1])}


def conditional_budget_optimum():
    # These values make unsubsidized adoption and the threshold exactly representable as fractions.
    capacity, price, financing = 0.5, 1.0, 0.1
    expansion_cost, n0 = 0.125, 0.5
    rho, delta = F(3, 8), F(5, 4)
    eta_critical = (rho + F(1, 10) * delta) / (1 - rho)

    def response(n):
        return 1 + sqrt(capacity / n)

    def rate(n):
        return price - (1 - n) * response(n)

    def marginal(n, external):
        q = response(n)
        q_n = -sqrt(capacity / n) / (2 * n)
        benefit_n = (1 - n) * q + (n - n * n / 2) * q_n
        outlay_n = rate(n) + n * (q - (1 - n) * q_n)
        return (1 + external) * benefit_n - price - financing * outlay_n

    def welfare(n, subsidy, external):
        q = response(n)
        outlay = expansion_cost + n * subsidy
        return ((1 + external) * (n - n * n / 2) * q
                - n * price - expansion_cost - financing * outlay)

    checked = 0
    for eta in (F(0), eta_critical, F(2)):
        external = float(eta)
        threshold_slope = eta * (1 - rho) - rho - F(1, 10) * delta
        check(isclose(marginal(n0, external), float(threshold_slope), abs_tol=1e-12),
              "Cutoff criterion and slope in adoption coordinates disagree")
        free = n0 if threshold_slope <= 0 else root(lambda n: -marginal(n, external), n0, 1)
        for budget in (expansion_cost / 2, expansion_cost, expansion_cost + 1/64,
                       expansion_cost + price, expansion_cost + 2 * price):
            # Verify feasibility and welfare against policies sampled in subsidy coordinates.
            policies = []
            for step in range(161):
                subsidy = price * step / 160
                n = root(lambda mass: rate(mass) - subsidy, n0, 1)
                if expansion_cost + subsidy * n <= budget + 1e-14:
                    policies.append(welfare(n, subsidy, external))
            if budget < expansion_cost:
                check(not policies, "An infeasible capacity was accepted")
            else:
                upper = 1.0 if budget >= expansion_cost + price else root(
                    lambda n: expansion_cost + rate(n) * n - budget, n0, 1)
                chosen = min(free, upper)
                check(expansion_cost + chosen * rate(chosen) <= budget + 1e-13,
                      "Choice exceeds the public budget")
                check(welfare(chosen, rate(chosen), external) >= max(policies) - 1e-12,
                      "A feasible subsidy on the grid beats the analytical optimum")
                if eta == eta_critical or budget == expansion_cost:
                    check(isclose(chosen, n0, abs_tol=1e-13), "A zero or infeasible entry gain was accepted")
            checked += 1
    return {"cases": checked, "threshold_external_benefit": str(eta_critical)}


def opposing_adoption_responses():
    # Solve the primitive two-group model in Appendix A.3 at each perturbed net price.
    def equilibrium(subsidy_change):
        first = 0.5 * (1 - (1 - subsidy_change) / 2)

        def second(intensity):
            cutoff = 2 / (1 + sqrt(intensity))
            cdf = min(1.0, max(0.0, (cutoff - 15/16) * 8))
            return 0.5 * (1 - cdf)

        h = root(lambda intensity: intensity * (3 * first + second(intensity)) - 1, 0, 2)
        return h, first, second(h), first + second(h)

    step = 1e-5
    high, low = equilibrium(step), equilibrium(-step)
    estimated = [(hi - lo) / (2 * step) for hi, lo in zip(high, low)]
    exact = (F(-3, 8), F(1, 4), F(-3, 8), F(-1, 8))
    errors = [abs(obs - float(ref)) for obs, ref in zip(estimated, exact)]
    check(max(errors) < 1e-8, "Two-group equilibrium sign example failed")
    return {"own": str(exact[1]), "other": str(exact[2]), "total": str(exact[3]),
            "max_absolute_error": max(errors)}


def targeted_buyer_surplus():
    """Re-solve the Appendix A.3 economies in levels, using only feasible subsidy increases."""
    group_mass, price, capacity = 0.5, 0.5, 0.5

    def equilibrium(exponent, subsidy):
        def benefit(intensity):
            return (1 + 3 * intensity) / (3 + intensity)

        def target_mass(quality):
            cutoff = (price - subsidy) / quality

            def rank_residual(rank):
                return rank + 9 * max(2 * rank - 1, 0) ** exponent - cutoff

            cutoff_rank = root(rank_residual, 0, 1)
            return group_mass * (1 - cutoff_rank)

        def excess_load(intensity):
            quality = benefit(intensity)
            other_mass = group_mass * (1 - price / quality)
            return intensity * (target_mass(quality) + other_mass) - capacity

        intensity = root(excess_load, 0.5, 1.5)
        quality = benefit(intensity)
        adopters = target_mass(quality)
        rank = 1 - adopters / group_mass
        # Integrate the valuation quantile over adopting ranks, then subtract their payments.
        upper_tail = (1 - max(2 * rank - 1, 0) ** (exponent + 1)) / (2 * (exponent + 1))
        valuations = group_mass * ((1 - rank ** 2) / 2 + 9 * upper_tail)
        surplus = quality * valuations - (price - subsidy) * adopters
        return intensity, adopters, surplus

    step = 1e-5
    errors = []
    cases = []
    for exponent, exact_surplus in ((2, F(-1, 16)), (3, F(0)), (5, F(1, 16))):
        base, near, far = (equilibrium(exponent, s) for s in (0, step, 2 * step))
        check(isclose(base[0], 1) and isclose(base[1], 0.25), "Reference allocation mismatch")
        exact = (F(-2, 3), F(5, 12), exact_surplus)
        for initial, first, second, slope in zip(base, near, far, exact):
            numerical = (4 * (first - initial) - (second - initial)) / (2 * step)
            errors.append(abs(numerical - float(slope)))
        cases.append({"exponent": exponent, "adoption_derivative": str(exact[1]),
                      "consumer_surplus_derivative": str(exact_surplus)})
    check(max(errors) < 1e-8, "Targeted buyer surplus or equilibrium response mismatch")
    return {"cases": cases, "max_absolute_error": max(errors)}


def boundary_directions():
    # The base subsidy is positive, so both subsidy directions are feasible.
    s0, p, cap, target = 0.1, 0.6, 0.75, 1.0

    def equilibrium(subsidy, capacity):
        def support(n):
            return min(target, capacity / n)
        n = root(lambda x: p - subsidy - (1 - x) * (1 + sqrt(support(x))), 0.25, 1)
        return n, support(n)

    n0, h0 = equilibrium(s0, cap)
    A, B_h = 0.5, 1/16
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, A), (-1, -A), (1, 2*A), (-1, -2*A))
    errors = []
    step = 1e-6
    for ds, dK in directions:
        dh = min(0, (dK - target * A * ds) / (n0 + target * B_h))
        dn = A * ds + B_h * dh
        n, h = equilibrium(s0 + step * ds, cap + step * dK)
        errors.extend((abs((n - n0) / step - dn), abs((h - h0) / step - dh)))
    check(max(errors) < 3e-6, "One-sided equilibrium derivative failed at capacity boundary")
    return {"directions": len(directions), "max_absolute_error": max(errors)}


def individual_use_and_benefit():
    # Fixed original users. Each row gives mass, valuation and separate local response schedules.
    people = ((0.30, 1, 0.15, 0.25, 1.60, -0.20),
              (0.20, 3, 0.65, -0.12, 0.50, 0.42))
    capacity, load, entrant_weight, incumbent_weight, need = 0.4, 0.5, 0.6, 1.0, 2.0
    h = capacity / load
    v = incumbent_weight * h / need
    scale = h * entrant_weight / load * incumbent_weight / need
    valuation = sum(mass * theta for mass, theta, *_ in people)
    use_loss = conditional_loss = 0.0
    sum_chi = sum_nu = sum_dchi = sum_dnu = 0.0
    for mass, theta, chi0, dchi, nu0, dnu in people:
        chi, nu = chi0 + dchi * v, nu0 + dnu * v
        weight = mass * theta
        use_loss += scale * weight * dchi * nu
        conditional_loss += scale * weight * chi * dnu
        sum_chi += weight * chi
        sum_nu += weight * nu
        sum_dchi += weight * dchi
        sum_dnu += weight * dnu
    shortcut = scale * (sum_dchi * sum_nu + sum_chi * sum_dnu) / valuation

    def gross(entrants):
        adequacy = incumbent_weight * capacity / ((load + entrant_weight * entrants) * need)
        return sum(m * theta * (c + dc * adequacy) * (b + db * adequacy)
                   for m, theta, c, dc, b, db in people)

    step = 1e-5
    total = use_loss + conditional_loss
    numerical_loss = (gross(-step) - gross(step)) / (2 * step)
    error = abs(total - numerical_loss)
    check(error < 1e-9 and abs(shortcut - total) > 0.001,
          "Fixed-cohort loss or the distinction from products of averages failed")
    return {"use_component": use_loss, "conditional_component": conditional_loss,
            "loss": total, "product_of_separate_means": shortcut, "absolute_error": error}


def marginal_episode_load():
    # Exact arithmetic. Age-specific replacement rates shift while total replacements stay fixed.
    ages = (F(4), F(4))
    weights = (F(1, 2), F(1))
    base = (F(1, 4), F(1, 4))
    first, w_first, w_refit = F(2), F(1), F(2)

    def grouped(n, hazards):
        replacements = sum(m * rate for m, rate in zip(ages, hazards))
        fits = n + replacements
        fitting_weight = (w_first * n + w_refit * replacements) / fits
        routine_load = sum(w * m * (1 - rate) for w, m, rate in zip(weights, ages, hazards))
        return fits * fitting_weight + routine_load, replacements, fitting_weight

    reference, refits, average = grouped(first, base)
    extra, _, _ = grouped(first + 1, base)
    shift = (F(1, 8), F(-1, 8))
    changed, same_refits, _ = grouped(first, tuple(rate + change for rate, change in zip(base, shift)))
    predicted = sum((w_refit - w) * n * delta for w, n, delta in zip(weights, ages, shift))
    check(extra - reference == w_first and average != w_first, "First-entrant weight replaced by the average")
    check(same_refits == refits and changed - reference == predicted != 0,
          "Age-composition effect lost at constant replacement count")
    return {"first_fitting_marginal_weight": str(w_first), "average_fitting_weight": str(average),
            "load_change_at_constant_refittings": str(predicted)}


if __name__ == "__main__":
    print(json.dumps({"budget": budget_boundary(), "conditional_optimum": conditional_budget_optimum(),
                      "adequacy": adequacy_derivative(), "individual_channels": individual_use_and_benefit(),
                      "device_age": age_bins(), "age_load": marginal_episode_load(),
                      "future_load": future_incumbent_load(), "group_adoption": opposing_adoption_responses(),
                      "targeted_buyer_surplus": targeted_buyer_surplus(),
                      "capacity_boundary": boundary_directions()}, indent=2))
