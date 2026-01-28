# CloudWarriors AI - Reusable Workflows

Central repository for reusable GitHub Actions workflows used across the CloudWarriors AI organization.

## Available Workflows

### `reusable-claude-autofix-rlm.yml`

Adversarial Claude auto-fix workflow with RLM codebase analysis.

**Usage:**
```yaml
jobs:
  autofix:
    uses: cloudwarriors-ai/workflows/.github/workflows/reusable-claude-autofix-rlm.yml@main
    with:
      issue_number: ${{ github.event.issue.number }}
    secrets: inherit
```

See [cloudwarriors-ai/.github](https://github.com/cloudwarriors-ai/.github) for full documentation.
