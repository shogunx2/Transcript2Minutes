"""
Output formatting utilities to convert raw summaries into structured minutes
"""

import re
import logging

logger = logging.getLogger(__name__)


class MinutesFormatter:
    """Formats raw summaries into structured meeting minutes"""
    
    @staticmethod
    def format_to_bullets(summary_text):
        """
        Return clean summary text without any formatting
        
        Args:
            summary_text: Raw summary text from model
            
        Returns:
            Clean formatted text
        """
        try:
            # Just clean and return as-is
            summary_text = summary_text.strip()
            
            if not summary_text:
                return "No summary generated."
            
            return summary_text
            
        except Exception as e:
            logger.error(f'Error formatting minutes: {str(e)}')
            return summary_text
    
    @staticmethod
    def _split_sentences(text):
        """Split text into sentences"""
        # Simple sentence splitting on periods, question marks, exclamation marks
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return sentences
    
    @staticmethod
    def format_with_structure(summary_text, transcript_text=None):
        """
        Format summary with structured sections (Key Points, Action Items, etc.)
        This is a more sophisticated formatter that attempts to organize content
        
        Args:
            summary_text: Raw summary text from model
            transcript_text: Original transcript (optional, for analysis)
            
        Returns:
            Structured formatted minutes
        """
        try:
            sentences = MinutesFormatter._split_sentences(summary_text)
            
            if not sentences:
                return "No summary generated."
            
            # Group sentences into logical sections
            # For now, simple bullet format - can be enhanced later
            formatted = "Meeting Minutes:\n\n"
            formatted += "Key Points:\n"
            formatted += '\n'.join([f'  • {s.strip()}' for s in sentences if s.strip()])
            
            return formatted
            
        except Exception as e:
            logger.error(f'Error in structured formatting: {str(e)}')
            return summary_text


def format_minutes(summary_text, format_type='bullets', transcript_text=None):
    """
    Helper function to format minutes
    
    Args:
        summary_text: Raw summary from model
        format_type: 'bullets' or 'structured'
        transcript_text: Optional original transcript
        
    Returns:
        Formatted minutes
    """
    formatter = MinutesFormatter()
    
    if format_type == 'structured':
        return formatter.format_with_structure(summary_text, transcript_text)
    else:
        return formatter.format_to_bullets(summary_text)
