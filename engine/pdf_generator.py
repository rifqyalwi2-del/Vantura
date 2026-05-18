"""
engine/pdf_generator.py — v2.0
Full A4 executive report with all sections.
"""
from __future__ import annotations
import io
from datetime import datetime
from typing import TYPE_CHECKING

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, KeepTogether, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

if TYPE_CHECKING:
    from engine.actuarial import ActuarialResult, UserProfile

GOLD   = colors.HexColor("#C9A84C")
TEAL   = colors.HexColor("#2DD4BF")
DARK   = colors.HexColor("#0A0D14")
MUTED  = colors.HexColor("#5A5768")
TEXT   = colors.HexColor("#1A1A2E")
LGREY  = colors.HexColor("#F4F2EC")
OFF_W  = colors.HexColor("#FAFAF8")
DANGER = colors.HexColor("#FF4757")
WARN   = colors.HexColor("#FFA502")
OK     = colors.HexColor("#2DD4BF")


def _rp(v: float) -> str:
    if abs(v) >= 1e9: return f"Rp {v/1e9:.2f} M"
    if abs(v) >= 1e6: return f"Rp {v/1e6:.1f} Jt"
    return f"Rp {v:,.0f}"


def _sc(s: float) -> tuple[colors.Color, str]:
    if s >= 75:  return OK,     "#2DD4BF"
    if s >= 50:  return WARN,   "#FFA502"
    return DANGER, "#FF4757"


def _ts_base() -> TableStyle:
    return TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  DARK),
        ("TEXTCOLOR",     (0,0),(-1,0),  GOLD),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1), 8),
        ("FONTNAME",      (0,1),(0,-1),  "Helvetica-Bold"),
        ("TEXTCOLOR",     (0,1),(-1,-1), TEXT),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [OFF_W,LGREY]),
        ("GRID",          (0,0),(-1,-1), 0.4, colors.HexColor("#DDDDDD")),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
    ])


