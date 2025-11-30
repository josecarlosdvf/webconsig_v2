# -*- encoding: utf-8 -*-
"""
Testes do Módulo de Operações/Contratos
"""

import pytest
from datetime import datetime
from apps import db
from apps.operacoes.models import (
    Tabela, FatoresDiariosTabela, Operacao, RPCOperacao, BoletoOperacao,
    TipoOperacao, StatusOperacao, TipoTabela, TipoRPC, StatusRPC
)


class TestTabelaModel:
    """Testes do modelo Tabela"""
    
    def test_tabela_creation(self, app, init_database):
        """Testa criação de tabela"""
        with app.app_context():
            tabela = Tabela(
                nome='Tabela Teste INSS',
                tipo=TipoTabela.NOVO,
                orgao='INSS',
                banco='BMG',
                num_parcelas=84,
                fator=0.0250,
                comissao_total=5.0
            )
            db.session.add(tabela)
            db.session.commit()
            
            assert tabela.id is not None
            assert tabela.nome == 'Tabela Teste INSS'
            assert tabela.tipo == TipoTabela.NOVO
    
    def test_tabela_display_name(self, app, init_database):
        """Testa nome para exibição"""
        with app.app_context():
            tabela = Tabela(
                nome='Tabela Premium',
                orgao='INSS',
                banco='Bradesco'
            )
            assert 'INSS' in tabela.display_name
            assert 'Bradesco' in tabela.display_name
    
    def test_tabela_get_ativas(self, app, init_database):
        """Testa busca de tabelas ativas"""
        with app.app_context():
            tabela1 = Tabela(nome='Ativa1', tipo=TipoTabela.NOVO, ativa=True)
            tabela2 = Tabela(nome='Inativa', tipo=TipoTabela.NOVO, ativa=False)
            db.session.add_all([tabela1, tabela2])
            db.session.commit()
            
            ativas = Tabela.get_ativas()
            nomes = [t.nome for t in ativas]
            assert 'Ativa1' in nomes
            assert 'Inativa' not in nomes


class TestFatoresDiariosModel:
    """Testes do modelo FatoresDiariosTabela"""
    
    def test_fatores_creation(self, app, init_database):
        """Testa criação de fatores diários"""
        with app.app_context():
            tabela = Tabela(nome='Tab Fatores', tipo=TipoTabela.NOVO)
            db.session.add(tabela)
            db.session.commit()
            
            fatores = FatoresDiariosTabela(
                tabela_id=tabela.id,
                dia_01=0.0250,
                dia_15=0.0252,
                dia_31=0.0255
            )
            db.session.add(fatores)
            db.session.commit()
            
            assert fatores.id is not None
            assert fatores.get_fator(1) == 0.0250
            assert fatores.get_fator(15) == 0.0252
    
    def test_fatores_set_fator(self, app, init_database):
        """Testa definição de fator"""
        with app.app_context():
            fatores = FatoresDiariosTabela()
            fatores.set_fator(10, 0.0260)
            assert fatores.get_fator(10) == 0.0260


