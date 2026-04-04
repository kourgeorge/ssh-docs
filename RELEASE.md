# Release Guide for ssh-docs v0.1.2

## What's New in v0.1.2

- **Enhanced documentation for AI agents**: No-auth mode is now prominently featured at the beginning of Quick Start sections in both README.md and the website
- **Better agent workflow guidance**: Clear explanation of why `--auth public` is ideal for AI coding agents and local development

## Pre-Release Checklist

- [x] Version bumped to 0.1.2 in `pyproject.toml`
- [x] Documentation updated (README.md and docs/index.html)
- [x] Distribution packages built successfully
  - `dist/ssh_docs-0.1.2.tar.gz` (source distribution)
  - `dist/ssh_docs-0.1.2-py3-none-any.whl` (wheel)

## Publishing to PyPI

### Prerequisites

1. Install/upgrade publishing tools:
```bash
pip install --upgrade twine
```

2. Ensure you have PyPI credentials configured:
   - Create an account at https://pypi.org/
   - Generate an API token at https://pypi.org/manage/account/token/
   - Configure credentials in `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN-HERE
```

### Test on TestPyPI (Recommended)

1. Upload to TestPyPI first:
```bash
python -m twine upload --repository testpypi dist/ssh_docs-0.1.2*
```

2. Test installation from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ssh-docs==0.1.2
```

3. Verify the package works:
```bash
ssh-docs --help
ssh-docs serve --auth public
```

### Publish to PyPI

Once testing is complete:

```bash
python -m twine upload dist/ssh_docs-0.1.2*
```

### Verify Publication

1. Check the package page: https://pypi.org/project/ssh-docs/
2. Install from PyPI:
```bash
pip install --upgrade ssh-docs
```
3. Verify version:
```bash
ssh-docs --version  # Should show 0.1.2
```

## Post-Release

1. **Tag the release in Git:**
```bash
git tag -a v0.1.2 -m "Release v0.1.2: Enhanced agent documentation"
git push origin v0.1.2
```

2. **Create GitHub Release:**
   - Go to https://github.com/kourgeorge/ssh-docs/releases/new
   - Select tag: v0.1.2
   - Title: "v0.1.2 - Enhanced Agent Documentation"
   - Description:
```markdown
## What's New

- **Better documentation for AI agents**: No-auth mode (`--auth public`) is now prominently featured at the beginning of Quick Start sections
- **Improved agent workflow guidance**: Clear explanation of why public mode is ideal for AI coding agents and local development

## Installation

```bash
pip install --upgrade ssh-docs
```

## Quick Start for Agents

```bash
# Serve with no authentication required
ssh-docs serve ./docs --auth public

# Connect without credentials
ssh localhost -p 2222
```

Perfect for AI coding agents, local development, and quick documentation sharing!
```

3. **Announce the release:**
   - Update project documentation
   - Notify users/contributors
   - Share on relevant platforms

## Troubleshooting

### Build Issues

If you need to rebuild the packages:
```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Rebuild
python -m build
```

### Upload Issues

If upload fails:
- Check your PyPI credentials
- Ensure the version number hasn't been used before
- Verify network connectivity
- Check for any package validation errors

### License Warning

The build shows deprecation warnings about license format. To fix in future releases, update `pyproject.toml`:

```toml
# Change from:
license = {text = "MIT"}

# To:
license = "MIT"

# And remove the classifier:
# "License :: OSI Approved :: MIT License"
```

## Files Ready for Upload

The following files are ready in the `dist/` directory:
- `ssh_docs-0.1.2.tar.gz` - Source distribution
- `ssh_docs-0.1.2-py3-none-any.whl` - Universal wheel

Both files have been successfully built and are ready for upload to PyPI.
