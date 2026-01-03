import argparse
import sys

from core.config import FSConfig
from core.generator.generator import FileSystemGenerator
from core.parser.lexer import Lexer
from core.parser.parser import *

class FSBuilderCLI:
    """Интерфейс командной строки"""
    
    @staticmethod
    def build_from_dsl(dsl_text: str, output_dir: str = ".", config_file: str = None):
        """Построение из DSL текста"""
        
        # Загрузка конфигурации
        config = {}
        if config_file:
            fs_config = FSConfig()
            fs_config.load_from_file(config_file)
            config = fs_config.get_config()
        
        # Лексический анализ
        lexer = Lexer(dsl_text)
        tokens = lexer.tokenize()
        
        # Парсинг
        parser = Parser(tokens)
        ast_nodes = parser.parse()
        
        # Генерация
        generator = FileSystemGenerator(output_dir, config)
        generator.generate(ast_nodes)
        
        return {
            'tokens': tokens,
            'ast': ast_nodes,
            'output_dir': output_dir
        }
    
    @staticmethod
    def main():
        parser = argparse.ArgumentParser(description='Build file system from DSL')
        
        # Основные параметры
        parser.add_argument('input', help='Input sttfs file')
        parser.add_argument('-o', '--output', default='.', help='Output directory')
        parser.add_argument('-c', '--config', help='Config file')
        
        # Дополнительные параметры
        parser.add_argument('--verbose', action='store_true', help='Detailed output')
        parser.add_argument('--dry-run', action='store_true', help='Only parse sttfs')
        parser.add_argument('--export-ast', default=False, help='Export AST to JSON file')
        
        args = parser.parse_args()
        
        # Чтение DSL
        with open(args.input, 'r', encoding='utf-8') as f:
            dsl_text = f.read()
        
        if args.dry_run:
            # Только парсинг
            lexer = Lexer(dsl_text)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast_nodes = parser.parse()
            
            print(f"✅ DSL успешно распарсен")
            print(f"  Токенов: {len(tokens)}")
            print(f"  Узлов AST: {len(ast_nodes)}")
            
            if args.export_ast:
                FSBuilderCLI._export_ast(ast_nodes, args.export_ast)
        else:
            # Полная сборка
            result = FSBuilderCLI.build_from_dsl(dsl_text, args.output, args.config)
            
            print(f"✅ Файловая система создана в: {args.output}")
            
            if args.export_ast:
                FSBuilderCLI._export_ast(result['ast'], args.export_ast)
    
    @staticmethod
    def _export_ast(ast_nodes, output_file):
        """Экспорт AST в JSON"""
        import json
        
        def node_to_dict(node):
            if isinstance(node, FolderNode):
                return {
                    'type': 'folder',
                    'name': node.name,
                    'attributes': node.attributes,
                    'children': [node_to_dict(c) for c in node.children]
                }
            elif isinstance(node, FileNode):
                return {
                    'type': 'file',
                    'name': node.name,
                    'attributes': node.attributes
                }
            elif isinstance(node, ForLoopNode):
                return {
                    'type': 'for_loop',
                    'var_name': node.var_name,
                    'start': node.start,
                    'end': node.end,
                    'step': node.step,
                    'condition': node.condition,
                    'children': [node_to_dict(c) for c in node.children]
                }
            return {}
        
        ast_dict = [node_to_dict(node) for node in ast_nodes]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ast_dict, f, indent=2, ensure_ascii=False)
        
        print(f"AST экспортирован в {output_file}")