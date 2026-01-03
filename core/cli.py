import argparse
import sys
import json
import yaml
from core.parser import Parser

class FSBuilderCLI:
    """Command Line Interface for File System Builder"""

    
    @staticmethod
    def _execute_dsl(dsl_text: str, output_dir: str = ".", config: dict = None, verbose: bool = False):
        """Execute STTFS code"""
        from core.lexer import Lexer
        from core.parser import Parser
        from core.generator import InteractiveFSGenerator
        
        lexer = Lexer(dsl_text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast_nodes = parser.parse()
        if verbose:
            print("Lexical analysis...")
            print(f"* Found {len(tokens)} tokens")
            print("Parsing...")
            print(f"* Built {len(ast_nodes)} AST nodes")
            print("Generating file system...")
        generator = InteractiveFSGenerator(output_dir, config or {})
        generator.generate(ast_nodes)
    

    
    @staticmethod
    def main():
        parser = argparse.ArgumentParser(
            description='File System Builder - Create file structures from sttfs files',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='''Examples:
  python main.py create example.sttfs'''
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Commands')
        
        # Run command
        run_parser = subparsers.add_parser('create', help='Run sttfs file')
        run_parser.add_argument('file', help='STTFS file (.sttfs)')
        run_parser.add_argument('-o', '--output', default='.', help='Output directory')
        run_parser.add_argument('-c', '--config', help='Configuration file')
        run_parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Verbose mode')
        
        args = parser.parse_args()
        
        if args.command == 'create':
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    dsl_text = f.read()
                
                config = {}
                if args.config:
                    if args.config.endswith('.yaml') or args.config.endswith('.yml'):
                        with open(args.config, 'r') as f:
                            config = yaml.safe_load(f)
                    elif args.config.endswith('.json'):
                        with open(args.config, 'r') as f:
                            config = json.load(f)
                
                FSBuilderCLI._execute_dsl(dsl_text, args.output, config, args.verbose)
                if args.verbose:
                    print(f"\nSummary:")
                    print(f"* Output directory: {args.output}")
                    print(f"* DSL file: {args.file}")
                    if args.config:
                        print(f"* Config file: {args.config}")
            except FileNotFoundError:
                print(f"\033[31m\033[1mError: \033[0m\033[1mFile \"{args.file}\" not found\033[0m")
                sys.exit(1)
        else:
            parser.print_help()