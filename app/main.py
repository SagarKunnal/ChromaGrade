import os
import time
import base64
import io
import cv2
import numpy as np
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps

from app.core.algorithms import (
    apply_color_grade,
    generate_cube_lut,
    extract_color_palette
)

app = FastAPI(
    title="ChromaGrade Pro — Studio Color Transfer",
    description="Professional color palette, mood, and aesthetic transfer engine inspired by Piczify and DaVinci Resolve.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DEMO_DIR = os.path.join(STATIC_DIR, "demo")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def _to_float(val: Any, default: float) -> float:
    if val is None or hasattr(val, "default"):
        return default
    try:
        return float(val)
    except Exception:
        return default

def _to_bool(val: Any, default: bool) -> bool:
    if val is None or hasattr(val, "default"):
        return default
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return bool(val)

def _to_str(val: Any, default: str) -> str:
    if val is None or hasattr(val, "default"):
        return default
    return str(val)

def _to_int(val: Any, default: int) -> int:
    if val is None or hasattr(val, "default"):
        return default
    try:
        return int(val)
    except Exception:
        return default

def read_image_from_bytes(file_bytes: bytes, max_dimension: int = 2560) -> np.ndarray:
    """
    Robustly decodes any user image format (JPEG, PNG, WEBP, TIFF, BMP, etc.),
    auto-corrects smartphone EXIF rotation, normalizes to 3-channel BGR,
    and bounds maximum dimensions for performance while preserving ultra-high quality.
    """
    if not file_bytes or len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty image data provided")

    try:
        pil_img = Image.open(io.BytesIO(file_bytes))

        # Auto-rotate based on smartphone EXIF orientation tag
        try:
            pil_img = ImageOps.exif_transpose(pil_img)
        except Exception:
            pass

        # Convert any mode (RGBA, Palette, Grayscale, CMYK) to RGB
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")

        # Downscale gracefully if beyond max_dimension (e.g. 24-48 MP down to 2560px max)
        w, h = pil_img.size
        if max(w, h) > max_dimension:
            scale = max_dimension / float(max(w, h))
            new_w, new_h = int(w * scale), int(h * scale)
            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Convert PIL RGB to OpenCV BGR
        rgb_arr = np.array(pil_img)
        bgr_img = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)
        return bgr_img

    except Exception as e:
        # Fallback to OpenCV native decode
        try:
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                return img
        except Exception:
            pass
        raise HTTPException(status_code=400, detail=f"Unsupported image file: {str(e)}")

def encode_image_to_base64(img_bgr: np.ndarray, quality: int = 92) -> str:
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, buffer = cv2.imencode(".jpg", img_bgr, encode_param)
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"

def extract_bytes_from_input(file_obj: Any, url_or_data: Optional[str]) -> Optional[bytes]:
    """Extracts raw bytes from either an uploaded file, a data URI, or a static demo path."""
    # 1. Check uploaded file
    if file_obj is not None and not hasattr(file_obj, "default") and hasattr(file_obj, "filename") and file_obj.filename:
        if hasattr(file_obj, "file"):
            file_obj.file.seek(0)
            return file_obj.file.read()

    # 2. Check URL or data URI
    clean_url = None if (url_or_data is None or hasattr(url_or_data, "default")) else str(url_or_data)
    if clean_url:
        # Base64 data URI
        if clean_url.startswith("data:image/"):
            try:
                header, b64_part = clean_url.split(",", 1)
                return base64.b64decode(b64_part)
            except Exception:
                pass
        # Static local path
        clean_path = clean_url.replace("/static/", "").replace("/", os.sep)
        disk_path = os.path.join(STATIC_DIR, clean_path)
        if os.path.exists(disk_path):
            with open(disk_path, "rb") as f:
                return f.read()

    return None

@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>ChromaGrade Pro</h1><p>Index page loading...</p>"

@app.get("/api/health")
def health_check():
    ghidra_dir = os.environ.get("GHIDRA_INSTALL_DIR", "d:\\colour\\tools\\ghidra\\ghidra_12.2_PUBLIC")
    ghidra_installed = os.path.exists(ghidra_dir)
    return {
        "status": "online",
        "service": "ChromaGrade Pro AI Studio",
        "version": "2.0.0",
        "opencv_version": cv2.__version__,
        "numpy_version": np.__version__,
        "engines": ["reinhard", "cdf", "split_tone", "bilateral"],
        "ghidra_status": "configured" if ghidra_installed else "not_configured",
        "ghidra_path": ghidra_dir if ghidra_installed else None,
        "rea_cli": "rea@6.7.0"
    }

