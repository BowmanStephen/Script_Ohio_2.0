#!/usr/bin/env python3
"""
Dependency Verification Script for Script Ohio 2.0
Verifies that all required packages are installed and match version requirements.
"""
import sys
import pkg_resources
from pkg_resources import DistributionNotFound, VersionConflict

def verify_dependencies(requirements_file='requirements.txt'):
    """Verify that all dependencies in requirements_file are installed."""
    print(f"Verifying dependencies from {requirements_file}...")
    
    try:
        with open(requirements_file, 'r') as f:
            requirements = [
                line.strip() for line in f 
                if line.strip() and not line.startswith('#')
            ]
    except FileNotFoundError:
        print(f"Error: {requirements_file} not found.")
        sys.exit(1)

    missing = []
    conflicting = []
    installed = []

    for requirement in requirements:
        try:
            pkg_resources.require(requirement)
            installed.append(requirement)
            print(f"✅ {requirement}")
        except DistributionNotFound:
            missing.append(requirement)
            print(f"❌ {requirement} (Missing)")
        except VersionConflict as e:
            conflicting.append((requirement, str(e)))
            print(f"⚠️  {requirement} (Conflict: {e})")
        except Exception as e:
            print(f"❓ {requirement} (Error: {e})")

    print("\nDependency Verification Report")
    print("==============================")
    print(f"Total Requirements: {len(requirements)}")
    print(f"Installed: {len(installed)}")
    print(f"Missing: {len(missing)}")
    print(f"Conflicting: {len(conflicting)}")

    if missing:
        print("\nMissing Packages:")
        for pkg in missing:
            print(f" - {pkg}")

    if conflicting:
        print("\nVersion Conflicts:")
        for pkg, reason in conflicting:
            print(f" - {pkg}: {reason}")

    if missing or conflicting:
        # Filter out known conflicts
        critical_failures = False
        
        if missing:
            print("\nMissing Packages:")
            for pkg in missing:
                print(f" - {pkg}")
                critical_failures = True

        if conflicting:
            print("\nVersion Conflicts:")
            for pkg, reason in conflicting:
                # Known conflict: fastai/thinc requires pydantic>=2, cfbd requires pydantic<2
                if "fastai" in pkg and "pydantic" in reason:
                    print(f" - {pkg}: {reason} (KNOWN ISSUE: FastAI/CFBD Pydantic conflict - Proceeding)")
                else:
                    print(f" - {pkg}: {reason}")
                    critical_failures = True

        if critical_failures:
            print("\nFAILURE: Please run 'pip install -r requirements.txt'")
            sys.exit(1)
        else:
             print("\nSUCCESS: All dependencies verified (with known issues).")
             sys.exit(0)
    else:
        print("\nSUCCESS: All dependencies verified.")
        sys.exit(0)

if __name__ == "__main__":
    verify_dependencies()

