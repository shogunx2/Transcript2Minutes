"""
MLservice - Inference server for meeting transcript summarization
Loads the fine-tuned T5 model and provides summarization endpoints
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
from dotenv import load_dotenv
import torch

from utils.model import load_model
from utils.formatter import format_minutes

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
MODEL_PATH = os.getenv('MODEL_PATH', os.path.join(os.path.dirname(__file__), '../MLmodel/models/flan_t5_meeting_minutes'))
MODEL_PATH = str(MODEL_PATH)  # Ensure it's a string
MAX_INPUT_LENGTH = int(os.getenv('MAX_INPUT_LENGTH', '1500'))  # words (reduced from 4000 to avoid truncation)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model instance
model = None


def load_model_on_startup():
    """Load model when the app starts"""
    global model
    try:
        logger.info(f'Loading fine-tuned AMI model from {MODEL_PATH}')
        model = load_model(model_name=MODEL_PATH, use_finetuned=True)
        logger.info('Model loaded successfully')
    except Exception as e:
        logger.error(f'Failed to load model: {str(e)}')
        raise


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model': 'T5 AMI Fine-tuned',
        'device': 'cuda' if torch.cuda.is_available() else 'cpu'
    })


@app.route('/summarize', methods=['POST'])
def summarize():
    """
    Summarize meeting transcript endpoint
    
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
        if model is None:
            return jsonify({'error': 'Model not loaded'}), 503
        
        data = request.get_json()
        
        if not data or 'transcript' not in data:
            return jsonify({'error': 'Missing transcript field'}), 400
        
        transcript = data['transcript'].strip()
        
        if not transcript:
            return jsonify({'error': 'Transcript cannot be empty'}), 400
        
        # Check length
        word_count = len(transcript.split())
        if word_count > MAX_INPUT_LENGTH:
            return jsonify({
                'error': f'Transcript too long. Maximum {MAX_INPUT_LENGTH} words. Got {word_count}.'
            }), 400
        
        logger.info(f'Summarizing transcript ({word_count} words)')
        
        # Generate summary
        summary = model.summarize(transcript)
        logger.info(f'Generated summary: {len(summary.split())} words')
        
        # Format into minutes
        minutes = format_minutes(summary, format_type='bullets')
        
        return jsonify({
            'minutes': minutes,
            'stats': {
                'input_words': word_count,
                'output_words': len(minutes.split())
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error during summarization: {str(e)}')
        return jsonify({'error': 'Failed to generate summary'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Internal error: {str(error)}')
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    load_model_on_startup()
    logger.info('Starting MLservice on http://localhost:5001')
    app.run(debug=False, port=5001, host='0.0.0.0')
