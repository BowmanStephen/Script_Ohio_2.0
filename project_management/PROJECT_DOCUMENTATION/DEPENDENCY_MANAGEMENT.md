# Dependency Management Guide

This document explains how dependency management works in Script Ohio 2.0.

## Overview

This project uses `pip-compile` (from `pip-tools`) for dependency management. This approach provides:

- **Reproducible builds**: Locked versions ensure consistent installations
- **Readable source files**: `.in` files are human-readable with version ranges
- **Automatic transitive dependency resolution**: pip-compile includes all dependencies

## File Structure

```
requirements.in           # Source file (edit this)
requirements.txt          # Locked file (generated, commit this)
requirements-dev.in       # Dev source file (edit this)
requirements-dev.txt      # Dev locked file (generated, commit this)
requirements-prod.txt     # Production dependencies (references requirements.txt)
requirements-optional.in  # Optional source file (edit this)
requirements-optional.txt # Optional locked file (generated, commit this)
```

## Workflow

### Installing Dependencies

```bash
# Core dependencies (all users)
pip install -r requirements.txt

# Development dependencies
pip install -r requirements-dev.txt

# Optional dependencies (CFBD API, etc.)
pip install -r requirements-optional.txt
```

### Updating Dependencies

1. **Edit source file**: Modify `requirements.in` (or `requirements-dev.in`)
2. **Regenerate locked file**: Run `pip-compile requirements.in`
3. **Test**: Install and test in fresh environment
4. **Commit**: Commit both `.in` and `.txt` files together

```bash
# Install pip-tools if not already installed
pip install pip-tools

# Update core dependencies
pip-compile requirements.in

# Update dev dependencies
pip-compile requirements-dev.in

# Update optional dependencies
pip-compile requirements-optional.in
```

### Upgrading All Dependencies

```bash
# Upgrade all packages to latest versions
pip-compile --upgrade requirements.in
pip-compile --upgrade requirements-dev.in
```

### Adding a New Dependency

1. Add to appropriate `.in` file:
   ```bash
   # Add to requirements.in
   echo "new-package>=1.0.0" >> requirements.in
   ```
2. Regenerate locked file:
   ```bash
   pip-compile requirements.in
   ```
3. Install and test:
   ```bash
   pip install -r requirements.txt
   ```

## Optional Dependencies

Some dependencies have graceful fallbacks:

- **psutil**: System monitoring (fallback: returns default values, logs warning)
- **fastai**: Deep learning models (fallback: skips neural network training)
- **shap**: Model interpretability (fallback: skips SHAP analysis)
- **cfbd**: CFBD API client (no fallback - install if needed)

When optional dependencies are missing, the code will:
- Log a warning using `logging.warning()`
- Continue execution with reduced functionality
- Return default/empty values where appropriate

## Production Dependencies

`requirements-prod.txt` is used for Docker builds and production deployments. It:
- Includes locked base requirements (`-r requirements.txt`)
- Uses exact versions for reproducibility
- Does NOT include FastAPI/uvicorn (removed - not currently used)

If web API is needed in future:
1. Add FastAPI to `requirements-prod.txt` or create `requirements-prod.in`
2. Create `agents/main.py` or `agents/api.py` with FastAPI app
3. Update Dockerfile CMD

## Version Pinning Strategy

- **Source files (`.in`)**: Use minimum version constraints (`>=`) for flexibility
- **Locked files (`.txt`)**: Exact versions (`==`) for reproducibility
- **Python version**: Constrained in `requirements.in` (`python>=3.13,<3.14`)

## Maintenance

### Monthly Tasks
- Review security vulnerabilities: `safety check` or `pip-audit`
- Check for outdated packages: `pip list --outdated`

### Quarterly Tasks
- Review and update dependencies
- Test in fresh environment
- Update locked files

### Security Response
1. Monitor automated security scans
2. Identify affected packages
3. Update `requirements.in` with patched version
4. Run `pip-compile` to update locked file
5. Test thoroughly
6. Deploy fix promptly

## Troubleshooting

### Dependency Conflicts
```bash
# Check for conflicts
pip check

# If conflicts found, review requirements.in files
# May need to adjust version constraints
```

### Installation Issues
```bash
# Clear pip cache
pip cache purge

# Install in fresh virtual environment
python -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt
```

### Lock File Out of Sync
```bash
# Regenerate all lock files
pip-compile requirements.in
pip-compile requirements-dev.in
pip-compile requirements-optional.in
```

## Best Practices

1. **Always commit both `.in` and `.txt` files together**
2. **Test in fresh environment after updating dependencies**
3. **Review changes in locked files before committing**
4. **Document breaking changes in dependency updates**
5. **Keep optional dependencies truly optional (graceful fallbacks)**

## References

- [pip-tools documentation](https://pip-tools.readthedocs.io/)
- [Python dependency management best practices](https://packaging.python.org/en/latest/guides/tool-recommendations/)

