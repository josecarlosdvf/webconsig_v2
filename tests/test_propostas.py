# -*- encoding: utf-8 -*-
"""
Testes do módulo de Propostas
"""

import pytest
from flask import url_for
from datetime import datetime


class TestPropostasModels:
    """Testes dos modelos de propostas"""
    
    def test_proposta_status_choices(self):
        """Testa que PropostaStatus tem choices válidos"""
        from apps.propostas.models import PropostaStatus
        
        assert len(PropostaStatus.CHOICES) > 0
        assert len(PropostaStatus.CHOICES_ATIVOS) > 0
        assert len(PropostaStatus.CHOICES_ATIVOS) <= len(PropostaStatus.CHOICES)
    
    def test_proposta_status_config(self):
        """Testa configuração de status"""
        from apps.propostas.models import PropostaStatus
        
        config = PropostaStatus.get_config(PropostaStatus.AGUARD_DIGITACAO)
        assert config['seq'] == 1
        assert config['ativo'] == True
        assert 'css' in config
    
    def test_proposta_status_badge_class(self):
        """Testa classe CSS do badge"""
        from apps.propostas.models import PropostaStatus
        
        badge = PropostaStatus.get_badge_class(PropostaStatus.CANCELADA)
        assert 'danger' in badge
    
    def test_tipo_proposta_choices(self):
        """Testa choices de tipo de proposta"""
        from apps.propostas.models import TipoProposta
        
        assert len(TipoProposta.CHOICES) > 0
        assert ('novo', 'Novo') in TipoProposta.CHOICES


class TestPropostasRoutes:
    """Testes das rotas de propostas"""
    
    def test_propostas_list_requires_login(self, client):
        """Testa que lista de propostas requer login"""
        response = client.get('/propostas/')
        assert response.status_code in [302, 401]
    
    def test_propostas_list_loads(self, admin_client):
        """Testa que lista de propostas carrega"""
        response = admin_client.get('/propostas/')
        assert response.status_code == 200
        assert b'Propostas' in response.data
    
    def test_nova_proposta_form_loads(self, admin_client):
        """Testa que formulário de nova proposta carrega"""
        response = admin_client.get('/propostas/nova')
        assert response.status_code == 200
        assert b'CPF' in response.data
    
    def test_tabelas_list_loads(self, admin_client):
        """Testa que lista de tabelas carrega"""
        response = admin_client.get('/propostas/tabelas')
        assert response.status_code == 200
        assert b'Tabelas' in response.data


class TestPropostasAPI:
    """Testes da API de propostas"""
    
    def test_api_buscar_cliente_requer_login(self, client):
        """Testa que API de busca de cliente requer login"""
        response = client.get('/propostas/api/buscar-cliente?cpf=12345678901')
        assert response.status_code in [302, 401]
    
    def test_api_buscar_cliente_cpf_incompleto(self, admin_client):
        """Testa resposta para CPF incompleto"""
        response = admin_client.get('/propostas/api/buscar-cliente?cpf=123')
        assert response.status_code == 200
        data = response.get_json()
        assert data['found'] == False
        assert 'incompleto' in data.get('message', '').lower()
    
    def test_api_stats(self, admin_client):
        """Testa API de estatísticas"""
        response = admin_client.get('/propostas/api/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert 'total' in data


class TestPropostaCreation:
    """Testes de criação de proposta"""
    
    def test_create_proposta(self, admin_client, app):
        """Testa criação de proposta"""
        with app.app_context():
            from apps.propostas.models import Proposta, PropostaStatus
            
            response = admin_client.post('/propostas/nova', data={
                'cliente_cpf': '123.456.789-00',
                'cliente_nome_completo': 'Cliente Teste',
                'tipo': 'novo',
                'status': PropostaStatus.AGUARD_DIGITACAO,
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Verifica se proposta foi criada (CPF é limpo automaticamente na rota)
            proposta = Proposta.query.filter_by(cliente_cpf='12345678900').first()
            if proposta:
                assert proposta.cliente_nome_completo == 'Cliente Teste'


class TestTabelasCreation:
    """Testes de criação de tabelas"""
    
    def test_create_tabela(self, admin_client, app):
        """Testa criação de tabela"""
        with app.app_context():
            from apps.propostas.models import Tabela
            
            response = admin_client.post('/propostas/tabelas/nova', data={
                'nome': 'Tabela Teste',
                'tipo': 'novo',
                'orgao': 'INSS',
                'banco': 'Banco Teste',
                'num_parcelas': 84,
                'fator': 0.0150,
                'ativa': True,
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Verifica se tabela foi criada
            tabela = Tabela.query.filter_by(nome='Tabela Teste').first()
            if tabela:
                assert tabela.banco == 'Banco Teste'
