# Release Process

This document describes the process for creating a new release of Home Assistant Sentry.

## Automated Version Updates

Starting from version 1.3.04, version numbers in configuration files are **automatically incremented on every commit to the main branch**.

### How It Works

When code is pushed to the main branch (including when a Pull Request is merged):

1. A GitHub Actions workflow (`.github/workflows/update-version.yml`) automatically triggers
2. **First, it syncs version between config files** if they're out of sync (config.yaml matches config.json)
3. Then it reads the current version from `ha_sentry/config.json`
4. **It automatically increments the patch version by 1** (preserving 2-character formatting when present)
5. It updates the version in both configuration files:
   - `ha_sentry/config.json`
   - `ha_sentry/config.yaml`
6. **It generates a meaningful CHANGELOG.md entry** using a smart three-tier approach:
   - **First priority**: Extracts Copilot PR review summary (from "## Pull request overview" section)
   - **Second priority**: Uses PR title and body summary if available
   - **Third priority**: Falls back to commit message(s) that triggered this version bump
     - For single commits: Uses the commit message directly
     - For batch merges (2-5 commits): Includes all commit messages
     - For large batches (6+ commits): Uses the most recent commit message
7. The changes are committed and pushed back to the `main` branch
8. The workflow includes safeguards to prevent infinite loops (skips if commit is from the bot or is version-related)

### Automatic Version Increment

The workflow automatically increments the **patch version** (smallest digit) on every push to main:

- **Automatic increment**: `+1` for every commit to main
  - Example: `1.3.04` → `1.3.05` → `1.3.06` → `1.3.07`
  - Example: `1.3.09` → `1.3.10` → `1.3.11`
  - Example: `2.5.99` → `2.5.100` → `2.5.101`
- **Format preservation**: 2-character formatting is preserved (e.g., `04` → `05`, not `5`)

### Version Synchronization

If config.json and config.yaml ever get out of sync:
- The workflow automatically syncs config.yaml to match config.json **before** incrementing
- This ensures both files always have the same version
- The sync happens in the same commit as the version increment

### Manual Version Management

If you need to manually set a specific version (e.g., for a minor or major version bump):

1. Edit `ha_sentry/config.json` to the desired version
2. Edit `ha_sentry/config.yaml` to match
3. Commit and push to main
4. The next automatic commit will increment from your new base version

**Important Notes**:
- The workflow automatically skips if the commit author is `github-actions[bot]` to prevent infinite loops
- The workflow also skips if the commit message starts with version-related prefixes (e.g., "chore: auto-increment version", "chore: sync config.yaml version")
- The workflow ignores changes to `.github/workflows/**` files
- Both config files are automatically synced and kept in sync
- Version format with 2-character numbers (e.g., `1.3.04`) is preserved throughout increments

### Creating a New Release

Since versions are automatically incremented on every commit, creating a release is simplified:

1. **CHANGELOG.md is automatically updated**
   - The workflow automatically generates changelog entries using a smart three-tier approach:
     1. **Copilot PR review summary** (highest priority) - Extracts detailed summary from Copilot's PR review
     2. **PR title and body** (fallback) - Uses PR title and description when review isn't available
     3. **Commit messages** (last resort) - Uses commit messages if PR info isn't accessible
   - For batch merges (2-5 commits), all commit messages are included
   - For single commits or large batches, only the most recent commit message is used
   - You can manually edit ha_sentry/CHANGELOG.md to refine or enhance the auto-generated entries
   - Follow Home Assistant Add-on changelog format
   - Example: `## 1.2.0` (version number only, no date)
   - Use simple bullet points for changes (no need for subsections like "Added", "Changed", though they are acceptable)
   - **Important**: Do not add dates or other suffixes to version headings
   - **Tip**: Write clear, descriptive PR descriptions and commit messages as they may appear in the CHANGELOG

2. **Create a Git Tag** (optional, for marking specific releases)
   ```bash
   git tag -a v1.2.0 -m "Release version 1.2.0"
   git push origin v1.2.0
   ```

3. **Create the GitHub Release** (optional, for publishing release notes)
   - Go to the repository on GitHub
   - Click "Releases" → "Draft a new release"
   - Choose an existing tag or create a new one (e.g., `v1.2.0`)
   - Add a title (e.g., "Version 1.2.0")
   - Copy release notes from CHANGELOG.md
   - Click "Publish release"

**Note**: Version numbers are automatically managed by commits to main. Tags and GitHub releases are optional and primarily used for documentation and user communication.

### Version Number Format

- Use semantic versioning: `MAJOR.MINOR.PATCH`
- Tags should be prefixed with `v` (e.g., `v1.2.0`)
- The workflow automatically strips the `v` prefix when updating config files

### Manual Version Updates

If you need to manually adjust the version (e.g., for a minor or major version bump):

1. Edit `ha_sentry/config.json`:
   ```json
   "version": "1.2.0"
   ```

2. Edit `ha_sentry/config.yaml`:
   ```yaml
   version: "1.2.0"
   ```

3. Commit the changes:
   ```bash
   git add ha_sentry/config.json ha_sentry/config.yaml
   git commit -m "chore: bump version to 1.2.0"
   git push
   ```

4. The next automatic commit to main will increment from this new base version.

