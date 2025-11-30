# -*- encoding: utf-8 -*-
"""
Serviço de integração com a API Lemit
Consulta de dados cadastrais por CPF

Exemplo de uso:
    from apps.services.lemit import LemitService
    
    # Buscar dados por CPF
    resultado = LemitService.consultar_cpf('12345678901')
    
    # Os dados são cacheados por 30 dias automaticamente
"""

import requests
import os
import re
from typing import Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass

from apps import db
from apps.logs import log_info, log_error, log_warning


# =============================================================================
# CONFIGURAÇÃO - Obtém do banco de dados ou variáveis de ambiente
# =============================================================================

def get_api_config():
    """Obtém configurações da API do banco de dados ou variáveis de ambiente"""
    try:
        from apps.settings.models import SystemSettings
        
        url = SystemSettings.get('api_consulta_url') or os.environ.get(
            'LEMIT_API_URL', 
            'https://api.lemit.com.br/api/v1/consulta/pessoa'
        )
        token = SystemSettings.get('api_consulta_token') or os.environ.get(
            'LEMIT_API_TOKEN', 
            'GL6gd3BCoTC7hAMNK1Hv6dFH8n9omtqQBXeGixKq'
        )
        cache_days = SystemSettings.get('api_consulta_cache_days') or int(os.environ.get('LEMIT_CACHE_DAYS', '30'))
        timeout = SystemSettings.get('api_consulta_timeout') or int(os.environ.get('LEMIT_TIMEOUT', '30'))
        enabled = SystemSettings.get('api_consulta_enabled')
        if enabled is None:
            enabled = True
        
        return {
            'url': url,
            'token': token,
            'cache_days': int(cache_days) if cache_days else 30,
            'timeout': int(timeout) if timeout else 30,
            'enabled': enabled
        }
    except Exception as e:
        log_warning(f'Lemit: Erro ao carregar config do banco, usando padrão: {e}')
        return {
            'url': os.environ.get('LEMIT_API_URL', 'https://api.lemit.com.br/api/v1/consulta/pessoa'),
            'token': os.environ.get('LEMIT_API_TOKEN', 'GL6gd3BCoTC7hAMNK1Hv6dFH8n9omtqQBXeGixKq'),
            'cache_days': int(os.environ.get('LEMIT_CACHE_DAYS', '30')),
            'timeout': int(os.environ.get('LEMIT_TIMEOUT', '30')),
            'enabled': True
        }


# Configurações legadas (para compatibilidade)
LEMIT_API_URL = os.environ.get(
    'LEMIT_API_URL', 
    'https://api.lemit.com.br/api/v1/consulta/pessoa'
)
LEMIT_API_TOKEN = os.environ.get(
    'LEMIT_API_TOKEN', 
    'GL6gd3BCoTC7hAMNK1Hv6dFH8n9omtqQBXeGixKq'
)
LEMIT_CACHE_DAYS = int(os.environ.get('LEMIT_CACHE_DAYS', '30'))
LEMIT_TIMEOUT = int(os.environ.get('LEMIT_TIMEOUT', '30'))


# =============================================================================
# MODELO DE CACHE/LOG DE CONSULTAS
# =============================================================================

