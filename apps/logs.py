# -*- coding: utf-8 -*-
"""
Módulo de logs do sistema.
Fornece funções de logging configuráveis.
"""

import logging
from flask import Flask, request
from typing import Any, Optional


# Logger principal
logger = logging.getLogger('webconsig')


def setup_logging(app: Flask) -> None:
    """
    Configura o sistema de logs da aplicação.
    
    Args:
        app: Instância da aplicação Flask
    """
    log_level = app.config.get('LOG_LEVEL', 'DEBUG')
    log_to_file = app.config.get('LOG_TO_FILE', False)
    log_to_console = app.config.get('LOG_TO_CONSOLE', True)
    log_dir = app.config.get('LOG_DIR', 'logs')
    
    # Configura nível de log
    level = getattr(logging, log_level.upper(), logging.DEBUG)
    logger.setLevel(level)
    
    # Formata mensagens
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # Handler para console
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Handler para arquivo
    if log_to_file:
        import os
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(
            os.path.join(log_dir, 'app.log'),
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def register_error_handlers(app: Flask) -> None:
    """
    Registra handlers de erro com logging.
    
    Args:
        app: Instância da aplicação Flask
    """
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Log de exceções não tratadas"""
        log_error(f'Exceção não tratada: {str(e)}', exc_info=True)
        # Re-raise para que o Flask trate o erro (preserva traceback)
        raise


def log_debug(message: str, extra: Optional[dict] = None) -> None:
    """Log de debug"""
    logger.debug(message, extra=extra)


def log_info(message: str, extra: Optional[dict] = None) -> None:
    """Log informativo"""
    logger.info(message, extra=extra)


def log_warning(message: str, extra: Optional[dict] = None) -> None:
    """Log de aviso"""
    logger.warning(message, extra=extra)


def log_error(message: str, extra: Optional[dict] = None, exc_info: bool = False) -> None:
    """Log de erro"""
    logger.error(message, extra=extra, exc_info=exc_info)


def log_critical(message: str, extra: Optional[dict] = None, exc_info: bool = False) -> None:
    """Log crítico"""
    logger.critical(message, extra=extra, exc_info=exc_info)
