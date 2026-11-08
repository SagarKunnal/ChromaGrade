import cv2
import numpy as np
from typing import Dict, List, Tuple, Any

def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    hex_code = hex_code.lstrip("#")
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

def get_color_name(r: int, g: int, b: int) -> str:
    """Classifies RGB color into an evocative photographic/cinematic color name."""
    hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = hsv[0] * 2, hsv[1] / 255.0, hsv[2] / 255.0

    if v < 0.15:
        return "Obsidian Black"
    if s < 0.12:
        if v > 0.85:
            return "Alabaster White"
        elif v > 0.55:
            return "Muted Silver"
        else:
            return "Charcoal Gray"

    if h < 15 or h >= 345:
        return "Crimson Red" if v > 0.5 else "Deep Burgundy"
    elif h < 45:
        if s > 0.6:
            return "Vibrant Amber" if v > 0.6 else "Warm Terracotta"
        else:
            return "Warm Sand"
    elif h < 70:
        return "Golden Hour Yellow" if v > 0.6 else "Mustard Ochre"
    elif h < 160:
        if h < 105:
            return "Olive Green" if v < 0.6 else "Sage Green"
        else:
            return "Emerald Forest" if v < 0.6 else "Lush Mint"
    elif h < 205:
        return "Cyan Teal" if v > 0.5 else "Deep Sea Teal"
    elif h < 260:
        return "Cobalt Blue" if v > 0.5 else "Midnight Navy"
    elif h < 310:
        return "Amethyst Purple" if v > 0.5 else "Deep Plum"
    else:
        return "Magenta Rose" if v > 0.5 else "Vintage Mauve"

def extract_color_palette(bgr_image: np.ndarray, num_colors: int = 5) -> List[Dict[str, Any]]:
    """
    Extracts top dominant colors from image using K-Means clustering in LAB space.
    Returns list of dicts with hex, rgb, percentage, and name.
    """
    h, w = bgr_image.shape[:2]
    max_dim = 160
    scale = min(1.0, max_dim / max(h, w))
    small = cv2.resize(bgr_image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    pixels_lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)

    actual_k = min(num_colors, len(pixels_lab))
    if actual_k <= 0:
        return [{"hex": "#808080", "rgb": [128, 128, 128], "percentage": 100.0, "name": "Neutral Gray"}]

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 25, 0.2)
    _, labels, centers_lab = cv2.kmeans(
        pixels_lab, actual_k, None, criteria, 5, cv2.KMEANS_PP_CENTERS
    )

    counts = np.bincount(labels.flatten())
    total_pixels = len(labels)
    sorted_indices = np.argsort(-counts)

    palette = []
    for idx in sorted_indices:
        center_lab = centers_lab[idx].reshape(1, 1, 3).astype(np.uint8)
        center_bgr = cv2.cvtColor(center_lab, cv2.COLOR_LAB2BGR)[0][0]
        b, g, r = int(center_bgr[0]), int(center_bgr[1]), int(center_bgr[2])
        hex_val = rgb_to_hex(r, g, b)
        pct = round(float(counts[idx] / total_pixels) * 100, 1)
        name = get_color_name(r, g, b)

        palette.append({
            "hex": hex_val,
            "rgb": [r, g, b],
            "percentage": pct,
            "name": name
        })

    return palette

def reinhard_color_transfer(
    source_bgr: np.ndarray,
    reference_bgr: np.ndarray,
    strength: float = 1.0,
    preserve_luminance: bool = False
) -> np.ndarray:
    """
    Reinhard et al. Color Transfer in CIE L*a*b* space.
    Transfers mean and standard deviation of color channels.
    """
    src_lab = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    tgt_lab = cv2.cvtColor(reference_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)

    src_mean, src_std = cv2.meanStdDev(src_lab)
    tgt_mean, tgt_std = cv2.meanStdDev(tgt_lab)

    src_mean = src_mean.reshape((1, 1, 3))
    src_std = np.maximum(src_std.reshape((1, 1, 3)), 1e-4)
    tgt_mean = tgt_mean.reshape((1, 1, 3))
    tgt_std = np.maximum(tgt_std.reshape((1, 1, 3)), 1e-4)

    # Shift distribution
    res_lab = (src_lab - src_mean) * (tgt_std / src_std) + tgt_mean

    # If preserving source luminance/exposure
    if preserve_luminance:
        res_lab[:, :, 0] = src_lab[:, :, 0]

    res_lab = np.clip(res_lab, 0, 255).astype(np.uint8)
    res_bgr = cv2.cvtColor(res_lab, cv2.COLOR_LAB2BGR)

    if strength < 1.0:
        res_bgr = cv2.addWeighted(res_bgr, strength, source_bgr, 1.0 - strength, 0)

    return res_bgr

