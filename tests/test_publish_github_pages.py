from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "publish_github_pages.py"


def load_module():
    spec = importlib.util.spec_from_file_location("publish_github_pages", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


publisher = load_module()


class GitHubPagesPublisherTests(unittest.TestCase):
    def test_generated_files_keep_versioned_immutable_path(self):
        generated = publisher.generated_files(
            version_key="abc123",
            payload_digest="f" * 64,
            file_count=3,
            producer="test-producer",
        )
        self.assertIn(".nojekyll", generated)
        self.assertIn("index.html", generated)
        self.assertIn("latest.json", generated)
        marker = json.loads(
            generated["play/abc123/_game_exp_build.json"].decode("utf-8")
        )
        self.assertEqual(marker["version_key"], "abc123")
        self.assertEqual(marker["path"], "play/abc123/")
        self.assertEqual(marker["payload_sha256"], "f" * 64)
        self.assertIn(b"./play/abc123/", generated["index.html"])

    def test_payload_hash_is_deterministic_and_content_sensitive(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "index.html").write_text("<html>ok</html>", encoding="utf-8")
            (root / "assets").mkdir()
            asset = root / "assets" / "a.txt"
            asset.write_text("one", encoding="utf-8")
            first = publisher.payload_sha256(publisher.collect_payload(root))
            second = publisher.payload_sha256(publisher.collect_payload(root))
            self.assertEqual(first, second)
            asset.write_text("two", encoding="utf-8")
            third = publisher.payload_sha256(publisher.collect_payload(root))
            self.assertNotEqual(first, third)

    def test_relative_entrypoint_rejects_root_absolute_asset_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            index = root / "index.html"
            index.write_text(
                '<script type="module" src="/assets/app.js"></script>',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                publisher.PublishError,
                "root-absolute",
            ):
                publisher.validate_relative_entrypoint(index)
            index.write_text(
                '<script type="module" src="./assets/app.js"></script>',
                encoding="utf-8",
            )
            publisher.validate_relative_entrypoint(index)

    def test_version_url_preserves_project_site_prefix(self):
        self.assertEqual(
            publisher.version_url(
                "https://alice.github.io/demo/",
                "deadbeef",
            ),
            "https://alice.github.io/demo/play/deadbeef/",
        )

    def test_same_version_and_payload_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "index.html").write_text("<html>ok</html>", encoding="utf-8")
            digest = publisher.payload_sha256(publisher.collect_payload(root))
            with (
                patch.object(publisher, "gh_api", return_value={"private": False}),
                patch.object(
                    publisher,
                    "_branch_state",
                    return_value=("a" * 40, "b" * 40),
                ),
                patch.object(
                    publisher,
                    "existing_marker",
                    return_value={"payload_sha256": digest},
                ),
                patch.object(
                    publisher,
                    "ensure_pages",
                    return_value={"html_url": "https://alice.github.io/demo/"},
                ),
                patch.object(publisher, "verify_deployment") as verify,
                patch.object(publisher, "_blob") as blob,
            ):
                result = publisher.publish(
                    repo="alice/demo",
                    source=root,
                    version_key="abc123",
                    producer="test",
                )
            self.assertTrue(result["idempotent"])
            self.assertTrue(result["deployment_verified"])
            blob.assert_not_called()
            verify.assert_called_once()

    def test_existing_version_key_never_overwrites_different_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "index.html").write_text("<html>new</html>", encoding="utf-8")
            with (
                patch.object(publisher, "gh_api", return_value={"private": False}),
                patch.object(
                    publisher,
                    "_branch_state",
                    return_value=("a" * 40, "b" * 40),
                ),
                patch.object(
                    publisher,
                    "existing_marker",
                    return_value={"payload_sha256": "0" * 64},
                ),
            ):
                with self.assertRaisesRegex(
                    publisher.PublishError,
                    "different payload",
                ):
                    publisher.publish(
                        repo="alice/demo",
                        source=root,
                        version_key="abc123",
                        producer="test",
                    )


if __name__ == "__main__":
    unittest.main()
