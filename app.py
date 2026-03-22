"""
app.py — Flask entry point.

Configures logging, registers blueprints, and starts the server.
All route logic lives in api/routes/.
"""

import logging
from flask import Flask
from werkzeug.exceptions import RequestEntityTooLarge

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="ui/templates")

# Blueprints
from api.routes.calculator import calculator_bp
from api.routes.files import files_bp
from api.routes.stats import stats_bp
from api.routes.lab import lab_bp

app.register_blueprint(calculator_bp)
app.register_blueprint(files_bp)
app.register_blueprint(stats_bp)
app.register_blueprint(lab_bp)


@app.errorhandler(RequestEntityTooLarge)
def handle_large_request(e):
    logger.warning("Request entity too large: %s", e)
    return "File too large.", 413


if __name__ == "__main__":
    app.run(debug=True)
