import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv; load_dotenv()

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from utils.session       import auth_guard
from engine.actuarial    import ActuarialEngine, UserProfile, PEER_TABLE, PEER_LABELS
from engine.data_fetcher import fetch_all_live_data
from pages._shared       import sidebar

st.set_page_config(page_title="Vantura — Peer Benchmarking", page_icon="⚜️",
                   layout="wide", initial_sidebar_state="expanded")
auth_guard()

if not st.session_state.get("user_profile"):
    email = st.session_state.get("user_email","")
    if email:
        from utils.db import load_profile
        saved = load_profile(email)
        if saved: st.session_state["user_profile"] = UserProfile.from_dict(saved)
        else: st.switch_page("pages/1_profil.py")
    else: st.switch_page("pages/1_profil.py")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=DM+Sans:wght@300;400;500&family=JetBrains+Mono:wght@300;400&display=swap');
:root{--gold:#C9A84C;--gold-l:#E8C97A;--gold-d:rgba(201,168,76,.15);--teal:#2DD4BF;
      --bg:#0A0D14;--bg2:#111520;--card:#161B2E;--tp:#F0EDE8;--ts:#9B97A0;--tm:#5A5768;
      --bdr:rgba(201,168,76,.18);--bdrs:rgba(255,255,255,.06);}
*,*::before,*::after{box-sizing:border-box;}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"]{
    background:var(--bg)!important;color:var(--tp)!important;font-family:'DM Sans',sans-serif!important;}
[data-testid="stSidebar"]{background:var(--bg2)!important;border-right:1px solid var(--bdr)!important;}
[data-testid="stSidebar"] *{font-family:'DM Sans',sans-serif!important;color:var(--ts)!important;}
[data-testid="stHeader"]{background:transparent!important;}
h1,h2,h3{font-family:'Cormorant Garamond',serif!important;color:var(--tp)!important;}
.stButton>button{background:linear-gradient(135deg,var(--gold),#A8862E)!important;
    color:#0A0D14!important;border:none!important;border-radius:6px!important;
    font-weight:500!important;font-size:.875rem!important;padding:.6rem 1.4rem!important;}
[data-testid="stMetricValue"]{color:var(--gold)!important;
    font-family:'Cormorant Garamond',serif!important;font-size:1.9rem!important;}
[data-testid="stMetricLabel"]{color:var(--ts)!important;font-size:.74rem!important;
    letter-spacing:.08em!important;text-transform:uppercase!important;}
.stMetric{background:var(--card)!important;border:1px solid var(--bdrs)!important;
    border-radius:10px!important;padding:1rem 1.2rem!important;}
label,[data-baseweb="label"]{color:var(--ts)!important;font-size:.78rem!important;
    letter-spacing:.07em!important;text-transform:uppercase!important;}
.stSelectbox>div>div{background:var(--card)!important;color:var(--tp)!important;
    border:1px solid var(--bdrs)!important;}
::-webkit-scrollbar{width:5px;height:5px;}::-webkit-scrollbar-track{background:var(--bg2);}
::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:3px;}
</style>""", unsafe_allow_html=True)

def rp(v):
    if abs(v)>=1e9: return f"Rp {v/1e9:.2f} M"
    if abs(v)>=1e6: return f"Rp {v/1e6:.1f} Jt"
    return f"Rp {v:,.0f}"

def rp_short(v):
    if abs(v)>=1e9: return f"{v/1e9:.1f}M"
    if abs(v)>=1e6: return f"{v/1e6:.0f}Jt"
    return f"{v:,.0f}"

def monthly_needed(gap, yrs):
    if gap<=0 or yrs<=0: return 0.0
    r = 0.085/12; n = yrs*12
    return gap*r/((1+r)**n-1) if r>0 else gap/n

with st.spinner("Memuat data benchmark…"):
    live = fetch_all_live_data()
sidebar(live)

profile: UserProfile = st.session_state["user_profile"]
res         = ActuarialEngine(profile).run()
user_wealth = res.nest_egg_at_retirement
user_now    = float(profile.current_savings)
age         = profile.current_age
yrs_to_ret  = max(1, profile.retirement_age - age)

bracket_key = (50,65)
for (lo,hi) in PEER_TABLE:
    if lo <= age < hi: bracket_key = (lo,hi); break
thresholds = PEER_TABLE[bracket_key]

ALL_BRACKETS = {
    "20-30 thn": PEER_TABLE[(20,30)],
    "30-40 thn": PEER_TABLE[(30,40)],
    "40-50 thn": PEER_TABLE[(40,50)],
    "50-65 thn": PEER_TABLE[(50,65)],
}

pct_str = res.peer_percentile
if   "Top 5"  in pct_str: pct_col,pct_emoji,pct_num = "#2DD4BF","🏆",95
elif "Top 20" in pct_str: pct_col,pct_emoji,pct_num = "#2DD4BF","🥇",80
elif "Top 30" in pct_str: pct_col,pct_emoji,pct_num = "#C9A84C","🥈",70
elif "Top 40" in pct_str: pct_col,pct_emoji,pct_num = "#FFA502","🥉",60
else:                      pct_col,pct_emoji,pct_num = "#FF4757","📈",20

score_col = res.readiness_color
mc_col    = "#2DD4BF" if res.mc_success_rate>=70 else "#FF4757"
gap40 = thresholds[1]-user_wealth; gap30 = thresholds[2]-user_wealth
gap20 = thresholds[3]-user_wealth; gap5  = thresholds[4]-user_wealth

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:1.5rem;">
    <h1 style="font-family:'Cormorant Garamond',serif;font-size:2.4rem;font-weight:300;
         color:#F0EDE8;letter-spacing:.04em;line-height:1.2;margin-bottom:.3rem;">
        Peer <span style="color:#C9A84C;">Benchmarking</span></h1>
    <p style="color:#5A5768;font-size:.84rem;">
        Posisi dana pensiun Anda dibandingkan orang seusia di Indonesia (estimasi BPS)</p>
</div>
""", unsafe_allow_html=True)

