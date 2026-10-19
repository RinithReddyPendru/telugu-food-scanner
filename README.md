# Annapurna: Telugu & South Indian Food Scanner

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg?style=flat&logo=python)](https://python.org)
[![Gemini](https://img.shields.io/badge/Google%20GenAI-Gemini%203.8%20%2F%20Gemma%204-8E75C2.svg?style=flat)](https://ai.google.dev)
[![ICMR-NIN](https://img.shields.io/badge/Nutrition-ICMR--NIN%20IFCT%202017-E65100.svg?style=flat)](https://www.nin.res.in)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat)](LICENSE)

An intelligent, high-accuracy computer vision and nutrition tracking engine built specifically for **Andhra & Telangana regional cuisines**, maternal healthcare programs (Janani Mitra), and South Indian dietary tracking.

Powered by Google Gemini Multimodal Vision + ICMR-NIN (National Institute of Nutrition, Hyderabad) Indian Food Composition Tables (IFCT 2017).

---

## 🌟 Highlights & Capabilities

- **121-Dish Curated Telugu Catalog**: 93 authentic clinical dishes mapped from the Janani Mitra health catalog plus 28 foundational staples (Pesarattu, Ragi Sangati, Gutti Vankaya, Gongura Pappu, Natukodi Pulusu, Ulava Charu, Balamrutham, etc.).
- **ICMR-NIN IFCT Macro & Micro Nutrition**: Precise quantification of Calories (kcal), Protein (g), Carbohydrates (g), Fat (g), Dietary Fiber (g), Iron (mg), Calcium (mg), Folate (µg), Vitamin A (µg), Vitamin C (mg), and Sodium (mg).
- **Portion & Cooking Oil Modifiers**: Dynamic recalculation based on oil usage (`low` 0.85x, `moderate` 1.0x, `high` 1.2x).
- **WHO / FAO MDD-W Diversity Score**: Tracks Minimum Dietary Diversity for Women across 10 official food groups (G1 to G10) to combat micronutrient deficiencies and gestational anemia.
- **Botanical & Gourd Disambiguation Engine**: Micro-prompt rules that accurately distinguish between visually similar cucurbits (Dosakaya yellow melon vs. Keera green cucumber vs. Sorakaya bottle gourd vs. Beerakaya ridge gourd).
- **Raw Salad vs. Cooked Curry Guardrails**: Prevents raw cucumber, tomato, or carrot slices from being falsely classified as cooked dals, sambars, or curries.
- **Multi-Model Auto-Failover Pool**:
  - `gemini-3.8-flash` (Maximum accuracy)
  - `gemini-3.1-flash-lite` (High quota)
  - `gemini-3.5-flash-lite` (High quota)
  - `gemma-4-31b-it` (14,400 RPD free tier fallback)
- **SHA-256 In-Memory Cache**: Identical image scans return in `<50ms` with 0 tokens consumed.
- **Client-Side Canvas Compression**: High-resolution mobile phone camera photos are auto-compressed to 800px (~80-120KB) for instant scanning and minimal token usage.
- **95% Benchmark Accuracy**: Verified on a 100-dish Andhra/Telangana photo test suite.

---

## 🚀 Quick Start (Local)

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/RinithReddyPendru/telugu-food-scanner.git
cd telugu-food-scanner

# Create and activate virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Gemini API Key
Set your Gemini API key in your environment or in a `.env` file:
```bash
# Windows PowerShell:
$env:GEMINI_API_KEY="your-gemini-api-key"

# Linux/macOS:
export GEMINI_API_KEY="your-gemini-api-key"
```

### 3. Launch Scanner Web App
```bash
python run.py
```
Open [http://localhost:8005](http://localhost:8005) in your web browser. Interactive Swagger API documentation is available at [http://localhost:8005/docs](http://localhost:8005/docs).

### 4. CLI Scan Mode
```bash
python run.py --image path/to/pesarattu.jpg --hint "Breakfast"
```

---

## 📡 REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Mobile-first Web UI (camera viewfinder, upload, paste, nutrient cards) |
| `/api/v1/scan` | `POST` | Multipart image upload scan with model failover and ICMR-NIN calculations |
| `/api/v1/scan-base64` | `POST` | JSON payload base64 image scan |
| `/api/v1/calculate` | `POST` | Deterministic nutrition calculation for known dish IDs and custom portions |
| `/api/v1/dishes` | `GET` | Search and filter 121 Telugu dishes with full nutritional profiles |
| `/api/v1/stats` | `GET` | Cache hits, active model pool, and catalog metrics |
| `/api/v1/health` | `GET` | Health check endpoint |

---

## 🌐 Deploy to Vercel

This repository is pre-configured for Vercel Serverless Python Functions:

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy to production
vercel --prod
```
Ensure you add `GEMINI_API_KEY` under **Project Settings → Environment Variables** on Vercel.

---

## 🧪 Testing & Validation

```bash
# Run Telugu catalog & nutrition test suite
python tests/test_catalog_and_nutrition.py

# Run targeted edge-case verification
python tests/test_targeted_edge_cases.py
```

---

## 📄 License
MIT License. Built for Andhra & Telangana regional health and nutrition advancement.