def generate_pdf(profile: "UserProfile", result: "ActuarialResult") -> bytes:
    buf = io.BytesIO()
    W   = A4[0] - 3*cm
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm,  bottomMargin=1.5*cm,
        title="Vantura — Laporan Aktuaria v2",
        author="Vantura Actuarial Intelligence")

    SS = getSampleStyleSheet()
    def S(n, **kw): return ParagraphStyle(n, parent=SS["Normal"], **kw)

    s_logo = S("L", fontSize=26, textColor=GOLD, fontName="Helvetica-Bold",
               alignment=TA_CENTER, spaceAfter=2, leading=32)
    s_sub  = S("Su", fontSize=8,  textColor=MUTED, fontName="Helvetica",
               alignment=TA_CENTER, spaceAfter=8)
    s_sec  = S("Se", fontSize=13, textColor=GOLD, fontName="Helvetica-Bold",
               spaceBefore=14, spaceAfter=8, leading=17)
    s_body = S("Bo", fontSize=9,  textColor=TEXT, fontName="Helvetica",
               leading=14, spaceAfter=4)
    s_rec  = S("Re", fontSize=9,  textColor=colors.HexColor("#1A3A2A"),
               fontName="Helvetica", leading=14, leftIndent=6)
    s_foot = S("Fo", fontSize=7,  textColor=MUTED, fontName="Helvetica",
               alignment=TA_CENTER, leading=10)
    s_disc = S("Di", fontSize=6.5, textColor=MUTED, fontName="Helvetica-Oblique",
               alignment=TA_CENTER, leading=9)

    story = []

    # Header
    story += [Paragraph("VANTURA", s_logo),
              Paragraph("ACTUARIAL WEALTH INTELLIGENCE v2.0", s_sub),
              HRFlowable(width=W, thickness=1, color=GOLD, spaceAfter=10)]

    meta = [["Laporan untuk:", profile.name or "Pengguna",
             "Tanggal:", datetime.now().strftime("%d %B %Y")],
            ["Skenario:", profile.scenario_key,
             "Gender:", profile.gender.title()]]
    mt = Table(meta, colWidths=[3.5*cm,6.5*cm,3*cm,5.5*cm])
    mt.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),"Helvetica"),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("FONTNAME",(2,0),(2,-1),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),8),
        ("TEXTCOLOR",(0,0),(-1,-1),TEXT),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),4),
    ]))
    story += [mt, Spacer(1,8)]

    # Score banner
    sc = result.readiness_score
    sc_col, sc_hex = _sc(sc)
    banner = [[
        Paragraph(f"<b>{sc:.0f}</b>",
            S("SB", fontSize=46, textColor=sc_col,
              fontName="Helvetica-Bold", alignment=TA_CENTER, leading=52)),
        Paragraph(
            f"<b>RETIREMENT READINESS SCORE</b><br/>"
            f"<font size=12 color='{sc_hex}'>{result.readiness_label}</font><br/><br/>"
            f"<font size=8 color='#555'>Proyeksi dana: <b>{_rp(result.nest_egg_at_retirement)}</b></font><br/>"
            f"<font size=8 color='#555'>Target dana: <b>{_rp(result.required_nest_egg)}</b></font><br/>"
            f"<font size=8 color='#555'>Monte Carlo sukses: <b>{result.mc_success_rate:.0f}%</b></font>",
            S("SD", fontSize=10, textColor=TEXT, fontName="Helvetica",
              leading=16, leftIndent=8)),
    ]]
    bt = Table(banner, colWidths=[4*cm, W-4*cm])
    bt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),OFF_W), ("BOX",(0,0),(-1,-1),1,GOLD),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),12), ("RIGHTPADDING",(0,0),(-1,-1),12),
        ("TOPPADDING",(0,0),(-1,-1),12),  ("BOTTOMPADDING",(0,0),(-1,-1),12),
    ]))
    story += [bt, Spacer(1,12)]

    # Section 1: Profil
    story.append(Paragraph("1. PROFIL AKTUARIA", s_sec))
    p_rows = [
        ["Parameter","Nilai","Parameter","Nilai"],
        ["Usia Saat Ini",    f"{profile.current_age} thn",   "Usia Pensiun",     f"{profile.retirement_age} thn"],
        ["Harapan Hidup",    f"{result.life_expectancy:.1f} thn","Masa Pensiun",  f"{result.years_in_retirement:.1f} thn"],
        ["Profesi",          profile.profession.split("/")[0].strip()[:24],
         "Domisili",         profile.domicile.split("(")[0].strip()[:24]],
        ["Gaji Bulanan",     _rp(profile.monthly_salary),    "Tabungan Awal",    _rp(profile.current_savings)],
        ["Tingkat Menabung", f"{profile.savings_rate_pct:.1f}%","Nabung Bersih", _rp(result.monthly_net_savings)],
        ["Sandwich Gen.",    _rp(profile.sandwich_monthly),  "Tapera","Ya (2.5%)" if profile.tapera_enabled else "Tidak"],
        ["Inflasi Efektif",  f"{result.eff_inflation*100:.1f}%","Inflasi Medis", f"{result.eff_medical_inflation*100:.1f}%"],
    ]
    pt = Table(p_rows, colWidths=[4.8*cm,3.8*cm,4.8*cm,5.1*cm])
    pt.setStyle(_ts_base()); story += [pt, Spacer(1,10)]

    # Section 2: Proyeksi
    story.append(Paragraph("2. PROYEKSI KEKAYAAN & BROKE AGE", s_sec))
    broke_str = "Tidak terdeteksi ✓"
    broke_bg, broke_tc = colors.HexColor("#E8F8EE"), colors.HexColor("#1A5C3A")
    if result.broke_age:
        broke_str = f"{result.broke_age:.0f} tahun"
        if result.broke_age < profile.retirement_age + 5:
            broke_bg, broke_tc = colors.HexColor("#FDEAEA"), DANGER
        elif result.broke_age < result.life_expectancy:
            broke_bg, broke_tc = colors.HexColor("#FFF3CD"), WARN

    proj_rows = [
        ["Metrik","Nilai","Keterangan"],
        ["Proyeksi saat Pensiun",  _rp(result.nest_egg_at_retirement), f"Akumulasi {result.years_to_retire} tahun"],
        ["Target Dana Pensiun",    _rp(result.required_nest_egg),       f"{result.years_in_retirement:.1f} thn pensiun"],
        ["Shortfall",              _rp(result.shortfall) if result.shortfall>0 else "Surplus ✓","—"],
        ["Top-up Nabung/Bln",      _rp(result.monthly_top_up_needed) if result.monthly_top_up_needed>0 else "—","Untuk tutup shortfall"],
        ["Broke Age",              broke_str,                          "Usia saldo Rp 0"],
        ["Monte Carlo Sukses",     f"{result.mc_success_rate:.0f}%",  f"dari {1000} simulasi"],
        ["Peer Percentile",        result.peer_percentile,             f"Usia {profile.current_age} tahun"],
    ]
    prt = Table(proj_rows, colWidths=[5.5*cm,4.5*cm,W-10*cm])
    ts2 = _ts_base()
    ts2.add("BACKGROUND",(0,5),(-1,5),broke_bg)
    ts2.add("TEXTCOLOR",(1,5),(1,5),broke_tc)
    ts2.add("FONTNAME",(1,5),(1,5),"Helvetica-Bold")
    prt.setStyle(ts2); story += [prt, Spacer(1,10)]

    # Section 3: Alokasi Aset
    story.append(Paragraph("3. REKOMENDASI ALOKASI ASET (GLIDE PATH)", s_sec))
    alloc_rows = [
        ["Aset","Alokasi","Keterangan"],
        ["Saham / Reksa Dana Saham", f"{result.glide_path_equity:.0f}%","Pertumbuhan jangka panjang"],
        ["Obligasi / Reksa Dana Pendapatan Tetap", f"{result.glide_path_bonds:.0f}%","Stabilitas & kupon rutin"],
        ["Emas (fisik / ETF)", f"{result.glide_path_gold:.0f}%","Lindung nilai inflasi"],
        ["Kas / Pasar Uang",  f"{result.glide_path_cash:.0f}%", "Dana darurat & likuiditas"],
    ]
    at = Table(alloc_rows, colWidths=[7*cm,3*cm,W-10*cm])
    at.setStyle(_ts_base()); story += [at, Spacer(1,10)]

    # Section 4: Rekomendasi
    story.append(Paragraph("4. REKOMENDASI TINDAKAN KONKRIT", s_sec))
    for i, rec in enumerate(_recs(profile, result), 1):
        cd = [[
            Paragraph(f"<b>{i}</b>",
                S("RN", fontSize=13, textColor=GOLD, fontName="Helvetica-Bold",
                  alignment=TA_CENTER, leading=15)),
            Paragraph(rec, s_rec),
        ]]
        rt = Table(cd, colWidths=[1.2*cm, W-1.2*cm])
        rt.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F5F0E8")),
            ("BOX",(0,0),(-1,-1),0.5,GOLD),
            ("LINEBEFORE",(0,0),(0,-1),3,GOLD),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("TOPPADDING",(0,0),(-1,-1),7),
            ("BOTTOMPADDING",(0,0),(-1,-1),7),
            ("LEFTPADDING",(0,0),(-1,-1),8),
        ]))
        story.append(KeepTogether([rt, Spacer(1,5)]))

    story += [Spacer(1,10),
              HRFlowable(width=W, thickness=0.5, color=GOLD, spaceBefore=10, spaceAfter=8),
              Paragraph(f"<b>VANTURA</b> v2.0 — Actuarial Wealth Intelligence  ·  "
                        f"Dibuat: {datetime.now().strftime('%d %B %Y, %H:%M WIB')}", s_foot),
              Paragraph("Laporan informatif berbasis asumsi aktuaria. "
                        "Bukan saran investasi resmi. "
                        "Konsultasikan dengan CFP bersertifikat.", s_disc)]

    doc.build(story)
    return buf.getvalue()


