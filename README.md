# ChromaGrade Pro 🎨

> **Production-grade, sub-100ms color grade transfer engine** that extracts the color palette, mood, tonal contrast, and cinematic aesthetic from any reference photograph and applies it to your images — 100% offline with zero cloud API dependencies.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.9%2B-5C3EE8.svg?logo=opencv&logoColor=white)](https://opencv.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.26%2B-013243.svg?logo=numpy&logoColor=white)](https://numpy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-16%20Passing-brightgreen.svg)]()

---

## 📸 Overview & Key Features

**ChromaGrade** was built from a rigorous reverse-engineering study of cloud-based color grading apps (such as Piczify). By replacing slow cloud queues and generic models with mathematically sound computer vision algorithms running on NumPy and OpenCV, ChromaGrade achieves **sub-100ms execution times** with **zero per-image cost** and **complete privacy**.

### ✨ Highlights

* **⚡ Sub-100ms Real-Time Inference**: Powered by vectorised NumPy and optimized C++ OpenCV primitives running locally. No waiting in remote queues.
* **🔬 4 Color Science Engines**:
  * **Reinhard LAB Statistical Transfer**: Transfers mean and variance in perceptually uniform $L^*a^*b^*$ color space.
  * **Histogram CDF Matching**: Non-linear cumulative distribution function matching using 256-bin lookup tables (`cv2.LUT`).
  * **Split-Tone Film Emulsion**: Emulates 35mm film stock response by separating shadow split-tones from highlight hues.
  * **Bilateral Edge-Preserving Harmonization**: Harmonizes color washes while preserving 100% of fine edge details and skin textures.
* **🎛️ Comprehensive Photographic Controls**:
  * **Grade Strength** (0% to 100% linear interpolation)
  * **Color Saturation** (-50% to +50% via LAB chroma scaling)
  * **White Balance / Temperature** (-50% Cool Blue to +50% Warm Amber)
  * **S-Curve Contrast Adjustment**
  * **Exposure & Brightness Bias**
  * **Vignette Simulation & Feathering**
  * **Luminance Lock** (preserves source image exposure while adapting chroma)
* **🖥️ Static Studio Grading Monitor**:
  * Modern, light-mode porcelain studio interface.
  * Interactive Before/After split comparison slider with double-click magnetic center snap (50/50).
  * 1:1 pixel inspection mode and fullscreen view.
  * Top 5 dominant palette swatches with hex codes and 1-click clipboard copy.
  * 3-Way Color Balance visualizer (Lift / Gamma / Gain).
  * Session history strip to instantly recall previous grades.
* **🎬 3D LUT (.CUBE) Export**:
  * Export industry-standard 33×33×33 `.cube` files directly compatible with **DaVinci Resolve**, **Adobe Premiere Pro**, **Final Cut Pro**, and **Adobe Photoshop**.
* **🛡️ Universal Format & Alpha Support**:
  * Transparent PNG alpha channel preservation.
  * Auto-rotation normalization via EXIF orientation tags.
  * Support for JPEG, PNG, WebP, TIFF, and single-channel Grayscale.

---

## 🔍 Reverse Engineering Analysis: Piczify vs. ChromaGrade

During initial research, we used **REA** (`rea-agents`) and browser bundle decomposition to deconstruct `https://app.piczify.com/color-grade-transfer`:

### Architecture Comparison

| Dimension | Piczify (`app.piczify.com`) | ChromaGrade Pro |
| :--- | :--- | :--- |
| **Engine Core** | Cloud queue (`fal-image-uploader` + async polling) | **Pure Local Python / OpenCV / NumPy** |
| **Latency** | 10 – 30 seconds per grade | **40 – 80 milliseconds** |
| **Cost** | 10 credits / generation (Paywalled) | **Free & Open Source** |
| **Privacy** | Uploads photos to third-party Cloudflare Worker | **100% Private (Runs locally on machine)** |
| **Comparison View** | Static single image preview | **Interactive dual-pane split slider** |
| **Grading Controls** | None (Single take output) | **Strength, Saturation, Temp, Contrast, Brightness, Vignette** |
| **Color Science** | Black-box model | **4 selectable mathematical engines** |
| **Video / LUT Export** | ❌ Not available | ✅ **33×33×33 `.CUBE` LUT Export** |
| **Palette Analysis** | ❌ None | ✅ **5-Color Dominant Hex Swatches** |

---

## 📐 Color Science & Mathematical Formulation

### 1. Reinhard LAB Color Transfer
Converts images from non-linear sRGB into CIELAB space, where the $L^*$ channel represents perceptual lightness, and $a^*$ and $b^*$ represent green-red and blue-yellow color opponents:

$$\mu_s = \frac{1}{N}\sum x_s, \quad \sigma_s = \sqrt{\frac{1}{N}\sum (x_s - \mu_s)^2}$$

The transferred channel value $x_{res}$ is computed as:

$$x_{res} = \left(\frac{\sigma_r}{\sigma_s}\right) (x_s - \mu_s) + \mu_r$$

Where $\mu_s, \sigma_s$ are source mean and standard deviation, and $\mu_r, \sigma_r$ are reference statistics.

### 2. Cumulative Distribution Function (CDF) Histogram Matching
For each channel $c \in \{R, G, B\}$, the empirical cumulative distribution functions $P_s(v)$ and $P_r(v)$ are calculated. The mapping function $M(v)$ maps source pixel intensities to reference intensities:

$$M(v) = \arg\min_{v'} |P_s(v) - P_r(v')|$$

We accelerate this transformation using an exact 256-element integer lookup table (`cv2.LUT`), achieving $O(1)$ per-pixel evaluation.

### 3. 3D LUT (.CUBE) Generation
A neutral 3D RGB identity lattice of dimensions $N \times N \times N$ ($N=33$, 35,937 color nodes) is synthesized:

$$(r_i, g_j, b_k) = \left(\frac{i}{N-1}, \frac{j}{N-1}, \frac{k}{N-1}\right)$$

The lattice is transformed through the selected grading engine and formatted into Adobe/DaVinci standard `.cube` specification.

---

## 📁 Project Structure

```
ChromaGrade/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   └── algorithms.py       # Reinhard, CDF LUT, Split-Tone, Bilateral, 3D LUT generator
│   ├── static/
│   │   ├── demo/               # Sample input & reference images
│   │   ├── app.js              # Split slider, dropzones, live preview & canvas logic
│   │   ├── index.html          # Light-mode studio interface
│   │   └── styles.css          # Porcelain design system & studio styles
│   ├── __init__.py
│   └── main.py                 # FastAPI endpoints & multipart handling
├── demo-images/                # High-res photography samples
├── tests/
│   ├── __init__.py
│   ├── test_api.py             # Endpoint & integration tests
│   └── test_color_transfer.py  # Mathematical engine validation tests
├── .gitignore                  # Clean exclusions (ignores tools/, ghidra, caches)
├── README.md                   # Full documentation & specifications
├── requirements.txt            # Minimal dependencies
└── run.py                      # Application launcher
```

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.13, 3.14)
- Git

