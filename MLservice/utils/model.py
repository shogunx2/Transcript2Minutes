"""
Model loading and inference utilities
"""

import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
import logging
import os

logger = logging.getLogger(__name__)


class SummarizationModel:
    """T5-based summarization model for meeting transcripts (fine-tuned on AMI corpus)"""
    
    def __init__(self, model_name='../MLmodel/models/flan_t5_meeting_minutes', use_finetuned=True):
        """
        Initialize the summarization model
        
        Args:
            model_name: Path to model or base model name from Hugging Face
            use_finetuned: Whether to load fine-tuned model (default: True)
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f'Using device: {self.device}')
        
        # Ensure model_name is a string
        model_name = str(model_name)
        logger.info(f'Loading model from: {model_name}')
        
        try:
            # Check if safetensors file exists
            safetensors_path = os.path.join(model_name, 'model.safetensors')
            if os.path.exists(safetensors_path):
                logger.info(f'Found safetensors model at {safetensors_path}')
                # Need to install safetensors: pip install safetensors
                try:
                    import safetensors
                    logger.info('safetensors library available')
                except ImportError:
                    logger.warning('safetensors not installed, using pytorch format')
            
            # Try to load from local path
            logger.info('Attempting to load tokenizer...')
            self.tokenizer = T5Tokenizer.from_pretrained(model_name, local_files_only=False)
            logger.info('Tokenizer loaded successfully')
            
            logger.info('Attempting to load model...')
            self.model = T5ForConditionalGeneration.from_pretrained(
                model_name,
                local_files_only=False,
                torch_dtype=torch.float32 if str(self.device) == 'cpu' else torch.float16
            )
            logger.info('Model loaded successfully from fine-tuned checkpoint')
            
        except Exception as e:
            logger.warning(f'Could not load from {model_name}: {e}')
            logger.info(f'Falling back to base model: t5-base')
            self.tokenizer = T5Tokenizer.from_pretrained('t5-base')
            self.model = T5ForConditionalGeneration.from_pretrained('t5-base')
        
        self.model.to(self.device)
        self.model.eval()
        logger.info('Model ready for inference')
    
    def summarize(self, text, max_length=250, min_length=50, num_beams=4):
        """
        Summarize the input text
        
        Args:
            text: Input transcript text
            max_length: Maximum length of summary tokens (increased from 150)
            min_length: Minimum length of summary tokens (increased from 30)
            num_beams: Number of beams for beam search
            
        Returns:
            Summary text
        """
        try:
            logger.info(f'Starting summarization for text of length {len(text)} chars')
            
            # Prepare input with summarize task prefix
            input_text = f'summarize: {text}'
            logger.info(f'Input prompt created: {input_text[:100]}...')
            
            inputs = self.tokenizer.encode(input_text, return_tensors='pt', max_length=512, truncation=True)
            logger.info(f'Input tokens shape: {inputs.shape}')
            
            inputs = inputs.to(self.device)
            
            # Generate summary
            logger.info(f'Generating summary with max_length={max_length}, min_length={min_length}, num_beams={num_beams}')
            with torch.no_grad():
                summary_ids = self.model.generate(
                    inputs,
                    max_length=max_length,
                    min_length=min_length,
                    num_beams=num_beams,
                    early_stopping=True,
                    length_penalty=2.0,
                    no_repeat_ngram_size=3
                )
            
            logger.info(f'Summary tokens generated: {summary_ids.shape}')
            
            # Decode summary
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            logger.info(f'Summary generated ({len(summary.split())} words): {summary[:100]}...')
            
            return summary
            
        except Exception as e:
            logger.error(f'Error during summarization: {str(e)}')
            raise


def load_model(model_name='t5-base', use_finetuned=False):
    """Helper function to load the model"""
    return SummarizationModel(model_name=model_name, use_finetuned=use_finetuned)
