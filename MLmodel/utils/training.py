"""
Training utilities and callbacks
"""

import logging
from transformers import Seq2SeqTrainingArguments, Seq2SeqTrainer, DataCollatorForSeq2Seq
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch

logger = logging.getLogger(__name__)


def create_training_arguments(output_dir, num_train_epochs, learning_rate, batch_size, **kwargs):
    """
    Create training arguments for T5 fine-tuning
    
    Args:
        output_dir: Output directory for checkpoints
        num_train_epochs: Number of training epochs
        learning_rate: Learning rate
        batch_size: Training batch size
        **kwargs: Additional arguments
        
    Returns:
        Seq2SeqTrainingArguments object
    """
    return Seq2SeqTrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        num_train_epochs=num_train_epochs,
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        warmup_steps=kwargs.get('warmup_steps', 500),
        weight_decay=kwargs.get('weight_decay', 0.01),
        gradient_accumulation_steps=kwargs.get('gradient_accumulation_steps', 1),
        logging_dir=kwargs.get('logging_dir', './logs'),
        logging_steps=100,
        save_steps=500,
        save_total_limit=3,
        eval_strategy='steps',
        eval_steps=500,
        load_best_model_at_end=True,
        metric_for_best_model='eval_loss',
        greater_is_better=False,
        fp16=kwargs.get('fp16', False),
        dataloader_num_workers=kwargs.get('num_workers', 4),
        seed=kwargs.get('seed', 42),
        report_to=['tensorboard'],
    )


def create_trainer(model, tokenizer, train_dataset, eval_dataset, training_args, **kwargs):
    """
    Create a Seq2SeqTrainer for T5 training
    
    Args:
        model: T5 model
        tokenizer: T5 tokenizer
        train_dataset: Training dataset
        eval_dataset: Evaluation dataset
        training_args: Training arguments
        **kwargs: Additional arguments
        
    Returns:
        Trainer object
    """
    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)
    
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )
    
    return trainer


def get_device():
    """Get the device (GPU or CPU)"""
    if torch.cuda.is_available():
        device = torch.device('cuda')
        logger.info(f'Using GPU: {torch.cuda.get_device_name(0)}')
    else:
        device = torch.device('cpu')
        logger.info('Using CPU')
    
    return device