# ── Hero 3 kolom ───────────────────────────────────────────────────────────────
h1,h2,h3 = st.columns(3)
with h1:
    st.markdown(
        "<div style='background:rgba(22,27,46,.7);border:1px solid rgba(201,168,76,.18);"
        "border-radius:14px;padding:1.4rem;text-align:center;'>"
        "<div style='font-size:.62rem;color:#5A5768;letter-spacing:.2em;"
        "text-transform:uppercase;margin-bottom:.6rem;'>POSISI ANDA</div>"
        f"<div style='font-size:2.2rem;margin-bottom:.3rem;'>{pct_emoji}</div>"
        f"<div style='font-family:\"Cormorant Garamond\",serif;font-size:2rem;"
        f"font-weight:600;color:{pct_col};line-height:1;'>{pct_str}</div>"
        f"<div style='font-size:.75rem;color:#9B97A0;margin-top:.5rem;'>"
        f"dari orang usia {bracket_key[0]}–{bracket_key[1]} tahun</div>"
        f"<div style='font-size:.72rem;color:#5A5768;margin-top:.3rem;'>"
        f"Lebih siap dari {pct_num}% rekan sebaya</div>"
        "</div>",
        unsafe_allow_html=True)

with h2:
    st.markdown(
        "<div style='background:rgba(22,27,46,.7);border:1px solid rgba(255,255,255,.06);"
        "border-radius:14px;padding:1.4rem;text-align:center;'>"
        "<div style='font-size:.62rem;color:#5A5768;letter-spacing:.15em;"
        "text-transform:uppercase;margin-bottom:.4rem;'>ASET SAAT INI</div>"
        f"<div style='font-family:\"Cormorant Garamond\",serif;font-size:1.6rem;"
        f"color:#C9A84C;'>{rp(user_now)}</div>"
        "<div style='font-size:.62rem;color:#5A5768;letter-spacing:.15em;"
        "text-transform:uppercase;margin:.7rem 0 .4rem;'>PROYEKSI SAAT PENSIUN</div>"
        f"<div style='font-family:\"Cormorant Garamond\",serif;font-size:1.6rem;"
        f"color:#E8C97A;'>{rp(user_wealth)}</div>"
        f"<div style='font-size:.7rem;color:#5A5768;margin-top:.4rem;'>"
        f"pada usia {profile.retirement_age} tahun</div>"
        "</div>",
        unsafe_allow_html=True)

