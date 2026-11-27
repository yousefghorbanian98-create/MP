"""Tests for the exact-path stage helper, using disposable local Git repos."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER = REPO_ROOT / "scripts" / "stage_slice.py"


def run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=False
    )


class StageSliceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="stage-slice-test-")
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.allowlist = self.repo / "allowlist.txt"
        self._git("init", "-q")
        self._git("config", "user.name", "Stage Slice Test")
        self._git("config", "user.email", "stage-slice@example.invalid")
        for relative, content in {
            "allowed.txt": "baseline\n",
            "unrelated.txt": "baseline\n",
            "pre-staged.txt": "baseline\n",
            "literal[1].txt": "baseline\n",
            "literal1.txt": "baseline\n",
            "folder/child.txt": "baseline\n",
        }.items():
            target = self.repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        self._git("add", "--", "allowed.txt", "unrelated.txt", "pre-staged.txt", "literal[1].txt", "literal1.txt", "folder/child.txt")
        self._git("commit", "-qm", "baseline")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _git(self, *args: str) -> str:
        result = run_git(self.repo, *args)
        if result.returncode:
            self.fail(f"git {' '.join(args)} failed: {result.stderr}")
        return result.stdout

    def _run_helper(self, text: str) -> subprocess.CompletedProcess[str]:
        self.allowlist.write_text(text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(HELPER), str(self.allowlist), "--repo", str(self.repo)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def _staged(self) -> set[str]:
        return set(self._git("diff", "--cached", "--name-only").splitlines())

    def test_stages_only_allowlisted_and_preserves_preexisting_index(self) -> None:
        (self.repo / "allowed.txt").write_text("selected change\n", encoding="utf-8")
        (self.repo / "unrelated.txt").write_text("must stay unstaged\n", encoding="utf-8")
        (self.repo / "pre-staged.txt").write_text("already staged\n", encoding="utf-8")
        self._git("add", "--", "pre-staged.txt")

        result = self._run_helper("# comment\nallowed.txt\n")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._staged(), {"allowed.txt", "pre-staged.txt"})
        self.assertIn("allowlisted_paths=1", result.stdout)
        self.assertIn("staged_allowlisted_count=1", result.stdout)
        self.assertIn("index_staged_path_count=2", result.stdout)
        self.assertNotIn("unrelated.txt", result.stdout)

    def test_literal_pathspec_does_not_expand_brackets(self) -> None:
        (self.repo / "literal[1].txt").write_text("selected\n", encoding="utf-8")
        (self.repo / "literal1.txt").write_text("must stay unstaged\n", encoding="utf-8")

        result = self._run_helper("literal[1].txt\n")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._staged(), {"literal[1].txt"})

    def test_rejects_directory_traversal_and_missing_path_without_staging(self) -> None:
        (self.repo / "allowed.txt").write_text("unstaged\n", encoding="utf-8")
        before = self._staged()
        for invalid in ("folder\n", "../outside.txt\n", "missing.txt\n"):
            with self.subTest(invalid=invalid):
                result = self._run_helper(invalid)
                self.assertEqual(result.returncode, 2)
                self.assertIn("stage_slice: error:", result.stderr)
                self.assertEqual(self._staged(), before)

    def test_stages_explicit_deletion(self) -> None:
        (self.repo / "allowed.txt").unlink()

        result = self._run_helper("allowed.txt\n")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._staged(), {"allowed.txt"})
        self.assertIn("staged_allowlisted_count=1", result.stdout)

    def test_rejects_duplicate_paths(self) -> None:
        result = self._run_helper("allowed.txt\nallowed.txt\n")
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate path", result.stderr)
        self.assertEqual(self._staged(), set())


if __name__ == "__main__":
    unittest.main(verbosity=2)
