# Artifact & Cache Policy

Large or sensitive artifacts should be kept out of the core git history and
protected at rest.

## What to Keep Out of Git

- Training data >5MB (use `data/` canonical paths, avoid commits)
- Model binaries (`*.pkl`, `*.joblib`) when possible
- Cache files (`cache/`, `logs/`, `memory/`) and generated predictions/exports

## Recommended Storage Options

1. **Git LFS (preferred for models)**
   - `git lfs install`
   - `git lfs track "*.pkl" "*.joblib" "reports/*.md"` (example)
   - Commit the updated `.gitattributes`
2. **Release Assets**
   - Attach versioned models and reports to GitHub Releases
   - Reference download URLs in `model_pack/README` or scripts
3. **Object Storage**
   - Push nightly artifacts to S3/Blob storage with lifecycle policies

## Encryption at Rest

- Encrypt model and cache files that contain proprietary features or API
  responses:
  - Use `cryptography.Fernet` for symmetric encryption of cached JSON/CSV files
  - Store encryption keys in environment variables (never in git)
  - Example pattern:
    ```python
    from cryptography.fernet import Fernet
    key = os.environ["SCRIPT_OHIO_CACHE_KEY"]
    cipher = Fernet(key)
    encrypted = cipher.encrypt(raw_bytes)
    ```
- Keep `.env` files ignored; rotate keys regularly.

## Operational Checklist

- Before committing, run `git lfs ls-files` to confirm large artifacts are
  tracked or excluded.
- Clean caches: `rm -rf cache/ logs/ memory/ outputs/` before publishing
  branches.
- Document model locations in `model_pack/README` and keep checksums with
  releases for reproducibility.
