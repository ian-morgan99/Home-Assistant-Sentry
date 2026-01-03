#!/usr/bin/env python3
"""
Test script to verify the changelog generation logic works correctly.
This simulates what the GitHub Actions workflow does when generating changelog entries.
"""

import subprocess
import tempfile
import os


def run_shell_command(command):
    """Execute a shell command and return the output."""
    # Use the directory where this test file is located to find the repo root
    test_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(test_dir)
    
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        cwd=repo_root
    )
    return result.stdout.strip(), result.returncode


def test_changelog_generation_single_commit():
    """Test changelog generation with a single commit."""
    print("\n=== Test: Single Commit Scenario ===")
    
    # Simulate single commit
    recent_commits = "Initial plan"
    
    # Run the improved logic
    cmd = f'''
    RECENT_COMMITS="{recent_commits}"
    LATEST_CHANGE=$(echo "$RECENT_COMMITS" | head -1)
    
    if [ -z "$LATEST_CHANGE" ] || [ -z "$RECENT_COMMITS" ]; then
        echo "- Version automatically incremented"
    else
        COMMIT_COUNT=$(echo "$RECENT_COMMITS" | grep -c . || echo "0")
        if [ $COMMIT_COUNT -gt 1 ] && [ $COMMIT_COUNT -le 5 ]; then
            echo "$RECENT_COMMITS" | sed 's/^/- /'
        else
            echo "- $LATEST_CHANGE"
        fi
    fi
    '''
    
    output, returncode = run_shell_command(cmd)
    print(f"Output: {output}")
    assert returncode == 0, "Command should succeed"
    assert output == "- Initial plan", f"Expected '- Initial plan', got '{output}'"
    print("✓ Test passed")


def test_changelog_generation_multiple_commits():
    """Test changelog generation with multiple commits (batch merge)."""
    print("\n=== Test: Multiple Commits Scenario (3 commits) ===")
    
    # Simulate multiple commits
    cmd = '''
    RECENT_COMMITS="feat: Add new dashboard feature
fix: Resolve sensor update issue
docs: Update configuration guide"
    LATEST_CHANGE=$(echo "$RECENT_COMMITS" | head -1)
    
    if [ -z "$LATEST_CHANGE" ] || [ -z "$RECENT_COMMITS" ]; then
        echo "- Version automatically incremented"
    else
        COMMIT_COUNT=$(echo "$RECENT_COMMITS" | grep -c . || echo "0")
        if [ $COMMIT_COUNT -gt 1 ] && [ $COMMIT_COUNT -le 5 ]; then
            echo "$RECENT_COMMITS" | sed 's/^/- /'
        else
            echo "- $LATEST_CHANGE"
        fi
    fi
    '''
    
    output, returncode = run_shell_command(cmd)
    print(f"Output:\n{output}")
    assert returncode == 0, "Command should succeed"
    assert "- feat: Add new dashboard feature" in output
    assert "- fix: Resolve sensor update issue" in output
    assert "- docs: Update configuration guide" in output
    print("✓ Test passed")


def test_changelog_generation_many_commits():
    """Test changelog generation with many commits (should only use most recent)."""
    print("\n=== Test: Many Commits Scenario (7 commits) ===")
    
    cmd = '''
    RECENT_COMMITS="feat: Add feature 1
feat: Add feature 2
feat: Add feature 3
fix: Fix bug 1
fix: Fix bug 2
docs: Update docs 1
docs: Update docs 2"
    LATEST_CHANGE=$(echo "$RECENT_COMMITS" | head -1)
    
    if [ -z "$LATEST_CHANGE" ] || [ -z "$RECENT_COMMITS" ]; then
        echo "- Version automatically incremented"
    else
        COMMIT_COUNT=$(echo "$RECENT_COMMITS" | grep -c . || echo "0")
        if [ $COMMIT_COUNT -gt 1 ] && [ $COMMIT_COUNT -le 5 ]; then
            echo "$RECENT_COMMITS" | sed 's/^/- /'
        else
            echo "- $LATEST_CHANGE"
        fi
    fi
    '''
    
    output, returncode = run_shell_command(cmd)
    print(f"Output: {output}")
    assert returncode == 0, "Command should succeed"
    assert output == "- feat: Add feature 1", f"Expected '- feat: Add feature 1', got '{output}'"
    print("✓ Test passed")


