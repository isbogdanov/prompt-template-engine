"""
This module makes the PromptBuilder class directly accessible from the
utils.prompt_engine package, allowing for a cleaner import statement:

from utils.prompt_engine import PromptBuilder
"""

from .builder import PromptBuilder

__all__ = ["PromptBuilder"]
