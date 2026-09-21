from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

for env_path in [
    os.path.join(backend_dir, '.env'),
    os.path.join(os.getcwd(), '.env'),
    os.path.join(os.getcwd(), 'backend', '.env'),
]:
    if os.path.exists(env_path):
        load_dotenv(env_path)


def _get_cors_origins():
    configured = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
    origins = [origin.strip() for origin in configured.split(',') if origin.strip()]
    return origins or ['http://localhost:3000']


app = Flask(__name__)
CORS(app, resources={r'/api/*': {'origins': _get_cors_origins()}})
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.path.join(backend_dir, 'uploads')
app.config['JSON_SORT_KEYS'] = False
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

from database import init_db
init_db(app)

from routes import portfolio_routes, upload_routes
app.register_blueprint(portfolio_routes.bp)
app.register_blueprint(upload_routes.bp)

with app.app_context():
    if os.getenv('AUTO_SEED_PORTFOLIO', '1').strip().lower() not in {'0', 'false', 'no'}:
        portfolio_routes.ensure_default_portfolio()


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Crypto Portfolio Analytics API'
    }), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500


if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', '0').lower() in {'1', 'true', 'yes', 'on'}
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5000'))
    print('Starting crypto portfolio backend...')
    app.run(debug=debug_mode, host=host, port=port, use_reloader=False)
