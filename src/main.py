from src.config import app
from src.validation import validation_bp

app.register_blueprint(validation_bp)

if __name__ == '__main__':
    app.run(debug=True) 