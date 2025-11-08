"""
Dataset loading and preprocessing utilities
"""

from datasets import load_dataset
import logging

logger = logging.getLogger(__name__)


def load_samsum_dataset(split='train', sample_size=None):
    """
    Load SAMSum dataset (meeting transcripts and summaries)
    
    Args:
        split: 'train', 'validation', or 'test'
        sample_size: Optional, number of samples to load (for testing)
        
    Returns:
        Dataset object
    """
    logger.info(f'Loading SAMSum dataset ({split} split)')
    
    try:
        dataset = load_dataset('samsum', split=split)
        
        if sample_size:
            dataset = dataset.select(range(min(sample_size, len(dataset))))
            logger.info(f'Using {len(dataset)} samples')
        else:
            logger.info(f'Loaded {len(dataset)} samples')
        
        return dataset
        
    except Exception as e:
        logger.error(f'Failed to load dataset: {str(e)}')
        raise


def preprocess_data(examples, tokenizer, max_input_length=512, max_target_length=150):
    """
    Preprocess dataset examples
    
    Args:
        examples: Dataset examples batch
        tokenizer: T5 tokenizer
        max_input_length: Max length for input tokens
        max_target_length: Max length for target tokens
        
    Returns:
        Tokenized batch
    """
    # Prepare inputs
    inputs = [f'summarize: {ex}' for ex in examples['dialogue']]
    targets = examples['summary']
    
    # Tokenize inputs
    model_inputs = tokenizer(
        inputs,
        max_length=max_input_length,
        truncation=True,
        padding='max_length',
        return_tensors='pt'
    )
    
    # Tokenize targets
    labels = tokenizer(
        targets,
        max_length=max_target_length,
        truncation=True,
        padding='max_length',
        return_tensors='pt'
    )
    
    model_inputs['labels'] = labels['input_ids']
    
    return model_inputs
