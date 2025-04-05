from config import app
from validation import validation_bp

# Register the blueprint
app.register_blueprint(validation_bp)

if __name__ == '__main__':
    app.run(debug=True) 