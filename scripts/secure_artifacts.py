#!/usr/bin/env python3
"""
Utility for encrypting and decrypting model/data artifacts.

Usage examples:
  python3 scripts/secure_artifacts.py generate-key > secrets/artifacts.key
  python3 scripts/secure_artifacts.py encrypt --target models --key-file secrets/artifacts.key
  python3 scripts/secure_artifacts.py decrypt --bundle outputs/secure/models_20251124T1030.zip.enc \
      --key-file secrets/artifacts.key --output-dir restored_models
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from cryptography.fernet import Fernet


def _load_key(key_file: Path) -> bytes:
    key = key_file.read_text(encoding="utf-8").strip().encode("utf-8")
    return key


def _generate_bundle_name(target: Path) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"{target.name}_{timestamp}"


def generate_key() -> None:
    sys.stdout.write(Fernet.generate_key().decode("utf-8"))


def encrypt(target: Path, key_file: Path, output_dir: Path) -> Path:
    if not target.exists():
        raise FileNotFoundError(f"Target {target} does not exist")

    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_name = _generate_bundle_name(target)
    key = _load_key(key_file)
    cipher = Fernet(key)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        if target.is_dir():
            archive_str = shutil.make_archive(
                str(tmp_path / bundle_name),
                "zip",
                root_dir=target.parent,
                base_dir=target.name,
            )
            archive_path = Path(archive_str)
        else:
            archive_path = tmp_path / f"{target.stem}.zip"
            with ZipFile(archive_path, "w") as bundle:
                bundle.write(target, arcname=target.name)

        encrypted = cipher.encrypt(archive_path.read_bytes())
        bundle_path = output_dir / f"{bundle_name}.zip.enc"
        bundle_path.write_bytes(encrypted)
        return bundle_path


def decrypt(bundle: Path, key_file: Path, output_dir: Path) -> Path:
    if not bundle.exists():
        raise FileNotFoundError(f"Bundle {bundle} not found")

    output_dir.mkdir(parents=True, exist_ok=True)
    key = _load_key(key_file)
    cipher = Fernet(key)
    decrypted = cipher.decrypt(bundle.read_bytes())

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_zip = Path(tmpdir) / "artifact.zip"
        tmp_zip.write_bytes(decrypted)
        shutil.unpack_archive(str(tmp_zip), extract_dir=output_dir)
    return output_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Encrypt/decrypt model and cache artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("generate-key", help="Emit a new Fernet key to stdout.")

    encrypt_parser = subparsers.add_parser("encrypt", help="Encrypt a file or directory into outputs/secure.")
    encrypt_parser.add_argument("--target", required=True, type=Path, help="File or directory to encrypt.")
    encrypt_parser.add_argument("--key-file", required=True, type=Path, help="Path to a file containing the Fernet key.")
    encrypt_parser.add_argument("--output-dir", default=Path("outputs/secure"), type=Path)

    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt an encrypted bundle.")
    decrypt_parser.add_argument("--bundle", required=True, type=Path, help="Encrypted .enc file.")
    decrypt_parser.add_argument("--key-file", required=True, type=Path)
    decrypt_parser.add_argument("--output-dir", required=True, type=Path, help="Destination directory for decrypted data.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "generate-key":
        generate_key()
        return

    if args.command == "encrypt":
        bundle_path = encrypt(args.target, args.key_file, args.output_dir)
        print(f"Encrypted bundle written to {bundle_path}")
        return

    if args.command == "decrypt":
        decrypt(args.bundle, args.key_file, args.output_dir)
        print(f"Bundle decrypted into {args.output_dir}")
        return

    parser.error(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()

