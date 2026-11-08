import os
import sys
import unittest
import numpy as np
import cv2

# Add parent dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.algorithms import (
    reinhard_color_transfer,
    cdf_histogram_transfer,
    split_tone_transfer,
    bilateral_harmonization,
    extract_color_palette,
    generate_cube_lut,
    apply_color_grade,
    adjust_adjustments
)

class TestColorTransferCore(unittest.TestCase):
    def setUp(self):
        # Create deterministic synthetic test images
        np.random.seed(42)
        # Source: neutral portrait tones (64x64 BGR)
        self.source = np.full((64, 64, 3), [180, 160, 140], dtype=np.uint8)
        # Reference: warm golden hour tones (64x64 BGR)
        self.reference = np.full((64, 64, 3), [50, 140, 240], dtype=np.uint8)

    def test_reinhard_transfer(self):
        result = reinhard_color_transfer(self.source, self.reference, strength=1.0)
        self.assertEqual(result.shape, self.source.shape)
        self.assertEqual(result.dtype, np.uint8)
        # Shift towards reference red/warmth
        self.assertGreater(result[32, 32, 2], self.source[32, 32, 2])

    def test_cdf_transfer(self):
        result = cdf_histogram_transfer(self.source, self.reference, strength=1.0)
        self.assertEqual(result.shape, self.source.shape)
        self.assertEqual(result.dtype, np.uint8)

    def test_split_tone_transfer(self):
        result = split_tone_transfer(self.source, self.reference, strength=1.0)
        self.assertEqual(result.shape, self.source.shape)
        self.assertEqual(result.dtype, np.uint8)

    def test_bilateral_harmonization(self):
        result = bilateral_harmonization(self.source, self.reference, strength=0.8)
        self.assertEqual(result.shape, self.source.shape)
        self.assertEqual(result.dtype, np.uint8)

    def test_palette_extraction(self):
        palette = extract_color_palette(self.reference, num_colors=3)
        self.assertEqual(len(palette), 3)
        for item in palette:
            self.assertTrue(item["hex"].startswith("#"))
            self.assertEqual(len(item["hex"]), 7)
            self.assertIn("name", item)
            self.assertIn("percentage", item)

    def test_cube_lut_generation(self):
        cube = generate_cube_lut(self.source, self.reference, algorithm="reinhard", lut_size=17)
        self.assertIn("LUT_3D_SIZE 17", cube)
        self.assertIn("DOMAIN_MIN 0.0 0.0 0.0", cube)
        lines = [line.strip() for line in cube.splitlines() if line.strip() and not line.startswith("#")]
        # Header has TITLE, LUT_3D_SIZE, DOMAIN_MIN, DOMAIN_MAX (4 lines), then 17^3 = 4913 data lines
        self.assertGreaterEqual(len(lines), 4913)

    def test_master_pipeline_with_adjustments(self):
        graded, palette = apply_color_grade(
            source_bgr=self.source,
            reference_bgr=self.reference,
            algorithm="reinhard",
            strength=0.9,
            preserve_luminance=True,
            saturation=0.1,
            temperature=0.1,
            contrast=0.15,
            brightness=0.05,
            vignette=0.3
        )
        self.assertEqual(graded.shape, self.source.shape)
        self.assertGreaterEqual(len(palette), 1)

    def test_adjust_adjustments(self):
        adjusted = adjust_adjustments(
            self.source,
            saturation_boost=0.2,
            temperature_shift=0.1,
            contrast=0.1,
            brightness=0.05,
            vignette=0.4
        )
        self.assertEqual(adjusted.shape, self.source.shape)
        self.assertEqual(adjusted.dtype, np.uint8)

if __name__ == "__main__":
    unittest.main()