class TestOperacaoModel:
    """Testes do modelo Operacao"""
    
    def test_operacao_creation(self, app, init_database):
        """Testa criação de operação"""
        with app.app_context():
            operacao = Operacao(
                cliente_cpf='12345678901',
                cliente_nome_completo='João da Silva',
                tipo=TipoOperacao.NOVO,
                status=StatusOperacao.DIGITACAO,
                valor_liquido=5000.00,
                prazo=84
            )
            db.session.add(operacao)
            db.session.commit()
            
            assert operacao.id is not None
            assert operacao.cliente_nome_completo == 'João da Silva'
    
    def test_cpf_formatted(self, app, init_database):
        """Testa formatação de CPF"""
        with app.app_context():
            operacao = Operacao(
                cliente_cpf='12345678901',
                cliente_nome_completo='Test',
                tipo=TipoOperacao.NOVO,
                status=StatusOperacao.DIGITACAO
            )
            assert operacao.cpf_formatted == '123.456.789-01'
    
    def test_status_badge_class(self, app, init_database):
        """Testa classe de badge para status"""
        with app.app_context():
            operacao = Operacao(
                cliente_cpf='12345678901',
                cliente_nome_completo='Test',
                tipo=TipoOperacao.NOVO,
                status=StatusOperacao.AVERBADA
            )
            assert operacao.status_badge_class == 'bg-success'
    
    def test_operacao_cancelar(self, app, init_database):
        """Testa cancelamento de operação"""
        with app.app_context():
            operacao = Operacao(
                cliente_cpf='12345678901',
                cliente_nome_completo='Test Cancel',
                tipo=TipoOperacao.NOVO,
                status=StatusOperacao.PENDENTE
            )
            db.session.add(operacao)
            db.session.commit()
            
            operacao.cancelar('Motivo teste', 'admin')
            
            assert operacao.status == StatusOperacao.CANCELADA
            assert operacao.motivo_cancelamento == 'Motivo teste'
    
    def test_operacao_averbar(self, app, init_database):
        """Testa averbação de operação"""
        with app.app_context():
            operacao = Operacao(
                cliente_cpf='12345678901',
                cliente_nome_completo='Test Averbar',
                tipo=TipoOperacao.NOVO,
                status=StatusOperacao.APROVADA
            )
            db.session.add(operacao)
            db.session.commit()
            
            operacao.averbar('admin')
            
            assert operacao.averbado == True
            assert operacao.status == StatusOperacao.AVERBADA
            assert operacao.usuario_averbacao == 'admin'
    
    def test_operacao_search(self, app, init_database):
        """Testa busca de operações"""
        with app.app_context():
            operacao = Operacao(
                cliente_cpf='99988877766',
                cliente_nome_completo='Maria Oliveira',
                tipo=TipoOperacao.NOVO,
                status=StatusOperacao.DIGITACAO
            )
            db.session.add(operacao)
            db.session.commit()
            
            results = Operacao.search('Maria')
            assert len(results) > 0
            assert results[0].cliente_nome_completo == 'Maria Oliveira'


class TestRPCOperacaoModel:
    """Testes do modelo RPCOperacao"""
    
    def test_rpc_creation(self, app, init_database):
        """Testa criação de RPC"""
        with app.app_context():
            operacao = Operacao(
                cliente_cpf='11122233344',
                cliente_nome_completo='Test RPC',
                tipo=TipoOperacao.REFINANCIAMENTO,
                status=StatusOperacao.DIGITACAO
            )
            db.session.add(operacao)
            db.session.commit()
            
            rpc = RPCOperacao(
                operacao_id=operacao.id,
                tipo=TipoRPC.REFIN,
                banco='Bradesco',
                valor_parcela=150.00,
                restantes=24,
                saldo_devedor=3600.00
            )
            db.session.add(rpc)
            db.session.commit()
            
            assert rpc.id is not None
            assert rpc.tipo == TipoRPC.REFIN
    
    def test_rpc_quitar(self, app, init_database):
        """Testa quitação de RPC"""
        with app.app_context():
            operacao = Operacao(
                cliente_cpf='22233344455',
                cliente_nome_completo='Test Quitar',
                tipo=TipoOperacao.REFINANCIAMENTO,
                status=StatusOperacao.DIGITACAO
            )
            db.session.add(operacao)
            db.session.commit()
            
            rpc = RPCOperacao(
                operacao_id=operacao.id,
                tipo=TipoRPC.REFIN,
                status=StatusRPC.PENDENTE
            )
            db.session.add(rpc)
            db.session.commit()
            
            rpc.quitar()
            
            assert rpc.status == StatusRPC.QUITADO


