import unittest
from unittest.mock import patch

from app.memory_manager import MemoryManager


class MemoryManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = MemoryManager()
        self.inventory = {
            "model_root": "D:/models/hub",
            "disk_free_bytes": 100,
            "disk_free_gb": 90.0,
            "models": [
                {"id": "layerdiff_bf16", "label": "LayerDiff", "present": True, "path": "D:/models/layer", "size_bytes": 10, "size_gb": 0.0, "load_state": "on_disk"},
                {"id": "depth_bf16", "label": "Depth", "present": True, "path": "D:/models/depth", "size_bytes": 10, "size_gb": 0.0, "load_state": "on_disk"},
                {"id": "layerdiff_nf4", "label": "LayerDiff NF4", "present": False, "path": None, "size_bytes": 0, "size_gb": 0.0, "load_state": "missing"},
                {"id": "depth_nf4", "label": "Depth NF4", "present": False, "path": None, "size_bytes": 0, "size_gb": 0.0, "load_state": "missing"},
            ],
        }
        self.snapshot = {"ram": {"available": 10, "available_gb": 10}, "gpu": {"devices": []}, "model_disk": {"free_gb": 90}, "recommendation": {"action": "ready_for_test", "summary": "Ready"}}

    def test_blockswap_plan_is_planning_only(self):
        with patch.object(self.manager, "model_inventory", return_value=self.inventory), patch.object(self.manager, "snapshot", return_value=self.snapshot):
            plan = self.manager.placement_plan(mode="blockswap")
        self.assertTrue(plan["planning_only"])
        self.assertFalse(plan["streaming_enabled"])
        self.assertTrue(plan["ready_to_run"])
        self.assertEqual(plan["recommended_mode"], "blockswap")

    def test_quantized_plan_reports_missing_models(self):
        with patch.object(self.manager, "model_inventory", return_value=self.inventory), patch.object(self.manager, "snapshot", return_value=self.snapshot):
            plan = self.manager.placement_plan(mode="quantized")
        self.assertFalse(plan["ready_to_run"])
        self.assertEqual(len(plan["missing_models"]), 2)
        self.assertFalse(plan["streaming_enabled"])


if __name__ == "__main__":
    unittest.main()
