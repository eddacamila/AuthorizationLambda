python -m venv .venv
source venv/bin/activate

pip install -r requirements.txt

# Create deployment directory
mkdir deployment
cp *.py deployment/
cd deployment
pip install -r ../requirements.txt -t .
zip -r ../deployment-package.zip .