def test_changelog_generation_empty():
    """Test changelog generation with no commits (fallback)."""
    print("\n=== Test: Empty Commits Scenario (Fallback) ===")
    
    cmd = '''
    RECENT_COMMITS=""
    LATEST_CHANGE=$(echo "$RECENT_COMMITS" | head -1)
    
    if [ -z "$LATEST_CHANGE" ] || [ -z "$RECENT_COMMITS" ]; then
        echo "- Version automatically incremented"
    else
        COMMIT_COUNT=$(echo "$RECENT_COMMITS" | grep -c . || echo "0")
        if [ $COMMIT_COUNT -gt 1 ] && [ $COMMIT_COUNT -le 5 ]; then
            echo "$RECENT_COMMITS" | sed 's/^/- /'
        else
            echo "- $LATEST_CHANGE"
        fi
    fi
    '''
    
    output, returncode = run_shell_command(cmd)
    print(f"Output: {output}")
    assert returncode == 0, "Command should succeed"
    assert output == "- Version automatically incremented", \
        f"Expected '- Version automatically incremented', got '{output}'"
    print("✓ Test passed")


def test_actual_git_log_filtering():
    """Test the actual git log filtering used in the workflow."""
    print("\n=== Test: Actual Git Log Filtering ===")
    
    # Get repo root dynamically
    test_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(test_dir)
    
    cmd = f'''
    cd {repo_root}
    RECENT_COMMITS=$(git log --format="%s" --no-merges -10 | \
        grep -v "^chore: auto-increment version" | \
        grep -v "^chore: sync config")
    
    if [ -z "$RECENT_COMMITS" ]; then
        echo "No commits found"
    else
        echo "$RECENT_COMMITS"
    fi
    '''
    
    output, returncode = run_shell_command(cmd)
    print(f"Output:\n{output}")
    assert returncode == 0, "Command should succeed"
    # Should have at least one commit
    assert len(output) > 0, "Should find at least one commit"
    # Should not contain version-related commits
    assert "chore: auto-increment version" not in output
    assert "chore: sync config" not in output
    print("✓ Test passed")


def test_copilot_review_extraction():
    """Test extraction of Copilot review summary for changelog."""
    print("\n=== Test: Copilot Review Summary Extraction ===")
    
    # Simulate a Copilot review body (from actual PR #97)
    copilot_review = """## Pull request overview

This pull request fixes a critical WebUI issue where the interface would hang for 60 seconds before showing an error when the dependency graph completed with zero integrations. The fix has two parts: correcting the status endpoint logic to properly detect completion with no integrations, and adding directory mappings to enable the add-on to access custom integration directories.

**Key Changes:**
- Fixed status endpoint to return `status='error'` when build completes with 0 integrations
- Enhanced JavaScript retry logic to detect completed/failed build states
- Added directory mappings in config.yaml

### Reviewed changes

Copilot reviewed 7 out of 7 changed files."""
    
    # Create temporary file with review content to avoid shell injection
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(copilot_review)
        review_file = f.name
    
    try:
        # Test the extraction logic used in the workflow
        cmd = f'''
        REVIEWS=$(cat {review_file})
        
        # Extract the first paragraph after "## Pull request overview"
        SUMMARY=$(echo "$REVIEWS" | awk '
          /## Pull request overview/ {{ in_section=1; next }}
          in_section && /^$/ {{ next }}
          in_section && NF {{ print; getline; while(NF && !/^\\*\\*/ && !/^##/ && !/^###/) {{ print; getline }} exit }}
        ')
        
        # Format as changelog entry
        if [ -n "$SUMMARY" ]; then
          echo "$SUMMARY" | tr '\\n' ' ' | sed 's/  */ /g' | sed 's/^ *//; s/ *$//; s/^/- /'
        else
          echo "ERROR: No summary extracted"
        fi
        '''
        
        output, returncode = run_shell_command(cmd)
        print(f"Output: {output}")
        assert returncode == 0, "Command should succeed"
        assert output.startswith("- This pull request"), f"Expected to start with '- This pull request', got '{output}'"
        assert "WebUI issue" in output, "Should contain 'WebUI issue'"
        assert "dependency graph" in output, "Should contain 'dependency graph'"
        # Should be a single line
        assert "\n" not in output, "Should be a single line"
        print("✓ Test passed")
    finally:
        os.unlink(review_file)


