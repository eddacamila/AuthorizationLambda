from mangum import Mangum
from config import app
import authentication  # This initializes the auth routes
from validation import validation_bp

app.register_blueprint(validation_bp)


handler = Mangum(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 