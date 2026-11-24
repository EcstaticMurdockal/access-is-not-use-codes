"""Generate original vector figures for the finals manuscript.

All numerical curves are explicitly illustrative and reproduce the primitives
stated in the manuscript.  No curve is a clinical estimate.
"""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
for _font in (Path.home()/".local/share/fonts/arial").glob("*.TTF"):
    font_manager.fontManager.addfont(str(_font))
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)

NAVY = "#183650"
BLUE = "#397FB8"
ORANGE = "#BD8744"
TEAL = "#528E4D"
PURPLE = "#9276B5"
GOLD = "#C2762B"
GREY = "#183650"
LIGHT_BLUE = "#EEF5FD"
LIGHT_ORANGE = "#FFF3E7"
LIGHT_TEAL = "#EFF9ED"
LIGHT_GREY = "#F3EEFC"

mpl.rcParams.update({
    "font.family": "Arial",
    "mathtext.fontset": "cm",
    "text.color": NAVY,
    "axes.labelcolor": NAVY,
    "axes.titlecolor": NAVY,
    "font.size": 10.5,
    "axes.formatter.use_mathtext": True,
    "axes.unicode_minus": False,
    "axes.edgecolor": NAVY,
    "xtick.color": NAVY,
    "ytick.color": NAVY,
    "axes.titlesize": 10.5,
    "axes.labelsize": 10.5,
    "legend.fontsize": 9.2,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "lines.linewidth": 2.0,
    "lines.markersize": 4.5,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def save(fig, stem):
    # Text is neutral black; color encodes plotted quantities, not typography.
    from matplotlib.text import Text
    for artist in fig.findobj(match=Text):
        artist.set_color("black")
    # Match the approved illustration: black type, stronger headings, soft color fields.
    panel_fills = ["#FFF9F0", "#F3F8FE", "#F4F9F0", "#F6F2FB"]
    panel_edges = ["#C9A46A", "#6E9EC9", "#83A76B", "#AA94C2"]
    for i, ax in enumerate(fig.axes):
        if ax.axison:
            ax.set_facecolor(panel_fills[i % 4])
            for spine in ax.spines.values():
                spine.set_color("#252525")
                spine.set_linewidth(.8)
            ax.tick_params(colors="black")
            ax.set_axisbelow(True)
            ax.title.set_fontweight("bold")
            ax.title.set_fontsize(10.2)
            ax.set_title(ax.get_title(), pad=12, color="black", fontweight="bold")
    if fig._suptitle is not None:
        fig._suptitle.set_fontweight("bold")
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.png", dpi=240, bbox_inches="tight")
    plt.close(fig)


def box(ax, xy, width, height, text, face, edge=NAVY, fontsize=8.4,
        radius=0.012, linewidth=1.0):
    patch = FancyBboxPatch(
        xy, width, height,
        boxstyle=f"round,pad=0.015,rounding_size={radius}",
        linewidth=linewidth, edgecolor=edge, facecolor=face,
    )
    ax.add_patch(patch)
    ax.text(xy[0] + width / 2, xy[1] + height / 2, text,
            ha="center", va="center", fontsize=fontsize, color="#183650")
    return patch


def arrow(ax, start, end, label=None, color=GREY, rad=0.0, label_offset=(0, 0)):
    patch = FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=11,
        linewidth=1.2, color=color,
        connectionstyle=f"arc3,rad={rad}", shrinkA=1, shrinkB=1,
    )
    ax.add_patch(patch)
    if label:
        mx = (start[0] + end[0]) / 2 + label_offset[0]
        my = (start[1] + end[1]) / 2 + label_offset[1]
        ax.text(mx, my, label, ha="center", va="center", fontsize=7.4,
                color=color, bbox=dict(facecolor="white", edgecolor="none", pad=0.7))


def benchmark_tradeoff():
    def solve(s, K=1.0):
        q = lambda h: 0.2 + np.sqrt(h)
        n = brentq(lambda z: (1-z)*q(K/z) - (0.5-s), 1e-10, 1.0)
        return n, K/n

    subsidies = np.linspace(0.0, 0.49, 150)
    vals = np.array([solve(s) for s in subsidies])
    n, h = vals[:, 0], vals[:, 1]
    fig, axes = plt.subplots(1, 3, figsize=(8.0, 3.05), constrained_layout=True)

    axes[0].plot(subsidies, n, color=BLUE, lw=2.25)
    axes[0].scatter([0, .49], [n[0], n[-1]], color=BLUE, s=25, zorder=3)
    axes[0].set(title="(a) Device access expands", xlabel="Device subsidy  $s$", ylabel="Adopter mass  $N(s)$")

    axes[1].plot(subsidies, h, color=ORANGE, lw=2.25)
    axes[1].scatter([0, .49], [h[0], h[-1]], color=ORANGE, s=25, zorder=3)
    axes[1].set(title="(b) Shared support is diluted", xlabel="Device subsidy  $s$", ylabel="Support intensity  $h(s)=K/N(s)$")

    # Proposition 1 in a policy-region graph.  This is a theoretical graph,
    # not a model architecture diagram and not an empirical estimate.
    rho = np.linspace(0.001, .94, 220)
    for fiscal, color, label in [(0.0, BLUE, r"$\lambda\delta_F=0$"),
                                 (0.15, PURPLE, r"$\lambda\delta_F=0.15$"),
                                 (0.30, ORANGE, r"$\lambda\delta_F=0.30$")]:
        axes[2].plot(rho, (rho + fiscal)/(1-rho), lw=1.9,
                     color=color, label=label)
    axes[2].set(title="(c) Welfare threshold", xlabel=r"Congestion share  $\rho$",
                ylabel=r"Required external value  $\eta_c$")
    axes[2].set_ylim(0, 8); axes[2].set_xlim(0, .9)
    axes[2].legend(frameon=False, loc="upper left", handlelength=1.5)

    for ax in axes:
        ax.grid(axis="y", color="#E6EDF5", lw=.7)
    axes[0].set_xlim(0, .50)
    axes[1].set_xlim(0, .50)
    fig.suptitle("Illustrative benchmark: access, support, and the welfare threshold", y=1.05, fontsize=10.7, weight="bold")
    save(fig, "benchmark_access_support_tradeoff")


def hsp_multiyear():
    """Plot official HSP annual aggregates without treating them as capacity."""
    years = np.array(["2021--22", "2022--23", "2023--24", "2024--25"])
    active = np.array([811991, 802861, 806473, 834048], dtype=float)
    new = np.array([222284, 291576, 317420, 325923], dtype=float)
    returning = np.array([589707, 511355, 496879, 515526], dtype=float)
    fitting = np.array([184947, 197330, 197062, 201610], dtype=float)
    maintenance = np.array([622630, 534634, 504852, 519989], dtype=float)
    rehabilitation = np.array([6007, 7917, 7685, 11207], dtype=float)
    review = np.array([302294, 383623, 403248, 420136], dtype=float)
    practitioners = np.array([3273, 3181, 3445, 3619], dtype=float)
    x = np.arange(len(years))

    fig, axes = plt.subplots(1, 3, figsize=(8.0, 3.15), constrained_layout=True)
    axes[0].plot(x, active/1000, color=BLUE, marker="o", label="Active")
    axes[0].plot(x, returning/1000, color=TEAL, marker="s", ls="--", label="Returning")
    axes[0].plot(x, new/1000, color=ORANGE, marker="^", label="New")
    axes[0].set(title="(a) Reported client counts", ylabel="People (thousands)", ylim=(0,900))
    axes[0].legend(frameon=False, loc="upper center", bbox_to_anchor=(.5,-.34), ncol=1, handlelength=1.2)

    for vals, color, marker, label in [
        (fitting, BLUE, "o", "Fitting"),
        (maintenance, ORANGE, "s", "Maintenance"),
        (review, PURPLE, "^", "Review"),
        (rehabilitation, TEAL, "D", "Rehabilitation")]:
        axes[1].plot(x, 100*vals/active, color=color, marker=marker,
                     ms=4.2, lw=2.0, ls={"Fitting":"-", "Maintenance":"--", "Review":"-.", "Rehabilitation":":"}[label], label=label)
    axes[1].set(title="(b) Paid service claims", ylabel="Claims per 100 active clients")
    axes[1].legend(frameon=False, loc="upper center", bbox_to_anchor=(.5,-.34), ncol=2, handlelength=1.4)

    ratio = active/practitioners
    axes[2].plot(x, ratio, color=PURPLE, marker="o", lw=2.0, ms=4.2)
    for xi, yi in zip(x, ratio):
        axes[2].text(xi, yi+2.3, f"{yi:.0f}", ha="center", fontsize=7.7, color=GREY)
    axes[2].set(title="(c) Scale proxy", ylabel="Active clients per practitioner")
    axes[2].set_ylim(210, 265)

    for ax in axes:
        ax.set_xticks(x, years, rotation=28, ha="right")
        ax.grid(axis="y", color="#E6EDF5", lw=.65)
    fig.suptitle("Australian Hearing Services Program: distinct stocks, claims, and workforce counts",
                 y=1.06, fontsize=10.7, weight="bold")
    save(fig, "hsp_multiyear_descriptive")


def nhanes_association():
    """Visualize the reproduced association without implying causality."""
    import json
    record = json.loads((ROOT / "nhanes_reproduction_results.json").read_text())
    rates = np.array([record["weighted_regular_wearing"]["recent_test"], record["weighted_regular_wearing"]["earlier_or_never"]])
    labels = ["Specialist test\n<1 year ago", "$\\geq$1 year ago\nor never"]
    fit = record["primary_adjusted_logit"]
    odds = fit["odds_ratio"]
    lo, hi = fit["ci_95"]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.9), constrained_layout=True)
    axes[0].bar([0, 1], 100*rates, color=["#86B5D9", "#BBA3D3"], edgecolor=[BLUE,PURPLE], linewidth=1.0, width=.62)
    for i, r in enumerate(rates):
        axes[0].text(i, 100*r+1.5, f"{100*r:.1f}%", ha="center", fontsize=9.5)
    axes[0].set(title="(a) Survey-weighted regular wearing", ylabel="Percent of current users")
    axes[0].set_xticks([0, 1], labels)
    axes[0].set_ylim(0, 105)

    axes[1].axvline(1, color=GREY, lw=1.0, ls="--")
    axes[1].errorbar([odds], [0], xerr=[[odds-lo], [hi-odds]], fmt="o",
                     color=PURPLE, ecolor=PURPLE, capsize=4, lw=1.8)
    axes[1].set_xscale("log")
    axes[1].set_xlim(.7, 9)
    axes[1].set_yticks([0], ["Adjusted association"])
    axes[1].set_ylim(-.45, .45)
    axes[1].set_xticks([1, 2, 4, 8], ["1", "2", "4", "8"])
    axes[1].set(title="(b) Survey-weighted logistic model", xlabel="Odds ratio (log scale)")
    axes[1].text(odds, .16, f"{odds:.2f}  [{lo:.2f}, {hi:.2f}]", ha="center", fontsize=9.5, color=NAVY)
    for ax in axes:
        ax.grid(axis="y", color="#E6EDF5", lw=.65)
    fig.suptitle("NHANES 2017--March 2020: specialist-test recency and hearing-aid use",
                 y=1.06, fontsize=10.7, weight="bold")
    save(fig, "nhanes_access_use_association")


