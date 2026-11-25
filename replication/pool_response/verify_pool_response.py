"""Check the local two-shock restriction against nonlinear equilibrium re-solves.

Illustrative mathematics only. Python 3.8+ standard library; no source data.
"""
import json
from math import sqrt


# Three recipient groups with uniform valuations, linear benefit and interior cutoffs.
MASS = (10 / 28, 7 / 28, 11 / 28)
WEIGHT = (1.0, 1.6, 0.5)
BASE = (0.8, 0.9, 0.7)
SLOPE = (0.6, 0.3, 0.8)
PRICE = (0.55, 0.62, 0.48)
CAPACITY = 0.5
STEP = 1e-5


def equilibrate(subsidy, capacity):
    def adoption(h):
        return tuple(m * (1 - (p - (subsidy if g == 0 else 0)) / (a + b * h))
                     for g, (m, p, a, b) in enumerate(zip(MASS, PRICE, BASE, SLOPE)))

    def resource_use(h):
        return h * sum(w * n for w, n in zip(WEIGHT, adoption(h)))

    lower, upper = 0.0, 1.0
    while resource_use(upper) < capacity:
        upper *= 2
    for _ in range(90):
        midpoint = (lower + upper) / 2
        if resource_use(midpoint) < capacity:
            lower = midpoint
        else:
            upper = midpoint
    h = (lower + upper) / 2
    masses = adoption(h)
    assert all(0 < n < m for n, m in zip(masses, MASS))
    return h, masses


def differences(positive, negative):
    return [(x - y) / (2 * STEP) for x, y in zip(positive, negative)]


def linked_pool_responses():
    """Three equally sized groups use the first pool, both pools or the second pool."""
    capacity = 7/18

    def resource_root(residual):
        lower, upper = .5, 1.5
        assert residual(lower) < 0 < residual(upper)
        for _ in range(54):
            mid = (lower+upper)/2
            if residual(mid) > 0:
                upper = mid
            else:
                lower = mid
        return (lower+upper)/2

    def solve(subsidy, complementary):
        def masses(x, y):
            middle = 1+2*sqrt(x*y) if complementary else 1+x+y
            return ((1-(1-subsidy)/(1+x))/3, (1-1/middle)/3, (1-1/(1+y))/3)
        def clear_second(x):
            return resource_root(lambda y: y*sum(masses(x,y)[1:])-capacity)
        x = resource_root(lambda x: x*sum(masses(x,clear_second(x))[:2])-capacity)
        y = clear_second(x)
        n = masses(x,y)
        assert max(abs(x*sum(n[:2])-capacity), abs(y*sum(n[1:])-capacity)) < 2e-14
        return (x,y,*n)

    # Both technologies have identical values and first derivatives at h=(1,1).
    first, second = -330/1003, 24/1003
    exact = (first,second,1/6+first/12,(first+second)/27,second/12)
    results = {}
    for name, complement in [('additive',False),('complementary',True)]:
        base = solve(0,complement)
        near, far = solve(STEP,complement), solve(2*STEP,complement)
        observed = [(4*(a-b)-(c-b))/(2*STEP) for a,b,c in zip(near,base,far)]
        error = max(abs(a-b) for a,b in zip(observed,exact))
        assert error < 2e-8
        results[name] = dict(baseline=list(base),derivatives=observed,maximum_error=error)
    return dict(order=['intensity_1','intensity_2','adoption_1','adoption_2','adoption_3'],
                analytical=exact,technologies=results)


def main():
    h, _ = equilibrate(0, CAPACITY)
    a_j = MASS[0] / (BASE[0] + SLOPE[0] * h)
    gross_offset = h * WEIGHT[0] * a_j
    capacity_response = differences(equilibrate(0, CAPACITY + STEP)[1],
                                    equilibrate(0, CAPACITY - STEP)[1])
    results = []
    for supply_response in (0, gross_offset, 2 * gross_offset):
        d_j = gross_offset - supply_response
        upper = equilibrate(STEP, CAPACITY + STEP * supply_response)
        lower = equilibrate(-STEP, CAPACITY - STEP * supply_response)
        policy_response = differences(upper[1], lower[1])
        offsets = [-policy_response[g] / capacity_response[g] for g in (1, 2)]
        restriction = (policy_response[1] * capacity_response[2]
                       - policy_response[2] * capacity_response[1])
        # Add the compensating units to the policy. Then equilibrium h must be stationary.
        compensated_h = differences(
            [equilibrate(STEP, CAPACITY + STEP * (supply_response + d_j))[0]],
            [equilibrate(-STEP, CAPACITY - STEP * (supply_response + d_j))[0]])[0]
        errors = [abs(offset - d_j) for offset in offsets]
        errors += [abs(restriction), abs(compensated_h),
                   abs(policy_response[0] + d_j * capacity_response[0] - a_j)]
        assert max(errors) < 1e-8
        results.append({'supply_response': supply_response, 'offset': d_j,
                        'recovered_from_untargeted_groups': offsets,
                        'cross_product': restriction, 'largest_error': max(errors)})
    # In two separate pools a targeted entry shock hits only the first pool, while
    # extra capacity is independently deployed to both. The two untreated outcomes
    # are group adoptions in otherwise identical pools: their tests must disagree.
    first_pool_slope = differences(equilibrate(STEP, CAPACITY)[1],
                                   equilibrate(-STEP, CAPACITY)[1])[1]
    two_pool_cross_product = first_pool_slope * capacity_response[1] / 2
    assert abs(two_pool_cross_product) > 1e-4
    print(json.dumps({'pooled_checks': results,
                      'separate_pools_counterexample': two_pool_cross_product,
                      'overlapping_patient_groups': linked_pool_responses()}, indent=2))


if __name__ == '__main__':
    main()
