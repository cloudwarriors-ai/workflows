from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/reusable-claude-autofix-rlm.yml"


class OpenRouterCredentialContractTests(unittest.TestCase):
    def test_claude_stages_use_documented_openrouter_bearer_contract(self):
        workflow = WORKFLOW.read_text()

        self.assertEqual(workflow.count('export ANTHROPIC_API_KEY=""'), 3)
        self.assertEqual(
            workflow.count('export ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY"'),
            3,
        )
        self.assertEqual(
            workflow.count(
                'export ANTHROPIC_BASE_URL="https://openrouter.ai/api"'
            ),
            3,
        )

    def test_openrouter_credential_is_rejected_before_agent_execution(self):
        workflow = WORKFLOW.read_text()

        self.assertIn("- name: Validate OpenRouter credential", workflow)
        self.assertIn("https://openrouter.ai/api/v1/key", workflow)
        self.assertIn('--output /dev/null', workflow)
        self.assertIn('if [ "$status" != "200" ]; then', workflow)

    def test_claude_cli_version_is_pinned(self):
        workflow = WORKFLOW.read_text()

        self.assertEqual(
            workflow.count(
                "npm install -g @anthropic-ai/claude-code@2.1.250"
            ),
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