class TestBoletoOperacaoModel:
    """Testes do modelo BoletoOperacao"""
    
    def test_boleto_creation(self, app, init_database):
        """Testa criação de boleto"""
        with app.app_context():
            operacao = Operacao(
                cliente_cpf='33344455566',
                cliente_nome_completo='Test Boleto',
                tipo=TipoOperacao.NOVO,
                status=StatusOperacao.AVERBADA
            )
            db.session.add(operacao)
            db.session.commit()
            
            boleto = BoletoOperacao(
                operacao_id=operacao.id,
                valor=1500.00,
                banco='BMG',
                comissao_empresa=75.00,
                comissao_corretor=50.00
            )
            db.session.add(boleto)
            db.session.commit()
            
            assert boleto.id is not None
            assert boleto.valor == 1500.00
    
    def test_boleto_total_comissoes(self, app, init_database):
        """Testa cálculo de total de comissões"""
        with app.app_context():
            boleto = BoletoOperacao(
                comissao_empresa=100.00,
                comissao_corretor=50.00,
                comissao_bonus=25.00
            )
            assert boleto.total_comissoes == 175.00
    
    def test_boleto_confirmar_deposito(self, app, init_database):
        """Testa confirmação de depósito"""
        with app.app_context():
            operacao = Operacao(
                cliente_cpf='44455566677',
                cliente_nome_completo='Test Confirmar',
                tipo=TipoOperacao.NOVO,
                status=StatusOperacao.AVERBADA
            )
            db.session.add(operacao)
            db.session.commit()
            
            boleto = BoletoOperacao(
                operacao_id=operacao.id,
                valor=2000.00,
                deposito_confirmado=False
            )
            db.session.add(boleto)
            db.session.commit()
            
            boleto.confirmar_deposito()
            
            assert boleto.deposito_confirmado == True


class TestRelacionamentos:
    """Testes de relacionamentos entre modelos"""
    
    def test_operacao_tabela(self, app, init_database):
        """Testa relacionamento operação -> tabela"""
        with app.app_context():
            tabela = Tabela(nome='Tab Rel Test', tipo=TipoTabela.NOVO)
            db.session.add(tabela)
            db.session.commit()
            
            operacao = Operacao(
                cliente_cpf='55566677788',
                cliente_nome_completo='Test Rel',
                tipo=TipoOperacao.NOVO,
                status=StatusOperacao.DIGITACAO,
                tabela_id=tabela.id
            )
            db.session.add(operacao)
            db.session.commit()
            
            assert operacao.tabela is not None
            assert operacao.tabela.nome == 'Tab Rel Test'
    
    def test_operacao_rpcs(self, app, init_database):
        """Testa relacionamento operação -> rpcs"""
        with app.app_context():
            operacao = Operacao(
                cliente_cpf='66677788899',
                cliente_nome_completo='Test RPCs',
                tipo=TipoOperacao.PORTABILIDADE,
                status=StatusOperacao.DIGITACAO
            )
            db.session.add(operacao)
            db.session.commit()
            
            rpc1 = RPCOperacao(operacao_id=operacao.id, tipo=TipoRPC.PORT)
            rpc2 = RPCOperacao(operacao_id=operacao.id, tipo=TipoRPC.REFIN)
            db.session.add_all([rpc1, rpc2])
            db.session.commit()
            
            assert operacao.rpcs_count == 2
    
    def test_operacao_boletos(self, app, init_database):
        """Testa relacionamento operação -> boletos"""
        with app.app_context():
            operacao = Operacao(
                cliente_cpf='77788899900',
                cliente_nome_completo='Test Boletos',
                tipo=TipoOperacao.NOVO,
                status=StatusOperacao.PAGA
            )
            db.session.add(operacao)
            db.session.commit()
            
            b1 = BoletoOperacao(operacao_id=operacao.id, valor=1000.00)
            b2 = BoletoOperacao(operacao_id=operacao.id, valor=500.00)
            db.session.add_all([b1, b2])
            db.session.commit()
            
            assert operacao.boletos_count == 2
            assert operacao.total_boletos == 1500.00


class TestOperacoesRoutes:
    """Testes das rotas de operações"""
    
    def test_operacoes_list_requires_login(self, client):
        """Testa que listagem requer login"""
        response = client.get('/operacoes/')
        assert response.status_code in [302, 401]
    
    def test_tabelas_list_requires_login(self, client):
        """Testa que listagem de tabelas requer login"""
        response = client.get('/operacoes/tabelas')
        assert response.status_code in [302, 401]
    
    def test_nova_operacao_requires_login(self, client):
        """Testa que criação requer login"""
        response = client.get('/operacoes/nova')
        assert response.status_code in [302, 401]
