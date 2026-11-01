"""Tests for the release scripts. Run: python3 -m unittest discover -s tests"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from close_issues import marker_problems  # noqa: E402

GIT_ENV = {
    **os.environ,
    # Ignore the user's and the system's git settings, such as signed tags.
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, env=GIT_ENV, capture_output=True, text=True)


def write(root, rel, text="x\n"):
    path = pathlib.Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


FAKE_GH = """#!/usr/bin/env bash
echo "$*" >> "$GH_DIR/log"
case "$1 $2" in
  "issue view") cat "$GH_DIR/$3.json" 2>/dev/null || { echo "no issue $3" >&2; exit 1; } ;;
  "issue comment") [ -f "$GH_DIR/fail-comment-$3" ] && exit 1; cat > "$GH_DIR/comment-$3.md" ;;
esac
"""


class CloseIssuesTest(unittest.TestCase):
    """scripts/close_issues.py, against a fake gh that logs its calls."""

    RELEASE_LINK = "https://github.com/example/kit/releases/tag/v1.2.0)"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self._tmp.name)
        write(self.dir, "bin/gh", FAKE_GH)
        (self.dir / "bin/gh").chmod(0o755)

    def tearDown(self):
        self._tmp.cleanup()

    def issue(self, number, state="OPEN", comments=(), kind="issues"):
        write(self.dir, f"{number}.json", json.dumps({
            "state": state, "url": f"https://github.com/example/kit/{kind}/{number}",
            "comments": [{"body": body} for body in comments]}))

    def close(self, notes, *args):
        write(self.dir, "notes.md", notes)
        env = {**GIT_ENV, "GH_DIR": str(self.dir), "PATH": f"{self.dir}/bin:{os.environ['PATH']}"}
        env.pop("GITHUB_REPOSITORY", None)
        return subprocess.run(["python3", str(REPO / "scripts/close_issues.py"), "--repo", "example/kit",
                               "--version", "1.2.0", "--notes", str(self.dir / "notes.md"), *args],
                              env=env, capture_output=True, text=True)

    def log(self):
        path = self.dir / "log"
        return path.read_text().splitlines() if path.exists() else []

    def writes(self):
        return [" ".join(line.split()[:3]) for line in self.log() if not line.startswith("issue view")]

    def test_closes_fixed_issues_and_comments_on_referenced_ones(self):
        for number in (11, 12, 20):
            self.issue(number)
        result = self.close("- First change. (ref #20, ref #11, #12)\n- Second, see #99. (#12)\n- Third.\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.writes(), ["issue comment 11", "issue comment 12", "issue close 12", "issue comment 20"])
        fixed = (self.dir / "comment-12.md").read_text()
        self.assertIn(f"Fixed in [1.2.0]({self.RELEASE_LINK}", fixed)
        self.assertIn("agd --home update", fixed)
        self.assertIn("- First change.\n", fixed)
        self.assertIn("- Second, see #99.\n", fixed)
        self.assertNotIn("Third", fixed)
        self.assertNotIn("(ref #20", fixed)
        related = (self.dir / "comment-20.md").read_text()
        self.assertIn(f"[1.2.0]({self.RELEASE_LINK}", related)
        self.assertIn("doesn't close this issue", related)
        self.assertIn("- First change.\n", related)
        self.assertNotIn("Second", related)

    def test_fix_wins_when_an_issue_is_also_referenced(self):
        self.issue(12)
        result = self.close("- First. (ref #12)\n- Second. (#12)\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.writes(), ["issue comment 12", "issue close 12"])
        self.assertIn("- First.\n", (self.dir / "comment-12.md").read_text())

    def test_running_again_changes_nothing(self):
        done = f"Fixed in [1.2.0]({self.RELEASE_LINK}."
        self.issue(12, "CLOSED", [done])
        self.issue(20, "OPEN", [done])
        result = self.close("- First. (ref #20, #12)\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.writes(), [])

    def test_comment_about_another_release_does_not_count(self):
        self.issue(20, "OPEN", ["See [1.2.01](https://github.com/example/kit/releases/tag/v1.2.01)."])
        self.close("- First. (ref #20)\n")
        self.assertEqual(self.writes(), ["issue comment 20"])

    def test_finishes_an_issue_that_was_commented_but_not_closed(self):
        self.issue(12, "OPEN", [f"Fixed in [1.2.0]({self.RELEASE_LINK}."])
        self.close("- First. (#12)\n")
        self.assertEqual(self.writes(), ["issue close 12"])

    def test_issue_closed_by_hand_still_gets_the_comment(self):
        self.issue(12, "CLOSED")
        self.close("- First. (#12)\n")
        self.assertEqual(self.writes(), ["issue comment 12"])

    def test_dry_run_writes_nothing_and_says_what_it_would_do(self):
        self.issue(12)
        self.issue(20)
        result = self.close("- First. (ref #20, #12)\n", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.writes(), [])
        self.assertIn("would close #12", result.stdout)
        self.assertIn("would comment on #20", result.stdout)

    def test_bad_number_is_reported_and_the_rest_still_runs(self):
        self.issue(13, kind="pull")
        self.issue(20)
        result = self.close("- First. (#12, #13, ref #20)\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("#12", result.stdout)
        self.assertIn("#13", result.stdout)
        self.assertEqual(self.writes(), ["issue comment 20"])

    def test_failed_comment_leaves_the_issue_open(self):
        self.issue(12)
        write(self.dir, "fail-comment-12", "")
        result = self.close("- First. (#12)\n")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.writes(), ["issue comment 12"])

    def test_malformed_marker_stops_before_anything_is_written(self):
        self.issue(12)
        result = self.close("- First. (#12)\n- Second. (part of #20)\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("#20", result.stdout)
        self.assertEqual(self.log(), [])

    def test_marker_on_a_continuation_line_counts(self):
        self.issue(12)
        self.close("- First line\n  and the second. (#12)\n")
        self.assertEqual(self.writes(), ["issue comment 12", "issue close 12"])
        self.assertIn("- First line and the second.\n", (self.dir / "comment-12.md").read_text())

    def test_no_markers_means_no_calls(self):
        result = self.close("- First.\n- Second, see #99.\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.log(), [])


class MarkerRuleTest(unittest.TestCase):
    """The changelog's issue markers, which close_issues.py acts on after a release."""

    def test_good_bullets_have_no_problems(self):
        for notes in ("- A change. (#12)\n", "- A change. (ref #20, ref #11, #12)\n", "- A change, see #99.\n",
                      "- A long change\n  on two lines. (#12)\n", "- A change.\n"):
            self.assertEqual(marker_problems(notes), [], notes)

    def test_bad_markers_and_closing_words_are_problems(self):
        for notes in ("- A change. (part of #20)\n", "- A change. (refs #20)\n", "- A change. (#20 #21)\n",
                      "- This closes #12 for good.\n", "- Fixes #12.\n", "- Long\n  and resolved #12 here.\n"):
            self.assertEqual(len(marker_problems(notes)), 1, notes)

    def test_the_unreleased_changelog_entry_has_no_problems(self):
        changelog = (REPO / "CHANGELOG.md").read_text()
        entry = re.search(r"^## \S+ \(unreleased\)\n(.*?)(?=^## |\Z)", changelog, re.M | re.S)
        self.assertEqual(marker_problems(entry.group(1)) if entry else [], [])


