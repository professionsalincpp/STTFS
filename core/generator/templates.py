from .generator import *

class TemplateEngine:
    """Движок шаблонов для более сложных подстановок"""
    
    @staticmethod
    def render(template: str, context: Dict[str, Any]) -> str:
        """Рендеринг шаблона с контекстом"""
        import re
        
        # Подстановка переменных ${var}
        for key, value in context.items():
            placeholder = r'\$\{' + re.escape(str(key)) + r'\}'
            template = re.sub(placeholder, str(value), template)
        
        # Условные блоки {if condition}...{endif}
        template = TemplateEngine._process_conditionals(template, context)
        
        # Циклы {for item in list}...{endfor}
        template = TemplateEngine._process_loops(template, context)
        
        return template
    
    @staticmethod
    def _process_conditionals(template: str, context: Dict[str, Any]) -> str:
        """Обработка условных блоков"""
        import re
        
        pattern = r'\{if\s+([^}]+)\}(.*?)\{endif\}'
        
        def replace_if(match):
            condition = match.group(1).strip()
            content = match.group(2)
            
            # Простая проверка условия
            try:
                # Заменяем переменные в условии
                for key, value in context.items():
                    condition = condition.replace(key, str(value))
                
                # Вычисляем условие
                if eval(condition, {"__builtins__": {}}, {}):
                    return content
                else:
                    return ""
            except:
                return match.group(0)  # В случае ошибки оставляем как есть
        
        return re.sub(pattern, replace_if, template, flags=re.DOTALL)
    
    @staticmethod
    def _process_loops(template: str, context: Dict[str, Any]) -> str:
        """Обработка циклов в шаблонах"""
        import re
        
        pattern = r'\{for\s+(\w+)\s+in\s+([^}]+)\}(.*?)\{endfor\}'
        
        def replace_for(match):
            var_name = match.group(1)
            list_expr = match.group(2).strip()
            content = match.group(3)
            
            # Получаем список из контекста
            if list_expr in context:
                items = context[list_expr]
            else:
                # Пытаемся вычислить выражение
                try:
                    items = eval(list_expr, {"__builtins__": {}}, context)
                except:
                    return match.group(0)
            
            # Генерируем содержимое для каждого элемента
            result_parts = []
            for item in items:
                local_context = context.copy()
                local_context[var_name] = item
                # Рекурсивно обрабатываем вложенные шаблоны
                rendered = TemplateEngine.render(content, local_context)
                result_parts.append(rendered)
            
            return ''.join(result_parts)
        
        return re.sub(pattern, replace_for, template, flags=re.DOTALL)

class AdvancedFileSystemGenerator(FileSystemGenerator):
    """Расширенный генератор с поддержкой шаблонов"""
    
    def _generate_file(self, node: FileNode, current_path: str):
        """Расширенная генерация файла с поддержкой шаблонов"""
        # Рендерим имя файла
        file_name = TemplateEngine.render(node.name, self.variables)
        path = os.path.join(current_path, file_name)
        
        # Проверяем атрибуты
        replace_if_exists = node.attributes.get('replaceifexists', True)
        if os.path.exists(path) and not replace_if_exists:
            if self.verbose:
                print(f"⚠️  Пропущен существующий файл: {path}")
            return
        
        # Создаем директорию если нужно
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Рендерим содержимое с помощью шаблонного движка
        content = TemplateEngine.render(node.content, self.variables)
        
        # Получаем кодировку
        encoding = node.attributes.get('encoding', 'utf-8')
        
        # Записываем файл
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        
        if self.verbose:
            print(f"📄 Создан файл: {path} (кодировка: {encoding})")