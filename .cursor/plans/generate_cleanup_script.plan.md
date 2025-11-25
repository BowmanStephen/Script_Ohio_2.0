## Objective
- Provide a reusable cleanup script that safely removes non-essential files and directories identified in the repository assessment, while supporting dry-run verification.

## Steps
1. Analyze repository structure to confirm current locations of removable items (e.g., `archive/`, `backup/`, `model_pack copy/`, `temp/`, legacy week14 agents).
2. Implement `scripts/cleanup_repository.py` that:
   - Defines allowlisted directory/file removal targets grouped by severity.
   - Accepts `--dry-run` (default) and `--apply` flags.
   - Logs skipped paths if missing and prevents accidental deletion outside workspace.
3. Add usage instructions and verification guidance in README snippet or separate doc section, including how to run dry runs and extend the allowlist.

## Notes
- Use Python 3.13+ with `pathlib` and `argparse`.
- Ensure script respects `.gitignore`? (n/a) but should avoid deleting essential directories (`agents/`, `scripts/`, `model_pack/`, etc.).
- Plan to test via `python scripts/cleanup_repository.py --dry-run`.

