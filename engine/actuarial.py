"""
engine/actuarial.py
Core actuarial + financial projection engine — v2.0
Pure Python, zero Streamlit dependency.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

# ── Lookup tables ─────────────────────────────────────────────────────────────

BASELINE_LIFE_EXP: dict[str, float] = {"pria": 72.0, "wanita": 76.0}

PROFESSION_ADJ: dict[str, float] = {
    "Pekerja Lapangan / Fisik Berat":  -3.5,
    "Pekerja Kantoran / Profesional":   0.0,
    "Wiraswasta / Pengusaha":           1.0,
    "Aparatur Sipil Negara (ASN)":      0.5,
    "Tenaga Kesehatan":                -1.0,
    "Lainnya":                          0.0,
}

DOMICILE_ADJ: dict[str, float] = {
    "Kota Besar (Jabodetabek / Surabaya / Medan)": -1.5,
    "Kota Menengah":                                -0.5,
    "Pedesaan / Daerah Terpencil":                   1.5,
}

SCENARIOS: dict[str, dict] = {
    "Normal": {
        "inflation_mult": 1.0,  "return_mult": 1.0,
        "medical_mult":   1.0,  "asset_shock": 0.0,
    },
    "Hiperinflasi Medis": {
        "inflation_mult": 1.8,  "return_mult": 0.85,
        "medical_mult":   3.0,  "asset_shock": 0.0,
    },
    "Market Crash -30%": {
        "inflation_mult": 1.2,  "return_mult": 0.70,
        "medical_mult":   1.3,  "asset_shock":-0.30,
    },
    "Resesi Ekonomi": {
        "inflation_mult": 1.5,  "return_mult": 0.60,
        "medical_mult":   1.5,  "asset_shock": 0.0,
    },
    "Skenario Optimis": {
        "inflation_mult": 0.70, "return_mult": 1.25,
        "medical_mult":   0.80, "asset_shock": 0.0,
    },
}

BASE_ANNUAL_RETURN  = 0.085
BASE_MEDICAL_COST   = 500_000

PEER_TABLE: dict[tuple, list[float]] = {
    (20, 30): [5_000_000,   20_000_000,   60_000_000,   150_000_000,   400_000_000],
    (30, 40): [20_000_000,  80_000_000,  250_000_000,   700_000_000, 2_000_000_000],
    (40, 50): [50_000_000, 200_000_000,  600_000_000, 1_500_000_000, 5_000_000_000],
    (50, 65): [80_000_000, 300_000_000,  900_000_000, 2_500_000_000, 8_000_000_000],
}
PEER_LABELS = ["Bottom 20%", "Top 40%", "Top 30%", "Top 20%", "Top 5%"]

MONTE_CARLO_RUNS = 1_000

# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class UserProfile:
    name:             str   = ""
    gender:           str   = "pria"
    current_age:      int   = 35
    retirement_age:   int   = 60
    monthly_salary:   float = 10_000_000
    current_savings:  float = 50_000_000
    savings_rate_pct: float = 20.0
    profession:       str   = "Pekerja Kantoran / Profesional"
    domicile:         str   = "Kota Besar (Jabodetabek / Surabaya / Medan)"
    sandwich_monthly: float = 0.0
    tapera_enabled:   bool  = True
    scenario_key:     str   = "Normal"
    inflation_rate:   float = 0.05
    medical_inf_rate: float = 0.10

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d: dict) -> "UserProfile":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class ActuarialResult:
    life_expectancy:          float = 0.0
    years_to_retire:          int   = 0
    years_in_retirement:      float = 0.0

    nest_egg_at_retirement:   float = 0.0
    required_nest_egg:        float = 0.0
    shortfall:                float = 0.0
    monthly_top_up_needed:    float = 0.0

    broke_age:                Optional[float] = None
    broke_age_years_post_ret: Optional[float] = None

    readiness_score:          float = 0.0
    readiness_label:          str   = ""
    readiness_color:          str   = "#FFA502"

    projection_ages:          list  = field(default_factory=list)
    projection_wealth:        list  = field(default_factory=list)

    eff_inflation:            float = 0.0
    eff_medical_inflation:    float = 0.0
    eff_annual_return:        float = 0.0
    monthly_net_savings:      float = 0.0

    peer_percentile:          str   = ""
    peer_wealth_ref:          float = 0.0

    # Monte Carlo
    mc_success_rate:          float = 0.0
    mc_median_broke_age:      Optional[float] = None
    mc_p10_wealth:            float = 0.0
    mc_p90_wealth:            float = 0.0
    mc_confidence_band_lo:    list  = field(default_factory=list)
    mc_confidence_band_hi:    list  = field(default_factory=list)

    # Glide path
    glide_path_equity:        float = 0.0
    glide_path_bonds:         float = 0.0
    glide_path_cash:          float = 0.0
    glide_path_gold:          float = 0.0


# ── Engine ────────────────────────────────────────────────────────────────────

class ActuarialEngine:

    def __init__(self, profile: UserProfile) -> None:
        self.p = profile
        sc = SCENARIOS.get(profile.scenario_key, SCENARIOS["Normal"])
        self.eff_inf    = profile.inflation_rate   * sc["inflation_mult"]
        self.eff_med    = profile.medical_inf_rate * sc["medical_mult"]
        self.eff_return = BASE_ANNUAL_RETURN       * sc["return_mult"]
        self.shock      = sc["asset_shock"]

    def _life_exp(self) -> float:
        base = BASELINE_LIFE_EXP.get(self.p.gender, 72.0)
        adj  = (PROFESSION_ADJ.get(self.p.profession, 0.0)
                + DOMICILE_ADJ.get(self.p.domicile, 0.0))
        return round(base + adj, 1)

    def _net_monthly(self) -> float:
        salary   = self.p.monthly_salary
        tapera   = salary * 0.025 if self.p.tapera_enabled else 0.0
        sandwich = self.p.sandwich_monthly
        # Take-home setelah potongan wajib (tapera & sandwich)
        take_home = max(0.0, salary - tapera - sandwich)
        # Tabungan dari take-home, bukan dari gaji bruto
        savings   = take_home * (self.p.savings_rate_pct / 100)
        return max(0.0, savings)

    def _required(self, life_exp: float) -> float:
        p = self.p
        ytr = max(0, p.retirement_age - p.current_age)
        yir = max(0.0, life_exp - p.retirement_age)
        if yir <= 0:
            return 0.0
        ms_now  = p.monthly_salary * 0.70
        ms_fut  = ms_now             * (1 + self.eff_inf) ** ytr
        med_fut = BASE_MEDICAL_COST  * (1 + self.eff_med) ** ytr
        annual  = (ms_fut + med_fut) * 12
        real_r  = max(0.001, self.eff_return * 0.5 - self.eff_inf)
        return annual * (1 - (1 + real_r) ** -yir) / real_r

    def _accumulate(self) -> tuple[float, list, list]:
        p    = self.p
        ytr  = max(0, p.retirement_age - p.current_age)
        save = self._net_monthly() * 12
        w    = float(p.current_savings) * (1 + self.shock)
        ages, vals = [], []
        for yr in range(ytr + 1):
            ages.append(float(p.current_age + yr))
            vals.append(w)
            if yr < ytr:
                w = w * (1 + self.eff_return) + save
        return w, ages, vals

    def _decumulate(
        self, w_ret: float, life_exp: float,
        ages: list, vals: list
    ) -> Optional[float]:
        p    = self.p
        ytr  = max(0, p.retirement_age - p.current_age)
        ms   = (p.monthly_salary * 0.70 * (1 + self.eff_inf) ** ytr
                + BASE_MEDICAL_COST   * (1 + self.eff_med) ** ytr)
        aw   = ms * 12
        w    = w_ret
        broke: Optional[float] = None
        max_age = max(life_exp + 5, p.retirement_age + 45)
        age  = float(p.retirement_age)
        while age < max_age:
            age += 1.0
            yr   = age - p.retirement_age
            w    = w * (1 + self.eff_return * 0.5) - aw * (1 + self.eff_inf) ** yr
            ages.append(age)
            vals.append(max(w, -w_ret * 0.5))
            if w <= 0 and broke is None:
                broke = age
                if age > life_exp + 5:
                    break
        return broke

    def _score(self, proj: float, req: float,
               broke: Optional[float], life_exp: float) -> tuple[float, str, str]:
        ratio = (proj / req) if req > 0 else 1.0
        raw   = min(100.0, ratio * 100)
        if broke and broke > life_exp:
            raw = min(100, raw + 8)
        elif broke and broke < self.p.retirement_age + 5:
            raw = max(0, raw - 25)
        s = round(raw, 1)
        if s >= 85:   lbl, col = "Sangat Siap ✦",    "#2DD4BF"
        elif s >= 65: lbl, col = "Cukup Siap",        "#C9A84C"
        elif s >= 40: lbl, col = "Perlu Perhatian",   "#FFA502"
        else:         lbl, col = "Berisiko Tinggi ⚠", "#FF4757"
        return s, lbl, col

    def _peer(self, proj: float) -> tuple[str, float]:
        age = self.p.current_age
        bracket = PEER_TABLE.get((50, 65))
        for (lo, hi), th in PEER_TABLE.items():
            if lo <= age < hi:
                bracket = th; break
        lbl, ref = PEER_LABELS[0], bracket[0]
        for i, t in enumerate(bracket):
            if proj >= t:
                lbl = PEER_LABELS[min(i, len(PEER_LABELS)-1)]
                ref = float(t)
        return lbl, ref

    def _glide_path(self) -> tuple[float, float, float, float]:
        """Age-based asset allocation recommendation."""
        age = self.p.current_age
        # Rule of thumb: equity = 110 - age, rest distributed
        equity = max(20.0, min(80.0, 110.0 - age))
        gold   = min(15.0, max(5.0, (age - 20) * 0.3))
        bonds  = max(10.0, min(60.0, age * 0.8))
        cash   = max(5.0, 100.0 - equity - gold - bonds)
        total  = equity + bonds + gold + cash
        return (round(equity/total*100,1), round(bonds/total*100,1),
                round(gold/total*100,1),   round(cash/total*100,1))

    def _monte_carlo(
        self, ytr: int, w_ret: float, req: float, life_exp: float
    ) -> dict:
        """
        Run MONTE_CARLO_RUNS simulations with randomised return & inflation.
        Returns success rate and confidence bands.
        """
        p          = self.p
        net_save   = self._net_monthly() * 12
        rng        = np.random.default_rng(42)
        successes  = 0
        broke_ages = []
        band_lo    = np.full(ytr + 1, np.inf)
        band_hi    = np.full(ytr + 1, -np.inf)
        wealths_at_ret = []

        for _ in range(MONTE_CARLO_RUNS):
            # Randomise annual return & inflation (normal distribution)
            ret_r  = rng.normal(self.eff_return, 0.04)
            inf_r  = rng.normal(self.eff_inf,    0.015)
            shock  = float(p.current_savings) * (1 + self.shock)
            w      = shock
            yr_vals = [w]

            for yr in range(ytr):
                w = w * (1 + ret_r) + net_save
                yr_vals.append(w)

            for i, v in enumerate(yr_vals):
                band_lo[i] = min(band_lo[i], v)
                band_hi[i] = max(band_hi[i], v)

            # Decumulation
            ms     = (p.monthly_salary * 0.70 * (1 + inf_r) ** ytr
                      + BASE_MEDICAL_COST    * (1 + inf_r) ** ytr)
            aw     = ms * 12
            dw     = w
            broke  = None
            yir    = max(0.0, life_exp - p.retirement_age)
            for dyr in range(1, int(yir) + 30):
                dw = dw * (1 + ret_r * 0.5) - aw * (1 + inf_r) ** dyr
                if dw <= 0 and broke is None:
                    broke = float(p.retirement_age + dyr)
                    break

            wealths_at_ret.append(w)
            if broke is None or broke > life_exp:
                successes += 1
            else:
                broke_ages.append(broke)

        # Replace inf with actual extremes
        band_lo = np.where(band_lo == np.inf, 0, band_lo)
        band_hi = np.where(band_hi == -np.inf, 0, band_hi)

        arr = np.array(wealths_at_ret)
        return {
            "success_rate":    round(successes / MONTE_CARLO_RUNS * 100, 1),
            "median_broke":    float(np.median(broke_ages)) if broke_ages else None,
            "p10_wealth":      float(np.percentile(arr, 10)),
            "p90_wealth":      float(np.percentile(arr, 90)),
            "band_lo":         band_lo.tolist(),
            "band_hi":         band_hi.tolist(),
        }

    def run(self) -> ActuarialResult:
        p        = self.p
        life_exp = self._life_exp()
        ytr      = max(0, p.retirement_age - p.current_age)
        yir      = max(0.0, life_exp - p.retirement_age)
        net_save = self._net_monthly()
        required = self._required(life_exp)

        w_ret, ages, vals = self._accumulate()
        broke = self._decumulate(w_ret, life_exp, ages, vals)
        score, label, color = self._score(w_ret, required, broke, life_exp)

        shortfall = max(0.0, required - w_ret)
        top_up    = 0.0
        if shortfall > 0 and ytr > 0:
            r = self.eff_return / 12
            n = ytr * 12
            top_up = (shortfall * r / ((1+r)**n - 1)) if r > 0 else shortfall / n

        peer_lbl, peer_ref = self._peer(w_ret)
        equity, bonds, gold, cash = self._glide_path()
        mc = self._monte_carlo(ytr, w_ret, required, life_exp)

        return ActuarialResult(
            life_expectancy          = life_exp,
            years_to_retire          = ytr,
            years_in_retirement      = yir,
            nest_egg_at_retirement   = w_ret,
            required_nest_egg        = required,
            shortfall                = shortfall,
            monthly_top_up_needed    = top_up,
            broke_age                = broke,
            broke_age_years_post_ret = (broke - p.retirement_age) if broke else None,
            readiness_score          = score,
            readiness_label          = label,
            readiness_color          = color,
            projection_ages          = ages,
            projection_wealth        = vals,
            eff_inflation            = self.eff_inf,
            eff_medical_inflation    = self.eff_med,
            eff_annual_return        = self.eff_return,
            monthly_net_savings      = net_save,
            peer_percentile          = peer_lbl,
            peer_wealth_ref          = peer_ref,
            mc_success_rate          = mc["success_rate"],
            mc_median_broke_age      = mc["median_broke"],
            mc_p10_wealth            = mc["p10_wealth"],
            mc_p90_wealth            = mc["p90_wealth"],
            mc_confidence_band_lo    = mc["band_lo"],
            mc_confidence_band_hi    = mc["band_hi"],
            glide_path_equity        = equity,
            glide_path_bonds         = bonds,
            glide_path_cash          = cash,
            glide_path_gold          = gold,
        )