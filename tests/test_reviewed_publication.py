"""Execute the production shell blocks, including real disposable Git remotes."""

import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github/workflows/reusable-claude-autofix-rlm.yml"
)


def block(name):
    step = WORKFLOW.read_text().split("      - name: " + name + "\n", 1)[1]
    return textwrap.dedent(
        step.split("        run: |\n", 1)[1].split("\n      - name:", 1)[0]
    )


class ReviewedPublicationTests(unittest.TestCase):
    def test_authority_matrix(self):
        script = block("Authorize reviewed publication")
        for repo, mode, base, head, issue, allowed in [
            (
                "cloudwarriors-ai/macd_agent",
                "true",
                "main",
                "autofix/issue-604",
                "604",
                True,
            ),
            (
                "cloudwarriors-ai/macd_agent",
                "false",
                "main",
                "autofix/issue-604",
                "604",
                False,
            ),
            (
                "cloudwarriors-ai/other",
                "true",
                "main",
                "autofix/issue-604",
                "604",
                False,
            ),
            (
                "cloudwarriors-ai/other",
                "false",
                "dev",
                "autofix/issue-604",
                "604",
                True,
            ),
            (
                "cloudwarriors-ai/macd_agent",
                "true",
                "dev",
                "autofix/issue-604",
                "604",
                False,
            ),
            ("cloudwarriors-ai/macd_agent", "true", "main", "main", "604", False),
            (
                "cloudwarriors-ai/macd_agent",
                "true",
                "main",
                "autofix/issue-605",
                "604",
                False,
            ),
            (
                "cloudwarriors-ai/macd_agent",
                "true",
                "main",
                "autofix/issue-0",
                "0",
                False,
            ),
        ]:
            with self.subTest(repo=repo, mode=mode, base=base, head=head):
                result = subprocess.run(
                    ["bash", "-c", script],
                    env={
                        **os.environ,
                        "GITHUB_REPOSITORY": repo,
                        "REVIEW_ONLY": mode,
                        "BASE": base,
                        "HEAD": head,
                        "ISSUE_NUM": issue,
                    },
                    capture_output=True,
                )
                self.assertEqual(result.returncode == 0, allowed)

    def test_normal_push_and_existing_branch_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / "remote.git"
            local = root / "local"

            def git(*args, cwd=None):
                return subprocess.check_output(
                    ["git", *args], cwd=cwd, stderr=subprocess.DEVNULL, text=True
                ).strip()

            git("init", "--bare", str(remote))
            git("init", str(local))
            git("config", "user.email", "test@example.invalid", cwd=local)
            git("config", "user.name", "Test", cwd=local)
            git("commit", "--allow-empty", "-m", "base", cwd=local)
            sha = git("rev-parse", "HEAD", cwd=local)
            script = block("Push committed patch").replace(
                "${{ inputs.head }}", "autofix/issue-604"
            )
            # Only replace the network endpoint; all validation and push logic is production code.
            script = script.replace(
                "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git",
                str(remote),
            )
            env = {**os.environ, "REVIEW_ONLY": "true", "COMMIT_SHA": sha}
            first = subprocess.run(
                ["bash", "-c", script], cwd=local, env=env, capture_output=True
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            git("commit", "--allow-empty", "-m", "candidate two", cwd=local)
            env["COMMIT_SHA"] = git("rev-parse", "HEAD", cwd=local)
            second = subprocess.run(
                ["bash", "-c", script], cwd=local, env=env, capture_output=True
            )
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(
                git(
                    "--git-dir",
                    str(remote),
                    "rev-parse",
                    "refs/heads/autofix/issue-604",
                ),
                sha,
            )
            # A concurrent, divergent publication after ls-remote must not be replaced.
            git(
                "--git-dir",
                str(remote),
                "update-ref",
                "-d",
                "refs/heads/autofix/issue-604",
            )
            candidate = env["COMMIT_SHA"]
            git("checkout", "--detach", sha, cwd=local)
            git("commit", "--allow-empty", "-m", "other publisher", cwd=local)
            competitor = git("rev-parse", "HEAD", cwd=local)
            git("push", str(remote), competitor + ":refs/heads/competitor", cwd=local)
            race = script.replace(
                "export LC_ALL=C",
                'git --git-dir "'
                + str(remote)
                + '" update-ref refs/heads/autofix/issue-604 '
                + competitor
                + "\nexport LC_ALL=C",
            )
            result = subprocess.run(
                ["bash", "-c", race], cwd=local, env=env, capture_output=True
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(
                git(
                    "--git-dir",
                    str(remote),
                    "rev-parse",
                    "refs/heads/autofix/issue-604",
                ),
                competitor,
            )
            self.assertNotEqual(competitor, candidate)
            reviewed = script.split('if [ "$REVIEW_ONLY" = "true" ]; then', 1)[1].split(
                "\nelse", 1
            )[0]
            self.assertNotIn("--force", reviewed)
