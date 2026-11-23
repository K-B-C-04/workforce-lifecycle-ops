"""
Workforce Lifecycle Operations: the strategy and operations read-out.

Turns the three lifecycle datasets into the questions leadership actually asks:
  Onboarding:  Can the team absorb the hiring plan? Where is setup work piling up?
  Offboarding: What company equipment and access is still outstanding, and what is it worth?
  Contractors: How dependent are we on a few vendors and on contractors in one department?

Usage (from the repo root):  python analysis/analyze.py
Prints the findings as JSON and writes charts to images/.
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "images"
IMG.mkdir(exist_ok=True)
AS_OF = pd.Timestamp("2026-11-20")

INK, MUTED, GRID = "#1f2937", "#6b7280", "#e5e7eb"
ACCENT, ALERT, CALM, OK = "#4338ca", "#dc2626", "#cbd5e1", "#16a34a"
SERIES = ["#4338ca", "#0891b2", "#d97706", "#9ca3af"]
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False,
})


def title(ax, text, sub=None):
    ax.set_title(text, loc="left", color=INK, fontweight="bold", pad=20 if sub else 8)
    if sub:
        ax.text(0, 1.02, sub, transform=ax.transAxes, color=MUTED, fontsize=9)


def save(fig, name):
    fig.savefig(IMG / name, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


on = pd.read_csv(ROOT / "data" / "onboarding.csv", parse_dates=["cohort_start"])
off = pd.read_csv(ROOT / "data" / "offboarding.csv", parse_dates=["termination_date"])
ct = pd.read_csv(ROOT / "data" / "contractors.csv", parse_dates=["start_date", "end_date"])
F = {}

# =============================================================== Onboarding
started = on[on["cohort_start"] <= AS_OF]
on["pending_setup"] = ~(on["asset_tracker_updated"] & on["security_key_shipped"] & on["nh_task_assigned"])
summer = on[on["cohort_start"] < "2026-09-01"].groupby("cohort").size().mean()
fall = on[on["cohort_start"] >= "2026-09-01"].groupby("cohort").size().mean()
by_analyst = on.groupby("analyst").agg(hires=("hire_id", "count"), pending=("pending_setup", "sum"))
by_analyst["share_hires"] = by_analyst["hires"] / by_analyst["hires"].sum()
by_analyst["share_pending"] = by_analyst["pending"] / by_analyst["pending"].sum()
lead = started.groupby("work_mode")["hardware_lead_days"].median()
F["onboarding"] = {
    "hires": int(len(on)), "cohorts": int(on["cohort"].nunique()),
    "avg_cohort_summer": round(summer, 1), "avg_cohort_fall": round(fall, 1),
    "fall_vs_summer": round(fall / summer, 2),
    "remote_share_pct": round((on["work_mode"] == "Remote").mean() * 100),
    "pending_setup": int(on["pending_setup"].sum()),
    "top_analyst_share_hires_pct": round(by_analyst["share_hires"].max() * 100),
    "top_analyst_share_pending_pct": round(by_analyst.loc[by_analyst["share_hires"].idxmax(), "share_pending"] * 100),
    "lead_days_hq": float(lead["HQ"]), "lead_days_remote": float(lead["Remote"]),
}

# chart: cohort volume by analyst
piv = on.pivot_table(index="cohort_start", columns="analyst", values="hire_id", aggfunc="count").fillna(0)
fig, ax = plt.subplots(figsize=(9.5, 4.2))
bottom = np.zeros(len(piv))
x = np.arange(len(piv))
for col, color in zip(piv.columns, SERIES):
    ax.bar(x, piv[col], bottom=bottom, color=color, width=0.7, label=col)
    bottom += piv[col].values
for i, v in enumerate(bottom):
    ax.text(i, v + 0.6, int(v), ha="center", fontsize=8, color=INK)
ax.axvline(5.5, color=GRID, linestyle="--")
ax.text(5.6, bottom.max() * 0.98, "Fall hiring wave", color=MUTED, fontsize=9, va="top")
ax.set_xticks(x, [d.strftime("%b %d") for d in piv.index], fontsize=8, rotation=45, ha="right")
ax.set_ylabel("New hires")
ax.legend(frameon=False, fontsize=8, ncol=4, loc="upper left")
title(ax, "Onboarding demand: cohort size doubled in the fall",
      f"Average cohort {summer:.0f} hires (Jun–Aug) → {fall:.0f} (Sep–Nov), same four analysts")
save(fig, "onboarding_capacity.png")

# chart: workload share vs pending share, and lead time
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={"width_ratios": [1.4, 1]})
yy = np.arange(len(by_analyst))
ax1.barh(yy + 0.18, by_analyst["share_hires"] * 100, height=0.36, color=CALM, label="Share of hires")
ax1.barh(yy - 0.18, by_analyst["share_pending"] * 100, height=0.36, color=ACCENT, label="Share of pending setup")
ax1.set_yticks(yy, by_analyst.index)
ax1.invert_yaxis()
ax1.set_xlabel("% of total")
ax1.legend(frameon=False, fontsize=8, loc="lower right")
title(ax1, "Setup backlog follows the assignment imbalance")
for mode, color, pos in (("HQ", CALM, 0), ("Remote", ALERT, 1)):
    vals = started.loc[started["work_mode"] == mode, "hardware_lead_days"]
    ax2.boxplot(vals, positions=[pos], widths=0.5, patch_artist=True, showfliers=False,
                boxprops=dict(facecolor=color, edgecolor=color), medianprops=dict(color=INK))
    ax2.text(pos, vals.median() + 0.3, f"{vals.median():.0f} days", ha="center", fontsize=9, color=INK)
ax2.set_xticks([0, 1], ["HQ hires", "Remote hires"])
ax2.set_ylabel("Days to receive hardware")
title(ax2, "Remote hires wait twice as long")
save(fig, "onboarding_bottlenecks.png")

# ============================================================== Offboarding
steps = ["equipment_return", "security_key", "account_disable", "mdm_removal",
         "license_reclaim", "tracker_update", "laptop_wipe"]
labels = {"equipment_return": "Equipment returned", "security_key": "Security key recovered",
          "account_disable": "Accounts disabled", "mdm_removal": "Device management removed",
          "license_reclaim": "Licenses reclaimed", "tracker_update": "Asset tracker updated",
          "laptop_wipe": "Laptop wiped"}
pending_rate = {s: (off[s] == "Pending").mean() for s in steps}
outstanding = off[off["equipment_return"] == "Pending"]
F["offboarding"] = {
    "departures": int(len(off)),
    "complete_pct": round((off["status"] == "Complete").mean() * 100),
    "slowest_step": labels[max(pending_rate, key=pending_rate.get)],
    "slowest_step_pending_pct": round(max(pending_rate.values()) * 100),
    "fastest_step": labels[min(pending_rate, key=pending_rate.get)],
    "laptops_outstanding": int(len(outstanding)),
    "laptop_value_outstanding_usd": int(outstanding["laptop_value_usd"].sum()),
    "remote_share_of_outstanding_pct": round((outstanding["work_mode"] == "Remote").mean() * 100),
    "remote_share_of_departures_pct": round((off["work_mode"] == "Remote").mean() * 100),
    "unreturned_rate_remote_pct": round((off.loc[off["work_mode"] == "Remote", "equipment_return"] == "Pending").mean() * 100),
    "unreturned_rate_hq_pct": round((off.loc[off["work_mode"] == "HQ", "equipment_return"] == "Pending").mean() * 100),
    "legal_holds": int(off["legal_hold"].sum()),
    "accounts_still_active": int((off["account_disable"] == "Pending").sum()),
    "peak_month": off["termination_date"].dt.strftime("%b").value_counts().idxmax(),
}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4), gridspec_kw={"width_ratios": [1.3, 1]})
order = sorted(steps, key=lambda s: pending_rate[s])
vals = [pending_rate[s] * 100 for s in order]
ax1.barh([labels[s] for s in order], vals,
         color=[ALERT if s in ("equipment_return", "laptop_wipe") else ACCENT for s in order])
for i, v in enumerate(vals):
    ax1.text(v + 0.4, i, f"{v:.0f}%", va="center", fontsize=8, color=MUTED)
ax1.set_xlabel("% of departures with this step still pending")
title(ax1, "Physical recovery is the bottleneck", "Digital steps close fast; laptops come back slowly")
val = outstanding.groupby("work_mode")["laptop_value_usd"].sum().reindex(["HQ", "Remote"]).fillna(0)
ax2.bar(val.index, val.values / 1000, color=[CALM, ALERT], width=0.55)
for i, v in enumerate(val.values):
    ax2.text(i, v / 1000 + 0.5, f"${v / 1000:.0f}K", ha="center", fontsize=10, color=INK, fontweight="bold")
ax2.set_ylabel("Laptop value outstanding ($K)")
title(ax2, f"${F['offboarding']['laptop_value_outstanding_usd'] / 1000:.0f}K of hardware not yet recovered",
      f"{F['offboarding']['remote_share_of_outstanding_pct']}% of it with remote leavers")
save(fig, "offboarding_risk.png")

# ============================================================== Contractors
active = ct[ct["status"] == "Active"]
vshare = active["vendor"].value_counts(normalize=True)
hhi = float((vshare * 100).pow(2).sum())
ct["start_q"] = ct["start_date"].dt.to_period("Q")
ct["end_q"] = ct["end_date"].dt.to_period("Q")
quarters = pd.period_range("2024Q1", "2026Q4", freq="Q")
flow = pd.DataFrame({
    "starts": [int((ct["start_q"] == q).sum()) for q in quarters],
    "exits": [int(((ct["end_q"] == q) & (ct["end_date"] <= AS_OF)).sum()) for q in quarters],
    "active_end": [int(((ct["start_date"] <= min(q.end_time, AS_OF)) & (ct["end_date"] > min(q.end_time, AS_OF))).sum())
                   for q in quarters],
}, index=[str(q) for q in quarters])
dept_share = active["department"].value_counts(normalize=True)
tenure = (ct.loc[ct["status"] == "Offboarded", "end_date"] - ct.loc[ct["status"] == "Offboarded", "start_date"]).dt.days
F["contractors"] = {
    "engagements": int(len(ct)), "active": int(len(active)),
    "vendors": int(ct["vendor"].nunique()), "countries": int(ct["country"].nunique()),
    "top3_vendor_share_pct": round(vshare.head(3).sum() * 100),
    "top_vendor": vshare.index[0], "top_vendor_share_pct": round(vshare.iloc[0] * 100),
    "vendor_hhi": round(hhi),
    "top_dept": dept_share.index[0], "top_dept_share_pct": round(dept_share.iloc[0] * 100),
    "median_tenure_months": round(tenure.median() / 30.4, 1),
    "active_growth_pct_2024q4_to_2026q4": round((flow.loc["2026Q4", "active_end"] / flow.loc["2024Q4", "active_end"] - 1) * 100),
}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw={"width_ratios": [1.1, 1]})
top = vshare.head(10).iloc[::-1] * 100
ax1.barh(top.index, top.values, color=[ALERT if i >= len(top) - 3 else CALM for i in range(len(top))])
for i, v in enumerate(top.values):
    ax1.text(v + 0.3, i, f"{v:.0f}%", va="center", fontsize=8, color=MUTED)
ax1.set_xlabel("% of active contractors")
title(ax1, "Vendor concentration",
      f"Top 3 vendors hold {F['contractors']['top3_vendor_share_pct']}% of active contractors")
xq = np.arange(len(flow))
ax2.bar(xq - 0.2, flow["starts"], width=0.4, color=OK, label="Starts")
ax2.bar(xq + 0.2, flow["exits"], width=0.4, color=CALM, label="Exits")
ax2b = ax2.twinx()
ax2b.plot(xq, flow["active_end"], color=ACCENT, linewidth=2.2, marker="o", markersize=3, label="Active (end of quarter)")
ax2b.spines["top"].set_visible(False)
ax2b.tick_params(colors=MUTED)
ax2.set_xticks(xq, [q.replace("20", "'", 1) for q in flow.index], fontsize=7.5, rotation=45)
ax2.set_ylabel("Starts / exits per quarter")
ax2b.set_ylabel("Active headcount", color=MUTED)
h1, l1 = ax2.get_legend_handles_labels()
h2, l2 = ax2b.get_legend_handles_labels()
ax2.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="upper left")
title(ax2, "Contractor flow by quarter", "Q4 2026 is quarter-to-date")
save(fig, "contractor_strategy.png")

print(json.dumps(F, indent=2, default=str))
print(by_analyst.round(2))
print(flow.tail(6))
print(dept_share.round(2).head(4))