class ConsultaLog(db.Model):
    """
    Log e cache de consultas à API Lemit.
    Armazena respostas por 30 dias para evitar cobranças desnecessárias.
    """
    
    __tablename__ = 'consultas_log'
    
    id = db.Column(db.Integer, primary_key=True)
    cpf = db.Column(
        db.String(11), 
        nullable=False, 
        index=True,
        comment='CPF consultado (apenas números)'
    )
    data_consulta = db.Column(
        db.DateTime, 
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment='Data/hora da consulta'
    )
    json_resposta = db.Column(
        db.JSON, 
        nullable=True,
        comment='Resposta completa da API (JSON)'
    )
    status_code = db.Column(
        db.Integer, 
        nullable=True,
        comment='Código HTTP da resposta'
    )
    sucesso = db.Column(
        db.Boolean, 
        default=True,
        comment='Se a consulta foi bem sucedida'
    )
    erro = db.Column(
        db.String(500), 
        nullable=True,
        comment='Mensagem de erro se houver'
    )
    
    # Auditoria
    usuario_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment='ID do usuário que fez a consulta'
    )
    usuario_nome = db.Column(
        db.String(64), 
        nullable=True,
        comment='Nome do usuário (para histórico)'
    )
    ip_address = db.Column(
        db.String(45), 
        nullable=True,
        comment='IP de origem da consulta'
    )
    user_agent = db.Column(
        db.String(500), 
        nullable=True,
        comment='User-Agent do navegador'
    )
    
    # Contadores
    num_consultas = db.Column(
        db.Integer, 
        default=1,
        comment='Número de vezes que este CPF foi consultado'
    )
    ultima_consulta_cache = db.Column(
        db.DateTime, 
        nullable=True,
        comment='Última vez que o cache foi utilizado'
    )
    consultas_cache = db.Column(
        db.Integer, 
        default=0,
        comment='Quantas vezes retornou do cache'
    )
    
    # Relacionamentos
    usuario = db.relationship(
        'Users',
        backref=db.backref('consultas_lemit', lazy='dynamic'),
        foreign_keys=[usuario_id]
    )
    
    def __repr__(self):
        return f'<ConsultaLog {self.cpf} em {self.data_consulta}>'
    
    @property
    def cpf_formatted(self):
        """CPF formatado"""
        if not self.cpf:
            return None
        cpf = self.cpf.zfill(11)
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    
    @property
    def nome_pessoa(self):
        """Nome da pessoa consultada (do JSON)"""
        if self.json_resposta and self.json_resposta.get('pessoa'):
            return self.json_resposta['pessoa'].get('nome')
        return None
    
    @property
    def cache_valido(self):
        """Verifica se o cache ainda é válido (30 dias)"""
        if not self.sucesso:
            return False
        limite = datetime.utcnow() - timedelta(days=LEMIT_CACHE_DAYS)
        return self.data_consulta > limite
    
    @classmethod
    def get_cache(cls, cpf: str) -> Optional['ConsultaLog']:
        """
        Busca consulta em cache (últimos 30 dias com sucesso)
        
        Args:
            cpf: CPF apenas números
            
        Returns:
            ConsultaLog ou None
        """
        limite = datetime.utcnow() - timedelta(days=LEMIT_CACHE_DAYS)
        return cls.query.filter(
            cls.cpf == cpf,
            cls.sucesso == True,
            cls.data_consulta > limite
        ).order_by(cls.data_consulta.desc()).first()
    
    @classmethod
    def registrar_uso_cache(cls, consulta: 'ConsultaLog'):
        """Atualiza contadores de uso do cache"""
        consulta.consultas_cache += 1
        consulta.ultima_consulta_cache = datetime.utcnow()
        db.session.commit()


# =============================================================================
# DATACLASS PARA RESPOSTA
# =============================================================================

