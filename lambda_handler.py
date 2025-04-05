from mangum import Mangum
from config import app
import authentication  # This will initialize the auth routes
from validation import validation_bp

# Register the blueprint
app.register_blueprint(validation_bp)

# Create the Lambda handler
handler = Mangum(app) 