import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import core as gui


def tree_for(contents):
    return {"sha": "a" * 40, "truncated": False, "tree": [
        {"path": name, "type": "blob", "mode": "100644", "sha": gui.git_hash(value)}
        for name, value in contents.items()
    ]}


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="optimizernxt-test-")
        self.addCleanup(self.temp.cleanup)
        self.repo = gui.Repository(Path(self.temp.name))
        self.contents = {
            "yaml/one.yaml": b"jobs:\r\n  - name: one\r\n",
            "yaml/one.yaml.sig": b"DEAD\x01\x00signature-one",
            "yaml/two.yaml": b"jobs:\n  - name: two\n",
            "yaml/two.yaml.sig": b"DEAD\x01\x00signature-two",
        }
        self.tree = tree_for(self.contents)
        self.packages = self.repo.packages_from_tree(self.tree)

    def request_blob(self, url, **_kwargs):
        self.assertIn("/" + "a" * 40 + "/", url)
        return self.contents["yaml/" + url.rsplit("/", 1)[1]]

    def test_catalog_requires_regular_files_and_matching_signature(self):
        tree = tree_for({**self.contents, "yaml/unsigned.yaml": b"ignored",
                         "yaml/../escape.yaml": b"bad", "yaml/../escape.yaml.sig": b"bad"})
        tree["tree"].append({"type": "blob", "mode": "120000", "path": "yaml/link.yaml",
                             "sha": "b" * 40})
        packages = self.repo.packages_from_tree(tree)
        self.assertEqual([p["name"] for p in packages], ["one.yaml", "two.yaml"])
        tree["truncated"] = True
        with self.assertRaises(ValueError):
            self.repo.packages_from_tree(tree)

    def test_exact_bytes_and_new_run_contains_only_its_selection(self):
        with patch.object(self.repo, "request", side_effect=self.request_blob):
            first = self.repo.download_packages(self.packages)
            second = self.repo.download_packages([self.packages[1]])
        self.assertNotEqual(first, second)
        self.assertEqual(sorted(p.name for p in second.iterdir()),
                         ["selection.json", "two.yaml", "two.yaml.sig"])
        self.assertEqual((first / "one.yaml").read_bytes(), self.contents["yaml/one.yaml"])
        self.assertEqual((second / "two.yaml.sig").read_bytes(), self.contents["yaml/two.yaml.sig"])

    def test_mismatched_hash_not_saved(self):
        with patch.object(self.repo, "request", return_value=b"tampered"):
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                self.repo.blob(self.packages[0])
        self.assertFalse((self.repo.data / "cache" / self.packages[0]["sha"]).exists())

    def test_bad_cache_refetched(self):
        cache = self.repo.data / "cache" / self.packages[0]["sha"]
        gui.atomic_write(cache, b"tampered")
        with patch.object(self.repo, "request", side_effect=self.request_blob):
            result = self.repo.blob(self.packages[0])
        self.assertEqual(result, self.contents["yaml/one.yaml"])

    def test_failed_batch_never_creates_runnable_folder(self):
        with patch.object(self.repo, "request", side_effect=OSError("offline")):
            with self.assertRaises(OSError):
                self.repo.download_packages(self.packages)
        self.assertFalse((self.repo.data / "runs").exists())

    def test_catalog_offline_fallback(self):
        gui.atomic_write(self.repo.data / "catalog.json", json.dumps(self.tree).encode())
        with patch.object(self.repo, "request", side_effect=OSError("offline")):
            packages, warning = self.repo.catalog()
        self.assertEqual(packages, self.packages)
        self.assertIn("offline", warning)

    def test_official_cli_digest_checked_before_save(self):
        content = b"MZ" + b"test executable; never executed"
        release = {"assets": [{"name": "optimizerNXT.exe",
                    "browser_download_url": gui.PROJECT_URL + "/releases/download/v1/test.exe",
                    "digest": "sha256:" + hashlib.sha256(content).hexdigest()}]}
        with patch.object(self.repo, "request", side_effect=[json.dumps(release).encode(), content]):
            path = self.repo.download_cli()
        self.assertEqual(path.read_bytes(), content)
        with patch.object(self.repo, "request", side_effect=[json.dumps(release).encode(), b"MZbad"]):
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                self.repo.download_cli()
        self.assertEqual(path.read_bytes(), content)

    def test_wrong_release_origin_refused(self):
        release = {"assets": [{"name": "optimizerNXT.exe", "browser_download_url": "https://example.com/app.exe"}]}
        with patch.object(self.repo, "request", return_value=json.dumps(release).encode()):
            with self.assertRaisesRegex(ValueError, "Unexpected release"):
                self.repo.download_cli()
