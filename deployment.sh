# Create and activate a virtual environment (optional but recommended)
python -m venv .venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create deployment directory
mkdir deployment
cp *.py deployment/
cd deployment
pip install -r ../requirements.txt -t .
zip -r ../deployment-package.zip .