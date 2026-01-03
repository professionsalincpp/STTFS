import re
from enum import Enum
from typing import List, Optional

class TokenType(Enum):
    # Ключевые слова
    FOLDER = "FOLDER"
    FILE = "FILE"
    FOR = "FOR"
    IF = "IF"
    ELSE = "ELSE"
    
    # Идентификаторы и литералы
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"
    
    # Операторы
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
    
    # Скобки и разделители
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COMMA = "COMMA"
    COLON = "COLON"
    SEMICOLON = "SEMICOLON"
    
    # Специальные
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
        
        # Ключевые слова
        self.keywords = {
            'folder': TokenType.FOLDER,
            'file': TokenType.FILE,
            'for': TokenType.FOR,
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'true': TokenType.IDENTIFIER,
            'false': TokenType.IDENTIFIER,
            'null': TokenType.IDENTIFIER,
        }
        
        # Операторы
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
            
            # Комментарии
            if char == '#':
                self._read_comment()
                continue
            
            # Строки в двойных кавычках
            if char == '"':
                self._read_string()
                continue
            
            # Числа
            if char.isdigit():
                self._read_number()
                continue
            
            # Переменные шаблона ${var}
            if char == '$' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '{':
                self._read_template_var()
                continue
            
            # Идентификаторы и ключевые слова
            if char.isalpha() or char == '_':
                self._read_identifier()
                continue
            
            # Операторы
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
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] != '\n':
            self.pos += 1
    
    def _read_string(self):
        self.pos += 1  # Пропускаем открывающую кавычку
        start = self.pos
        while self.pos < len(self.text):
            if self.text[self.pos] == '"':
                value = self.text[start:self.pos]
                self.tokens.append(Token(TokenType.STRING, value, self.line, start - self.line_start + 1))
                self.pos += 1
                return
            elif self.text[self.pos] == '\\' and self.pos + 1 < len(self.text):
                self.pos += 2  # Пропускаем escape-символ
            else:
                self.pos += 1
        raise SyntaxError(f"Незакрытая строка на строке {self.line}")
    
    def _read_number(self):
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isdigit() or self.text[self.pos] == '.'):
            self.pos += 1
        value = self.text[start:self.pos]
        self.tokens.append(Token(TokenType.NUMBER, value, self.line, start - self.line_start + 1))
    
    def _read_template_var(self):
        start = self.pos
        self.pos += 2  # Пропускаем ${
        depth = 1
        content_start = self.pos
        
        while self.pos < len(self.text) and depth > 0:
            if self.text[self.pos] == '{':
                depth += 1
            elif self.text[self.pos] == '}':
                depth -= 1
            self.pos += 1
        
        if depth > 0:
            raise SyntaxError(f"Незакрытая переменная шаблона на строке {self.line}")
        
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
        # Пробуем найти самый длинный оператор
        for length in [2, 1]:
            if self.pos + length <= len(self.text):
                op = self.text[self.pos:self.pos+length]
                if op in self.operators:
                    self.tokens.append(Token(self.operators[op], op, self.line, self.pos - self.line_start + 1))
                    self.pos += length
                    return True
        return False