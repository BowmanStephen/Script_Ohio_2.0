## Data & Model Asset Security Strategy

To keep the repository lightweight while protecting sensitive artifacts,
Script Ohio now follows the workflow below.

### 1. Separate large binaries

- Track canonical training/model artifacts via GitHub Releases or an
  internal object store.  The suggested layout:
  - `releases/<season>/ridge_model_2025.joblib`
  - `releases/<season>/training_data_weekXX.parquet`
- Use Git LFS **only** for intermediate items that must remain in-tree
  (e.g., baseline ridge model) and keep each file <100 MB.
- Update `docs/DATA_ORGANIZATION.md` whenever a new artifact moves out of
  the repo so analysts know where to fetch it.

### 2. Encrypt at rest

- The helper script `scripts/secure_artifacts.py` wraps the official
  `cryptography` Fernet implementation.
- Generate a key (stored outside git):
  ```bash
  python3 scripts/secure_artifacts.py generate-key > secrets/artifacts.key
  ```
- Encrypt folders such as `models/`, `cache/`, or `outputs/`:
  ```bash
  python3 scripts/secure_artifacts.py encrypt \
      --target models \
      --key-file secrets/artifacts.key
  ```
- Encrypted bundles land in `outputs/secure/` and can be safely synced to an
  S3 bucket or artifact registry.  The same script decrypts them locally.

### 3. CI enforcement

- Dependency scans (`pip-audit`, `safety`, `npm audit`) run on every PR.
- Bandit ensures no accidental plaintext secrets leak into Python modules.
- A follow-up PR can wire `secure_artifacts.py` into release jobs so that
  packaged artifacts are encrypted automatically before upload.

### 4. Operational guardrails

- Never commit generated datasets >5 MB—store them under `outputs/` which is
  already ignored.
- Document any manual data pulls or redacted exports in
  `reports/` with provenance and checksum metadata.
- Rotate CFBD API keys monthly and log rotations under `docs/SECURITY_LOG.md`
  (new file to be created when the first rotation occurs).

