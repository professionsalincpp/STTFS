import os
import json
import yaml
import re
from typing import Dict, Any, List
from datetime import datetime
from core.parser.parser import *

class FileSystemGenerator:
    def __init__(self, base_path: str = ".", config: Dict[str, Any] = None):
        self.base_path = base_path
        self.config = config or {}
        self.variables = {}
        self.file_contents = self.config.get('file_contents', {})
        self.templates = self.config.get('templates', {})
    
    def generate(self, nodes: List[ASTNode]):
        os.makedirs(self.base_path, exist_ok=True)
        
        for node in nodes:
            self._generate_node(node, self.base_path)
    
    def _generate_node(self, node: ASTNode, current_path: str):
        if isinstance(node, FolderNode):
            self._generate_folder(node, current_path)
        elif isinstance(node, FileNode):
            self._generate_file(node, current_path)
        elif isinstance(node, ForLoopNode):
            self._generate_for_loop(node, current_path)
    
    def _generate_folder(self, node: FolderNode, current_path: str):
        # Применяем шаблонные переменные к имени
        folder_name = self._apply_template_vars(node.name, self.variables)
        path = os.path.join(current_path, folder_name)
        
        # Создаем папку с атрибутами
        self._create_folder(path, node.attributes)
        
        # Рекурсивная генерация содержимого
        for child in node.children:
            self._generate_node(child, path)
    
    def _create_folder(self, path: str, attributes: Dict[str, Any]):
        # Основные атрибуты
        hidden = attributes.get('hidden', False)
        permissions = attributes.get('permissions', '755')
        
        # Создаем папку
        os.makedirs(path, exist_ok=True)
        
        # Применяем атрибуты
        if hidden and os.name == 'nt':  # Windows
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(path, 2)  # FILE_ATTRIBUTE_HIDDEN
        
        # Устанавливаем права доступа (Unix)
        if os.name != 'nt':
            try:
                os.chmod(path, int(permissions, 8))
            except:
                pass
        
        print(f"📁 Создана папка: {path}")
    
    def _generate_file(self, node: FileNode, current_path: str):
        # Применяем шаблонные переменные к имени
        file_name = self._apply_template_vars(node.name, self.variables)
        path = os.path.join(current_path, file_name)
        
        # Получаем содержимое файла
        content = self._get_file_content(node, file_name)
        
        # Применяем шаблонные переменные к содержимому
        content = self._apply_template_vars(content, self.variables)
        
        # Создаем файл с атрибутами
        self._create_file(path, content, node.attributes)
    
    def _get_file_content(self, node: FileNode, file_name: str) -> str:
        # 1. Проверяем атрибут content
        if 'content' in node.attributes:
            return str(node.attributes['content'])
        
        # 2. Проверяем атрибут template
        if 'template' in node.attributes:
            template_name = node.attributes['template']
            if template_name in self.templates:
                return self.templates[template_name]
        
        # 3. Проверяем глобальную конфигурацию файлов
        if file_name in self.file_contents:
            return self.file_contents[file_name]
        
        # 4. Проверяем паттерн имени файла
        for pattern, content in self.file_contents.items():
            if re.match(pattern, file_name):
                return content
        
        # 5. Возвращаем содержимое по умолчанию
        file_type = node.attributes.get('type', FileType.TEXT)
        
        defaults = {
            FileType.TEXT: f"# File: {file_name}\n# Created: {datetime.now()}\n",
            FileType.JSON: '{\n  "name": "' + file_name + '"\n}\n',
            FileType.YAML: f"# {file_name}\ncreated: {datetime.now().isoformat()}\n",
            FileType.XML: f'<?xml version="1.0"?>\n<root>\n  <file>{file_name}</file>\n</root>\n',
            FileType.BINARY: ""
        }
        
        return defaults.get(file_type, "")
    
    def _create_file(self, path: str, content: str, attributes: Dict[str, Any]):
        # Проверяем атрибут replaceifexists
        replace_if_exists = attributes.get('replaceifexists', True)
        if os.path.exists(path) and not replace_if_exists:
            print(f"⚠️  Пропущен существующий файл: {path}")
            return
        
        # Создаем директорию если нужно
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Получаем кодировку
        encoding = attributes.get('encoding', 'utf-8')
        
        # Получаем тип файла
        file_type = attributes.get('type', FileType.TEXT)
        
        # Записываем файл
        if file_type == FileType.BINARY:
            mode = 'wb'
            content = content.encode(encoding) if isinstance(content, str) else content
        else:
            mode = 'w'
        
        with open(path, mode, encoding=None if file_type == FileType.BINARY else encoding) as f:
            f.write(content)
        
        # Применяем атрибуты
        self._apply_file_attributes(path, attributes)
        
        print(f"📄 Создан файл: {path} ({file_type.value}, кодировка: {encoding})")
    
    def _apply_file_attributes(self, path: str, attributes: Dict[str, Any]):
        # Скрытый файл (Windows)
        hidden = attributes.get('hidden', False)
        if hidden and os.name == 'nt':
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(path, 2)
        
        # Права доступа (Unix)
        permissions = attributes.get('permissions')
        if permissions and os.name != 'nt':
            try:
                os.chmod(path, int(str(permissions), 8))
            except:
                pass
        
        # Исполняемый файл (Unix)
        executable = attributes.get('executable', False)
        if executable and os.name != 'nt':
            import stat
            st = os.stat(path)
            os.chmod(path, st.st_mode | stat.S_IEXEC)
    
    def _generate_for_loop(self, node: ForLoopNode, current_path: str):
        # Вычисляем диапазон значений
        values = []
        
        if node.condition == '<':
            condition_func = lambda x: x < node.end
        elif node.condition == '<=':
            condition_func = lambda x: x <= node.end
        elif node.condition == '>':
            condition_func = lambda x: x > node.end
        elif node.condition == '>=':
            condition_func = lambda x: x >= node.end
        else:
            condition_func = lambda x: x != node.end
        
        # Генерируем значения
        i = node.start
        while condition_func(i):
            values.append(i)
            i += node.step
        
        # Для каждого значения генерируем дочерние элементы
        for value in values:
            old_value = self.variables.get(node.var_name)
            self.variables[node.var_name] = str(value)
            
            for child in node.children:
                self._generate_node(child, current_path)
            
            if old_value is not None:
                self.variables[node.var_name] = old_value
            else:
                del self.variables[node.var_name]
    
    def _apply_template_vars(self, text: str, variables: Dict[str, str]) -> str:
        if not variables:
            return text
        
        result = text
        for var_name, var_value in variables.items():
            pattern = r'\$\{' + re.escape(var_name) + r'\}'
            result = re.sub(pattern, str(var_value), result)
        
        return result