### 2. Clone Repository
```bash
git clone https://github.com/SagarKunnal/ChromaGrade.git
cd ChromaGrade
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Studio Application
```bash
python run.py
```
Or directly with Uvicorn:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open your browser and navigate to:
```
http://localhost:8000
```

---

## 🧪 Running Automated Tests

Run the complete test suite (unit and integration tests for all 4 engines, API endpoints, format handlers, and 3D LUT export):

```bash
python -m unittest discover tests
```

Expected output:
```
................
----------------------------------------------------------------------
Ran 16 tests in 1.1s

OK
```

---

## 📡 REST API Reference

### `POST /api/transfer`
Applies color grading from a reference image onto a source image.

* **Request Type**: `multipart/form-data`
* **Parameters**:
  * `source_file` *(UploadFile)*: Source photo file.
  * `source_url` *(string, optional)*: URL to source image.
  * `reference_file` *(UploadFile)*: Reference aesthetic/look photo file.
  * `reference_url` *(string, optional)*: URL to reference image.
  * `algorithm` *(string)*: `"reinhard"` | `"cdf"` | `"split_tone"` | `"bilateral"` (default: `"reinhard"`).
  * `strength` *(float)*: Blending factor from `0.0` to `1.0` (default: `1.0`).
  * `preserve_luminance` *(bool)*: Preserve original source lightness (default: `false`).
  * `saturation` *(float)*: Chroma bias from `-0.5` to `0.5` (default: `0.0`).
  * `temperature` *(float)*: Warmth shift from `-0.5` to `0.5` (default: `0.0`).
  * `contrast` *(float)*: S-curve contrast shift from `-0.5` to `0.5` (default: `0.0`).
  * `brightness` *(float)*: Exposure adjustment from `-0.5` to `0.5` (default: `0.0`).
  * `vignette` *(float)*: Peripheral vignette factor from `0.0` to `1.0` (default: `0.0`).

* **Response**: `application/json`
  ```json
  {
    "success": true,
    "image_data": "data:image/jpeg;base64,...",
    "width": 1920,
    "height": 1080,
    "palette": [
      {"hex": "#d4822f", "name": "Warm Ochre", "percentage": 36.4, "rgb": [212, 130, 47]},
      {"hex": "#284b63", "name": "Slate Teal", "percentage": 24.1, "rgb": [40, 75, 99]},
      {"hex": "#e9d8a6", "name": "Dune Gold", "percentage": 18.2, "rgb": [233, 216, 166]},
      {"hex": "#1b263b", "name": "Midnight", "percentage": 12.8, "rgb": [27, 38, 59]},
      {"hex": "#9a031e", "name": "Carmine", "percentage": 8.5, "rgb": [154, 3, 30]}
    ],
    "processing_time_ms": 54.2
  }
  ```

---

### `POST /api/export-lut`
Generates and downloads a standardized 3D `.CUBE` LUT matching the reference grade.

* **Parameters**: `reference_file` (or `reference_url`), `algorithm`, `strength`, `lut_size` (default: `33`).
* **Response**: Binary `.cube` file stream (`Content-Disposition: attachment; filename="grade_reinhard_33x33.cube"`).

---

### `GET /api/sample-images`
Returns curated library of high-resolution demo images and cinematic reference looks.

---

### `GET /api/health`
System diagnostics and server health check.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
