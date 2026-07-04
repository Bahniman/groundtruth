"""GroundTruth command line - the full lifecycle from a terminal.

    python -m groundtruth demo
    python -m groundtruth curve                 # advance-rate curve table
    python -m groundtruth finance --invoice 1863900 --score 0.91 --days 148
    python -m groundtruth compare --invoice 1863900 --days 148
"""
import argparse

from .finance import (Financing, FinancingTerms, advance_rate_for,
                      status_quo_cost, ADVANCE_CURVE)


def _inr(x):
    return f"Rs {x:,.0f}"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="groundtruth",
                                 description="Verified work becomes next-morning capital")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("demo", help="run the guided demo")
    sub.add_parser("curve", help="print the reliability -> advance-rate curve")

    f = sub.add_parser("finance", help="run one invoice through the waterfall")
    f.add_argument("--invoice", type=float, required=True)
    f.add_argument("--score", type=float, required=True)
    f.add_argument("--days", type=int, default=150)
    f.add_argument("--deduction", type=float, default=0.0)
    f.add_argument("--interest", type=float, default=0.11)
    f.add_argument("--fee", type=float, default=0.0035)

    c = sub.add_parser("compare", help="GroundTruth vs status quo for one invoice")
    c.add_argument("--invoice", type=float, required=True)
    c.add_argument("--days", type=int, default=150)
    c.add_argument("--score", type=float, default=0.91)
    c.add_argument("--informal-rate", type=float, default=0.22)

    a = ap.parse_args(argv)

    if a.cmd == "demo":
        from . import demo_scenario
        demo_scenario.run()

    elif a.cmd == "curve":
        print("reliability score -> bank advance rate")
        for floor, rate in ADVANCE_CURVE:
            if rate > 0:
                print(f"  >= {floor:.2f}   {rate*100:4.0f}%")
        print("   < 0.80   not financeable")
        print("\nThe curve is the moat: settled history moves a contractor up it.")

    elif a.cmd == "finance":
        fin = Financing(a.invoice, a.score,
                        FinancingTerms(a.interest, a.fee)).advance()
        if not fin.financeable:
            print(f"score {a.score:.2f} is below the financeable floor (0.80)")
            return
        fin.settle(a.days, treasury_deduction=a.deduction)
        for label, amount in fin.waterfall():
            sign = " " if amount >= 0 else "-"
            print(f"  {label:<58} {sign}{_inr(abs(amount))}")
        print(f"\n  contractor nets {fin.contractor_net_pct:.2f}% "
              f"(all-in cost {fin.effective_cost_pct:.2f}%)"
              f" | bank yield {fin.bank_yield_annualized():.2f}% p.a.")

    elif a.cmd == "compare":
        fin = Financing(a.invoice, a.score).advance().settle(a.days)
        sq = status_quo_cost(a.invoice, a.days, a.informal_rate)
        print(f"invoice {_inr(a.invoice)}, treasury settles day {a.days}\n")
        print(f"  STATUS QUO   first rupee: day {sq['first_rupee_day']}  "
              f"bridge cost {_inr(sq['bridge_cost'])}  nets {sq['net_pct']:.1f}%")
        print(f"  GROUNDTRUTH  first rupee: day 1 ({_inr(fin.advance_amount)})  "
              f"all-in cost {fin.effective_cost_pct:.2f}%  nets {fin.contractor_net_pct:.1f}%")
        print(f"\n  working capital unlocked on day 1: {_inr(fin.advance_amount)}")


if __name__ == "__main__":
    main()
