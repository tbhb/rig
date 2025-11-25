# GitHub CLI requirements

**MANDATORY: ALL GitHub interactions MUST use `gh` CLI**

## Core requirement

**NEVER use WebFetch to browse GitHub.com:**

- GitHub has a powerful CLI tool (`gh`)
- It provides structured, machine-readable output
- It respects rate limits and authentication
- It's faster and more reliable than web scraping

## Common commands

### Pull requests

```bash
# View PR details
gh pr view <number>
gh pr view <number> --json title,body,state,author
gh pr view <number> --comments

# Create PR
gh pr create --title "feat: add feature" --body "Description"
gh pr create --title "fix: resolve bug" --body "$(cat <<'EOF'
## Summary
Bug fix description

## Test plan
- [ ] Test 1
- [ ] Test 2
EOF
)"

# List PRs
gh pr list
gh pr list --state open
gh pr list --author @me

# Check PR status
gh pr checks
gh pr checks <number>

# View PR diff
gh pr diff <number>

# Merge PR
gh pr merge <number> --squash
```

### Issues

```bash
# View issue
gh issue view <number>
gh issue view <number> --json title,body,state,author

# Create issue
gh issue create --title "Bug: description" --body "Details"

# List issues
gh issue list
gh issue list --label bug
gh issue list --assignee @me

# Comment on issue
gh issue comment <number> --body "Comment text"
```

### Repository information

```bash
# View repository info
gh repo view
gh repo view --json name,description,url,topics

# Clone repository
gh repo clone owner/repo

# Fork repository
gh repo fork owner/repo
```

### Releases

```bash
# List releases
gh release list

# View release
gh release view <tag>

# Create release
gh release create v1.0.0 --title "Version 1.0.0" --notes "Release notes"
```

### Workflows and actions

```bash
# List workflow runs
gh run list
gh run list --workflow=test.yml

# View workflow run
gh run view <run-id>
gh run view <run-id> --log

# Re-run workflow
gh run rerun <run-id>
```

### API access

```bash
# Direct API access when CLI doesn't have command
gh api repos/owner/repo/pulls/123/comments
gh api graphql -f query='...'
```

## Why use gh CLI instead of WebFetch

### WRONG - Using WebFetch

```python
# DON'T DO THIS
result = WebFetch(
    url="https://github.com/owner/repo/pull/123",
    prompt="Extract PR title and description"
)
```

**Problems:**

- Fragile - breaks when GitHub changes HTML
- Slow - full page download and parsing
- Rate limited - no authentication
- Incomplete - misses structured data
- Unreliable - web UI is for humans, not automation

### CORRECT - Using gh CLI

```bash
# DO THIS INSTEAD
gh pr view 123 --json title,body,state,author
```

**Benefits:**

- Stable - uses official GitHub API
- Fast - structured JSON response
- Authenticated - respects your credentials
- Complete - all data available
- Reliable - designed for automation

## Integration with tools

### In Bash commands

```bash
# Get PR information
PR_INFO=$(gh pr view 123 --json title,body,state,author)
echo "$PR_INFO" | jq '.title'

# List open PRs
gh pr list --state open --json number,title
```

### With grep and processing

```bash
# Find PRs with specific labels
gh pr list --json number,title,labels | \
  jq '.[] | select(.labels[] | .name == "bug")'

# Get PR diff for specific files
gh pr diff 123 | grep "src/"
```

## Common tasks

### Review PR changes

```bash
# View full PR
gh pr view 123

# View PR diff
gh pr diff 123

# View PR commits
gh pr view 123 --json commits

# Check CI status
gh pr checks 123
```

### Get PR comments

```bash
# View all comments
gh pr view 123 --comments

# API access for structured data
gh api repos/owner/repo/pulls/123/comments
```

### Work with issues

```bash
# View issue details
gh issue view 456

# Add comment to issue
gh issue comment 456 --body "This is related to PR #123"

# Close issue
gh issue close 456
```

## Authentication

The `gh` CLI uses your GitHub authentication:

```bash
# Login (one time setup)
gh auth login

# Check auth status
gh auth status

# Use specific token
GH_TOKEN=your_token gh pr list
```

## Error handling

When `gh` commands fail:

```bash
# Check if authenticated
gh auth status

# Verify repository exists
gh repo view owner/repo

# Check rate limits
gh api rate_limit
```

## References

For more information:

- Official docs: `gh --help`
- PR commands: `gh pr --help`
- Issue commands: `gh issue --help`
- API access: `gh api --help`
- GitHub CLI manual: <https://cli.github.com/manual/>
