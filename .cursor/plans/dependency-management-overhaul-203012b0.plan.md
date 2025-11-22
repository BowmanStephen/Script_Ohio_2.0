<!-- 203012b0-9d22-491d-bbe0-3c63e60e0815 1370bd1d-917e-4fd6-88bf-b12ea94d63b2 -->
# Dependency Management Overhaul Plan

## Problem Statement

The project currently lacks proper dependency management infrastructure:

- No `requirements.txt` in root (Dockerfile expects it)
- `.gitignore` missing `.venv/`, `.mypy_cache/`, `.pytest_cache/`
- Dependencies scattered across documentation
- Production requirements file exists but contains unused dependencies
- Dockerfile references FastAPI/uvicorn but they're not actually used in codebase
- No clear separation between core, dev, and production dependencies

## Analysis Summary

**Actually Used Dependencies:**

- Core: pandas, numpy, scikit-learn, joblib, matplotlib, seaborn, jupyter
- ML: xgboost, fastai (optional with fallback), shap (optional with fallback)
- Agent System: pydantic
- Optional: psutil (graceful fallback), cfbd (optional API client)
- Testing: pytest, pytest-cov, pytest-mock

**Referenced But Not Used:**

- FastAPI, uvicorn, gunicorn (Dockerfile references `agents.main:app` which doesn't exist)
- Many production dependencies in `PRODUCTION_REQUIREMENTS.txt` (redis, postgres, celery, etc.)

## Implementation Plan

### Phase 1: Create Core Requirements Files

**1.1 Create `requirements.txt` (Root - Core Dependencies)**

- Location: `/requirements.txt`
- Purpose: Base dependencies needed for all users
- Contents:
  - Data/ML: pandas, numpy, scikit-learn, joblib, matplotlib, seaborn, jupyter
  - ML Models: xgboost, fastai, shap
  - Agent System: pydantic
  - Optional with fallback: psutil
- Strategy: Use minimum version constraints (>=) for flexibility
- Notes: FastAI may have Python version constraints

**1.2 Create `requirements-dev.txt` (Development Dependencies)**

- Location: `/requirements-dev.txt`
- Purpose: Development and testing tools
- Contents:
  - Include base: `-r requirements.txt`
  - Testing: pytest, pytest-cov, pytest-mock
  - Code Quality: mypy, black (optional), flake8 (optional)
- Strategy: Extends base requirements

**1.3 Create `requirements-prod.txt` (Production Dependencies)**

- Location: `/requirements-prod.txt`
- Purpose: Production deployment (for Docker)
- Contents:
  - Include base: `-r requirements.txt`
  - Web Server: fastapi, uvicorn[standard], gunicorn (if web API needed)
  - OR: Minimal production setup if no web API
- Strategy: Decision needed on FastAPI inclusion

**1.4 Create `requirements-optional.txt` (Optional Extras)**

- Location: `/requirements-optional.txt`
- Purpose: Optional features that enhance functionality
- Contents:
  - CFBD API: cfbd
  - Enhanced monitoring: (if needed)
- Strategy: Document but don't require

### Phase 2: Update .gitignore

**2.1 Add Missing Cache Directories**

- Add `.venv/` (virtual environment)
- Add `.mypy_cache/` (mypy type checking cache)
- Add `.pytest_cache/` (pytest cache)
- Add `.coverage` and `htmlcov/` (coverage reports)
- Add `.dmypy.json` and `dmypy.json` (mypy daemon)

**2.2 Organize .gitignore Sections**

- Group related entries
- Add comments for clarity
- Ensure no conflicts with existing patterns

### Phase 3: Dependency Analysis & Cleanup

**3.1 Audit Production Requirements File**

- Review `project_management/STRATEGIC_PLANNING/PRODUCTION_REQUIREMENTS.txt`
- Identify which dependencies are actually used
- Document unused dependencies for future reference
- Decide: Keep as "future production" reference or remove

**3.2 Resolve FastAPI/Web Server Question**

- Option A: Remove FastAPI references (project is library, not web service)
- Option B: Add minimal FastAPI setup for future API endpoints
- Option C: Mark as optional for future use
- Decision needed: Check if web API is planned

**3.3 Document Optional Dependencies**

- Clearly mark dependencies with graceful fallbacks (psutil, fastai, shap)
- Document what features are disabled when optional deps missing
- Add installation notes in README/AGENTS.md

### Phase 4: Update Documentation

**4.1 Update AGENTS.md**

- Replace manual pip install commands with `pip install -r requirements.txt`
- Add section on optional dependencies
- Update setup instructions to use requirements files

**4.2 Update Dockerfile (if needed)**

- Align with actual requirements files
- Remove FastAPI references if not used
- OR: Add minimal FastAPI setup if needed

**4.3 Update Other Documentation**

- Update `model_pack/QUICK_START_AGENT_SYSTEM.md`
- Update `documentation/technical/deployment_guide.md`
- Ensure consistency across all setup guides

### Phase 5: Validation & Testing

**5.1 Test Requirements Installation**

- Create fresh virtual environment
- Test `pip install -r requirements.txt`
- Test `pip install -r requirements-dev.txt`
- Verify all imports work

**5.2 Test Optional Dependencies**

- Test graceful fallback when psutil not installed
- Test graceful fallback when fastai not installed
- Test graceful fallback when shap not installed

**5.3 Verify .gitignore**

- Ensure cache directories are ignored
- Test that .venv is ignored
- Verify no important files are accidentally ignored

**5.4 Docker Build Test (if applicable)**

- Test Docker build with new requirements files
- Verify production requirements work
- Check for any missing dependencies

## File Structure After Implementation

```
/
├── requirements.txt          # Core dependencies (NEW)
├── requirements-dev.txt      # Development dependencies (NEW)
├── requirements-prod.txt     # Production dependencies (NEW)
├── requirements-optional.txt # Optional extras (NEW)
├── .gitignore               # Updated with cache dirs
└── project_management/
    └── STRATEGIC_PLANNING/
        └── PRODUCTION_REQUIREMENTS.txt  # Keep as reference or archive
```

## Decision Points

1. **FastAPI/Web Server**: Should we include FastAPI in requirements-prod.txt even though it's not currently used?

   - Recommendation: Include as optional or remove from Dockerfile

2. **Production Requirements File**: Keep the extensive production requirements file?

   - Recommendation: Keep as reference but don't use for actual installation

3. **Version Pinning**: Use exact versions (==) or minimum versions (>=)?

   - Recommendation: Minimum versions (>=) for flexibility, exact versions in production

4. **Python Version Constraints**: Add Python version markers?

   - Recommendation: Yes, for packages that require specific Python versions

## Success Criteria

- ✅ `requirements.in` and `requirements.txt` exist (source + locked)
- ✅ `requirements-dev.in` and `requirements-dev.txt` exist
- ✅ `requirements-prod.txt` has exact versions for reproducibility
- ✅ `.gitignore` properly excludes all cache directories, .env files, logs
- ✅ Documentation updated to reference requirements files and pip-compile workflow
- ✅ Fresh environment can be set up with single command: `pip install -r requirements.txt`
- ✅ Docker build works with requirements-prod.txt
- ✅ All existing functionality still works after dependency changes
- ✅ Optional dependencies have graceful fallbacks with proper logging
- ✅ CI/CD includes dependency validation (if applicable)
- ✅ `pip check` passes with no conflicts
- ✅ Security scan (safety/pip-audit) passes or documents known issues
- ✅ Test suite passes with new dependency setup

## Risk Mitigation

- Test in fresh virtual environment before committing
- Keep existing documentation as backup
- Version control all changes for easy rollback
- Document any breaking changes in dependency versions
- Test optional dependency fallbacks thoroughly
- Verify Docker build before merging
- Run full test suite after dependency changes
- Keep production requirements file as reference for future features
- Document upgrade process for future maintenance

## Future Enhancements (Post-Implementation)

- Consider migrating to `pyproject.toml` with poetry or setuptools
- Set up automated dependency update PRs (Dependabot, Renovate)
- Add dependency license scanning
- Create dependency update schedule (monthly/quarterly reviews)
- Document process for handling security vulnerabilities
- Consider dependency vulnerability monitoring service