def test_pr_number_extraction():
    """Test extraction of PR number from merge commit message."""
    print("\n=== Test: PR Number Extraction ===")
    
    test_cases = [
        ("Merge pull request #97 from ian-morgan99/branch", "97"),
        ("Merge pull request #123 from user/feature", "123"),
        ("Regular commit message", ""),
    ]
    
    for commit_msg, expected_pr in test_cases:
        # Use a temporary file to safely pass the commit message
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(commit_msg)
            msg_file = f.name
        
        try:
            cmd = f'''
            PR_NUMBER=$(cat {msg_file} | grep -oP 'Merge pull request #\\K\\d+' || echo "")
            echo "$PR_NUMBER"
            '''
            
            output, returncode = run_shell_command(cmd)
            assert returncode == 0, f"Command should succeed for: {commit_msg}"
            assert output == expected_pr, f"Expected PR '{expected_pr}' from '{commit_msg}', got '{output}'"
        finally:
            os.unlink(msg_file)
    
    print("✓ Test passed")


def test_changelog_file_update():
    """Test that the changelog update logic works correctly."""
    print("\n=== Test: CHANGELOG.md Update Logic ===")
    
    # Create a temporary test changelog
    test_changelog = """# Changelog

## 1.3.14
- Version automatically incremented
- Manual update recommended: Add detailed release notes here


## 1.3.13
- Version automatically incremented
- Manual update recommended: Add detailed release notes here
"""
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write(test_changelog)
        temp_file = f.name
    
    try:
        # Test the awk command that updates the changelog
        version = "1.3.15"
        changelog_entries = "- feat: Auto-generate meaningful changelog entries"
        
        # This command recreates the changelog insertion logic:
        # 1. First awk: Print header and everything before it, then stop
        # 2. Echo new version section
        # 3. Second awk: Print everything after the header (excluding header)
        cmd = f'''
        {{
            # Print up to and including "# Changelog" header
            awk '/^# Changelog$/ {{print; print ""; exit}} {{print}}' {temp_file}
            # Add new version entry
            echo "## {version}"
            echo "{changelog_entries}"
            echo ""
            # Print everything after the header (skip=1 means skip until we see the header)
            awk 'BEGIN{{skip=1}} /^# Changelog$/{{skip=0; next}} !skip' {temp_file}
        }} > {temp_file}.tmp && cat {temp_file}.tmp
        '''
        
        output, returncode = run_shell_command(cmd)
        print(f"Output:\n{output}")
        assert returncode == 0, "Command should succeed"
        assert "# Changelog" in output
        assert f"## {version}" in output
        assert changelog_entries in output
        assert "## 1.3.14" in output
        print("✓ Test passed")
        
    finally:
        # Clean up
        os.unlink(temp_file)
        if os.path.exists(f"{temp_file}.tmp"):
            os.unlink(f"{temp_file}.tmp")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Changelog Generation Logic")
    print("=" * 60)
    
    tests = [
        test_changelog_generation_single_commit,
        test_changelog_generation_multiple_commits,
        test_changelog_generation_many_commits,
        test_changelog_generation_empty,
        test_actual_git_log_filtering,
        test_copilot_review_extraction,
        test_pr_number_extraction,
        test_changelog_file_update,
    ]
    
    failed_tests = []
    
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed_tests.append(test.__name__)
        except Exception as e:
            print(f"✗ Test error: {e}")
            failed_tests.append(test.__name__)
    
    print("\n" + "=" * 60)
    if failed_tests:
        print(f"FAILED: {len(failed_tests)} test(s) failed:")
        for test_name in failed_tests:
            print(f"  - {test_name}")
        return 1
    else:
        print("SUCCESS: All tests passed!")
        return 0


if __name__ == "__main__":
    exit(main())
