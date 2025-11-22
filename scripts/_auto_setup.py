import subprocess
import sys
import pkg_resources

def check_and_install_dependencies():
    """
    Checks for required dependencies and installs them if missing.
    Uses requirements.txt as the source of truth.
    """
    requirements_path = 'requirements.txt'
    
    try:
        with open(requirements_path, 'r') as f:
            requirements = [
                line.strip() for line in f 
                if line.strip() and not line.startswith('#')
            ]
    except FileNotFoundError:
        print(f"Warning: {requirements_path} not found. Skipping dependency check.")
        return

    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = []

    for requirement in requirements:
        # Parse requirement to get package name (ignoring version constraints for simple check)
        # This is a basic check; for robust version checking, we'd use packaging.requirements
        pkg_name = requirement.split('>')[0].split('<')[0].split('=')[0].strip().lower()
        if pkg_name not in installed:
            missing.append(requirement)

    if missing:
        print(f"Missing dependencies found: {', '.join(missing)}")
        print("Installing missing dependencies...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])
            print("Dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e}")
            sys.exit(1)
    else:
        print("All dependencies are satisfied.")

if __name__ == "__main__":
    check_and_install_dependencies()
