import re
from enum import Enum
from typing import List, Optional

class TokenType(Enum):
    FOLDER = "FOLDER"
    FILE = "FILE"
    FOR = "FOR"
    IF = "IF"
    ELSE = "ELSE"
    STDOUT = "STDOUT"
    STDIN = "STDIN"
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"
    ASSIGN = "ASSIGN"
    EQ = "EQ"
    NE = "NE"
    LT = "LT"
    GT = "GT"
    LE = "LE"
    GE = "GE"
    PLUS = "PLUS"
    MINUS = "MINUS"
    MUL = "MUL"
    DIV = "DIV"
    MOD = "MOD"
    INCR = "INCR"
    DECR = "DECR"
    LSHIFT = "LSHIFT"
    RSHIFT = "RSHIFT"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COMMA = "COMMA"
    COLON = "COLON"
    SEMICOLON = "SEMICOLON"
    TEMPLATE_VAR = "TEMPLATE_VAR"
    EOF = "EOF"

class Token:
    def __init__(self, type: TokenType, value: str = "", line: int = 1, column: int = 1):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
    
    def __repr__(self):
        return f"Token({self.type}, '{self.value}', line={self.line})"

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.line_start = 0
        self.tokens: List[Token] = []
        
        self.keywords = {
            'folder': TokenType.FOLDER,
            'file': TokenType.FILE,
            'for': TokenType.FOR,
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'stdout': TokenType.STDOUT,
            'stdin': TokenType.STDIN,
            'true': TokenType.IDENTIFIER,
            'false': TokenType.IDENTIFIER,
            'null': TokenType.IDENTIFIER,
        }
        
        self.operators = {
            '=': TokenType.ASSIGN,
            '==': TokenType.EQ,
            '!=': TokenType.NE,
            '<': TokenType.LT,
            '>': TokenType.GT,
            '<=': TokenType.LE,
            '>=': TokenType.GE,
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.MUL,
            '/': TokenType.DIV,
            '%': TokenType.MOD,
            '++': TokenType.INCR,
            '--': TokenType.DECR,
            '<<': TokenType.LSHIFT,
            '>>': TokenType.RSHIFT,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            '[': TokenType.LBRACKET,
            ']': TokenType.RBRACKET,
            ',': TokenType.COMMA,
            ':': TokenType.COLON,
            ';': TokenType.SEMICOLON,
        }
    
    def tokenize(self) -> List[Token]:
        while self.pos < len(self.text):
            self._skip_whitespace()
            if self.pos >= len(self.text):
                break
            
            char = self.text[self.pos]
            
            if char == '#':
                self._read_comment()
                continue
            
            if char == '"':
                self._read_string()
                continue
            
            if char.isdigit():
                self._read_number()
                continue
            
            if char == '$' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '{':
                self._read_template_var()
                continue
            
            if char.isalpha() or char == '_':
                self._read_identifier()
                continue
            
            if self._read_operator():
                continue
            
            self.pos += 1
        
        self.tokens.append(Token(TokenType.EOF, "", self.line, 0))
        return self.tokens
    
    def _skip_whitespace(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            if self.text[self.pos] == '\n':
                self.line += 1
                self.line_start = self.pos + 1
            self.pos += 1
    
    def _read_comment(self):
        while self.pos < len(self.text) and self.text[self.pos] != '\n':
            self.pos += 1
    
    def _read_string(self):
        self.pos += 1
        start = self.pos
        while self.pos < len(self.text):
            if self.text[self.pos] == '"':
                value = self.text[start:self.pos]
                self.tokens.append(Token(TokenType.STRING, value, self.line, start - self.line_start + 1))
                self.pos += 1
                return
            elif self.text[self.pos] == '\\' and self.pos + 1 < len(self.text):
                self.pos += 2
            else:
                self.pos += 1
        raise SyntaxError(f"Unclosed string at line {self.line}")
    
    def _read_number(self):
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isdigit() or self.text[self.pos] == '.'):
            self.pos += 1
        value = self.text[start:self.pos]
        self.tokens.append(Token(TokenType.NUMBER, value, self.line, start - self.line_start + 1))
    
    def _read_template_var(self):
        start = self.pos
        self.pos += 2
        depth = 1
        content_start = self.pos
        
        while self.pos < len(self.text) and depth > 0:
            if self.text[self.pos] == '{':
                depth += 1
            elif self.text[self.pos] == '}':
                depth -= 1
            self.pos += 1
        
        if depth > 0:
            raise SyntaxError(f"Unclosed template variable at line {self.line}")
        
        content = self.text[content_start:self.pos-1].strip()
        self.tokens.append(Token(TokenType.TEMPLATE_VAR, content, self.line, start - self.line_start + 1))
    
    def _read_identifier(self):
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        
        value = self.text[start:self.pos]
        token_type = self.keywords.get(value.lower(), TokenType.IDENTIFIER)
        self.tokens.append(Token(token_type, value, self.line, start - self.line_start + 1))
    
    def _read_operator(self) -> bool:
        for length in [2, 1]:
            if self.pos + length <= len(self.text):
                op = self.text[self.pos:self.pos+length]
                if op in self.operators:
                    self.tokens.append(Token(self.operators[op], op, self.line, self.pos - self.line_start + 1))
                    self.pos += length
                    return True
        return False