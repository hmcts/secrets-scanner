<div style="display: flex; align-items: center; justify-content: left; gap: 1rem;">
  <img src="./assets/hmcts-logo.png" alt="HM Courts & Tribunals Service logo" width="120" />
  <h1 style="margin: 0;">🔐 Secrets Scanner GitHub Action</h1>
</div>

This GitHub Action runs both [Gitleaks](https://github.com/gitleaks/gitleaks) and [TruffleHog](https://github.com/trufflesecurity/trufflehog) to scan for secrets in your codebase.

> ⚠️ **Note:** This custom Action is not strictly necessary. Both tools can be easily configured on a per-repository basis using GitHub workflows.  
> However, in large programmes or departments, this Action:
>
> - Eases configuration
> - Encourages best practice
> - Reduces setup and maintenance overhead
> - Enables consistent improvements across teams without the need for coordination

## 🚀 Usage

```yaml
- uses: hmcts/secrets-scanner-action@v1
```

## ✅ Tools Included

- **Gitleaks**: Fast, lightweight secret scanner for git repos
- **TruffleHog**: Finds secrets via regex and entropy analysis

## 📂 Example Workflow

```yaml
name: Scan for Secrets

on:
  pull_request:
    branches:
      - master
      - main
  schedule:
    - cron: '0 4 * * 4' # Every Thursday at 04:00
  workflow_dispatch:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: hmcts/secrets-scanner-action@v1
```

## 🔄 Keeping Up to Date

This Action centralises improvements so teams benefit automatically from:

- Updates to scanning rules
- New secret patterns
- Better failure messages
- Toolchain upgrades

## Tagging on Release

When creating a new version of this action, it's important to maintain a floating `vX`, e.g. `v1`, tag in addition to the full semantic version tag (e.g., `v1.0.1`).

### Why We Do This

Consumers of this GitHub Action often want to use a floating version, i.e. `@v1`, rather than pinning to a specific version, i.e. `@v1.0.1`.  
This allows them to automatically benefit from bug fixes and minor enhancements without manually upgrading their workflows.

By maintaining the floating tag, we:
- Reduce friction for consumers
- Avoid enforcing unnecessary upgrades
- Support safe iteration and patching within a major version

This helps reduce long-term run and maintain costs across consuming projects.

### How to Tag

1. Tag and push the new version via the command line or GitHub UI:

   ```bash
   git tag v1.0.1 HEAD
   git push origin v1.0.1
   ```

2. Update the `v1` tag to point to the new release:

   ```bash
   git tag -f v1 v1.0.1
   git push origin v1 --force
   ```

### Verify

You can verify that `v1` now points to the latest version by visiting:

[https://github.com/hmcts/artefact-version-action/tags](https://github.com/hmcts/artefact-version-action/tags)

Make sure both the full version tag (e.g., `v1.0.1`) and the floating `v1` tag appear, and that `v1` points to the latest commit.

## License

This project is licensed under the [MIT License](LICENSE).
