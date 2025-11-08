"""
Evaluation metrics utilities
"""

from datasets import load_metric
import logging

logger = logging.getLogger(__name__)


def get_eval_metrics():
    """Load evaluation metrics for summarization"""
    try:
        rouge_metric = load_metric('rouge')
        return {'rouge': rouge_metric}
    except Exception as e:
        logger.warning(f'Could not load metrics: {str(e)}')
        return {}


def compute_metrics(eval_pred, tokenizer):
    """
    Compute ROUGE scores for evaluation
    
    Args:
        eval_pred: EvalPrediction object with predictions and label_ids
        tokenizer: T5 tokenizer
        
    Returns:
        Dictionary of metrics
    """
    predictions, labels = eval_pred
    
    # Decode predictions and labels
    decoded_preds = tokenizer.batch_decode(predictions, skip_special_tokens=True)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    
    # Compute ROUGE
    try:
        rouge = load_metric('rouge')
        result = rouge.compute(
            predictions=decoded_preds,
            references=decoded_labels,
            use_stem=True
        )
        
        return {
            'rouge1': result['rouge1'].mid.fmeasure,
            'rouge2': result['rouge2'].mid.fmeasure,
            'rougeL': result['rougeL'].mid.fmeasure,
        }
    except Exception as e:
        logger.warning(f'Could not compute metrics: {str(e)}')
        return {}