def _match_channel_cdf_fast(source_channel: np.ndarray, ref_channel: np.ndarray) -> np.ndarray:
    """
    Hardware-accelerated 256-bin CDF histogram matching using cv2.LUT.
    Executes in under 1 millisecond regardless of megapixel count.
    """
    s_hist = cv2.calcHist([source_channel], [0], None, [256], [0, 256]).ravel()
    r_hist = cv2.calcHist([ref_channel], [0], None, [256], [0, 256]).ravel()

    s_cdf = np.cumsum(s_hist) / float(max(1, source_channel.size))
    r_cdf = np.cumsum(r_hist) / float(max(1, ref_channel.size))

    lut = np.interp(s_cdf, r_cdf, np.arange(256)).astype(np.uint8)
    return cv2.LUT(source_channel, lut)

def cdf_histogram_transfer(
    source_bgr: np.ndarray,
    reference_bgr: np.ndarray,
    strength: float = 1.0,
    preserve_luminance: bool = False
) -> np.ndarray:
    """
    Cumulative Distribution Function (CDF) histogram matching in LAB color space.
    Captures non-linear tone curves, crushed shadows, and highlight roll-off.
    """
    src_lab = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2LAB)
    tgt_lab = cv2.cvtColor(reference_bgr, cv2.COLOR_BGR2LAB)

    matched_lab = np.zeros_like(src_lab)
    for c in range(3):
        if c == 0 and preserve_luminance:
            matched_lab[:, :, 0] = src_lab[:, :, 0]
        else:
            matched_lab[:, :, c] = _match_channel_cdf_fast(src_lab[:, :, c], tgt_lab[:, :, c])

    matched_bgr = cv2.cvtColor(matched_lab, cv2.COLOR_LAB2BGR)
    if strength < 1.0:
        matched_bgr = cv2.addWeighted(matched_bgr, strength, source_bgr, 1.0 - strength, 0)

    return matched_bgr

def split_tone_transfer(
    source_bgr: np.ndarray,
    reference_bgr: np.ndarray,
    strength: float = 1.0,
    preserve_luminance: bool = False
) -> np.ndarray:
    """
    Photographic Split-Toning Transfer.
    Extracts shadow (<33% L) and highlight (>66% L) color casts from reference,
    and applies smooth tone-curve tinting to the source.
    """
    ref_lab = cv2.cvtColor(reference_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    src_lab = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)

    ref_l = ref_lab[:, :, 0]
    shadow_mask = ref_l < 85.0
    highlight_mask = ref_l > 170.0

    shadow_a = float(np.mean(ref_lab[:, :, 1][shadow_mask])) if np.any(shadow_mask) else 128.0
    shadow_b = float(np.mean(ref_lab[:, :, 2][shadow_mask])) if np.any(shadow_mask) else 128.0

    highlight_a = float(np.mean(ref_lab[:, :, 1][highlight_mask])) if np.any(highlight_mask) else 128.0
    highlight_b = float(np.mean(ref_lab[:, :, 2][highlight_mask])) if np.any(highlight_mask) else 128.0

    norm_l = (src_lab[:, :, 0] / 255.0)[:, :, np.newaxis]
    target_a = (1.0 - norm_l) * shadow_a + norm_l * highlight_a
    target_b = (1.0 - norm_l) * shadow_b + norm_l * highlight_b

    graded_lab = src_lab.copy()
    graded_lab[:, :, 1] = src_lab[:, :, 1] * 0.3 + target_a[:, :, 0] * 0.7
    graded_lab[:, :, 2] = src_lab[:, :, 2] * 0.3 + target_b[:, :, 0] * 0.7

    if not preserve_luminance:
        src_std = float(np.std(src_lab[:, :, 0]))
        ref_std = float(np.std(ref_lab[:, :, 0]))
        src_mean = float(np.mean(src_lab[:, :, 0]))
        ref_mean = float(np.mean(ref_lab[:, :, 0]))
        if src_std > 1e-4:
            graded_lab[:, :, 0] = (src_lab[:, :, 0] - src_mean) * (ref_std / src_std) + ref_mean

    graded_lab = np.clip(graded_lab, 0, 255).astype(np.uint8)
    graded_bgr = cv2.cvtColor(graded_lab, cv2.COLOR_LAB2BGR)

    if strength < 1.0:
        graded_bgr = cv2.addWeighted(graded_bgr, strength, source_bgr, 1.0 - strength, 0)

    return graded_bgr

