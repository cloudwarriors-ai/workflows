from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/reusable-claude-autofix-rlm.yml"


class OpenRouterCredentialContractTests(unittest.TestCase):
    def test_claude_stages_use_bearer_token_without_empty_api_key(self):
        workflow = WORKFLOW.read_text()

        self.assertNotIn('export ANTHROPIC_API_KEY=""', workflow)
        self.assertEqual(workflow.count("unset ANTHROPIC_API_KEY"), 3)
        self.assertEqual(
            workflow.count('export ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY"'),
            3,
        )

    def test_direct_anthropic_stages_keep_api_key_precedence(self):
        workflow = WORKFLOW.read_text()

        self.assertEqual(
            workflow.count(
                'export ANTHROPIC_API_KEY="$DIRECT_ANTHROPIC_API_KEY"'
            ),
            3,
        )
        self.assertEqual(workflow.count("unset ANTHROPIC_AUTH_TOKEN"), 3)
        self.assertEqual(workflow.count("unset ANTHROPIC_BASE_URL"), 3)


if __name__ == "__main__":
    unittest.main()
