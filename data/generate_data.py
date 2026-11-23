"""
Generate the synthetic dataset for Workforce Lifecycle Operations.

Everything here is invented: the company (Larkspur & Vane, a fictional professional
services firm), every person, vendor, serial number and figure. No real company or
employee data is used.

Three linked datasets, one per stage of the workforce lifecycle:
  onboarding.csv   ~13 new-hire cohorts (Jun-Nov 2026): equipment and access setup
  offboarding.csv  departures (Jan-Nov 2026): equipment recovery and access removal checklist
  contractors.csv  contractor engagements (2023-2026) across vendors, countries and departments

Patterns planted so the analysis has decisions to support:
  - Onboarding volume doubles for the fall cohorts; one analyst absorbs most of the
    pending equipment work, and remote hires wait longer for hardware.
  - Offboarding: hardware recovery is the slowest checklist step; remote leavers
    return laptops far less reliably, leaving dollars of equipment outstanding.
  - Contractors: a few vendors hold a large share of active headcount, and one
    department relies on contractors far more than the rest.

Usage (from data/):  python generate_data.py
Writes the three CSVs here and ../docs/data.json for the interactive demo.
"""
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(2026)
HERE = Path(__file__).resolve().parent
TODAY = date(2026, 11, 20)

FIRST = """Avery Blake Cameron Dana Elliot Farah Gabriel Hana Isaac Jada Kenji Lena Marco Nadia Omar
Priya Quinn Rafael Sofia Tariq Uma Victor Wren Ximena Yusuf Zara Amara Bruno Chloe Diego Esme Felix
Grace Hugo Ines Jonah Keira Liam Maya Noah Olivia Pedro Rosa Samir Tessa Ulrich Vera Wesley Yara Zion
Adaeze Bilal Carmen Darius Elena Femi Gia Hiro Ivy Joel Kofi Lucia Mateo Nia Oscar Paloma Ravi Selin""".split()
LAST = """Abbott Ahn Alvarez Banks Becker Bello Castillo Chen Cole Dalton Diaz Duarte Ellis Eze Farrow
Fischer Grant Gupta Hale Haddad Ibarra Iyer Jensen Joshi Kaplan Kim Lam Lindqvist Mbeki Moreau Nakamura
Novak Okafor Ortiz Park Patel Quinlan Rahman Reyes Rossi Santos Sato Shah Silva Sung Tanaka Torres
Underwood Vance Varga Walsh Weber Xu Yilmaz Young Zamora Zhou Adeyemi Brennan Coelho Dube""".split()


def person():
    return f"{random.choice(FIRST)} {random.choice(LAST)}"


ANALYSTS = ["Analyst A", "Analyst B", "Analyst C", "Analyst D"]
DEPTS = {  # department -> (weight, typical titles)
    "Consulting": (30, ["Associate Consultant", "Consultant", "Senior Consultant"]),
    "Client Success": (20, ["Client Success Associate", "Client Success Manager"]),
    "Engineering": (18, ["Software Engineer", "Data Engineer", "QA Analyst"]),
    "Sales": (12, ["Account Executive", "Sales Development Rep"]),
    "Finance": (7, ["Financial Analyst", "Accountant"]),
    "People & Talent": (6, ["Recruiter", "HR Generalist"]),
    "Legal": (4, ["Paralegal", "Counsel"]),
    "Security": (3, ["Security Analyst"]),
}
HQ = "Arlington, VA (HQ)"
REMOTE_CITIES = ["Austin, TX", "Denver, CO", "Raleigh, NC", "Chicago, IL", "Atlanta, GA",
                 "Columbus, OH", "Phoenix, AZ", "Seattle, WA", "Boston, MA", "Nashville, TN"]
LAPTOPS = {  # model -> (replacement cost USD, weight)
    "ThinkBook 14 Pro": (1350, 50),
    "MacBook Pro 14": (2200, 20),
    "MacBook Air 13": (1300, 12),
    "EliteBook 840": (1450, 15),
    "Other": (1100, 3),
}


