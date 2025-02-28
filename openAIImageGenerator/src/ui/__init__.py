"""UI components for the OpenAI Image Generator."""

from .tabs.generation_tab import GenerationTab
from .tabs.history_tab import HistoryTab
from .main_window import MainWindow
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.error_viewer import ErrorReportViewer
from .dialogs.template_dialog import TemplateDialog
from .dialogs.variable_input_dialog import VariableInputDialog

__all__ = [
    'MainWindow', 
    'GenerationTab', 
    'HistoryTab',
    'SettingsDialog',
    'ErrorReportViewer',
    'TemplateDialog',
    'VariableInputDialog'
] 