@dataclass
class PessoaLemit:
    """Representa os dados de uma pessoa retornados pela API Lemit"""
    cpf: str
    nome: str = None
    data_nascimento: str = None
    sexo: str = None
    nome_mae: str = None
    nome_pai: str = None
    falecido: bool = False
    situacao_cpf: str = None
    renda: str = None
    ocupacao: str = None
    score_credito: str = None
    
    # Listas
    celulares: list = None
    fixos: list = None
    emails: list = None
    enderecos: list = None
    vinculos: list = None
    participacao_societaria: list = None
    carros: list = None
    
    # Dados brutos
    raw_data: dict = None
    
    def __post_init__(self):
        self.celulares = self.celulares or []
        self.fixos = self.fixos or []
        self.emails = self.emails or []
        self.enderecos = self.enderecos or []
        self.vinculos = self.vinculos or []
        self.participacao_societaria = self.participacao_societaria or []
        self.carros = self.carros or []
    
    @classmethod
    def from_api_response(cls, cpf: str, data: dict) -> 'PessoaLemit':
        """Cria instância a partir da resposta da API"""
        pessoa = data.get('pessoa', {})
        
        risco = pessoa.get('risco_credito', {})
        
        return cls(
            cpf=cpf,
            nome=pessoa.get('nome'),
            data_nascimento=pessoa.get('data_nascimento'),
            sexo=pessoa.get('sexo'),
            nome_mae=pessoa.get('nome_mae'),
            nome_pai=pessoa.get('nome_pai'),
            falecido=pessoa.get('falecido', False),
            situacao_cpf=pessoa.get('situacao_cpf'),
            renda=pessoa.get('renda'),
            ocupacao=pessoa.get('ocupacao'),
            score_credito=risco.get('score_credito') if risco else None,
            celulares=pessoa.get('celulares', []),
            fixos=pessoa.get('fixos', []),
            emails=pessoa.get('emails', []),
            enderecos=pessoa.get('enderecos', []),
            vinculos=pessoa.get('vinculos', []),
            participacao_societaria=pessoa.get('participacao_societaria', []),
            carros=pessoa.get('carros', []),
            raw_data=data
        )
    
    @property
    def telefone_principal(self) -> Optional[str]:
        """Retorna o primeiro celular com WhatsApp ou o primeiro disponível"""
        for cel in self.celulares:
            if cel.get('whatsapp'):
                ddd = cel.get('ddd', '')
                numero = cel.get('numero', '')
                return f"({ddd}) {numero}"
        
        if self.celulares:
            cel = self.celulares[0]
            ddd = cel.get('ddd', '')
            numero = cel.get('numero', '')
            return f"({ddd}) {numero}"
        
        if self.fixos:
            fixo = self.fixos[0]
            ddd = fixo.get('ddd', '')
            numero = fixo.get('numero', '')
            return f"({ddd}) {numero}"
        
        return None
    
    @property
    def email_principal(self) -> Optional[str]:
        """Retorna o primeiro email"""
        if self.emails:
            return self.emails[0].get('email')
        return None
    
    @property
    def endereco_principal(self) -> Optional[dict]:
        """Retorna o primeiro endereço"""
        if self.enderecos:
            return self.enderecos[0]
        return None
    
    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'cpf': self.cpf,
            'nome': self.nome,
            'data_nascimento': self.data_nascimento,
            'sexo': self.sexo,
            'nome_mae': self.nome_mae,
            'nome_pai': self.nome_pai,
            'falecido': self.falecido,
            'situacao_cpf': self.situacao_cpf,
            'renda': self.renda,
            'ocupacao': self.ocupacao,
            'score_credito': self.score_credito,
            'telefone_principal': self.telefone_principal,
            'email_principal': self.email_principal,
            'endereco_principal': self.endereco_principal,
            'celulares': self.celulares,
            'fixos': self.fixos,
            'emails': self.emails,
            'enderecos': self.enderecos,
        }


# =============================================================================
# SERVIÇO PRINCIPAL
# =============================================================================

