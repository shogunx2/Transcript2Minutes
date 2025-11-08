"""
Inference script to test the fine-tuned model locally
Useful for testing before deploying to MLservice
"""

import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_finetuned_model(model_dir='./models/flan_t5_meeting_minutes'):
    """Load fine-tuned T5 model"""
    logger.info(f'Loading model from {model_dir}')
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    tokenizer = T5Tokenizer.from_pretrained(model_dir)
    model = T5ForConditionalGeneration.from_pretrained(model_dir)
    
    model.to(device)
    model.eval()
    
    logger.info('Model loaded successfully')
    return model, tokenizer, device


def summarize(text, model, tokenizer, device):
    """Summarize text using the model"""
    inputs = tokenizer.encode(f'summarize: {text}', return_tensors='pt', max_length=512, truncation=True)
    inputs = inputs.to(device)
    
    with torch.no_grad():
        summary_ids = model.generate(
            inputs,
            max_length=250,
            min_length=50,
            num_beams=4,
            early_stopping=True,
            length_penalty=2.0,
            no_repeat_ngram_size=3
        )
    
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary


if __name__ == '__main__':
    # Example usage
    model, tokenizer, device = load_finetuned_model()
    
    sample_transcript = """
    John: Good morning everyone. Let's start the weekly sync. First, let's review our sprint progress.
    Sarah: We completed the user authentication module. It's ready for testing.
    Mike: Great! I've been working on the API integration. Should be done by Friday.
    John: Excellent. What about the frontend updates?
    Sarah: The dashboard redesign is 80% complete. We'll have it ready for review by end of week.
    John: Perfect. Let's make sure to test everything thoroughly. We need to fix any bugs before the release.
    Mike: I'll coordinate with QA. We should have time for a full regression test.
    John: Thanks everyone. Let's meet again next week to check progress.
    """
    
    print('Original transcript:')
    print(sample_transcript)
    print('\n' + '='*50 + '\n')
    
    summary = summarize(sample_transcript, model, tokenizer, device)
    
    print('Generated summary:')
    print(summary)
