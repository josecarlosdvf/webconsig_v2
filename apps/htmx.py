# -*- encoding: utf-8 -*-
"""
HTMX Support para Flask
Utilitários para navegação dinâmica com HTMX
"""

from flask import request, make_response


def is_htmx_request():
    """Verifica se a requisição atual é uma requisição HTMX"""
    return request.headers.get('HX-Request') == 'true'


def is_htmx_boosted():
    """Verifica se a requisição veio de um link boosted"""
    return request.headers.get('HX-Boosted') == 'true'


def get_htmx_trigger():
    """Retorna o ID do elemento que disparou a requisição"""
    return request.headers.get('HX-Trigger')


def get_htmx_target():
    """Retorna o ID do elemento target"""
    return request.headers.get('HX-Target')


def get_htmx_current_url():
    """Retorna a URL atual do navegador"""
    return request.headers.get('HX-Current-URL')


class HTMXMiddleware:
    """
    Middleware para processar respostas HTMX.
    Converte redirects em HX-Redirect para funcionamento correto.
    """
    
    def __init__(self, app):
        self.app = app
        self._setup_after_request()
    
    def _setup_after_request(self):
        @self.app.after_request
        def handle_htmx_redirects(response):
            """Converte redirects HTTP em HX-Redirect para requisições HTMX"""
            
            # Se é uma requisição HTMX com redirect, converte para HX-Redirect
            if is_htmx_request() or is_htmx_boosted():
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get('Location')
                    if location:
                        # Cria uma resposta vazia com o header HX-Redirect
                        new_response = make_response('', 200)
                        new_response.headers['HX-Redirect'] = location
                        return new_response
            
            return response


def init_htmx(app):
    """
    Inicializa suporte HTMX na aplicação Flask.
    
    - Adiciona middleware para tratar redirects
    - Adiciona variáveis ao contexto de templates
    
    Usage:
        from apps.htmx import init_htmx
        init_htmx(app)
    """
    # Registra middleware
    HTMXMiddleware(app)
    
    # Adiciona helpers ao contexto de templates
    @app.context_processor
    def htmx_context():
        return {
            'is_htmx': is_htmx_request() or is_htmx_boosted(),
            'htmx_request': is_htmx_request(),
            'htmx_boosted': is_htmx_boosted(),
        }
    
    # Log
    app.logger.info('HTMX support initialized')