def pick(d):
    return random.choices(list(d), [v[0] if isinstance(v, tuple) else v for v in d.values()])[0]


def laptop():
    return random.choices(list(LAPTOPS), [v[1] for v in LAPTOPS.values()])[0]


def serial():
    return "LV" + "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=8))


# ------------------------------------------------------------- onboarding
cohort_dates = [date(2026, 6, 1), date(2026, 6, 15), date(2026, 7, 6), date(2026, 7, 20),
                date(2026, 8, 3), date(2026, 8, 17), date(2026, 9, 8), date(2026, 9, 21),
                date(2026, 10, 5), date(2026, 10, 19), date(2026, 11, 2), date(2026, 11, 16),
                date(2026, 11, 30)]
cohort_sizes = [14, 11, 16, 13, 18, 15, 34, 31, 28, 39, 24, 19, 22]  # fall hiring wave

onboarding = []
for cdate, size in zip(cohort_dates, cohort_sizes):
    for _ in range(size):
        dept = pick(DEPTS)
        remote = random.random() < 0.36
        analyst = random.choices(ANALYSTS, [40, 30, 20, 10])[0]
        upcoming = cdate > TODAY
        # one analyst carries the heaviest pending load; remote hires lag on hardware
        p_task = 0.55 if upcoming else 0.97
        p_asset = (0.35 if upcoming else 0.80) - (0.15 if analyst == "Analyst A" else 0) - (0.10 if remote else 0)
        ship_days = None
        if not upcoming:
            ship_days = round(max(1, random.gauss(9 if remote else 4, 2.5)), 1)
        onboarding.append({
            "hire_id": f"NH-{len(onboarding) + 1001}",
            "name": person(),
            "cohort_start": cdate.isoformat(),
            "cohort": f"Cohort {cdate:%m/%d}",
            "quarter": f"Q{(cdate.month - 1) // 3 + 1} 2026",
            "department": dept,
            "job_title": random.choice(DEPTS[dept][1]),
            "analyst": analyst,
            "work_location": random.choice(REMOTE_CITIES) if remote else HQ,
            "work_mode": "Remote" if remote else "HQ",
            "orientation": "Virtual" if remote else "In person",
            "laptop_model": laptop(),
            "nh_task_assigned": random.random() < p_task,
            "asset_tracker_updated": random.random() < p_asset,
            "security_key_shipped": random.random() < (p_asset + 0.08),
            "hardware_lead_days": ship_days if ship_days is not None else "",
        })

# ------------------------------------------------------------ offboarding
STEPS = ["equipment_return", "security_key", "account_disable", "mdm_removal",
         "license_reclaim", "tracker_update", "laptop_wipe"]
monthly = [14, 16, 19, 18, 22, 21, 26, 29, 41, 37, 23]  # Jan..Nov 2026
offboarding = []
for m, count in enumerate(monthly, start=1):
    for _ in range(count):
        d = date(2026, m, random.randint(1, 28))
        dept = pick(DEPTS)
        remote = random.random() < 0.42
        analyst = random.choices(ANALYSTS, [36, 34, 20, 10])[0]
        age = (TODAY - d).days
        legal_hold = random.random() < 0.09
        model = laptop()
        steps = {}
        # automated/IT-side steps finish fast; physical recovery depends on the leaver
        for s in STEPS:
            if s in ("account_disable", "license_reclaim"):
                done = random.random() < min(0.99, 0.80 + age / 200)
            elif s in ("equipment_return", "laptop_wipe"):
                base = 0.45 if remote else 0.80
                done = random.random() < min(0.97, base + age / 300)
            else:
                done = random.random() < min(0.97, 0.62 + age / 250)
            steps[s] = "Done" if done else "Pending"
        if steps["equipment_return"] == "Pending":
            steps["laptop_wipe"] = "Pending"
        if legal_hold:
            steps["laptop_wipe"] = "Legal hold"
        if steps["equipment_return"] == "Done" and random.random() < 0.06:
            steps["equipment_return"] = "Damaged"
        n_done = sum(v in ("Done", "Damaged", "Legal hold") for v in steps.values())
        status = "Complete" if n_done == len(STEPS) else ("Not started" if n_done == 0 else "In progress")
        offboarding.append({
            "offboard_id": f"OB-{len(offboarding) + 5001}",
            "name": person(),
            "department": dept,
            "work_mode": "Remote" if remote else "HQ",
            "work_location": random.choice(REMOTE_CITIES) if remote else HQ,
            "analyst": analyst,
            "termination_date": d.isoformat(),
            "laptop_model": model,
            "laptop_serial": serial(),
            "laptop_value_usd": LAPTOPS[model][0],
            "legal_hold": legal_hold,
            **steps,
            "status": status,
        })