def _recs(profile: "UserProfile", result: "ActuarialResult") -> list[str]:
    r = []
    if result.monthly_top_up_needed > 0:
        r.append(f"<b>Tambah investasi {_rp(result.monthly_top_up_needed)}/bulan</b> "
                 f"untuk menutup kekurangan {_rp(result.shortfall)}. "
                 f"Reksa dana campuran atau ORI/SBR (7–9%/thn) jadi pilihan utama.")
    if result.broke_age and result.broke_age < result.life_expectancy:
        gap = result.life_expectancy - result.broke_age
        r.append(f"<b>PERINGATAN: Dana habis {gap:.0f} thn sebelum harapan hidup.</b> "
                 f"Pertimbangkan anuitas DPLK atau properti sewa.")
    if result.mc_success_rate < 70:
        r.append(f"Monte Carlo hanya {result.mc_success_rate:.0f}% sukses — "
                 f"rencana rentan terhadap volatilitas pasar. "
                 f"Tingkatkan tabungan atau diversifikasi ke aset defensif.")
    if profile.savings_rate_pct < 20:
        r.append(f"Tabungan {profile.savings_rate_pct:.0f}% di bawah 20%. "
                 f"Terapkan <i>Pay Yourself First</i>: otomasi transfer di hari gajian.")
    r.append(f"Alokasi ideal usia Anda: Saham {result.glide_path_equity:.0f}% · "
             f"Obligasi {result.glide_path_bonds:.0f}% · "
             f"Emas {result.glide_path_gold:.0f}% · Kas {result.glide_path_cash:.0f}%.")
    r.append(f"Inflasi medis {result.eff_medical_inflation*100:.1f}%/thn. "
             f"Siapkan asuransi kesehatan swasta dan dana darurat kesehatan 3× premi.")
    return r[:6]