@app.get("/api/sample-images")
def get_sample_images():
    """Returns demo sample inputs and reference images."""
    inputs = [
        {"id": "input1", "title": "Street Portrait", "url": "/static/demo/color_input1.jpg", "category": "Portrait"},
        {"id": "input2", "title": "Urban Architecture", "url": "/static/demo/color_input2.jpg", "category": "Architecture"},
        {"id": "input3", "title": "Model Editorial", "url": "/static/demo/color_input3.jpg", "category": "Fashion"},
    ]
    references = [
        {"id": "ref1", "title": "Warm Autumn Film", "url": "/static/demo/color_reference_1.jpg", "tag": "Warm Golden"},
        {"id": "ref2", "title": "Golden Sunset Horizon", "url": "/static/demo/color_reference_2.jpg", "tag": "Amber Twilight"},
        {"id": "ref3", "title": "Cinematic Cyber Teal", "url": "/static/demo/color_reference_3.jpg", "tag": "Sci-Fi Neon"},
    ]
    return {"inputs": inputs, "references": references}

@app.get("/api/presets")
def get_presets():
    """Returns curated cinematic & film stock reference presets."""
    presets = [
        {
            "id": "portra400",
            "name": "Kodak Portra 400",
            "subtitle": "Natural skin tones & warm golden grain",
            "algorithm": "reinhard",
            "url": "/static/demo/presets/preset_portra400.jpg",
            "tags": ["Analog Film", "Warm", "Portraits"],
            "description": "Legendary color negative emulsion featuring creamy, true-to-life skintones, gentle highlight roll-off, and warm pastel undertones."
        },
        {
            "id": "velvia50",
            "name": "Fujifilm Velvia 50",
            "subtitle": "Vivid saturated landscapes & deep cyan skies",
            "algorithm": "cdf",
            "url": "/static/demo/presets/preset_velvia50.jpg",
            "tags": ["High Saturation", "Vibrant", "Landscape"],
            "description": "Ultra-fine grain slide film renowned for deep emerald foliage, electric cyan skies, and punchy dramatic contrast."
        },
        {
            "id": "cyberpunk",
            "name": "Cyberpunk 2049",
            "subtitle": "High-contrast neon magenta & midnight cyan",
            "algorithm": "split_tone",
            "url": "/static/demo/presets/preset_cyberpunk.jpg",
            "tags": ["Sci-Fi", "Split-Tone", "Cinematic"],
            "description": "Blade Runner aesthetic balancing cold deep-sea shadows against searing neon magenta and amber highlights."
        },
        {
            "id": "bleach_bypass",
            "name": "Bleach Bypass",
            "subtitle": "Gritty silver retention & desaturated drama",
            "algorithm": "cdf",
            "url": "/static/demo/presets/preset_bleach_bypass.jpg",
            "tags": ["Gritty", "Action", "High Contrast"],
            "description": "Silver retention photochemical process delivering harsh contrast, desaturated hues, and cold metallic textures."
        },
        {
            "id": "wes_anderson",
            "name": "Wes Anderson Pastel",
            "subtitle": "Whimsical nostalgic yellow & soft mint greens",
            "algorithm": "reinhard",
            "url": "/static/demo/presets/preset_wes_anderson.jpg",
            "tags": ["Pastel", "Whimsical", "Editorial"],
            "description": "Quirky storybook aesthetic featuring buttery mustard yellows, soft mint greens, and low-contrast warm shadows."
        },
        {
            "id": "noir",
            "name": "Classic Monochrome Noir",
            "subtitle": "Deep obsidian blacks & velvety silver highlights",
            "algorithm": "cdf",
            "url": "/static/demo/presets/preset_noir.jpg",
            "tags": ["Monochrome", "Dramatic", "Moody"],
            "description": "Timeless 35mm panchromatic film look with deep crushed shadows, rich specular highlights, and pure tonal contrast."
        }
    ]
    return {"presets": presets}

