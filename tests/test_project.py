import unittest
from pathlib import Path

from app.main import APP_VERSION, app, health
from app.psd_export import _safe
from scripts.download_models import BASE_MODELS, NF4_MODELS

ROOT = Path(__file__).resolve().parents[1]


class ProjectTests(unittest.TestCase):
    def test_health_reports_project_version(self):
        result = health()
        self.assertTrue(result["ok"])
        self.assertEqual(result["version"], APP_VERSION)
        self.assertEqual(APP_VERSION, "0.4.7")

    def test_layer_export_routes_exist(self):
        paths = {route.path for route in app.routes}
        self.assertIn("/api/jobs/{jid}/inspect", paths)
        self.assertIn("/api/jobs/{jid}/layer/{layer_id}/preview", paths)
        self.assertIn("/api/jobs/{jid}/export_zip", paths)

    def test_export_name_is_filesystem_safe(self):
        self.assertEqual(_safe("hair/front: left"), "hair_front__left")
        self.assertEqual(_safe(""), "layer")

    def test_root_one_click_files_and_license_exist(self):
        for filename in (
            "LICENSE",
            "INSTALL_ANIME_LAYER_STUDIO.bat",
            "DOWNLOAD_MODELS.bat",
            "RUN_ANIME_LAYER_STUDIO.bat",
        ):
            with self.subTest(filename=filename):
                self.assertTrue((ROOT / filename).is_file())

    def test_model_downloader_targets_default_and_optional_models(self):
        self.assertEqual(len(BASE_MODELS), 2)
        self.assertEqual(len(NF4_MODELS), 2)
        self.assertIn("seethroughv0.0.2_layerdiff3d", [dest for _, dest in BASE_MODELS])
        self.assertIn("seethroughv0.0.2_layerdiff3d_nf4", [dest for _, dest in NF4_MODELS])


if __name__ == "__main__":
    unittest.main()
