# Publishing nrgkick-api Library to GitHub and PyPI

This guide walks through extracting the `nrgkick-api` library from this repository, publishing it as a standalone GitHub repository, and releasing it on PyPI.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Create New GitHub Repository](#step-1-create-new-github-repository)
4. [Step 2: Extract Library to New Repository](#step-2-extract-library-to-new-repository)
5. [Step 3: Set Up PyPI Account and API Token](#step-3-set-up-pypi-account-and-api-token)
6. [Step 4: Configure GitHub Secrets](#step-4-configure-github-secrets)
7. [Step 5: Test the Library Independently](#step-5-test-the-library-independently)
8. [Step 6: Publish to PyPI](#step-6-publish-to-pypi)
9. [Step 7: Update Home Assistant Integration](#step-7-update-home-assistant-integration)
10. [Step 8: Clean Up Original Repository](#step-8-clean-up-original-repository)
11. [Development Workflow: Local vs Published Library](#development-workflow-local-vs-published-library)
12. [Maintenance and Versioning](#maintenance-and-versioning)

---

## Overview

Currently, the `nrgkick-api` library lives inside the Home Assistant integration repository at `nrgkick-api/`. To publish it to PyPI, we need to:

1. Create a new standalone GitHub repository for the library
2. Move the library code there
3. Set up PyPI publishing via GitHub Actions
4. Update the integration to use the published package
5. Establish a development workflow for working with both repositories

**Repository Structure After Publishing:**

```
GitHub Repositories:
├── andijakl/nrgkick-api          # Standalone library (NEW)
│   ├── src/nrgkick_api/
│   ├── tests/
│   ├── pyproject.toml
│   └── .github/workflows/
│
└── andijakl/nrgkick-homeassistant  # Home Assistant integration (EXISTING)
    ├── custom_components/nrgkick/
    ├── tests/
    └── requirements_dev.txt      # Points to published nrgkick-api
```

---

## Prerequisites

Before starting, ensure you have:

- [ ] GitHub account with permissions to create repositories
- [ ] PyPI account (https://pypi.org/account/register/)
- [ ] Git installed locally
- [ ] Python 3.11+ installed
- [ ] All dev tools are included in `pyproject.toml` - install with `pip install -e ".[dev]"`

---

## Step 1: Create New GitHub Repository

### 1.1 Create Repository on GitHub

1. Go to https://github.com/new
2. Fill in the details:
   - **Repository name:** `nrgkick-api`
   - **Description:** `Async Python client for NRGkick Gen2 EV charger local REST API`
   - **Visibility:** Public (required for PyPI)
   - **Initialize:** Do NOT add README, .gitignore, or license (we'll push existing files)
3. Click **Create repository**

### 1.2 Note the Repository URL

Save the repository URL for later:
```
https://github.com/andijakl/nrgkick-api.git
```

---

## Step 2: Extract Library to New Repository

### 2.1 Create a Clean Copy of the Library

Open a terminal and run these commands:

```bash
# Navigate to a temporary location outside the integration repo
cd /mnt/d/Source/GitHub

# Create the new repository directory
mkdir nrgkick-api
cd nrgkick-api

# Initialize git
git init

# Copy library files from the integration repo
cp -r ../nrgkick/nrgkick-api/* .

# Verify the structure
ls -la
# Should show: src/, tests/, pyproject.toml, README.md, LICENSE, etc.
```

### 2.2 Verify pyproject.toml URLs

Open `pyproject.toml` and verify the URLs point to the new repository:

```toml
[project.urls]
Homepage = "https://github.com/andijakl/nrgkick-api"
Documentation = "https://github.com/andijakl/nrgkick-api#readme"
Repository = "https://github.com/andijakl/nrgkick-api.git"
Issues = "https://github.com/andijakl/nrgkick-api/issues"
Changelog = "https://github.com/andijakl/nrgkick-api/blob/main/CHANGELOG.md"
```

### 2.3 Create Initial Commit and Push

```bash
# Add all files
git add .

# Create initial commit
git commit -m "Initial release of nrgkick-api library v1.0.0

Async Python client for NRGkick Gen2 EV charger local REST API.

Features:
- Full REST API support (info, control, values endpoints)
- Automatic retry with exponential backoff
- HTTP Basic Auth support
- Comprehensive error handling
- Type hints throughout
- 31 unit tests with ~91% coverage"

# Add remote
git remote add origin https://github.com/andijakl/nrgkick-api.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 2.4 Create Release Tag

```bash
# Create version tag
git tag -a v1.0.0 -m "Release v1.0.0 - Initial public release"

# Push tag
git push origin v1.0.0
```

---

## Step 3: Set Up PyPI Account and API Token

### 3.1 Create PyPI Account (if needed)

1. Go to https://pypi.org/account/register/
2. Create an account and verify your email
3. Enable 2FA for security (recommended)

### 3.2 Create API Token

1. Log in to PyPI
2. Go to **Account Settings** → **API tokens**
3. Click **Add API token**
4. Fill in:
   - **Token name:** `nrgkick-api-github-actions`
   - **Scope:** `Entire account` (for first upload) or project-specific after first upload
5. Click **Create token**
6. **IMPORTANT:** Copy the token immediately (starts with `pypi-`)
   - You won't be able to see it again!
   - Save it temporarily in a secure location

### 3.3 (Optional) Test on TestPyPI First

For safety, you can test on TestPyPI first:

1. Create account at https://test.pypi.org/account/register/
2. Create API token at https://test.pypi.org/manage/account/token/
3. Use `--repository testpypi` when uploading

---

## Step 4: Configure GitHub Secrets

### 4.1 Add PyPI Token to GitHub Secrets

1. Go to your new repository: https://github.com/andijakl/nrgkick-api
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the secret:
   - **Name:** `PYPI_API_TOKEN`
   - **Value:** Paste your PyPI token (the one starting with `pypi-`)
5. Click **Add secret**

### 4.2 Verify GitHub Actions Workflow

The repository already has `.github/workflows/publish.yml` configured. Verify it contains:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install build dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

---

## Step 5: Test the Library Independently

Before publishing, verify the library works standalone.

### 5.1 Create Test Virtual Environment

```bash
cd /mnt/d/Source/GitHub/nrgkick-api

# Create fresh virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install in development mode
pip install -e ".[dev]"
```

### 5.2 Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/nrgkick_api --cov-report=term-missing

# Expected: 31 tests passing, ~91% coverage
```

### 5.3 Set Up Pre-commit Hooks (Recommended)

Pre-commit hooks run the same linting checks locally before you commit, catching issues before they fail in GitHub Actions:

```bash
# Install pre-commit hooks (one-time setup)
pre-commit install

# Run all checks manually
pre-commit run --all-files

# Hooks will now run automatically on every commit
```

The `.pre-commit-config.yaml` includes:
- **black** - Code formatting
- **isort** - Import sorting
- **flake8** - Style checking (configured to match black's 88-char line length)
- **mypy** - Type checking
- **pylint** - Code analysis

### 5.4 Test Build Process

```bash
# Build the package
python -m build

# Check the built files
ls dist/
# Should show:
# - nrgkick_api-1.0.0-py3-none-any.whl
# - nrgkick_api-1.0.0.tar.gz

# Verify package contents
twine check dist/*
# Should show: PASSED
```

### 5.5 Test Installation from Built Package

```bash
# Create another test environment
deactivate
python3 -m venv install-test-venv
source install-test-venv/bin/activate

# Install from wheel
pip install dist/nrgkick_api-1.0.0-py3-none-any.whl

# Test import
python -c "from nrgkick_api import NRGkickAPI; print('Import successful')"
```

---

## Step 6: Publish to PyPI

### 6.1 Option A: Publish via GitHub Release (Recommended)

This uses the GitHub Actions workflow for automated publishing:

1. Go to https://github.com/andijakl/nrgkick-api/releases
2. Click **Create a new release**
3. Fill in:
   - **Tag:** `v1.0.0` (select existing tag)
   - **Title:** `v1.0.0 - Initial Release`
   - **Description:**
     ```markdown
     ## nrgkick-api v1.0.0

     Initial public release of the async Python client for NRGkick Gen2 EV chargers.

     ### Features
     - Full REST API support (info, control, values endpoints)
     - Automatic retry with exponential backoff (3 attempts)
     - HTTP Basic Auth support
     - Comprehensive error handling with typed exceptions
     - Type hints throughout
     - Python 3.11+ support

     ### Installation
     ```bash
     pip install nrgkick-api
     ```

     ### Documentation
     See [README](https://github.com/andijakl/nrgkick-api#readme) for usage examples.
     ```
4. Click **Publish release**
5. Go to **Actions** tab to monitor the publish workflow
6. Once complete, verify at https://pypi.org/project/nrgkick-api/

### 6.2 Option B: Manual Upload (Alternative)

If you prefer manual control:

```bash
cd /mnt/d/Source/GitHub/nrgkick-api-standalone

# Build
python -m build

# Upload to PyPI
twine upload dist/*
# Enter your PyPI username: __token__
# Enter your PyPI password: pypi-YOUR_TOKEN_HERE
```

### 6.3 Verify Publication

1. Check https://pypi.org/project/nrgkick-api/
2. Test installation:
   ```bash
   pip install nrgkick-api
   python -c "from nrgkick_api import NRGkickAPI; print('Success!')"
   ```

---

## Step 7: Update Home Assistant Integration

### 7.1 Update requirements_dev.txt

In the integration repository (`nrgkick-homeassistant`), update `requirements_dev.txt`:

```diff
- -e ./nrgkick-api
+ nrgkick-api>=1.0.0
```

The file should have:
```
# NRGkick API Library
# For CI/production: use published PyPI package
nrgkick-api>=1.0.0
# For local development with library changes, comment above and use:
# -e ../nrgkick-api
```

### 7.2 GitHub Actions Workflows

The workflows (`test.yml`, `quality.yml`, `validate.yml`) don't need changes - they use `requirements_dev.txt` which now pulls from PyPI.

However, if tests fail because the library isn't published yet, you can temporarily modify the workflow to install from the library repo:

```yaml
# In test.yml, before "Install dependencies" step, add:
- name: Checkout nrgkick-api library
  uses: actions/checkout@v6
  with:
    repository: andijakl/nrgkick-api
    path: nrgkick-api-lib

- name: Install library from source
  run: pip install -e ./nrgkick-api-lib
```

Remove this workaround after the library is published to PyPI.

### 7.2 Update manifest.json (if needed)

Verify `custom_components/nrgkick/manifest.json` has:

```json
{
  "requirements": ["nrgkick-api==1.0.0"]
}
```

### 7.3 Test Integration with Published Library

```bash
cd /mnt/d/Source/GitHub/nrgkick

# Create fresh environment
python -m venv fresh-venv
source fresh-venv/bin/activate

# Install from PyPI (not local)
pip install nrgkick-api>=1.0.0

# Install other dev dependencies
pip install -r requirements_dev.txt

# Run integration tests
pytest tests/ -v
```

---

## Step 8: Clean Up Original Repository

### 8.1 Remove Library from Integration Repository

After confirming everything works with the published library:

```bash
cd /mnt/d/Source/GitHub/nrgkick

# Remove the embedded library directory
rm -rf nrgkick-api/

# Update .gitignore if needed
echo "nrgkick-api/" >> .gitignore
```

### 8.2 Update Documentation

Update `README.md` to mention the library is now separate:

```markdown
## Architecture

This integration uses the [nrgkick-api](https://github.com/andijakl/nrgkick-api)
library for device communication. The library is available on
[PyPI](https://pypi.org/project/nrgkick-api/).
```

### 8.3 Commit Changes

```bash
git add -A
git commit -m "Extract nrgkick-api library to separate repository

The API client library is now maintained separately at:
https://github.com/andijakl/nrgkick-api

This enables:
- Independent versioning and releases
- Easier contribution to either project
- Potential Home Assistant core integration
- Use of the library in other projects"

git push
```

---

## Development Workflow: Local vs Published Library

### Understanding the Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| **Always use PyPI** | Tests match production exactly | Slow iteration when changing library |
| **Always use local** | Fast iteration | Tests might pass locally but fail in production |
| **Switchable** | Best of both worlds | More complex setup |

### Recommended: Switchable Development Setup

#### Option 1: Environment Variable Toggle

Create a script or use environment variables to switch:

**requirements_dev.txt:**
```
# Base dependencies
pytest>=7.0.0
pytest-asyncio>=0.21.0
# ... other deps ...

# Library - installed separately based on environment
# See install instructions below
```

**Install script (install-dev.sh):**
```bash
#!/bin/bash

if [ "$USE_LOCAL_LIB" = "1" ]; then
    echo "Installing local nrgkick-api library..."
    pip install -e ../nrgkick-api-standalone
else
    echo "Installing published nrgkick-api library..."
    pip install nrgkick-api>=1.0.0
fi

pip install -r requirements_dev.txt
```

**Usage:**
```bash
# For development with local library changes
USE_LOCAL_LIB=1 ./install-dev.sh

# For testing with published library
./install-dev.sh
```

#### Option 2: Separate CI Jobs

In `.github/workflows/test.yml`, add a job that tests with the published library:

```yaml
jobs:
  test-local:
    name: Test with local library
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Checkout library
        uses: actions/checkout@v4
        with:
          repository: andijakl/nrgkick-api
          path: nrgkick-api-lib
      - name: Install local library
        run: pip install -e ./nrgkick-api-lib
      - name: Run tests
        run: pytest tests/

  test-published:
    name: Test with PyPI library
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install published library
        run: pip install nrgkick-api>=1.0.0
      - name: Run tests
        run: pytest tests/
```

#### Option 3: pip install with --editable flag

The simplest approach for daily development:

```bash
# When working on library changes (in integration repo)
pip install -e ../nrgkick-api-standalone

# When testing production behavior
pip uninstall nrgkick-api
pip install nrgkick-api>=1.0.0
```

### Recommended Daily Workflow

1. **Normal integration development:** Use published library
   ```bash
   pip install nrgkick-api>=1.0.0
   ```

2. **When you need to change the library:**
   ```bash
   # Clone/pull library repo
   cd ../nrgkick-api-standalone
   git pull

   # Install in editable mode
   pip install -e .

   # Make changes, test in integration
   cd ../nrgkick
   pytest tests/

   # When done, commit to library repo
   cd ../nrgkick-api-standalone
   git add -A && git commit -m "Your changes"
   git push
   ```

3. **Release new library version:**
   - Update version in `pyproject.toml`
   - Create GitHub release
   - Update integration's `manifest.json` to new version

---

## Maintenance and Versioning

### Version Strategy

Use [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0 → 2.0.0): Breaking API changes
- **MINOR** (1.0.0 → 1.1.0): New features, backward compatible
- **PATCH** (1.0.0 → 1.0.1): Bug fixes, backward compatible

### Release Checklist

When releasing a new library version:

1. [ ] Update version in `pyproject.toml`
2. [ ] Update `CHANGELOG.md`
3. [ ] Run full test suite
4. [ ] Create git tag: `git tag -a v1.1.0 -m "Release v1.1.0"`
5. [ ] Push tag: `git push origin v1.1.0`
6. [ ] Create GitHub release (triggers PyPI publish)
7. [ ] Verify on PyPI
8. [ ] Update integration's `manifest.json` requirement
9. [ ] Test integration with new library version
10. [ ] Release new integration version

### Keeping Repositories in Sync

When the library API changes:

1. **Backward compatible changes:** Update library, release, then update integration
2. **Breaking changes:**
   - Release library as new major version
   - Update integration to support new API
   - Update integration's version requirement
   - Release both together

---

## Troubleshooting

### Common Issues

**"Package already exists" on PyPI:**
- You cannot overwrite a version. Increment the version number.

**GitHub Actions publish fails:**
- Check the `PYPI_API_TOKEN` secret is set correctly
- Verify token has correct scope (project or account-wide)

**Import errors after publishing:**
- Ensure package name in `pyproject.toml` matches import name
- Check `[tool.setuptools.packages.find]` configuration

**Tests pass locally but fail in CI:**
- Ensure CI uses same Python version
- Check all dependencies are listed in `pyproject.toml`

### Getting Help

- PyPI documentation: https://packaging.python.org/
- GitHub Actions: https://docs.github.com/en/actions
- Twine documentation: https://twine.readthedocs.io/

---

## Quick Reference Commands

### Helper Scripts

The repository includes two helper scripts for common tasks:

```bash
# Validate code before committing (pre-commit hooks + tests)
./validate.sh

# Validate without updating hooks
./validate.sh --no-update

# Validate without running tests (faster)
./validate.sh --no-update --no-tests

# Create a release with a new version
./create_release.sh 1.0.1

# Create a release with current version
./create_release.sh
```

### Manual Commands

```bash
# Build package
python -m build

# Check package
twine check dist/*

# Upload to TestPyPI (for testing)
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ nrgkick-api

# Install from PyPI
pip install nrgkick-api

# Install local editable
pip install -e ../nrgkick-api-standalone
```