@app.post("/api/transfer")
def transfer_color_grade(
    source_file: Optional[UploadFile] = File(None),
    reference_file: Optional[UploadFile] = File(None),
    source_url: Optional[str] = Form(None),
    reference_url: Optional[str] = Form(None),
    algorithm: str = Form("reinhard"),
    strength: float = Form(1.0),
    preserve_luminance: bool = Form(False),
    saturation: float = Form(0.0),
    temperature: float = Form(0.0),
    contrast: float = Form(0.0),
    brightness: float = Form(0.0),
    vignette: float = Form(0.0)
):
    start_time = time.time()

    # Normalize parameters
    algo = _to_str(algorithm, "reinhard")
    str_val = _to_float(strength, 1.0)
    pres_lum = _to_bool(preserve_luminance, False)
    sat_val = _to_float(saturation, 0.0)
    temp_val = _to_float(temperature, 0.0)
    con_val = _to_float(contrast, 0.0)
    bri_val = _to_float(brightness, 0.0)
    vig_val = _to_float(vignette, 0.0)

    # Load source bytes
    source_bytes = extract_bytes_from_input(source_file, source_url)
    if not source_bytes or len(source_bytes) == 0:
        raise HTTPException(status_code=400, detail="Source image is required")

    # Load reference bytes
    reference_bytes = extract_bytes_from_input(reference_file, reference_url)
    if not reference_bytes or len(reference_bytes) == 0:
        raise HTTPException(status_code=400, detail="Reference image is required")

    src_bgr = read_image_from_bytes(source_bytes)
    ref_bgr = read_image_from_bytes(reference_bytes)

    # Perform color grade transfer
    graded_bgr, palette = apply_color_grade(
        source_bgr=src_bgr,
        reference_bgr=ref_bgr,
        algorithm=algo,
        strength=str_val,
        preserve_luminance=pres_lum,
        saturation=sat_val,
        temperature=temp_val,
        contrast=con_val,
        brightness=bri_val,
        vignette=vig_val
    )

    output_b64 = encode_image_to_base64(graded_bgr)
    elapsed = round((time.time() - start_time) * 1000, 1)

    return {
        "success": True,
        "image_data": output_b64,
        "width": src_bgr.shape[1],
        "height": src_bgr.shape[0],
        "palette": palette,
        "algorithm": algo,
        "processing_time_ms": elapsed
    }

@app.post("/api/export-lut")
def export_lut(
    reference_file: Optional[UploadFile] = File(None),
    reference_url: Optional[str] = Form(None),
    algorithm: str = Form("reinhard"),
    strength: float = Form(1.0),
    preserve_luminance: bool = Form(False),
    saturation: float = Form(0.0),
    temperature: float = Form(0.0),
    contrast: float = Form(0.0),
    brightness: float = Form(0.0),
    vignette: float = Form(0.0),
    lut_size: int = Form(33)
):
    algo = _to_str(algorithm, "reinhard")
    str_val = _to_float(strength, 1.0)
    pres_lum = _to_bool(preserve_luminance, False)
    sat_val = _to_float(saturation, 0.0)
    temp_val = _to_float(temperature, 0.0)
    con_val = _to_float(contrast, 0.0)
    bri_val = _to_float(brightness, 0.0)
    vig_val = _to_float(vignette, 0.0)
    l_size = _to_int(lut_size, 33)

    reference_bytes = extract_bytes_from_input(reference_file, reference_url)
    if not reference_bytes or len(reference_bytes) == 0:
        raise HTTPException(status_code=400, detail="Reference image is required to generate 3D LUT")

    ref_bgr = read_image_from_bytes(reference_bytes)
    dummy_source = np.zeros_like(ref_bgr)

    cube_content = generate_cube_lut(
        source_bgr=dummy_source,
        reference_bgr=ref_bgr,
        algorithm=algo,
        strength=str_val,
        preserve_luminance=pres_lum,
        saturation=sat_val,
        temperature=temp_val,
        contrast=con_val,
        brightness=bri_val,
        vignette=vig_val,
        lut_size=l_size
    )

    filename = f"grade_{algo}_{l_size}x{l_size}.cube"
    return Response(
        content=cube_content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
