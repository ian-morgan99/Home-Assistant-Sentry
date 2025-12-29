# Release Process

This document describes the process for creating a new release of Home Assistant Sentry.

## Automated Version Updates

Starting from version 1.1.0, version numbers in configuration files are automatically updated when a new release is created.

### How It Works

When you create a new release on GitHub:

1. A GitHub Actions workflow (`.github/workflows/update-version.yml`) automatically triggers
2. The workflow extracts the version number from the release tag
3. It updates the version in both configuration files:
   - `ha_sentry/config.json`
   - `ha_sentry/config.yaml`
4. The changes are committed and pushed to the `main` branch

### Creating a New Release

1. **Update the CHANGELOG.md**
   - Add release notes for the new version
   - Change the version from "TBD" to the actual release date
   - Example: `## [1.2.0] - 2024-12-30`

2. **Create a Git Tag**
   ```bash
   git tag -a v1.2.0 -m "Release version 1.2.0"
   git push origin v1.2.0
   ```

3. **Create the GitHub Release**
   - Go to the repository on GitHub
   - Click "Releases" → "Draft a new release"
   - Choose the tag you just created (e.g., `v1.2.0`)
   - Add a title (e.g., "Version 1.2.0")
   - Copy release notes from CHANGELOG.md
   - Click "Publish release"

4. **Automatic Version Update**
   - The workflow will automatically run after the release is published
   - It will update the version numbers in the config files
   - Changes will be committed to the main branch with the message: `chore: update version to X.Y.Z`

### Version Number Format

- Use semantic versioning: `MAJOR.MINOR.PATCH`
- Tags should be prefixed with `v` (e.g., `v1.2.0`)
- The workflow automatically strips the `v` prefix when updating config files

### Manual Version Updates

If you need to manually update the version before a release:

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

## Pre-Release Checklist

Before creating a release, ensure:

- [ ] All changes are documented in CHANGELOG.md
- [ ] All tests pass
- [ ] Documentation is up to date
- [ ] Version number follows semantic versioning
- [ ] Breaking changes are clearly documented

## Post-Release

After the release workflow completes:

1. Verify the version was updated in both config files on the main branch
2. The new version will be available to users via Home Assistant's add-on store
3. Users with auto-update enabled will receive the update automatically

## Troubleshooting

### Workflow Fails to Update Version

If the automated workflow fails:

1. Check the workflow run in the "Actions" tab on GitHub
2. Review the error messages
3. Manually update the version if needed (see "Manual Version Updates" above)

### Version Not Updated After Release

If the version wasn't updated automatically:

1. Verify the release was published (not just created as a draft)
2. Check that the tag has the correct format (e.g., `v1.2.0`)
3. Review the workflow logs in the Actions tab
4. Manually update if the workflow can't be re-run
