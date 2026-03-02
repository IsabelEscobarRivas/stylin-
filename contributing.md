# Contributing to Stylin'

Thank you for contributing to Stylin'. This document outlines our standards for branching, commits, pull requests, and code quality.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Branch Strategy](#branch-strategy)
3. [Commit Conventions](#commit-conventions)
4. [Pull Request Process](#pull-request-process)
5. [Code Standards](#code-standards)
6. [Environment & Secrets](#environment--secrets)

---

## Getting Started

1. Fork the repository and clone your fork locally.
2. Create a feature branch from `main` (never commit directly to `main` or `develop`).
3. Set up your `.env` using `.env.example` as a reference.
4. Install dependencies: `pip install -r requirements.txt`

---

## Branch Strategy

We follow a **GitFlow-inspired** model:

| Branch Type | Pattern | Purpose |
|---|---|---|
| Feature | `feature/short-description` | New functionality |
| Bug Fix | `bugfix/short-description` | Fix for a known issue |
| Hotfix | `hotfix/short-description` | Urgent production fix |
| Release | `release/v1.x.x` | Release preparation |

**Rules:**
- Always branch from `main`
- Never push directly to `main`, `develop`, or `sandbox`
- Branch names must be lowercase and hyphenated
- Delete merged branches after PR is closed

**Examples:**
```
feature/vision-scout-integration
bugfix/style-profile-null-response
hotfix/auth-token-expiry
```

---

## Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/).

### Format

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

### Types

| Type | When to Use |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation changes only |
| `style` | Formatting, no logic change |
| `refactor` | Code restructuring, no feature change |
| `test` | Adding or updating tests |
| `chore` | Build process, dependency updates |
| `ci` | CI/CD configuration changes |

### Examples

```
feat(vision-scout): add multi-image batch analysis support
fix(auth): handle expired token refresh edge case
docs(architecture): update agent data flow diagram
chore(deps): upgrade requests to 2.32.0
```

**Rules:**
- Subject line ≤ 50 characters
- Use imperative mood: "add" not "added" or "adds"
- Never commit secrets, API keys, or `.env` files
- Never commit to `dist/`, `build/`, or generated output directories

---

## Pull Request Process

1. **Update your branch** — rebase or merge latest `main` before opening a PR
2. **Fill out the PR template** — every section is required
3. **Link related issues** — use `Closes #123` in the PR description
4. **Request at least 1 reviewer** before merging
5. **Pass all CI checks** before requesting review
6. **Squash commits** when merging if the branch has many small fixup commits

### PR Title Format

Follow the same Conventional Commits format:

```
feat(style-curator): add budget-tier filtering to outfit recommendations
```

---

## Code Standards

### Python

- PEP 8 compliance required
- Type hints on all public functions
- Docstrings on all classes and public methods (Google style)
- Max line length: 100 characters
- Use `black` for formatting, `flake8` for linting

```python
def calling_agent(access_token: str, chat_id: str, question: str) -> str:
    """
    Send a message to the agent and return its response.

    Args:
        access_token: Valid OAuth2 bearer token.
        chat_id: Active chat session ID.
        question: User message to send.

    Returns:
        Agent response as a string.

    Raises:
        Exception: If the API returns a non-200 status.
    """
```

### General

- No hardcoded credentials or environment-specific values
- All secrets via environment variables
- Logs must go to `logs/` directory in JSON format
- No `print()` in production code — use the logging module

---

## Environment & Secrets

- Copy `.env.example` → `.env` and fill in your values
- `.env` is gitignored — **never commit it**
- Required variables:

| Variable | Description |
|---|---|
| `CLIENT_ID` | Deploy AI OAuth client ID |
| `CLIENT_SECRET` | Deploy AI OAuth client secret |
| `AUTH_URL` | OAuth2 token endpoint |
| `API_URL` | Deploy AI Core API base URL |
| `ORG_ID` | Your organization ID |

---

*Questions? Tag the relevant agent or team member in the channel.*
