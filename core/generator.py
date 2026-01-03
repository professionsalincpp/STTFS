import os
import re
from typing import Dict, Any, List
from datetime import datetime
from core.parser import *

class InteractiveFSGenerator:
    def __init__(self, base_path: str = ".", config: Dict[str, Any] = None):
        self.base_path = base_path
        self.config = config or {}
        self.variables = {}
        self.file_contents = self.config.get('file_contents', {})
        self.templates = self.config.get('templates', {})
        
        # Add system variables
        self.variables['date'] = datetime.now().strftime("%Y-%m-%d")
        self.variables['time'] = datetime.now().strftime("%H:%M:%S")
    
    def generate(self, nodes: List[ASTNode]):
        os.makedirs(self.base_path, exist_ok=True)
        
        print("Starting file system generation...")
        
        for node in nodes:
            self._generate_node(node, self.base_path)
        
        print("Generation completed successfully!")
    
    def _generate_node(self, node: ASTNode, current_path: str):
        if isinstance(node, FolderNode):
            self._generate_folder(node, current_path)
        elif isinstance(node, FileNode):
            self._generate_file(node, current_path)
        elif isinstance(node, ForLoopNode):
            self._generate_for_loop(node, current_path)
        elif isinstance(node, OutputNode):
            self._generate_output(node)
        elif isinstance(node, InputNode):
            self._generate_input(node)
    
    def _generate_output(self, node: OutputNode):
        message = self._apply_template_vars(node.message, self.variables)
        print(message, end='')
    
    def _generate_input(self, node: InputNode):
        value = input()
        self.variables[node.variable] = value
    
    def _generate_folder(self, node: FolderNode, current_path: str):
        folder_name = self._apply_template_vars(node.name, self.variables)
        path = os.path.join(current_path, folder_name)
        
        self._create_folder(path, node.attributes)
        
        for child in node.children:
            self._generate_node(child, path)
    
    def _create_folder(self, path: str, attributes: Dict[str, Any]):
        hidden = attributes.get('hidden', False)
        permissions = attributes.get('permissions', '755')
        
        os.makedirs(path, exist_ok=True)
        
        if hidden and os.name == 'nt':
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(path, 2)
        
        if os.name != 'nt':
            try:
                os.chmod(path, int(permissions, 8))
            except:
                pass
        
        print(f"Created folder: {path}")
    
    def _generate_file(self, node: FileNode, current_path: str):
        file_name = self._apply_template_vars(node.name, self.variables)
        path = os.path.join(current_path, file_name)
        
        content = self._get_file_content(node, file_name)
        content = self._apply_template_vars(content, self.variables)
        
        self._create_file(path, content, node.attributes)
    
    def _get_file_content(self, node: FileNode, file_name: str) -> str:
        if 'content' in node.attributes:
            return str(node.attributes['content'])
        
        if 'template' in node.attributes:
            template_name = node.attributes['template']
            if template_name in self.templates:
                return self.templates[template_name]
        
        if file_name in self.file_contents:
            return self.file_contents[file_name]
        
        for pattern, content in self.file_contents.items():
            if re.match(pattern, file_name):
                return content
        
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
        replace_if_exists = attributes.get('replaceifexists', True)
        if os.path.exists(path) and not replace_if_exists:
            print(f"\033[1;31m!  Skipped existing file: {path}")
            return
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        encoding = attributes.get('encoding', 'utf-8')
        file_type = attributes.get('type', FileType.TEXT)
        
        if file_type == FileType.BINARY:
            mode = 'wb'
            content = content.encode(encoding) if isinstance(content, str) else content
        else:
            mode = 'w'
        
        with open(path, mode, encoding=None if file_type == FileType.BINARY else encoding) as f:
            f.write(content)
        
        self._apply_file_attributes(path, attributes)
        
        print(f"Created file: {path} ({file_type.value}, encoding: {encoding})")
    
    def _apply_file_attributes(self, path: str, attributes: Dict[str, Any]):
        hidden = attributes.get('hidden', False)
        if hidden and os.name == 'nt':
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(path, 2)
        
        permissions = attributes.get('permissions')
        if permissions and os.name != 'nt':
            try:
                os.chmod(path, int(str(permissions), 8))
            except:
                pass
        
        executable = attributes.get('executable', False)
        if executable and os.name != 'nt':
            import stat
            st = os.stat(path)
            os.chmod(path, st.st_mode | stat.S_IEXEC)
    
    def _generate_for_loop(self, node: ForLoopNode, current_path: str):
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
        
        i = node.start
        while condition_func(i):
            values.append(i)
            i += node.step
        
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