**Note**: To skip auto-increment on a specific commit, you cannot prevent it. However, you can always manually adjust the version in a subsequent commit if needed.

## Writing Good Commit Messages and PR Descriptions

Since commit messages and PR descriptions may be automatically included in the CHANGELOG, follow these best practices:

### Pull Request Descriptions
When Copilot creates a PR, it automatically generates a detailed review summary. You can also manually write PR descriptions:

- **Include a clear summary**: The first paragraph or "## Summary" section should concisely explain the changes
- **Be user-focused**: Describe what changed from a user's perspective, not implementation details
- **Use structured sections**: Use `## Summary`, `## Overview`, or similar headings for better parsing

**Good PR description example:**
```markdown
## Summary

This PR fixes a critical issue where the WebUI would hang for 60 seconds when the dependency graph completed with zero integrations. The fix corrects the status endpoint logic and adds directory mappings.

## Changes
- Fixed status endpoint to return proper error state
- Enhanced JavaScript retry logic
- Added directory mappings in config.yaml
```

### Commit Messages
- **Be descriptive**: Write clear, user-friendly commit messages that explain what changed and why
- **Use conventional commit format** (optional but recommended):
  - `feat: Add new dashboard feature` - New features
  - `fix: Resolve issue with sensor updates` - Bug fixes
  - `docs: Update configuration examples` - Documentation changes
  - `refactor: Improve dependency analysis performance` - Code improvements
  - `chore: Update dependencies` - Maintenance tasks
- **Focus on what, not how**: Describe the change from a user's perspective
- **Be concise but complete**: One-line messages are fine if they're clear
- **Avoid vague messages**: Instead of "Fix bug", write "Fix issue with HACS integration detection"

**Good examples:**
- `feat: Add support for auto-update configuration`
- `fix: Resolve dashboard creation failure on startup`
- `docs: Add troubleshooting guide for AI providers`

**Poor examples:**
- `Update files` (too vague)
- `WIP` (not descriptive)
- `Fix` (what was fixed?)

Remember: Your PR description or commit message may appear in the CHANGELOG and be visible to all users!

## Pre-Release Checklist

Before merging to main (which will trigger auto-increment), ensure:

- [ ] Commit message is clear and descriptive (it will appear in CHANGELOG.md automatically)
- [ ] All tests pass
- [ ] Documentation is up to date
- [ ] Consider if the change warrants a minor or major version bump (manually adjust if needed)
  - [ ] Patch auto-increment (0.0.1) is appropriate for most changes
  - [ ] Minor bump (0.1.0) may be needed for significant new features
  - [ ] Major bump (1.0.0) may be needed for breaking changes
- [ ] Breaking changes are clearly documented

## Changelog Format

The ha_sentry/CHANGELOG.md follows the Home Assistant Add-on standard format:

- **Version heading**: Use `## X.Y.Z` (version number only, no date suffix)
  - Example: `## 1.2.0`
  - Home Assistant Supervisor parses these headings to match the version in config.yaml
  - **Important**: Do NOT add dates or "TBD" suffixes as Home Assistant expects exact version matches
- **Changes**: List changes as simple bullet points with `-`
  - Keep entries clear and concise
  - Group related changes together
  - You may use subsections (Added, Changed, Fixed, etc.) for clarity, but they're optional
- **Order**: Newest version at the top
- **Format**: Use standard Markdown formatting

Example:
```markdown
## 1.2.0
- Added new feature X
- Fixed bug in Y component
- Improved performance of Z operation
- Updated documentation for clarity

## 1.1.0
- Added support for Home Assistant 2024.12
- Fixed dashboard creation issue
```

**Why this format?**

Home Assistant Supervisor:
1. Reads config.yaml → gets version (e.g., "1.2.0")
2. Looks for ha_sentry/CHANGELOG.md (in the add-on directory)
3. Parses markdown headings looking for exact match: `## 1.2.0`
4. Displays the content under that heading

If the version heading includes dates or other suffixes, Home Assistant will not find a match and will show "No changelog found".

## Post-Release

After code is merged to main:

1. The version is automatically incremented in both config files
2. The new version will be available to users via Home Assistant's add-on store (when the add-on is published)
3. Users with auto-update enabled will receive the update automatically

## Troubleshooting

### Workflow Doesn't Run

If the auto-increment workflow doesn't run after a commit to main:

1. Check the workflow run in the "Actions" tab on GitHub
2. Verify the commit was made to the `main` branch
3. Check if the commit was made by `github-actions[bot]` (it will skip to prevent infinite loops)
4. Verify the push didn't only modify `.github/workflows/**` files (these are ignored)

### Version Not Incremented

If the version wasn't incremented after a commit:

1. Check the workflow logs in the "Actions" tab on GitHub
2. Look for the "Check if commit is from bot" step - it may have skipped
3. Verify both config files have the same version format (X.Y.Z)
4. Manually update the version if needed (see "Manual Version Updates" above)

### Infinite Loop Prevention

The workflow has built-in safeguards:
- Skips execution if the commit author is `github-actions[bot]`
- Ignores changes to workflow files (`.github/workflows/**`)
- Only commits if there are actual changes to the version files

If you suspect an infinite loop:
1. Check the commit history for repeated bot commits
2. Review the workflow logs for any errors
3. The safeguards should prevent this, but you can temporarily disable the workflow if needed
