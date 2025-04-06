rm -rf .aws-sam/
rm -rf src/__pycache__/
rm -rf src/*.pyc
rm -rf src/*.so
rm -rf src/*.pyd
# Create a temporary directory for building dependencies
mkdir build_temp
cd build_temp

# Create and activate a new virtual environment
python -m venv venv
source venv/Scripts/activate

# Install dependencies
pip install -r ../src/requirements.txt --target ../src

# Deactivate virtual environment and cleanup
deactivate
cd ..
rm -rf build_temp