"""
Flask backend API for Transcript2Minutes
Handles incoming transcript requests and communicates with MLservice
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
MLSERVICE_URL = os.getenv('MLSERVICE_URL', 'http://localhost:5001')
MAX_TRANSCRIPT_LENGTH = 1500  # words (matches MLservice limit)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        mlservice_response = requests.get(f'{MLSERVICE_URL}/health', timeout=5)
        mlservice_status = 'healthy' if mlservice_response.status_code == 200 else 'unhealthy'
    except:
        mlservice_status = 'unreachable'
    
    return jsonify({
        'status': 'healthy',
        'mlservice': mlservice_status
    })


@app.route('/summarize', methods=['POST'])
def summarize():
    """
    Main endpoint to summarize meeting transcripts
    
    Request JSON:
    {
        "transcript": "meeting transcript text..."
    }
    
    Response JSON:
    {
        "minutes": "formatted minutes as bullet points..."
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'transcript' not in data:
            return jsonify({'error': 'Missing transcript field'}), 400
        
        transcript = data['transcript'].strip()
        
        if not transcript:
            return jsonify({'error': 'Transcript cannot be empty'}), 400
        
        # Check transcript length (rough word count)
        word_count = len(transcript.split())
        if word_count > MAX_TRANSCRIPT_LENGTH:
            return jsonify({
                'error': f'Transcript too long. Maximum {MAX_TRANSCRIPT_LENGTH} words allowed. Got {word_count} words.'
            }), 400
        
        # Forward request to MLservice
        logger.info(f'Sending transcript to MLservice ({word_count} words)')
        response = requests.post(
            f'{MLSERVICE_URL}/summarize',
            json={'transcript': transcript},
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f'MLservice error: {response.text}')
            return jsonify({'error': 'Failed to generate minutes. Please try again.'}), 500
        
        result = response.json()
        logger.info('Successfully generated minutes')
        
        return jsonify(result), 200
        
    except requests.exceptions.ConnectionError:
        logger.error('Cannot connect to MLservice')
        return jsonify({'error': 'MLservice is not available. Please try again later.'}), 503
    except requests.exceptions.Timeout:
        logger.error('MLservice request timeout')
        return jsonify({'error': 'Request timeout. Transcript may be too long.'}), 504
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}')
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Internal server error: {str(error)}')
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    logger.info('Starting Flask backend on http://localhost:5002')
    logger.info(f'MLservice URL: {MLSERVICE_URL}')
    app.run(debug=False, port=5002, host='0.0.0.0')
