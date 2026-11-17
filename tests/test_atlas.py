"""Regression cases for scope, evidence integrity, routing and freshness."""
import copy
import datetime as dt
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from atlas_core import Catalogue
from atlas_generate import generated_diff, render
from atlas import expand_nav, freshness, inspect_remote, review_notice
from atlas_core import read_yaml


class AtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = Catalogue(ROOT)

    def setUp(self):
        self.catalogue = copy.deepcopy(self.original)

    def test_canonical_corpus_validates(self):
        self.assertEqual(self.catalogue.validate(), [])

    def test_cross_model_evidence_rejected(self):
        cap = self.catalogue.records["capability.om5-ii-alpha12-overall"]
        cap["evidence_refs"] = ["evidence.om5-prealpha1-boot"]
        self.assertTrue(any("different camera_id" in e for e in self.catalogue.validate()))

    def test_cross_package_evidence_rejected(self):
        self.catalogue.records["capability.om5-ii-alpha12-overall"]["mod_build"] = "v0.1.0-alpha13"
        self.assertTrue(any("different mod_build" in e for e in self.catalogue.validate()))

    def test_firmware_cannot_change_camera(self):
        self.catalogue.records["evidence.om5-prealpha1-boot"]["firmware_id"] = "firmware.om5-ii-1100"
        self.assertTrue(any("belongs to camera.om5-ii" in e for e in self.catalogue.validate()))

    def test_expected_hash_does_not_complete_report(self):
        row = self.catalogue.records["evidence.om5-ii-alpha12-owner"]
        row["quality"] = "complete"
        errors = self.catalogue.validate()
        self.assertTrue(any("requires package_sha256" in e for e in errors))
        self.assertTrue(any("requires procedure" in e for e in errors))

    def test_label_only_cannot_claim_installed_digest(self):
        row = self.catalogue.records["evidence.om5-ii-alpha12-owner"]
        row["package_sha256"] = row["expected_package_sha256"]
        self.assertTrue(any("label-only" in e for e in self.catalogue.validate()))

    def test_synthetic_complete_report_is_accepted(self):
        row = self.catalogue.records["evidence.om5-ii-alpha12-owner"]
        row.update(quality="complete", identity_level="reported-hash", package_sha256="a" * 64, tested_on="2026-11-16",
                   procedure="Synthetic fixture: identify input, install, exercise the stated behaviour and record result.")
        self.assertEqual(self.catalogue.validate(), [])

    def test_posting_date_does_not_fill_unknown_test_date(self):
        row = self.catalogue.records["evidence.om5-prealpha1-boot"]
        self.assertIsNone(row["tested_on"])
        row["quality"] = "complete"
        self.assertTrue(any("requires tested_on" in e for e in self.catalogue.validate()))

    def test_missing_emulator_profile_rejected(self):
        del self.catalogue.records["evidence.om5-ii-image-store-probe"]["emulator"]
        self.assertTrue(any("emulator evidence needs" in e for e in self.catalogue.validate()))

    def test_dependency_cycles_rejected(self):
        row = self.catalogue.articles["guide.platform.identity"]
        row["depends_on"] = [row["id"]]
        self.assertTrue(any("dependency cycle" in e for e in self.catalogue.validate()))

    def test_deep_dependency_chain_rejected(self):
        base = self.catalogue.articles["guide.platform.identity"]
        for i in range(4):
            node = copy.deepcopy(base)
            node["id"] = f"guide.test.{i}"
            node["depends_on"] = [f"guide.test.{i+1}"] if i < 3 else []
            self.catalogue.articles[node["id"]] = node
        self.assertTrue(any("exceeds three guides" in e for e in self.catalogue.validate()))

    def test_ambiguous_family_requires_exact_model(self):
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            self.catalogue.resolve_camera("OM5")
        self.assertEqual(self.catalogue.resolve_camera("camera.om5"), "camera.om5")
        self.assertEqual(self.catalogue.resolve_camera("E148"), "camera.om5-ii")

    def test_look_task_does_not_load_tools(self):
        plan = self.catalogue.reading_plan("research", camera="om5-ii", topic="interfaces")
        self.assertIn("knowledge/interfaces/looks.md", plan)
        self.assertNotIn("knowledge/tooling/analysis.md", plan)
        self.assertEqual(len(plan), len(set(plan)))

    def test_required_base_precedes_tool_profile(self):
        plan = self.catalogue.reading_plan("research", camera="ep7", topic="tooling")
        self.assertLess(plan.index("knowledge/platform/identity.md"), plan.index("knowledge/tooling/analysis.md"))

    def test_release_url_routes_to_sparse_repo(self):
        plan = self.catalogue.reading_plan("ingest", source="https://github.com/azqeurio/om-c-firmware/releases/tag/dbv0.4.1")
        self.assertIn("agents/routes/projects/db-firmware.md", plan)

    def test_generated_human_report_retains_missing_identity(self):
        output = render(self.catalogue)["views/evidence/om5-ii-alpha12-owner.md"]
        self.assertIn("Reported/observed package SHA-256:** not recorded", output)
        self.assertIn("Expected manifest SHA-256:", output)
        self.assertIn("partial report", output)

    def test_generated_drift_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "views").mkdir()
            (root / "views/test.md").write_text("manual edit", encoding="utf-8")
            self.assertIn("views/test.md", generated_diff(root, {"views/test.md": "canonical output"}))

    def test_network_failure_preserves_canonical_sources(self):
        before = copy.deepcopy(self.catalogue.records)

        def unavailable(*args, **kwargs):
            raise urllib.error.URLError("synthetic offline fixture")

        report = freshness(self.catalogue, fetch=True, today=dt.date(2026, 11, 18), fetcher=unavailable)
        self.assertTrue(all(row["state"] == "check-failed" for row in report["sources"]))
        self.assertEqual(before, self.catalogue.records)

    def test_repo_advance_is_not_claim_promotion(self):
        source = self.catalogue.records["source.om5.readme"]
        result = inspect_remote(source, lambda *args, **kwargs: [{"sha": "f" * 40}])
        self.assertEqual(result["state"], "upstream-advanced")
        self.assertEqual(source["last_reviewed"], "2026-11-17")

    def test_source_schema_rejects_unknown_fields(self):
        schema = json.loads((ROOT / "schemas/records.schema.json").read_text())
        selected = {"$ref": "#/$defs/source", "$defs": schema["$defs"]}
        row = copy.deepcopy(self.catalogue.records["source.om5.readme"])
        row["verified_safe"] = True
        self.assertTrue(Catalogue.schema_errors(selected, row, "synthetic source"))

    def test_publication_age_does_not_renew_sources(self):
        row = self.catalogue.records["camera.om5-ii"]
        notice = review_notice(self.catalogue, row, dt.date(2027, 1, 1))
        self.assertIn("Source review due", notice)
        self.assertEqual(self.catalogue.records["source.om5.readme"]["last_checked"], "2026-11-17")

    def test_community_directory_has_direct_venue_links(self):
        output = render(self.catalogue)["views/community/index.md"]
        self.assertIn("https://discord.gg/fKpcKGsNPY", output)
        self.assertIn("https://www.reddit.com/r/M43/", output)

    def test_navigation_lists_every_camera_and_guide(self):
        nav = expand_nav(read_yaml(ROOT / "mkdocs.yml")["nav"], self.catalogue)
        paths = []

        def walk(entries):
            for entry in entries:
                for value in entry.values():
                    walk(value) if isinstance(value, list) else paths.append(value)

        walk(nav)
        for row in self.catalogue.of_type("camera"):
            self.assertIn(f"views/cameras/{row['id'].split('.', 1)[1]}.md", paths)
        for article in self.catalogue.articles.values():
            self.assertIn(article["path"], paths)
        self.assertNotIn("knowledge/README.md", paths)

    def test_camera_page_leads_with_projects_and_support(self):
        output = render(self.catalogue)["views/cameras/om5-ii.md"]
        project = self.catalogue.records["project.caduceus-om5"]
        self.assertLess(output.index("## Projects for this camera"), output.index("## Features and observations"))
        self.assertIn(f"[Ask or report issues]({project['contribution_home']})", output)
        self.assertIn("partial report", output)


if __name__ == "__main__":
    unittest.main()
