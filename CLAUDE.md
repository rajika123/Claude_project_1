# CLAUDE.md

This file provides guidance to AI assistants (Claude and others) when working with this repository.

## Repository Overview

This is a fresh repository hosted at `rajika123/Claude_project_1`. It is currently in its initial state with no project files yet. This CLAUDE.md serves as a foundation for future development guidance.

## Git Configuration

- **Remote**: `http://local_proxy@127.0.0.1:40229/git/rajika123/Claude_project_1`
- **Commit signing**: GPG/SSH signing is enabled for all commits (`commit.gpgsign=true`)
- **Signing key**: `/home/claude/.ssh/commit_signing_key.pub` via SSH

## Branch Strategy

- Feature branches follow the pattern: `claude/<description>-<session-id>`
- Always develop on the designated feature branch, never directly on `main`/`master`
- Push with `-u` flag to set upstream tracking: `git push -u origin <branch-name>`

## Git Workflow

```bash
# Switch to or create your feature branch
git checkout -b claude/<feature-name>-<id>

# Stage and commit changes
git add <specific-files>
git commit -m "descriptive commit message"

# Push to remote
git push -u origin <branch-name>
```

### Push Retry Logic

If push fails due to network errors, retry with exponential backoff:
- Wait 2s, retry
- Wait 4s, retry
- Wait 8s, retry
- Wait 16s, retry (final attempt)

Do **not** retry on 403 errors — these indicate permission/branch issues.

## Commit Message Conventions

Write clear, descriptive commit messages:
- Use imperative mood: "Add feature" not "Added feature"
- Keep the subject line under 72 characters
- Reference relevant issue/PR numbers when applicable
- Examples:
  - `Add user authentication module`
  - `Fix null pointer exception in data parser`
  - `Refactor database connection pooling`

## Development Principles

### Code Quality
- Write clean, readable, self-documenting code
- Keep functions small and focused on a single responsibility
- Avoid premature abstractions — only abstract when a pattern repeats 3+ times
- Delete dead code rather than commenting it out

### Security
- Never commit secrets, API keys, passwords, or credentials
- Validate all user input at system boundaries
- Avoid common vulnerabilities: SQL injection, XSS, command injection (OWASP Top 10)
- Use `.gitignore` to exclude sensitive files (`.env`, credentials, etc.)

### Dependencies
- Keep dependencies minimal and justified
- Pin dependency versions for reproducible builds
- Audit dependencies for known vulnerabilities before adding them

## File Organization Conventions

When the project grows, follow these conventions:

```
project-root/
├── CLAUDE.md          # This file — AI assistant guidance
├── README.md          # Human-facing project documentation
├── .gitignore         # Files to exclude from version control
├── src/               # Source code
├── tests/             # Test files mirroring src/ structure
├── docs/              # Additional documentation
└── scripts/           # Build, deploy, utility scripts
```

## Testing

- Write tests alongside new features (or before, if using TDD)
- Tests should live in a `tests/` directory mirroring the source structure
- Ensure all tests pass before committing
- Do not skip or disable tests without a documented reason

## Environment Configuration

- Use `.env` files for local environment variables (never commit these)
- Provide a `.env.example` with placeholder values for documentation
- Use environment-specific configs for dev/staging/production

## When Adding New Features

1. Understand the existing patterns before introducing new ones
2. Make the minimal change required — avoid scope creep
3. Update relevant documentation if behavior changes
4. Add or update tests for new functionality
5. Commit with a clear message describing what and why

## When Fixing Bugs

1. Reproduce the bug first — understand root cause before fixing
2. Fix the underlying cause, not just the symptom
3. Add a regression test that would have caught the bug
4. Keep the fix focused — avoid unrelated changes in the same commit

## AI Assistant Guidelines

When working in this repository as an AI assistant:

- **Read before editing**: Always read a file before modifying it
- **Minimal changes**: Only change what is necessary for the task
- **No guessing**: If requirements are unclear, ask for clarification
- **No invented URLs**: Do not generate or guess URLs unless confident they are correct
- **Security-first**: Never introduce security vulnerabilities
- **Reversibility**: Prefer reversible actions; confirm before destructive operations
- **Branch discipline**: Always work on the designated feature branch
- **Push responsibly**: Push only when changes are complete and tested

## Updating This File

This CLAUDE.md should be kept current as the project evolves. Update it when:
- New technologies or frameworks are added
- Development workflows change
- New conventions are established
- CI/CD pipelines are configured
- Testing strategies are updated