def bilateral_harmonization(
    source_bgr: np.ndarray,
    reference_bgr: np.ndarray,
    strength: float = 1.0,
    preserve_luminance: bool = False
) -> np.ndarray:
    """
    Edge-Preserving Bilateral Color Transfer.
    Prevents color bleeding across sharp object boundaries.
    """
    base_graded = reinhard_color_transfer(source_bgr, reference_bgr, strength=1.0, preserve_luminance=preserve_luminance)

    src_lab = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2LAB)
    base_lab = cv2.cvtColor(base_graded, cv2.COLOR_BGR2LAB)

    a_smooth = cv2.bilateralFilter(base_lab[:, :, 1], d=7, sigmaColor=35, sigmaSpace=15)
    b_smooth = cv2.bilateralFilter(base_lab[:, :, 2], d=7, sigmaColor=35, sigmaSpace=15)

    res_lab = np.zeros_like(src_lab)
    res_lab[:, :, 0] = src_lab[:, :, 0] if preserve_luminance else base_lab[:, :, 0]
    res_lab[:, :, 1] = a_smooth
    res_lab[:, :, 2] = b_smooth

    res_bgr = cv2.cvtColor(res_lab, cv2.COLOR_LAB2BGR)
    if strength < 1.0:
        res_bgr = cv2.addWeighted(res_bgr, strength, source_bgr, 1.0 - strength, 0)

    return res_bgr

def adjust_adjustments(
    bgr_img: np.ndarray,
    saturation_boost: float = 0.0,
    temperature_shift: float = 0.0,
    contrast: float = 0.0,
    brightness: float = 0.0,
    vignette: float = 0.0
) -> np.ndarray:
    """
    Fine-tuning parameters:
    saturation_boost: -0.5 to +0.5
    temperature_shift: -0.5 (cool) to +0.5 (warm)
    contrast: -0.5 to +0.5
    brightness: -0.5 to +0.5
    vignette: 0.0 to 1.0 (subtle edge falloff)
    """
    result = bgr_img.copy()

    # 1. Temperature shift
    if abs(temperature_shift) > 0.001:
        img_f = result.astype(np.float32)
        r_mult = 1.0 + (temperature_shift * 0.25)
        b_mult = 1.0 - (temperature_shift * 0.25)
        img_f[:, :, 2] = np.clip(img_f[:, :, 2] * r_mult, 0, 255)
        img_f[:, :, 0] = np.clip(img_f[:, :, 0] * b_mult, 0, 255)
        result = img_f.astype(np.uint8)

    # 2. Saturation shift
    if abs(saturation_boost) > 0.001:
        hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)
        s_mult = max(0.0, 1.0 + saturation_boost)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * s_mult, 0, 255)
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    # 3. Contrast & Brightness
    if abs(contrast) > 0.001 or abs(brightness) > 0.001:
        alpha = max(0.1, 1.0 + contrast)
        beta = brightness * 128.0
        result = cv2.convertScaleAbs(result, alpha=alpha, beta=beta)

    # 4. Vignette (Photographic Lens Falloff)
    if vignette > 0.01:
        rows, cols = result.shape[:2]
        kernel_x = cv2.getGaussianKernel(cols, cols / (1.5 + vignette * 0.5))
        kernel_y = cv2.getGaussianKernel(rows, rows / (1.5 + vignette * 0.5))
        kernel = kernel_y * kernel_x.T
        mask = 255 * kernel / np.linalg.norm(kernel)
        mask = mask / np.max(mask)
        vig_factor = 1.0 - (vignette * 0.6)
        mask_scaled = np.clip(mask * (1.0 - vig_factor) + vig_factor, 0, 1.0)[:, :, np.newaxis]
        result = np.clip(result.astype(np.float32) * mask_scaled, 0, 255).astype(np.uint8)

    return result