class ReleaseScriptsTest(unittest.TestCase):
    """scripts/bump.sh and scripts/release.py, on a copy of them in a temporary repository."""

    CHANGELOG = "# Changelog\n\nWhat changed.\n\n## 0.1.0 (unreleased)\n\n- First release.\n"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        shutil.copytree(REPO / "scripts", self.root / "scripts")
        write(self.root, "VERSION", "0.1.0\n")
        write(self.root, "CHANGELOG.md", self.CHANGELOG)
        run(["git", "init", "-q", "-b", "main"], self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def release(self):
        return run(["python3", "scripts/release.py", "--repo", "example/kit", "--date", "2026-02-02",
                    "--notes", "notes.md"], self.root)

    def test_release_moves_the_entry_into_the_notes(self):
        result = self.release()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "0.1.0")
        self.assertEqual((self.root / "notes.md").read_text(), "- First release.\n")
        changelog = (self.root / "CHANGELOG.md").read_text()
        self.assertNotIn("unreleased", changelog)
        self.assertIn("- [0.1.0](https://github.com/example/kit/releases/tag/v0.1.0) (2026-02-02)", changelog)

    def test_release_refuses_a_todo(self):
        write(self.root, "CHANGELOG.md", self.CHANGELOG.replace("First release.", "TODO: describe the change"))
        self.assertNotEqual(self.release().returncode, 0)
        self.assertFalse((self.root / "notes.md").exists())

    def test_bump_starts_the_next_version_after_a_release(self):
        self.assertEqual(self.release().returncode, 0)
        result = run(["bash", "scripts/bump.sh", "0.2.0"], self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "VERSION").read_text(), "0.2.0\n")
        changelog = (self.root / "CHANGELOG.md").read_text()
        self.assertLess(changelog.index("## 0.2.0 (unreleased)"), changelog.index("## Released"))


if __name__ == "__main__":
    unittest.main()
