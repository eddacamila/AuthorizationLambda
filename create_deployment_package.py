import os
import shutil
import subprocess
from pathlib import Path

def create_deployment_package():
    # Create a deployment directory
    deployment_dir = Path('deployment')
    if deployment_dir.exists():
        shutil.rmtree(deployment_dir)
    deployment_dir.mkdir()

    # Copy source files
    src_dir = Path('src')
    for file in src_dir.glob('*.py'):
        shutil.copy2(file, deployment_dir)

    # Install dependencies to deployment directory
    subprocess.run([
        'pip', 'install',
        '-r', str(src_dir / 'requirements.txt'),
        '--target', str(deployment_dir)
    ])

    # Create a zip file
    shutil.make_archive('lambda_deployment_package', 'zip', deployment_dir)
    
    # Clean up
    shutil.rmtree(deployment_dir)
    
    print("Deployment package created: lambda_deployment_package.zip")

if __name__ == '__main__':
    create_deployment_package() 