"""Skillora application factory."""

import os
from flask import Flask


def create_app(test_config=None):
    """Create and configure the Skillora Flask application.

    Args:
        test_config: Optional dictionary of config overrides for testing.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        # Load default development configuration
        app.config.from_object('config.DevelopmentConfig')
    else:
        # Apply test configuration
        app.config.update(test_config)

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize database
    import db
    db.init_app(app)

    # Register blueprints
    import auth
    app.register_blueprint(auth.bp)

    import main
    app.register_blueprint(main.bp)

    import assessment
    app.register_blueprint(assessment.bp)

    import roadmap
    app.register_blueprint(roadmap.bp)

    import analytics
    app.register_blueprint(analytics.bp)

    return app




if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