with h3:
    st.markdown(
        "<div style='background:rgba(22,27,46,.7);border:1px solid rgba(255,255,255,.06);"
        "border-radius:14px;padding:1.4rem;text-align:center;'>"
        "<div style='font-size:.62rem;color:#5A5768;letter-spacing:.15em;"
        "text-transform:uppercase;margin-bottom:.4rem;'>READINESS SCORE</div>"
        f"<div style='font-family:\"Cormorant Garamond\",serif;font-size:1.6rem;"
        f"color:{score_col};'>{res.readiness_score:.0f}/100</div>"
        "<div style='font-size:.62rem;color:#5A5768;letter-spacing:.15em;"
        "text-transform:uppercase;margin:.7rem 0 .4rem;'>MONTE CARLO</div>"
        f"<div style='font-family:\"Cormorant Garamond\",serif;font-size:1.6rem;"
        f"color:{mc_col};'>{res.mc_success_rate:.0f}% sukses</div>"
        f"<div style='font-size:.7rem;color:#5A5768;margin-top:.4rem;'>"
        f"dari 1.000 simulasi pasar</div>"
        "</div>",
        unsafe_allow_html=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── KPI ────────────────────────────────────────────────────────────────────────
m1,m2,m3,m4,m5 = st.columns(5)
with m1: st.metric("Aset Saat Ini", rp(user_now))
with m2: st.metric("Proyeksi Dana Pensiun", rp(user_wealth))
with m3: st.metric("Median Kelompok Usia", rp(thresholds[1]),
                   help=f"50% orang usia {bracket_key[0]}–{bracket_key[1]} tahun memiliki dana di bawah angka ini")
with m4:
    diff = user_wealth-thresholds[1]
    st.metric("Vs Median", rp(abs(diff)),
              delta=f"+{rp(diff)} di atas" if diff>=0 else f"{rp(diff)} di bawah",
              help="Selisih proyeksi dana Anda dibandingkan nilai median kelompok usia")
with m5: st.metric("Threshold Top 5%", rp(thresholds[4]),
                   help="Dana minimum untuk masuk kelompok 5% terbaik di usia Anda")

# Narasi posisi
if gap20 <= 0:
    narasi = f"Anda sudah di posisi {pct_str} — lebih baik dari {pct_num}% orang seusia. Fokus pada optimasi pajak dan diversifikasi."
    n_col = "#2DD4BF"
elif gap40 > 0:
    narasi = f"Butuh tambahan {rp(gap40)} untuk masuk Top 40%. Setara {rp(monthly_needed(gap40,yrs_to_ret))}/bulan selama {yrs_to_ret} tahun dengan return 8.5%."
    n_col = "#FFA502"
else:
    narasi = f"Anda sudah Top 40%. Butuh {rp(gap20)} lagi untuk masuk Top 20%, setara {rp(monthly_needed(gap20,yrs_to_ret))}/bulan."
    n_col = "#C9A84C"

st.markdown(f"""
<div style="background:rgba(22,27,46,.8);border-left:3px solid {n_col};
     border-radius:0 8px 8px 0;padding:.7rem 1.1rem;margin-bottom:1rem;">
    <span style="color:{n_col};font-size:.8rem;font-weight:600;">💡 Posisi Anda: </span>
    <span style="color:#9B97A0;font-size:.8rem;">{narasi}</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Chart 1: Bar + Gauge ───────────────────────────────────────────────────────
cl, cr = st.columns([3,2])
with cl:
    bar_colors = ["#C9A84C" if user_wealth>=t else "#1E2640" for t in thresholds]
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=PEER_LABELS, y=thresholds,
        marker=dict(color=bar_colors, line=dict(color="rgba(255,255,255,.08)",width=1)),
        text=[rp_short(t) for t in thresholds], textposition="outside",
        textfont=dict(size=9,color="#9B97A0"),
        hovertemplate="%{x}<br><b>%{y:,.0f}</b><extra></extra>"))
    fig_bar.add_hline(y=user_wealth,
        line=dict(color="#2DD4BF",width=2.5,dash="dash"),
        annotation_text=f"Proyeksi Anda: {rp(user_wealth)}",
        annotation_position="top left",
        annotation_font=dict(color="#2DD4BF",size=10))
    fig_bar.add_hline(y=user_now,
        line=dict(color="#C9A84C",width=1.5,dash="dot"),
        annotation_text=f"Aset kini: {rp(user_now)}",
        annotation_position="bottom right",
        annotation_font=dict(color="#C9A84C",size=9))
    fig_bar.update_layout(height=340, showlegend=False,
        paper_bgcolor="#161B2E", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10,r=10,t=65,b=10),
        font=dict(family="DM Sans",color="#9B97A0",size=11),
        title=dict(
            text=f"Distribusi Kekayaan — Usia {bracket_key[0]}–{bracket_key[1]} Tahun"
                 "<br><span style='font-size:9px;color:#5A5768;'>"
                 "Bar emas = sudah Anda capai · Garis teal = proyeksi pensiun Anda</span>",
            font=dict(family="Cormorant Garamond",size=16,color="#F0EDE8"),
            x=0.02, xanchor="left"),
        xaxis=dict(tickfont=dict(size=10,color="#9B97A0"),gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(tickformat=",.0s",tickfont=dict(size=9),gridcolor="rgba(255,255,255,.04)"),
        shapes=[dict(type="rect",xref="paper",yref="paper",x0=0,y0=0,x1=1,y1=1,
                     line=dict(color="rgba(255,255,255,.06)",width=1),
                     fillcolor="rgba(0,0,0,0)",layer="below")])
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar":False})

with cr:
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number", value=pct_num,
        number={"suffix":"th","font":{"size":34,"color":pct_col,"family":"Cormorant Garamond"}},
        title={"text":f"<b>{pct_str}</b><br><span style='font-size:10px;color:#5A5768;'>"
                      f"Lebih baik dari {pct_num}% sebaya</span>",
               "font":{"size":13,"color":"#9B97A0"}},
        gauge={
            "axis":{"range":[0,100],"tickwidth":1,"tickcolor":"#5A5768",
                    "tickfont":{"size":9,"color":"#5A5768"},"nticks":6},
            "bar":{"color":pct_col,"thickness":.34},
            "bgcolor":"rgba(22,27,46,.8)","borderwidth":0,
            "steps":[
                {"range":[0,40],  "color":"rgba(255,71,87,.10)"},
                {"range":[40,60], "color":"rgba(255,165,2,.08)"},
                {"range":[60,80], "color":"rgba(201,168,76,.08)"},
                {"range":[80,100],"color":"rgba(45,212,191,.14)"},
            ],
            "threshold":{"line":{"color":"#C9A84C","width":2},"thickness":.85,"value":60},
        }))
    fig_g.update_layout(height=260,
        paper_bgcolor="#161B2E", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10,r=10,t=55,b=10),
        font=dict(family="DM Sans",color="#9B97A0",size=11),
        title=dict(text="Posisi Persentil<br><span style='font-size:9px;color:#5A5768;'>"
                        "Gauge vs kelompok usia Anda</span>",
                   font=dict(family="Cormorant Garamond",size=16,color="#F0EDE8"),
                   x=0.02, xanchor="left"),
        shapes=[dict(type="rect",xref="paper",yref="paper",x0=0,y0=0,x1=1,y1=1,
                     line=dict(color="rgba(255,255,255,.06)",width=1),
                     fillcolor="rgba(0,0,0,0)",layer="below")])
    st.plotly_chart(fig_g, use_container_width=True, config={"displayModeBar":False})

    diff_val = user_wealth-thresholds[1]
    for lbl,val,col in [
        ("Usia Anda", f"{age} tahun", "#F0EDE8"),
        ("Bracket Referensi", f"{bracket_key[0]}-{bracket_key[1]} thn", "#9B97A0"),
        ("Median Bracket", rp(thresholds[1]), "#9B97A0"),
        ("Vs Median", f"+{rp(diff_val)}" if diff_val>=0 else rp(diff_val),
         "#2DD4BF" if diff_val>=0 else "#FF4757"),
    ]:
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"padding:.45rem 0;border-bottom:1px solid rgba(255,255,255,.04);'>"
            f"<span style='color:#9B97A0;font-size:.78rem;'>{lbl}</span>"
            f"<span style='color:{col};font-size:.84rem;font-weight:500;"
            f"font-family:\"JetBrains Mono\",monospace;'>{val}</span></div>",
            unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Chart 2: Multi-bracket ─────────────────────────────────────────────────────
LINE_COLORS = ["#C9A84C","#2DD4BF","#E8C97A","#9B97A0"]
user_bracket_name = f"{bracket_key[0]}-{bracket_key[1]} thn"
fig_multi = go.Figure()
for i,(bname,bvals) in enumerate(ALL_BRACKETS.items()):
    is_user = bname == user_bracket_name
    fig_multi.add_trace(go.Scatter(
        x=PEER_LABELS, y=bvals, mode="lines+markers",
        name=f"Usia {bname}",
        line=dict(color=LINE_COLORS[i],width=2.5 if is_user else 1.2),
        marker=dict(size=7 if is_user else 5),
        opacity=1.0 if is_user else 0.4,
        hovertemplate=f"Usia {bname}<br>%{{x}}: <b>%{{y:,.0f}}</b><extra></extra>"))
fig_multi.add_hline(y=user_wealth,
    line=dict(color="#FF4757",width=2,dash="dash"),
    annotation_text=f"Proyeksi Anda: {rp(user_wealth)}",
    annotation_position="top left",
    annotation_font=dict(color="#FF4757",size=10))
fig_multi.update_layout(height=340,
    paper_bgcolor="#161B2E", plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10,r=10,t=65,b=10),
    font=dict(family="DM Sans",color="#9B97A0",size=11),
    title=dict(
        text="Perbandingan Lintas Semua Kelompok Usia"
             "<br><span style='font-size:9px;color:#5A5768;'>"
             "Garis merah = proyeksi Anda · Garis tebal = kelompok usia Anda saat ini</span>",
        font=dict(family="Cormorant Garamond",size=16,color="#F0EDE8"),
        x=0.02, xanchor="left"),
    xaxis=dict(title="Persentil",titlefont=dict(size=10,color="#5A5768"),
               gridcolor="rgba(255,255,255,.04)",zeroline=False,tickfont=dict(size=9)),
    yaxis=dict(title="Kekayaan (Rp)",titlefont=dict(size=10,color="#5A5768"),
               gridcolor="rgba(255,255,255,.04)",tickfont=dict(size=9),tickformat=",.0s"),
    legend=dict(orientation="h",y=-0.16,font=dict(size=10,color="#9B97A0"),bgcolor="rgba(0,0,0,0)"),
    shapes=[dict(type="rect",xref="paper",yref="paper",x0=0,y0=0,x1=1,y1=1,
                 line=dict(color="rgba(255,255,255,.06)",width=1),
                 fillcolor="rgba(0,0,0,0)",layer="below")])
st.plotly_chart(fig_multi, use_container_width=True, config={"displayModeBar":False})

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Tabel Benchmark ────────────────────────────────────────────────────────────
st.markdown("<div style='font-family:\"Cormorant Garamond\",serif;font-size:1.1rem;"
            "color:#F0EDE8;margin-bottom:.6rem;'>Tabel Benchmark Lengkap</div>",
            unsafe_allow_html=True)
tbl_rows = []
for bname, bvals in ALL_BRACKETS.items():
    row = {"Kelompok Usia": f"Usia {bname}"}
    for j,lbl in enumerate(PEER_LABELS):
        row[lbl] = rp(bvals[j])
    tbl_rows.append(row)
df_tbl = pd.DataFrame(tbl_rows).set_index("Kelompok Usia")

def _highlight(row):
    target = f"Usia {bracket_key[0]}-{bracket_key[1]} thn"
    if row.name == target:
        return ["background-color:rgba(201,168,76,.12);color:#F0EDE8"]*len(row)
    return ["color:#9B97A0"]*len(row)

st.dataframe(df_tbl.style.apply(_highlight,axis=1), use_container_width=True)
st.markdown("<div style='font-size:.72rem;color:#5A5768;margin-top:.4rem;'>"
            "📌 Baris emas = kelompok usia Anda saat ini · Data estimasi BPS Indonesia</div>",
            unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Roadmap ────────────────────────────────────────────────────────────────────
ins_l, ins_r = st.columns(2)
with ins_l:
    if gap20 <= 0:
        st.markdown(
            "<div style='background:rgba(45,212,191,.06);border:1px solid rgba(45,212,191,.18);"
            "border-radius:12px;padding:1.3rem 1.6rem;'>"
            "<div style='font-family:\"Cormorant Garamond\",serif;font-size:1.1rem;"
            "color:#F0EDE8;margin-bottom:.6rem;'>🏆 Posisi Sangat Baik!</div>"
            "<p style='color:#9B97A0;font-size:.84rem;line-height:1.7;margin:0 0 .8rem;'>"
            "Anda sudah di <b style='color:#2DD4BF;'>Top 20% atau lebih tinggi</b>!</p>"
            "<ul style='color:#9B97A0;font-size:.82rem;line-height:1.9;padding-left:1.2rem;margin:0;'>"
            "<li>Optimalkan pajak via <b style='color:#C9A84C;'>ORI/SBR</b></li>"
            "<li>Estate planning dengan notaris</li><li>Diversifikasi aset internasional</li>"
            "<li>Reksa dana indeks global (MSCI World)</li></ul></div>",
            unsafe_allow_html=True)
    else:
        t_lbl = "Top 40%" if gap40>0 else ("Top 30%" if gap30>0 else "Top 20%")
        t_gap = gap40 if gap40>0 else (gap30 if gap30>0 else gap20)
        m_needed = monthly_needed(t_gap, yrs_to_ret)
        st.markdown(
            f"<div style='background:rgba(201,168,76,.06);border:1px solid rgba(201,168,76,.18);"
            f"border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:.6rem;'>"
            f"<div style='font-family:\"Cormorant Garamond\",serif;font-size:1.05rem;"
            f"color:#F0EDE8;margin-bottom:.5rem;'>💡 Target Selanjutnya: {t_lbl}</div>"
            f"<p style='color:#9B97A0;font-size:.83rem;line-height:1.6;margin:0;'>"
            f"Butuh tambahan <b style='color:#C9A84C;'>{rp(t_gap)}</b> untuk masuk {t_lbl}.<br>"
            f"Setara investasi <b style='color:#C9A84C;'>{rp(m_needed)}/bulan</b> "
            f"selama {yrs_to_ret} tahun (return 8.5%/thn).</p></div>",
            unsafe_allow_html=True)
        st.markdown(
            "<div style='background:rgba(22,27,46,.8);border:1px solid rgba(255,255,255,.06);"
            "border-radius:12px;padding:1.2rem 1.5rem;'>"
            "<div style='font-size:.65rem;color:#5A5768;letter-spacing:.15em;"
            "text-transform:uppercase;margin-bottom:.5rem;'>Instrumen yang Disarankan</div>"
            "<div style='font-size:.81rem;color:#9B97A0;line-height:1.8;'>"
            "Reksa Dana Saham Indeks (IDX80) · ORI/SBR 7–9%/thn · DPLK / Dana Pensiun Swasta"
            "</div></div>",
            unsafe_allow_html=True)

with ins_r:
    levels = [("Top 40%",thresholds[1],gap40),("Top 30%",thresholds[2],gap30),
              ("Top 20%",thresholds[3],gap20),("Top 5%",thresholds[4],gap5)]
    st.markdown(
        "<div style='background:#161B2E;border:1px solid rgba(255,255,255,.06);"
        "border-radius:12px;padding:1.5rem;'>"
        "<div style='font-size:.62rem;color:#5A5768;letter-spacing:.18em;"
        "text-transform:uppercase;margin-bottom:.9rem;'>🗺 Roadmap Kekayaan</div>",
        unsafe_allow_html=True)
    for lbl,threshold,gap in levels:
        achieved  = gap<=0
        pct_done  = min(100.0,(user_wealth/threshold*100)) if threshold>0 else 100.0
        bar_col   = "#2DD4BF" if achieved else "#C9A84C"
        m_inv     = monthly_needed(gap,yrs_to_ret)
        status    = "✓ Tercapai" if achieved else f"Butuh {rp(m_inv)}/bln"
        s_col     = "#2DD4BF" if achieved else "#9B97A0"
        st.markdown(
            f"<div style='margin-bottom:.9rem;'>"
            f"<div style='display:flex;justify-content:space-between;margin-bottom:.3rem;align-items:center;'>"
            f"<span style='font-size:.84rem;color:#F0EDE8;font-weight:500;'>{lbl}</span>"
            f"<span style='font-size:.76rem;color:{s_col};'>{status}</span></div>"
            f"<div style='background:rgba(255,255,255,.05);border-radius:4px;height:7px;overflow:hidden;'>"
            f"<div style='background:{bar_col};height:100%;width:{pct_done:.1f}%;border-radius:4px;'></div></div>"
            f"<div style='display:flex;justify-content:space-between;margin-top:.2rem;'>"
            f"<span style='font-size:.68rem;color:#5A5768;'>{rp(user_wealth)}</span>"
            f"<span style='font-size:.68rem;color:#5A5768;'>Target: {rp(threshold)}</span>"
            f"</div></div>",
            unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Waterfall ──────────────────────────────────────────────────────────────────
initial_grown = float(profile.current_savings)*((1+0.085)**yrs_to_ret)
invest_return = max(0.0, initial_grown-float(profile.current_savings))
contrib_total = max(0.0, user_wealth-initial_grown)

fig_wf = go.Figure(go.Waterfall(
    orientation="v",
    measure=["absolute","relative","relative","total"],
    x=["Tabungan Awal","Return Investasi","Kontribusi Rutin","Total Dana Pensiun"],
    y=[float(profile.current_savings), invest_return, contrib_total, 0],
    connector=dict(line=dict(color="rgba(255,255,255,.1)",width=1)),
    decreasing=dict(marker=dict(color="#FF4757")),
    increasing=dict(marker=dict(color="#2DD4BF")),
    totals=dict(marker=dict(color=pct_col)),
    text=[rp(float(profile.current_savings)),rp(invest_return),rp(contrib_total),rp(user_wealth)],
    textposition="outside", textfont=dict(size=9,color="#9B97A0")))

# Insight waterfall
dom_pct = (invest_return/user_wealth*100) if user_wealth>0 else 0
dom_txt = (f"{dom_pct:.0f}% dana pensiun Anda berasal dari return investasi — "
           f"bukan tabungan langsung. Ini kekuatan compounding.")
fig_wf.update_layout(height=340, showlegend=False,
    paper_bgcolor="#161B2E", plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10,r=10,t=75,b=10),
    font=dict(family="DM Sans",color="#9B97A0",size=11),
    title=dict(
        text="Komposisi Proyeksi Dana Pensiun"
             f"<br><span style='font-size:9px;color:#5A5768;'>{dom_txt}</span>",
        font=dict(family="Cormorant Garamond",size=16,color="#F0EDE8"),
        x=0.02, xanchor="left"),
    xaxis=dict(tickfont=dict(size=10,color="#9B97A0")),
    yaxis=dict(tickformat=",.0s",tickfont=dict(size=9),gridcolor="rgba(255,255,255,.04)"),
    shapes=[dict(type="rect",xref="paper",yref="paper",x0=0,y0=0,x1=1,y1=1,
                 line=dict(color="rgba(255,255,255,.06)",width=1),
                 fillcolor="rgba(0,0,0,0)",layer="below")])
st.plotly_chart(fig_wf, use_container_width=True, config={"displayModeBar":False})

st.markdown(
    "<div style='text-align:center;margin-top:2rem;padding-bottom:2rem;"
    "color:#2A2A3E;font-size:.7rem;letter-spacing:.08em;'>"
    "VANTURA v2.0 © 2025 · Benchmark estimasi BPS Indonesia · Bukan saran investasi resmi</div>",
    unsafe_allow_html=True)