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
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        cwd="/home/runner/work/Home-Assistant-Sentry/Home-Assistant-Sentry"
    )
    return result.stdout.strip(), result.returncode


def test_changelog_generation_single_commit():
    """Test changelog generation with a single commit."""
    print("\n=== Test: Single Commit Scenario ===")
    
    # Simulate single commit
    recent_commits = "Initial plan"
    
    # Run the logic
    cmd = f'''
    RECENT_COMMITS="{recent_commits}"
    LATEST_CHANGE=$(echo "$RECENT_COMMITS" | head -1)
    COMMIT_COUNT=$(echo "$RECENT_COMMITS" | wc -l)
    
    if [ -z "$LATEST_CHANGE" ]; then
        echo "- Version automatically incremented"
    else
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
    COMMIT_COUNT=$(echo "$RECENT_COMMITS" | wc -l)
    
    if [ -z "$LATEST_CHANGE" ]; then
        echo "- Version automatically incremented"
    else
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
    COMMIT_COUNT=$(echo "$RECENT_COMMITS" | wc -l)
    
    if [ -z "$LATEST_CHANGE" ]; then
        echo "- Version automatically incremented"
    else
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
    
    if [ -z "$LATEST_CHANGE" ]; then
        echo "- Version automatically incremented"
    else
        COMMIT_COUNT=$(echo "$RECENT_COMMITS" | wc -l)
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
    
    cmd = '''
    cd /home/runner/work/Home-Assistant-Sentry/Home-Assistant-Sentry
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
        
        cmd = f'''
        {{
            awk '/^# Changelog$/ {{print; print ""; exit}} {{print}}' {temp_file}
            echo "## {version}"
            echo "{changelog_entries}"
            echo ""
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
