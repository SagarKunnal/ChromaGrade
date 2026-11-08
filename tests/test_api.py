import os
import sys
import unittest
import io
from PIL import Image
from fastapi import UploadFile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import (
    health_check,
    get_sample_images,
    get_presets,
    transfer_color_grade,
    export_lut
)

def create_synthetic_image_bytes(mode="RGB", size=(128, 128), color=(200, 100, 50), fmt="JPEG"):
    img = Image.new(mode, size, color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()

class TestColorGradeAPISync(unittest.TestCase):
    def test_health_check(self):
        res = health_check()
        self.assertEqual(res["status"], "online")
        self.assertIn("engines", res)
        self.assertEqual(len(res["engines"]), 4)

    def test_sample_images(self):
        res = get_sample_images()
        self.assertEqual(len(res["inputs"]), 3)
        self.assertEqual(len(res["references"]), 3)

    def test_presets(self):
        res = get_presets()
        self.assertEqual(len(res["presets"]), 6)
        preset_ids = [p["id"] for p in res["presets"]]
        self.assertIn("portra400", preset_ids)
        self.assertIn("velvia50", preset_ids)
        self.assertIn("cyberpunk", preset_ids)

    def test_transfer_with_sample_urls(self):
        res = transfer_color_grade(
            source_url="/static/demo/color_input1.jpg",
            reference_url="/static/demo/color_reference_1.jpg",
            algorithm="reinhard",
            strength=0.85,
            contrast=0.1,
            brightness=-0.05,
            vignette=0.2
        )
        self.assertTrue(res["success"])
        self.assertTrue(res["image_data"].startswith("data:image/jpeg;base64,"))
        self.assertNotIn("ai_analysis", res)

    def test_transfer_user_files(self):
        src_bytes = create_synthetic_image_bytes("RGB", (120, 120), (180, 160, 140), "JPEG")
        ref_bytes = create_synthetic_image_bytes("RGB", (120, 120), (50, 120, 240), "JPEG")

        src_upload = UploadFile(file=io.BytesIO(src_bytes), filename="source.jpg")
        ref_upload = UploadFile(file=io.BytesIO(ref_bytes), filename="ref.jpg")

        res = transfer_color_grade(
            source_file=src_upload,
            reference_file=ref_upload,
            algorithm="cdf",
            strength=1.0,
            saturation=0.1,
            temperature=0.15
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["width"], 120)
        self.assertEqual(res["height"], 120)
        self.assertGreater(len(res["palette"]), 0)

    def test_transfer_rgba_png(self):
        src_bytes = create_synthetic_image_bytes("RGBA", (100, 100), (220, 180, 140, 255), "PNG")
        ref_bytes = create_synthetic_image_bytes("RGB", (100, 100), (30, 80, 160), "JPEG")

        src_upload = UploadFile(file=io.BytesIO(src_bytes), filename="alpha.png")
        ref_upload = UploadFile(file=io.BytesIO(ref_bytes), filename="ref.jpg")

        res = transfer_color_grade(
            source_file=src_upload,
            reference_file=ref_upload,
            algorithm="split_tone"
        )
        self.assertTrue(res["success"])

    def test_transfer_grayscale(self):
        src_bytes = create_synthetic_image_bytes("L", (100, 100), 120, "JPEG")
        ref_bytes = create_synthetic_image_bytes("RGB", (100, 100), (200, 140, 60), "JPEG")

        src_upload = UploadFile(file=io.BytesIO(src_bytes), filename="gray.jpg")
        ref_upload = UploadFile(file=io.BytesIO(ref_bytes), filename="ref.jpg")

        res = transfer_color_grade(
            source_file=src_upload,
            reference_file=ref_upload,
            algorithm="reinhard"
        )
        self.assertTrue(res["success"])

    def test_export_lut(self):
        ref_bytes = create_synthetic_image_bytes("RGB", (64, 64), (220, 120, 40), "JPEG")
        ref_upload = UploadFile(file=io.BytesIO(ref_bytes), filename="grade.jpg")

        response = export_lut(
            reference_file=ref_upload,
            algorithm="reinhard",
            lut_size=17,
            contrast=0.1,
            saturation=0.2
        )
        content = response.body.decode("utf-8")
        self.assertIn("LUT_3D_SIZE 17", content)
        self.assertIn("TITLE \"ColorGradeTransfer_REINHARD\"", content)

if __name__ == "__main__":
    unittest.main()
