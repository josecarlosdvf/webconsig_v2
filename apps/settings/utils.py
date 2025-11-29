# -*- encoding: utf-8 -*-
"""
Utilitários de Configurações do Sistema
"""

from functools import lru_cache
from apps.settings.models import SystemSettings


class SystemSettingsCache:
    """Cache de configurações do sistema para evitar consultas repetidas"""
    
    _cache = {}
    _initialized = False
    
    @classmethod
    def clear(cls):
        """Limpa o cache"""
        cls._cache = {}
        cls._initialized = False
    
    @classmethod
    def load(cls):
        """Carrega todas as configurações públicas no cache"""
        try:
            settings = SystemSettings.query.all()
            for setting in settings:
                cls._cache[setting.key] = setting.get_typed_value()
            cls._initialized = True
        except Exception:
            # Tabela pode não existir ainda
            cls._initialized = False
    
    @classmethod
    def get(cls, key: str, default=None):
        """Obtém valor do cache ou do banco"""
        if not cls._initialized:
            cls.load()
        
        if key in cls._cache:
            return cls._cache[key]
        
        # Tenta buscar do banco
        try:
            value = SystemSettings.get(key, default)
            cls._cache[key] = value
            return value
        except Exception:
            return default
    
    @classmethod
    def set(cls, key: str, value):
        """Atualiza cache após alteração"""
        cls._cache[key] = value


def get_system_settings() -> dict:
    """
    Retorna dicionário com configurações do sistema para uso em templates.
    Esta função é chamada pelo context processor.
    """
    cache = SystemSettingsCache
    
    return {
        # Sistema
        'name': cache.get('app_name', 'WebConsig'),
        'description': cache.get('app_description', 'Sistema de Gestão'),
        'version': cache.get('app_version', '1.0.0'),
        
        # Desenvolvedor
        'developer_name': cache.get('developer_name', 'Desenvolvedor'),
        'developer_url': cache.get('developer_url', '#'),
        'developer_email': cache.get('developer_email', ''),
        
        # Empresa
        'company_name': cache.get('company_name', 'Empresa'),
        'company_cnpj': cache.get('company_cnpj', ''),
        'company_address': cache.get('company_address', ''),
        'company_phone': cache.get('company_phone', ''),
        'company_email': cache.get('company_email', ''),
        
        # Aparência
        'logo_url': cache.get('logo_url', '/static/assets/img/brand/logo.svg'),
        'logo_dark_url': cache.get('logo_dark_url', '/static/assets/img/brand/logo-light.svg'),
        'favicon_url': cache.get('favicon_url', '/static/assets/img/favicon/favicon.svg'),
        'primary_color': cache.get('primary_color', '#1F2937'),
        'secondary_color': cache.get('secondary_color', '#6B7280'),
        
        # Localização
        'language': cache.get('language', 'pt-BR'),
        'timezone': cache.get('timezone', 'America/Sao_Paulo'),
        'date_format': cache.get('date_format', 'DD/MM/YYYY'),
        'currency': cache.get('currency', 'BRL'),
        
        # Segurança
        'session_timeout': cache.get('session_timeout', 3600),
        'maintenance_mode': cache.get('maintenance_mode', False),
    }


def refresh_settings_cache():
    """Atualiza o cache de configurações"""
    SystemSettingsCache.clear()
    SystemSettingsCache.load()


# Categorias de configurações para a interface
SETTINGS_CATEGORIES = {
    'sistema': {
        'label': 'Sistema',
        'icon': 'fas fa-cog',
        'description': 'Configurações gerais do sistema'
    },
    'empresa': {
        'label': 'Empresa',
        'icon': 'fas fa-building',
        'description': 'Dados da empresa que utiliza o sistema'
    },
    'desenvolvedor': {
        'label': 'Desenvolvedor',
        'icon': 'fas fa-code',
        'description': 'Informações da empresa desenvolvedora'
    },
    'aparencia': {
        'label': 'Aparência',
        'icon': 'fas fa-palette',
        'description': 'Logo, cores e personalização visual'
    },
    'localizacao': {
        'label': 'Localização',
        'icon': 'fas fa-globe',
        'description': 'Idioma, fuso horário e formatos'
    },
    'seguranca': {
        'label': 'Segurança',
        'icon': 'fas fa-shield-alt',
        'description': 'Configurações de segurança e acesso'
    },
}