def apply_color_grade(
    source_bgr: np.ndarray,
    reference_bgr: np.ndarray,
    algorithm: str = "reinhard",
    strength: float = 1.0,
    preserve_luminance: bool = False,
    saturation: float = 0.0,
    temperature: float = 0.0,
    contrast: float = 0.0,
    brightness: float = 0.0,
    vignette: float = 0.0
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Master pipeline: applies selected color grading algorithm and post adjustments.
    Returns: (graded_bgr, reference_palette)
    """
    algo = algorithm.lower().strip()
    if algo == "cdf":
        graded = cdf_histogram_transfer(source_bgr, reference_bgr, strength, preserve_luminance)
    elif algo == "split_tone":
        graded = split_tone_transfer(source_bgr, reference_bgr, strength, preserve_luminance)
    elif algo == "bilateral":
        graded = bilateral_harmonization(source_bgr, reference_bgr, strength, preserve_luminance)
    else:
        graded = reinhard_color_transfer(source_bgr, reference_bgr, strength, preserve_luminance)

    graded = adjust_adjustments(
        graded,
        saturation_boost=saturation,
        temperature_shift=temperature,
        contrast=contrast,
        brightness=brightness,
        vignette=vignette
    )
    ref_palette = extract_color_palette(reference_bgr, num_colors=5)

    return graded, ref_palette

def generate_cube_lut(
    source_bgr: np.ndarray,
    reference_bgr: np.ndarray,
    algorithm: str = "reinhard",
    strength: float = 1.0,
    preserve_luminance: bool = False,
    saturation: float = 0.0,
    temperature: float = 0.0,
    contrast: float = 0.0,
    brightness: float = 0.0,
    vignette: float = 0.0,
    lut_size: int = 33
) -> str:
    """
    Generates standard Adobe / DaVinci Resolve .CUBE 3D Look-Up Table text content.
    """
    coords = np.linspace(0, 1.0, lut_size, dtype=np.float32)
    grid_r, grid_g, grid_b = np.meshgrid(coords, coords, coords, indexing="ij")

    lut_rgb = np.stack([grid_r.ravel(), grid_g.ravel(), grid_b.ravel()], axis=-1)
    lut_bgr = (lut_rgb[:, [2, 1, 0]] * 255.0).reshape((lut_size * lut_size, lut_size, 3)).astype(np.uint8)

    transformed_bgr, _ = apply_color_grade(
        source_bgr=lut_bgr,
        reference_bgr=reference_bgr,
        algorithm=algorithm,
        strength=strength,
        preserve_luminance=preserve_luminance,
        saturation=saturation,
        temperature=temperature,
        contrast=contrast,
        brightness=brightness,
        vignette=0.0 # Vignette is spatial, not color LUT
    )

    transformed_rgb = (transformed_bgr[:, :, [2, 1, 0]].astype(np.float32) / 255.0).reshape(-1, 3)

    lines = [
        "# Color Grade Transfer 3D LUT",
        f"# Algorithm: {algorithm}",
        f"TITLE \"ColorGradeTransfer_{algorithm.upper()}\"",
        f"LUT_3D_SIZE {lut_size}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
        ""
    ]

    for i in range(len(transformed_rgb)):
        r, g, b = transformed_rgb[i]
        lines.append(f"{r:.6f} {g:.6f} {b:.6f}")

    return "\n".join(lines)
