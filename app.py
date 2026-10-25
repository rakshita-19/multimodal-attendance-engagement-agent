import os
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from backend.config import Config
from backend.database.db import init_db
from backend.routes import (
    session_bp,
    processing_bp,
    attendance_bp,
    analytics_bp,
    export_bp
)

def create_app(test_config=None) -> Flask:
    """Application factory for the Multimodal Attendance & Engagement Agent."""
    app = Flask(__name__, static_folder="frontend", static_url_path="")
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Load configuration
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH

    if test_config:
        app.config.update(test_config)

    # Ensure required runtime directories
    Config.ensure_directories()

    # Initialize SQLite database schema
    init_db()

    # Register API blueprints
    app.register_blueprint(session_bp)
    app.register_blueprint(processing_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(export_bp)

    # Health check route
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "Multimodal Attendance & Engagement Agent",
            "version": "1.0.0",
            "storage": {
                "db": Config.DATABASE_PATH,
                "upload_dir": str(Config.UPLOAD_FOLDER)
            }
        })

    # Serve Frontend Single-Page Interface
    @app.route("/")
    def serve_frontend_index():
        frontend_dir = Path(__file__).parent / "frontend"
        return send_from_directory(str(frontend_dir), "index.html")

    @app.route("/<path:path>")
    def serve_static_assets(path):
        frontend_dir = Path(__file__).parent / "frontend"
        file_path = frontend_dir / path
        if file_path.exists():
            return send_from_directory(str(frontend_dir), path)
        return send_from_directory(str(frontend_dir), "index.html")

    # Global Error Handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"status": "error", "message": "Resource not found"}), 404

    @app.errorhandler(413)
    def handle_payload_too_large(e):
        return jsonify({
            "status": "error",
            "message": f"Uploaded file exceeds maximum allowed limit of {Config.MAX_CONTENT_LENGTH // (1024 * 1024)}MB"
        }), 413

    @app.errorhandler(500)
    def handle_internal_error(e):
        return jsonify({"status": "error", "message": "Internal server error occurred"}), 500

    return app

app = create_app()

if __name__ == "__main__":
    print(f"Starting Multimodal Classroom Intelligence Server on http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