class LemitService:
    """Serviço para consulta de CPF via API Lemit"""
    
    @staticmethod
    def _clean_cpf(cpf: str) -> str:
        """Remove caracteres não numéricos do CPF"""
        return re.sub(r'\D', '', cpf)
    
    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """Valida se o CPF tem 11 dígitos"""
        cpf = LemitService._clean_cpf(cpf)
        return len(cpf) == 11 and cpf.isdigit()
    
    @classmethod
    def consultar_cpf(
        cls, 
        cpf: str, 
        force_api: bool = False,
        user_id: int = None,
        user_name: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> tuple:
        """
        Consulta dados cadastrais por CPF.
        
        Args:
            cpf: CPF com ou sem formatação
            force_api: Se True, ignora o cache e consulta a API
            user_id: ID do usuário para auditoria
            user_name: Nome do usuário para auditoria
            ip_address: IP de origem
            user_agent: User-Agent do navegador
            
        Returns:
            tuple: (PessoaLemit ou None, mensagem de erro ou None, from_cache: bool)
        """
        cpf = cls._clean_cpf(cpf)
        
        log_info(f'Lemit: Iniciando consulta para CPF {cpf[:3]}***{cpf[-2:]}')
        
        if not cls.validate_cpf(cpf):
            log_warning(f'Lemit: CPF inválido: {cpf[:3]}***')
            return None, 'CPF inválido. Deve conter 11 dígitos.', False
        
        # Obtém configurações dinâmicas
        config = get_api_config()
        log_info(f'Lemit: Config carregada - URL: {config["url"][:30]}..., Enabled: {config["enabled"]}')
        
        # Verifica se API está habilitada
        if not config['enabled']:
            log_warning('Lemit: API está desabilitada nas configurações')
            return None, 'API de consulta está desabilitada. Contate o administrador.', False
        
        # Verifica cache (se não forçar API)
        if not force_api:
            cache = ConsultaLog.get_cache(cpf)
            if cache:
                log_info(f'Lemit: Retornando CPF {cpf[:3]}***{cpf[-2:]} do cache (consulta de {cache.data_consulta})')
                ConsultaLog.registrar_uso_cache(cache)
                pessoa = PessoaLemit.from_api_response(cpf, cache.json_resposta)
                return pessoa, None, True
        
        # Consulta a API
        try:
            log_info(f'Lemit: Consultando API externa para CPF {cpf[:3]}***{cpf[-2:]}')
            log_info(f'Lemit: URL={config["url"]}, Timeout={config["timeout"]}s')
            
            headers = {
                'Authorization': f'Bearer {config["token"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                config['url'],
                headers=headers,
                json={'documento': cpf},
                timeout=config['timeout']
            )
            
            log_info(f'Lemit: Resposta HTTP {response.status_code}')
            
            # Registra a consulta no log
            consulta = ConsultaLog(
                cpf=cpf,
                status_code=response.status_code,
                usuario_id=user_id,
                usuario_nome=user_name,
                ip_address=ip_address,
                user_agent=user_agent[:500] if user_agent else None
            )
            
            if response.status_code == 200:
                data = response.json()
                consulta.json_resposta = data
                consulta.sucesso = True
                
                db.session.add(consulta)
                db.session.commit()
                
                log_info(f'Lemit: Sucesso! Nome encontrado: {data.get("pessoa", {}).get("nome", "N/A")[:20]}...')
                pessoa = PessoaLemit.from_api_response(cpf, data)
                return pessoa, None, False
            
            elif response.status_code == 400:
                consulta.sucesso = False
                consulta.erro = 'CPF ou formato inválido'
                db.session.add(consulta)
                db.session.commit()
                return None, 'CPF ou formato inválido', False
            
            elif response.status_code == 401:
                consulta.sucesso = False
                consulta.erro = 'Token inválido ou expirado'
                db.session.add(consulta)
                db.session.commit()
                log_error('Lemit: Token inválido ou expirado')
                return None, 'Erro de autenticação: Token inválido ou expirado. Verifique as configurações da API.', False
            
            elif response.status_code == 403:
                consulta.sucesso = False
                consulta.erro = 'Acesso negado (403) - API indisponível'
                db.session.add(consulta)
                db.session.commit()
                log_error('Lemit: Acesso negado (403) - API pode estar fora do horário comercial')
                return None, 'API indisponível. A API Lemit só funciona em dias úteis, das 8h às 18h.', False
            
            elif response.status_code == 404:
                consulta.sucesso = False
                consulta.erro = 'CPF não encontrado'
                db.session.add(consulta)
                db.session.commit()
                return None, 'CPF não encontrado na base de dados', False
            
            elif response.status_code == 500:
                consulta.sucesso = False
                consulta.erro = 'Erro interno do servidor Lemit'
                db.session.add(consulta)
                db.session.commit()
                log_error('Lemit: Erro interno do servidor (500)')
                return None, 'Erro interno no servidor da API. Tente novamente mais tarde.', False
            
            else:
                consulta.sucesso = False
                consulta.erro = f'Erro HTTP {response.status_code}'
                db.session.add(consulta)
                db.session.commit()
                log_warning(f'Lemit: Resposta inesperada HTTP {response.status_code}')
                return None, f'Erro na API: HTTP {response.status_code}. Tente novamente mais tarde.', False
                
        except requests.Timeout:
            log_error('Lemit: Timeout na consulta')
            return None, 'Timeout na consulta. Tente novamente.', False
        
        except requests.RequestException as e:
            log_error(f'Lemit: Erro de conexão: {str(e)}')
            return None, 'Erro de conexão com a API', False
        
        except Exception as e:
            log_error(f'Lemit: Erro inesperado: {str(e)}')
            return None, f'Erro inesperado: {str(e)}', False
    
    @classmethod
    def get_historico(
        cls, 
        cpf: str = None, 
        limit: int = 100,
        apenas_sucesso: bool = False
    ) -> list:
        """
        Retorna histórico de consultas
        
        Args:
            cpf: Filtrar por CPF específico
            limit: Limite de registros
            apenas_sucesso: Se True, retorna apenas consultas bem sucedidas
        """
        query = ConsultaLog.query
        
        if cpf:
            cpf = cls._clean_cpf(cpf)
            query = query.filter(ConsultaLog.cpf == cpf)
        
        if apenas_sucesso:
            query = query.filter(ConsultaLog.sucesso == True)
        
        return query.order_by(ConsultaLog.data_consulta.desc()).limit(limit).all()
    
    @classmethod
    def get_estatisticas(cls) -> dict:
        """Retorna estatísticas das consultas"""
        from sqlalchemy import func
        
        total = ConsultaLog.query.count()
        sucesso = ConsultaLog.query.filter(ConsultaLog.sucesso == True).count()
        cache_hits = db.session.query(func.sum(ConsultaLog.consultas_cache)).scalar() or 0
        
        # Consultas últimos 30 dias
        limite = datetime.utcnow() - timedelta(days=30)
        ultimos_30_dias = ConsultaLog.query.filter(
            ConsultaLog.data_consulta > limite
        ).count()
        
        # CPFs únicos
        cpfs_unicos = db.session.query(
            func.count(func.distinct(ConsultaLog.cpf))
        ).scalar() or 0
        
        return {
            'total_consultas': total,
            'consultas_sucesso': sucesso,
            'taxa_sucesso': round((sucesso / total * 100) if total > 0 else 0, 1),
            'cache_hits': cache_hits,
            'economia_cache': cache_hits,  # Quantas chamadas à API foram economizadas
            'ultimos_30_dias': ultimos_30_dias,
            'cpfs_unicos': cpfs_unicos
        }


# =============================================================================
# FUNÇÕES DE CONVENIÊNCIA
# =============================================================================

def consultar_cpf(cpf: str, force_api: bool = False) -> tuple:
    """
    Função de conveniência para consultar CPF
    
    Exemplo:
        from apps.services.lemit import consultar_cpf
        pessoa, erro, from_cache = consultar_cpf('12345678901')
        if pessoa:
            print(pessoa.nome)
    """
    return LemitService.consultar_cpf(cpf, force_api)


def validar_cpf(cpf: str) -> bool:
    """Valida formato do CPF (11 dígitos)"""
    return LemitService.validate_cpf(cpf)