def group_model(wL, s=(0.0, 0.0), K=0.3, eta=0.5, lam=0.1, cx=0.25):
    s = np.asarray(s, dtype=float)
    m = np.array([0.5, 0.5]); w = np.array([wL, 1.0])
    a = np.array([0.8, 0.2]); b = np.array([0.2, 1.0]); p = np.array([0.5, 0.5])

    def at(h):
        q = a + b * (-np.expm1(-w*h))
        t = np.clip((p-s)/q, 0, 1)
        n = m*(1-t)
        return q, t, n

    hi = 1.0
    while hi*np.dot(w, at(hi)[2]) < K:
        hi *= 2
    h = brentq(lambda z: z*np.dot(w, at(z)[2])-K, 1e-12, hi)
    q, t, n = at(h)
    D = w@n; M = m*(1-t*t)/2
    qp = b*w*np.exp(-w*h); S = M@qp
    A = m/q; B = m*t*qp/q; Lambda = D + h*(w@B)
    dhds = -h*w*A/Lambda
    dns = np.diag(A) + np.outer(B, dhds)
    C = w*h*S/D
    J = (1+eta)*(t*q-C) - p - lam*s
    Ws = J@dns - lam*n
    return Ws, dns


def heterogeneity_policy():
    weights = np.linspace(0, 1.0, 161)
    Ws = []
    spill = []
    for w in weights:
        out, dns = group_model(w)
        Ws.append(out)
        spill.append(dns[1, 0])
    Ws = np.asarray(Ws); spill = np.asarray(spill)

    fig, axes = plt.subplots(1, 2, figsize=(7.7, 3.35), constrained_layout=True)
    axes[0].axhline(0, color="#7E9FCA", lw=.9)
    axes[0].plot(weights, Ws[:, 0], color=BLUE, lw=2.1, label=r"$W_{s_L}$")
    axes[0].plot(weights, Ws[:, 1], color=ORANGE, lw=2.1, label=r"$W_{s_H}$")
    axes[0].set(title="(a) Local welfare derivatives", xlabel=r"Group-$L$ allocation weight  $w_L$", ylabel="Welfare derivative (model units)")
    axes[0].legend(frameon=False)

    axes[1].axhline(0, color="#7E9FCA", lw=.9)
    axes[1].plot(weights, spill, color=PURPLE, lw=2.1)
    axes[1].set(title="(b) Cross-group adoption spillover", xlabel=r"Group-$L$ allocation weight  $w_L$", ylabel=r"$\partial n_H/\partial s_L$")

    for ax in axes:
        ax.grid(axis="y", color="#E6EDF5", lw=.7)
        ax.set_xlim(0, 1.0)
    fig.suptitle("Illustrative heterogeneity: institutional resource claims change policy spillovers", y=1.05, fontsize=10.7, weight="bold")
    save(fig, "heterogeneity_policy_effects")


