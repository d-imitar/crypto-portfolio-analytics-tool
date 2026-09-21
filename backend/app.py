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

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.path.join(backend_dir, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

from database import init_db
init_db(app)

from routes import portfolio_routes, upload_routes
app.register_blueprint(portfolio_routes.bp)
app.register_blueprint(upload_routes.bp)

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
    print('Starting crypto portfolio backend...')
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
