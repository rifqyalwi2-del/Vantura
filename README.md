# ⚜️ VANTURA — Wealth Intelligence v2.0

> **Kalkulator aktuaria pensiun personal berbasis data ekonomi Indonesia real-time.**  
> Proyeksi kekayaan · Monte Carlo · Peer Benchmarking · Stress Test · Laporan PDF

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app.streamlit.app)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red)
![Supabase](https://img.shields.io/badge/Database-Supabase-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📸 Preview

| Dashboard | Stress Test | Peer Benchmark |
|-----------|-------------|----------------|
| Skor kesiapan 0–100 | 5 skenario ekonomi | Posisi vs sebaya |
| Grafik lintasan kekayaan | Monte Carlo 1.000 sim | Roadmap kekayaan |

---

## ✨ Fitur Utama

- **🎯 Skor Kesiapan Pensiun** — 0–100 dengan penjelasan faktor penyebab
- **📊 Proyeksi Aktuaria** — Lintasan kekayaan hingga usia 100 tahun
- **🎲 Monte Carlo 1.000 Simulasi** — Uji ketahanan terhadap volatilitas pasar
- **⚡ Stress Test** — 5 skenario: Normal, Hiperinflasi, Market Crash, Resesi, Optimis
- **👥 Peer Benchmarking** — Posisi vs demografi sebaya Indonesia (BPS-adjusted)
- **📄 Laporan PDF** — Dokumen A4 eksekutif dengan 6 rekomendasi konkrit
- **🔐 Auth + OTP Email** — Login 2-step dengan verifikasi email
- **📡 Live Data** — CPI, BI Rate, Inflasi Medis, Harga Emas real-time

---

## 🗂️ Struktur Project

```
vantura/
├── app.py                     # Entry point
├── pages/
│   ├── 0_login.py             # Login & register (OTP 2-step)
│   ├── 1_profil.py            # Input profil finansial
│   ├── 2_dashboard.py         # Dashboard proyeksi utama
│   ├── 3_stress_test.py       # Stress test skenario ekstrem
│   ├── 4_benchmark.py         # Peer benchmarking
│   ├── 5_report.py            # Generate & unduh PDF
│   ├── 6_settings.py          # Pengaturan akun
│   ├── 7_simulator.py         # Simulasi cepat (tanpa login)
│   └── _shared.py             # Sidebar & komponen bersama
├── engine/
│   ├── actuarial.py           # Core engine proyeksi aktuaria
│   ├── data_fetcher.py        # Live data: CPI, BI Rate, Emas
│   ├── pdf_generator.py       # Generate laporan PDF
│   └── validators.py          # Validasi input
├── utils/
│   ├── auth.py                # Autentikasi + OTP flow
│   ├── db.py                  # Database layer (Supabase)
│   ├── otp.py                 # Generate & kirim OTP via email
│   ├── session.py             # Session management
│   └── logger.py              # Centralized logging
├── .streamlit/
│   ├── config.toml            # Streamlit config & theme
│   └── secrets.toml           # ⚠️ JANGAN di-commit! (lihat .gitignore)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🚀 Cara Menjalankan Lokal

### 1. Clone repository
```bash
git clone https://github.com/username/vantura.git
cd vantura
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Supabase
1. Buat project di [supabase.com](https://supabase.com)
2. Jalankan SQL berikut di **SQL Editor**:

```sql
CREATE TABLE IF NOT EXISTS users (
  email TEXT PRIMARY KEY, name TEXT,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_login TIMESTAMPTZ, login_count INTEGER DEFAULT 0,
  session_token TEXT
);
CREATE TABLE IF NOT EXISTS profiles (
  email TEXT PRIMARY KEY REFERENCES users(email) ON DELETE CASCADE,
  data JSONB NOT NULL DEFAULT '{}', updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS history (
  id BIGSERIAL PRIMARY KEY,
  email TEXT REFERENCES users(email) ON DELETE CASCADE,
  data JSONB NOT NULL DEFAULT '{}', created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS analytics (
  key TEXT PRIMARY KEY, value INTEGER DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS otp_tokens (
  email TEXT NOT NULL, token TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL, used BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (email, token)
);
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE history DISABLE ROW LEVEL SECURITY;
ALTER TABLE analytics DISABLE ROW LEVEL SECURITY;
ALTER TABLE otp_tokens DISABLE ROW LEVEL SECURITY;
```

### 4. Buat `.streamlit/secrets.toml`
```toml
[supabase]
url = "https://xxxxxxxxxxxx.supabase.co"
key = "eyJhbGci..."

[app]
secret_key = "random-string-minimal-32-karakter"

[email]
smtp_user     = "emailkamu@gmail.com"
smtp_password = "xxxx xxxx xxxx xxxx"   # Gmail App Password
sender_name   = "Vantura"
```

> **Gmail App Password:** myaccount.google.com → Keamanan → Verifikasi 2 Langkah → Sandi Aplikasi

### 5. Jalankan
```bash
streamlit run app.py
```

Buka browser di `http://localhost:8501`

---

## ☁️ Deploy ke Streamlit Cloud

1. Push repo ke GitHub (**pastikan `secrets.toml` tidak ikut**)
2. Buka [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Pilih repo → Branch: `main` → Main file: `app.py`
4. Klik **Advanced settings** → **Secrets** → paste isi `secrets.toml`
5. Klik **Deploy!**

---

## ⚙️ Engine Aktuaria

Vantura menggunakan model aktuaria berbasis data Indonesia:

| Parameter | Sumber |
|-----------|--------|
| Harapan hidup | BPS Indonesia (pria 72 thn, wanita 76 thn) |
| Inflasi CPI | World Bank API (real-time) |
| Inflasi medis | 2× CPI (estimasi) |
| Return investasi | 8.5%/tahun (baseline) |
| Peer benchmark | Estimasi distribusi kekayaan BPS |

**Skenario Stress Test:**
- **Normal** — Baseline CPI 5%, return 8.5%
- **Hiperinflasi Medis** — Biaya kesehatan 3× lipat, return −15%
- **Market Crash −30%** — Portofolio turun 30% seketika
- **Resesi Ekonomi** — Inflasi 7.5%, return −40%
- **Skenario Optimis** — Inflasi 3.5%, return +25%

---

## 🔐 Keamanan

- Password di-hash dengan **SHA-256 + salt**
- Session token menggunakan **HMAC signature**
- Login 2-step dengan **OTP 6 digit** (expired 5 menit)
- Rate limiting: maks **5 percobaan** login, lockout **15 menit**
- Secrets tidak pernah di-commit ke repository

---

## 📦 Dependencies

```
streamlit>=1.35.0      # Web framework
plotly>=5.20.0         # Interactive charts
numpy>=1.26.0          # Monte Carlo calculations
pandas>=2.2.0          # Data processing
reportlab>=4.0.0       # PDF generation
supabase>=2.4.0        # Cloud database
requests>=2.31.0       # Live data fetching
python-dotenv>=1.0.0   # Environment variables
```

---

## ⚠️ Disclaimer

> Vantura adalah alat bantu perencanaan finansial berbasis model aktuaria.  
> **Bukan merupakan saran investasi resmi.**  
> Konsultasikan keputusan finansial Anda dengan perencana keuangan bersertifikat (CFP).

---

## 📄 Lisensi

MIT License — bebas digunakan dan dimodifikasi dengan mencantumkan kredit.

---

<div align="center">
  <b>VANTURA</b> · Wealth Intelligence v2.0 · Built with Streamlit & ❤️
</div>