"""Exact enumeration for the booking-release extension. Run with Python 3."""
from fractions import Fraction
from itertools import product
import json
from pathlib import Path


def service(rostered, booked, attendance, recovery):
    new = attendance * booked
    waiting = rostered - booked + recovery * (booked - new)
    idle = rostered - new - waiting
    return new, waiting, idle


def main():
    shares = [Fraction(i, 10) for i in range(11)]
    count = 0
    for booked, attendance, recovery in product(range(1, 100), shares, shares):
        new, waiting, idle = service(100, booked, attendance, recovery)
        _, waiting_next, _ = service(100, booked + 1, attendance, recovery)
        displacement = waiting - waiting_next
        assert idle == (1 - recovery) * (1 - attendance) * booked
        assert new >= 0 and waiting >= 0 and idle >= 0
        assert displacement == 1 - recovery * (1 - attendance)
        assert attendance <= displacement <= 1
        if recovery == 1:
            assert idle == 0 and displacement == attendance
        if recovery == 0:
            assert displacement == 1
        if attendance == 1:
            assert idle == 0 and displacement == 1
        count += 1
    new, waiting, idle = service(100, 20, Fraction(4, 5), Fraction(1, 2))
    assert (new, waiting, idle) == (16, 82, 2)
    result = {"exact_cases": count, "illustrative_units": {
        "rostered": 100, "booked": 20, "new_users": int(new),
        "incumbents": int(waiting), "unassigned_to_either_cohort": int(idle)}}
    output = json.dumps(result, indent=2) + "\n"
    Path(__file__).with_name("checks.json").write_text(output)
    print(output, end="")


if __name__ == "__main__":
    main()