# ----------------------------------------------------------- contractors
VENDORS = {  # fictional vendors -> weight (a few dominate)
    "Corvid Talent Partners": 22, "Bluefin Staffing": 17, "Northgate Technical": 12,
    "Sable & Finch Consulting": 9, "Orchard Workforce": 7, "Keystone Delivery Group": 6,
    "Harbor Lane Solutions": 5, "Pinecrest Analytics": 4, "Ridgeway Digital": 4,
    "Tallow Systems": 3, "Mirabel Partners": 3, "Quill & Lantern": 2, "Ashgrove Labs": 2,
    "Westerly Contracting": 2, "Fable Point": 2,
}
COUNTRIES = {  # country -> (region, weight)
    "United States": ("Americas", 48), "India": ("APAC", 22), "United Kingdom": ("EMEA", 6),
    "Australia": ("APAC", 5), "Canada": ("Americas", 4), "Mexico": ("Americas", 3),
    "Germany": ("EMEA", 3), "Spain": ("EMEA", 2), "Brazil": ("Americas", 2),
    "Philippines": ("APAC", 2), "Poland": ("EMEA", 2), "Colombia": ("Americas", 1),
}
C_DEPTS = {"Client Success": 40, "Engineering": 18, "Consulting": 12, "Finance": 9,
           "Security": 7, "Sales": 7, "People & Talent": 4, "Legal": 3}
contractors = []
start_window = (date(2023, 1, 1), date(2026, 11, 15))
span = (start_window[1] - start_window[0]).days
for i in range(2750):
    # starts accelerate over time
    s = start_window[0] + timedelta(days=int(span * random.random() ** 0.7))
    tenure = int(random.lognormvariate(5.2, 0.6))  # median ~6 months
    e = s + timedelta(days=tenure)
    country = random.choices(list(COUNTRIES), [v[1] for v in COUNTRIES.values()])[0]
    contractors.append({
        "contractor_id": f"CT-{i + 20001}",
        "name": person(),
        "vendor": random.choices(list(VENDORS), list(VENDORS.values()))[0],
        "country": country,
        "region": COUNTRIES[country][0],
        "department": random.choices(list(C_DEPTS), list(C_DEPTS.values()))[0],
        "start_date": s.isoformat(),
        "end_date": e.isoformat(),
        "status": "Active" if e > TODAY else "Offboarded",
        "contracts": 1 + (random.random() < 0.18) + (random.random() < 0.05),
    })


def write(name, rows):
    with open(HERE / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


write("onboarding.csv", onboarding)
write("offboarding.csv", offboarding)
write("contractors.csv", contractors)
docs = HERE.parent / "docs"
docs.mkdir(exist_ok=True)
(docs / "data.json").write_text(json.dumps({
    "company": "Larkspur & Vane (fictional)",
    "as_of": TODAY.isoformat(),
    "onboarding": onboarding, "offboarding": offboarding, "contractors": contractors,
    "laptop_costs": {k: v[0] for k, v in LAPTOPS.items()},
}, separators=(",", ":")))
print(f"onboarding {len(onboarding)}, offboarding {len(offboarding)}, contractors {len(contractors)}")
