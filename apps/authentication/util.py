# -*- encoding: utf-8 -*-
"""
Utilitários de Autenticação
"""

import re
import bcrypt


def hash_password(password: str) -> bytes:
    """
    Gera hash da senha usando bcrypt.
    Retorna bytes para armazenar no banco.
    """
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password, salt)


def verify_password(password: str, hashed: bytes) -> bool:
    """
    Verifica se a senha corresponde ao hash.
    """
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    try:
        return bcrypt.checkpw(password, hashed)
    except Exception:
        return False


def validate_password(password: str, min_length: int = 8) -> tuple[bool, str]:
    """
    Valida força da senha.
    Retorna (is_valid, message)
    """
    if len(password) < min_length:
        return False, f'A senha deve ter pelo menos {min_length} caracteres.'
    
    if not re.search(r'[A-Z]', password):
        return False, 'A senha deve conter pelo menos uma letra maiúscula.'
    
    if not re.search(r'[a-z]', password):
        return False, 'A senha deve conter pelo menos uma letra minúscula.'
    
    if not re.search(r'[0-9]', password):
        return False, 'A senha deve conter pelo menos um número.'
    
    return True, 'Senha válida.'


def validate_email(email: str) -> bool:
    """
    Valida formato do e-mail.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username: str) -> tuple[bool, str]:
    """
    Valida nome de usuário.
    Retorna (is_valid, message)
    """
    if len(username) < 3:
        return False, 'O nome de usuário deve ter pelo menos 3 caracteres.'
    
    if len(username) > 64:
        return False, 'O nome de usuário deve ter no máximo 64 caracteres.'
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, 'O nome de usuário pode conter apenas letras, números e underscore.'
    
    return True, 'Nome de usuário válido.'


def sanitize_input(value: str) -> str:
    """
    Remove caracteres potencialmente perigosos.
    """
    if not value:
        return ''
    
    # Remove espaços extras
    value = ' '.join(value.split())
    
    # Remove caracteres de controle
    value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
    
    return value.strip()