def capacity_regimes():
    fig,ax=plt.subplots(figsize=(7,3.5),layout='constrained')
    n=np.linspace(.08,1.2,300)
    ax.plot(n,np.minimum(1,.6/n),color=TEAL,lw=2.2)
    ax.axvline(.6,color=GREY,ls='--',lw=.8)
    ax.text(.3,1.13,'Slack capacity',ha='center',fontsize=10)
    ax.text(.92,1.13,'Binding capacity',ha='center',fontsize=10)
    ax.text(.28,.86,r'$h=\bar h$',ha='center')
    ax.text(.98,.85,r'$h=K/N$',ha='center')
    ax.set(xlim=(.08,1.2),ylim=(.4,1.22),xlabel=r'Recipient mass $N$',ylabel=r'Delivered support per recipient $h$')
    ax.grid(axis='y',color='#E6EDF5',lw=.6)
    save(fig,'capacity_regimes')


if __name__ == "__main__":
    benchmark_tradeoff()
    heterogeneity_policy()
    capacity_regimes()
    hsp_multiyear()
    nhanes_association()
    from publication_diagrams import generate
    import sys
    generate(sys.modules[__name__])
    from visual_audit_additions import generate as additions
    additions(sys.modules[__name__])
    print(f"Wrote figures to {OUT}")
