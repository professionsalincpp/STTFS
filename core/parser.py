from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from enum import Enum as PyEnum
from core.lexer import Token, TokenType

class FileType(PyEnum):
    TEXT = "text"
    BINARY = "binary"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"

class Permission(PyEnum):
    READ_ONLY = "444"
    WRITABLE = "644"
    EXECUTABLE = "755"
    FULL = "777"

@dataclass
class ASTNode:
    line: int = 0
    column: int = 0

@dataclass
class FileNode(ASTNode):
    name: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    template_vars: Dict[str, str] = field(default_factory=dict)

@dataclass
class FolderNode(ASTNode):
    name: str = ""
    children: List[ASTNode] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ForLoopNode(ASTNode):
    var_name: str = ""
    start: Any = 0
    end: Any = 0
    step: Any = 1
    condition: str = "<"
    children: List[ASTNode] = field(default_factory=list)

@dataclass
class OutputNode(ASTNode):
    message: str = ""

@dataclass
class InputNode(ASTNode):
    variable: str = ""

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current_token = tokens[0] if tokens else None
    
    def error(self, message: str):
        token = self.current_token
        raise SyntaxError(f"{message} at line {token.line}, position {token.column}")
    
    def eat(self, token_type: TokenType, value: Optional[str] = None):
        if self.current_token.type == token_type:
            if value is not None and self.current_token.value != value:
                self.error(f"Expected '{value}', got '{self.current_token.value}'")
            self.pos += 1
            if self.pos < len(self.tokens):
                self.current_token = self.tokens[self.pos]
            else:
                self.current_token = Token(TokenType.EOF, "")
        else:
            self.error(f"Expected token {token_type}, got {self.current_token.type}")
    
    def peek(self, offset: int = 1) -> Optional[Token]:
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return None
    
    def parse(self) -> List[ASTNode]:
        nodes = []
        while self.current_token.type != TokenType.EOF:
            node = self.parse_statement()
            if node:
                nodes.append(node)
        return nodes
    
    def parse_statement(self) -> Optional[ASTNode]:
        token = self.current_token
        
        if token.type == TokenType.FOLDER:
            return self.parse_folder()
        elif token.type == TokenType.FILE:
            return self.parse_file()
        elif token.type == TokenType.FOR:
            return self.parse_for_loop()
        elif token.type == TokenType.STDOUT:
            return self.parse_output()
        elif token.type == TokenType.STDIN:
            return self.parse_input()
        
        self.error(f"Unexpected token: {token}")
    
    def parse_output(self) -> OutputNode:
        self.eat(TokenType.STDOUT)
        self.eat(TokenType.LSHIFT)
        
        if self.current_token.type != TokenType.STRING:
            self.error("Expected string after <<")
        
        message = self.current_token.value
        self.eat(TokenType.STRING)
        
        return OutputNode(message=message)
    
    def parse_input(self) -> InputNode:
        self.eat(TokenType.STDIN)
        self.eat(TokenType.RSHIFT)
        
        if self.current_token.type != TokenType.IDENTIFIER:
            self.error("Expected variable identifier after >>")
        
        variable = self.current_token.value
        self.eat(TokenType.IDENTIFIER)
        
        return InputNode(variable=variable)
    
    def parse_folder(self) -> FolderNode:
        self.eat(TokenType.FOLDER)
        
        if self.current_token.type in [TokenType.IDENTIFIER, TokenType.STRING]:
            name = self.current_token.value
            self.eat(self.current_token.type)
        else:
            self.error("Expected folder name")
        
        attributes = {}
        if self.current_token.type == TokenType.LPAREN:
            attributes = self.parse_attributes()
        
        self.eat(TokenType.LBRACE)
        
        children = []
        while self.current_token.type != TokenType.RBRACE:
            child = self.parse_statement()
            if child:
                children.append(child)
        
        self.eat(TokenType.RBRACE)
        return FolderNode(name=name, children=children, attributes=attributes)
    
    def parse_file(self) -> FileNode:
        self.eat(TokenType.FILE)
        
        if self.current_token.type in [TokenType.IDENTIFIER, TokenType.STRING]:
            name = self.current_token.value
            self.eat(self.current_token.type)
        else:
            self.error("Expected file name")
        
        attributes = {}
        if self.current_token.type == TokenType.LPAREN:
            attributes = self.parse_attributes()
        
        template_vars = self._extract_template_vars(name)
        
        return FileNode(name=name, attributes=attributes, template_vars=template_vars)
    
    def parse_for_loop(self) -> ForLoopNode:
        self.eat(TokenType.FOR)
        self.eat(TokenType.LBRACKET)
        
        if self.current_token.type != TokenType.IDENTIFIER:
            self.error("Expected loop variable name")
        var_name = self.current_token.value
        self.eat(TokenType.IDENTIFIER)
        
        self.eat(TokenType.ASSIGN)
        
        if self.current_token.type == TokenType.NUMBER:
            start = int(self.current_token.value)
            self.eat(TokenType.NUMBER)
        else:
            self.error("Expected numeric start value")
        
        self.eat(TokenType.SEMICOLON)
        
        if self.current_token.type != TokenType.IDENTIFIER or self.current_token.value != var_name:
            self.error(f"Expected loop variable '{var_name}'")
        self.eat(TokenType.IDENTIFIER)
        
        condition_op = self.current_token.value
        if condition_op not in ['<', '<=', '>', '>=', '!=']:
            self.error(f"Unsupported comparison operator: {condition_op}")
        self.eat(self.current_token.type)
        
        if self.current_token.type == TokenType.NUMBER:
            end = int(self.current_token.value)
            self.eat(TokenType.NUMBER)
        else:
            self.error("Expected numeric end value")
        
        self.eat(TokenType.SEMICOLON)
        
        if self.current_token.type != TokenType.IDENTIFIER or self.current_token.value != var_name:
            self.error(f"Expected loop variable '{var_name}'")
        self.eat(TokenType.IDENTIFIER)
        
        step = 1
        if self.current_token.type == TokenType.INCR:
            step = 1
            self.eat(TokenType.INCR)
        elif self.current_token.type == TokenType.DECR:
            step = -1
            self.eat(TokenType.DECR)
        else:
            self.error("Expected increment/decrement operator")
        
        self.eat(TokenType.RBRACKET)
        self.eat(TokenType.LBRACE)
        
        children = []
        while self.current_token.type != TokenType.RBRACE:
            child = self.parse_statement()
            if child:
                children.append(child)
        
        self.eat(TokenType.RBRACE)
        
        return ForLoopNode(var_name=var_name, start=start, end=end, 
                          step=step, condition=condition_op, children=children)
    
    def parse_attributes(self) -> Dict[str, Any]:
        self.eat(TokenType.LPAREN)
        attributes = {}
        
        while self.current_token.type != TokenType.RPAREN:
            if self.current_token.type != TokenType.IDENTIFIER:
                self.error("Expected attribute name")
            attr_name = self.current_token.value
            self.eat(TokenType.IDENTIFIER)
            
            self.eat(TokenType.ASSIGN)
            
            attr_value = self.parse_attribute_value()
            attributes[attr_name] = attr_value
            
            if self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
        
        self.eat(TokenType.RPAREN)
        return attributes
    
    def parse_attribute_value(self) -> Any:
        if self.current_token.type == TokenType.STRING:
            value = self.current_token.value
            self.eat(TokenType.STRING)
            if value.lower() in ["text", "binary", "json", "yaml", "xml"]:
                return FileType(value.lower())
            elif value in ["444", "644", "755", "777"]:
                return Permission(value)
            return value
        elif self.current_token.type == TokenType.NUMBER:
            value = int(self.current_token.value)
            self.eat(TokenType.NUMBER)
            return value
        elif self.current_token.type == TokenType.IDENTIFIER:
            if self.current_token.value.lower() in ['true', 'false']:
                value = self.current_token.value.lower() == 'true'
                self.eat(TokenType.IDENTIFIER)
                return value
            elif self.current_token.value.lower() == 'null':
                self.eat(TokenType.IDENTIFIER)
                return None
            else:
                value = self.current_token.value
                self.eat(TokenType.IDENTIFIER)
                return value
        else:
            self.error("Unsupported attribute value type")
    
    def _extract_template_vars(self, text: str) -> Dict[str, str]:
        import re
        vars = {}
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, text)
        for match in matches:
            vars[match] = ""
        return vars