# Release Process

This document describes the process for creating a new release of Home Assistant Sentry.

## Automated Version Updates

Starting from version 1.1.0, version numbers in configuration files are automatically updated and validated when a new release is created.

### How It Works

When you create a new release on GitHub:

1. A GitHub Actions workflow (`.github/workflows/update-version.yml`) automatically triggers
2. The workflow extracts the version number from the release tag
3. **It validates that the version is properly incremented** (following semantic versioning)
4. It updates the version in both configuration files:
   - `ha_sentry/config.json`
   - `ha_sentry/config.yaml`
5. The changes are committed and pushed to the `main` branch

### Version Increment Rules

The workflow enforces semantic versioning and requires that each release increments the version:

- **Patch version (x.y.Z)**: Increment by `0.0.1` for bug fixes and minor changes
  - Example: `1.1.0` → `1.1.1`
- **Minor version (x.Y.0)**: Increment by `0.1.0` for new features or larger changes
  - Example: `1.1.0` → `1.2.0`
- **Major version (X.0.0)**: Increment by `1.0.0` for breaking changes
  - Example: `1.1.0` → `2.0.0`

**Important**: The workflow will fail if you try to:
- Create a release with the same version number as the current version
- Create a release with a version that is lower than the current version
- Create a release with an invalid version increment

### Creating a New Release

1. **Update the CHANGELOG.md**
   - Add release notes for the new version
   - Change the version from "TBD" to the actual release date
   - Follow Home Assistant Add-on changelog format
   - Example: `## 1.2.0 - 2024-12-30`
   - Use simple bullet points for changes (no need for subsections like "Added", "Changed", though they are acceptable)

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

4. **Automatic Version Update and Validation**
   - The workflow will automatically run after the release is published
   - It will validate that the version is properly incremented
   - It will update the version numbers in the config files
   - Changes will be committed to the main branch with a message showing the version change

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
- [ ] Version number follows semantic versioning and is properly incremented
  - [ ] Patch increment (0.0.1) for bug fixes
  - [ ] Minor increment (0.1.0) for new features
  - [ ] Major increment (1.0.0) for breaking changes
- [ ] Breaking changes are clearly documented

## Changelog Format

The CHANGELOG.md follows the Home Assistant Add-on standard format:

- **Version heading**: Use `## X.Y.Z - YYYY-MM-DD` (without square brackets)
  - Example: `## 1.2.0 - 2024-12-30`
  - Use `TBD` for unreleased versions: `## 1.2.0 - TBD`
- **Changes**: List changes as simple bullet points with `-`
  - Keep entries clear and concise
  - Group related changes together
  - You may use subsections (Added, Changed, Fixed, etc.) for clarity, but they're optional
- **Order**: Newest version at the top
- **Format**: Use standard Markdown formatting

Example:
```markdown
## 1.2.0 - 2024-12-30
- Added new feature X
- Fixed bug in Y component
- Improved performance of Z operation
- Updated documentation for clarity

## 1.1.0 - 2024-12-15
- Added support for Home Assistant 2024.12
- Fixed dashboard creation issue
```

## Post-Release

After the release workflow completes:

1. Verify the version was updated in both config files on the main branch
2. The new version will be available to users via Home Assistant's add-on store
3. Users with auto-update enabled will receive the update automatically

## Troubleshooting

### Version Validation Fails

If the workflow fails with a version validation error:

1. Check the workflow run in the "Actions" tab on GitHub for the specific error message
2. Common causes:
   - **Same version**: You're trying to release version X.Y.Z but the config files already have that version
   - **Version decrement**: The new version is lower than the current version (e.g., 1.2.0 → 1.1.0)
   - **Invalid increment**: The version jump doesn't follow semver rules
3. To fix:
   - Create a new tag with the correct incremented version
   - Delete the incorrect tag if needed: `git tag -d vX.Y.Z && git push --delete origin vX.Y.Z`
   - Create a new release with the correct version

### Workflow Fails to Update Version

If the automated workflow fails for other reasons:

1. Check the workflow run in the "Actions" tab on GitHub
2. Review the error messages
3. Manually update the version if needed (see "Manual Version Updates" above)

### Version Not Updated After Release

If the version wasn't updated automatically:

1. Verify the release was published (not just created as a draft)
2. Check that the tag has the correct format (e.g., `v1.2.0`)
3. Review the workflow logs in the Actions tab
4. Manually update if the workflow can't be re-run
