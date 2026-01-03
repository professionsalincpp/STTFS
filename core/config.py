import json
import yaml
from pathlib import Path

from core.parser import FileType

class FSConfig:
    """Конфигурация для генерации файловой системы"""
    
    def __init__(self):
        self.file_contents = {}
        self.templates = {}
        self.defaults = {
            'encoding': 'utf-8',
            'replaceifexists': True,
            'type': FileType.TEXT,
            'permissions': '644',
            'hidden': False,
            'executable': False,
        }
    
    def load_from_file(self, config_path: str):
        """Загрузка конфигурации из файла"""
        path = Path(config_path)
        
        if path.suffix == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        elif path.suffix in ['.yaml', '.yml']:
            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")
        
        self.file_contents = config.get('file_contents', {})
        self.templates = config.get('templates', {})
        self.defaults.update(config.get('defaults', {}))
        
        return self
    
    def load_from_dict(self, config_dict: dict):
        """Загрузка конфигурации из словаря"""
        self.file_contents = config_dict.get('file_contents', {})
        self.templates = config_dict.get('templates', {})
        self.defaults.update(config_dict.get('defaults', {}))
        return self
    
    def get_config(self) -> dict:
        """Получение конфигурации"""
        return {
            'file_contents': self.file_contents,
            'templates': self.templates,
            'defaults': self.defaults,
        }