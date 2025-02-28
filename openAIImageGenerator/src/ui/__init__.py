"""UI components for the OpenAI Image Generator."""

from .tabs.generation_tab import GenerationTab
from .tabs.history_tab import HistoryTab
from .main_window import MainWindow

__all__ = ['MainWindow', 'GenerationTab', 'HistoryTab'] 
