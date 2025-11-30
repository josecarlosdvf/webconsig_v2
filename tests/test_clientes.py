# -*- encoding: utf-8 -*-
"""
Testes do Módulo de Clientes
"""

import pytest
from apps import db
from apps.clientes.models import (
    Cliente, Telefone, Endereco, Email,
    Identidade, DadosBancarios, Matricula, DataNascimento
)


class TestClienteModel:
    """Testes do modelo Cliente"""
    
    def test_cliente_creation(self, app, init_database):
        """Testa criação de cliente"""
        with app.app_context():
            cliente = Cliente(
                cpf='12345678901',
                nome_completo='João da Silva'
            )
            db.session.add(cliente)
            db.session.commit()
            
            assert cliente.cpf == '12345678901'
            assert cliente.nome_completo == 'João da Silva'
    
    def test_cpf_formatted(self, app, init_database):
        """Testa formatação de CPF"""
        with app.app_context():
            cliente = Cliente(
                cpf='12345678901',
                nome_completo='Test User'
            )
            assert cliente.cpf_formatted == '123.456.789-01'
    
    def test_primeiro_nome(self, app, init_database):
        """Testa obtenção do primeiro nome"""
        with app.app_context():
            cliente = Cliente(
                cpf='12345678901',
                nome_completo='Maria José da Silva'
            )
            assert cliente.primeiro_nome == 'Maria'
    
    def test_get_by_cpf(self, app, init_database):
        """Testa busca por CPF"""
        with app.app_context():
            cliente = Cliente(
                cpf='98765432100',
                nome_completo='Pedro Santos'
            )
            db.session.add(cliente)
            db.session.commit()
            
            found = Cliente.get_by_cpf('98765432100')
            assert found is not None
            assert found.nome_completo == 'Pedro Santos'
    
    def test_search_by_name(self, app, init_database):
        """Testa busca por nome"""
        with app.app_context():
            cliente = Cliente(
                cpf='11122233344',
                nome_completo='Carlos Eduardo Oliveira'
            )
            db.session.add(cliente)
            db.session.commit()
            
            results = Cliente.search('Carlos')
            assert len(results) > 0


class TestTelefoneModel:
    """Testes do modelo Telefone"""
    
    def test_telefone_creation(self, app, init_database):
        """Testa criação de telefone"""
        with app.app_context():
            cliente = Cliente(cpf='55566677788', nome_completo='Test')
            db.session.add(cliente)
            db.session.commit()
            
            telefone = Telefone(
                cpf=cliente.cpf,
                telefone='11987654321',
                tipo='celular'
            )
            db.session.add(telefone)
            db.session.commit()
            
            assert telefone.id is not None
            assert telefone.tipo == 'celular'
    
    def test_telefone_formatted(self, app, init_database):
        """Testa formatação de telefone"""
        with app.app_context():
            telefone = Telefone(telefone='11987654321')
            assert telefone.telefone_formatted == '(11) 98765-4321'


class TestEnderecoModel:
    """Testes do modelo Endereco"""
    
    def test_endereco_creation(self, app, init_database):
        """Testa criação de endereço"""
        with app.app_context():
            cliente = Cliente(cpf='44455566677', nome_completo='Test')
            db.session.add(cliente)
            db.session.commit()
            
            endereco = Endereco(
                cpf=cliente.cpf,
                logradouro='Rua das Flores',
                numero='123',
                cidade='São Paulo',
                uf='SP',
                cep='01234567'
            )
            db.session.add(endereco)
            db.session.commit()
            
            assert endereco.id is not None
            assert endereco.cidade == 'São Paulo'
    
    def test_cep_formatted(self, app, init_database):
        """Testa formatação de CEP"""
        with app.app_context():
            endereco = Endereco(cep='01234567')
            assert endereco.cep_formatted == '01234-567'


class TestEmailModel:
    """Testes do modelo Email"""
    
    def test_email_creation(self, app, init_database):
        """Testa criação de email"""
        with app.app_context():
            cliente = Cliente(cpf='66677788899', nome_completo='Email Test')
            db.session.add(cliente)
            db.session.commit()
            
            email = Email(
                cpf=cliente.cpf,
                email='teste@exemplo.com',
                status='ativo'
            )
            db.session.add(email)
            db.session.commit()
            
            assert email.id is not None
            assert email.email == 'teste@exemplo.com'


class TestIdentidadeModel:
    """Testes do modelo Identidade"""
    
    def test_identidade_creation(self, app, init_database):
        """Testa criação de identidade"""
        with app.app_context():
            cliente = Cliente(cpf='99988877700', nome_completo='ID Test')
            db.session.add(cliente)
            db.session.commit()
            
            identidade = Identidade(
                cpf=cliente.cpf,
                rg='123456789',
                orgao_emissor='SSP',
                sexo='M',
                estado_civil='Solteiro'
            )
            db.session.add(identidade)
            db.session.commit()
            
            assert identidade.id is not None
            assert identidade.rg == '123456789'


class TestDadosBancariosModel:
    """Testes do modelo DadosBancarios"""
    
    def test_dados_bancarios_creation(self, app, init_database):
        """Testa criação de dados bancários"""
        with app.app_context():
            cliente = Cliente(cpf='11122233355', nome_completo='Bank Test')
            db.session.add(cliente)
            db.session.commit()
            
            dados = DadosBancarios(
                cpf=cliente.cpf,
                banco='Banco do Brasil',
                numero_banco='001',
                agencia='1234',
                conta='123456-7',
                chave_pix='11122233355'
            )
            db.session.add(dados)
            db.session.commit()
            
            assert dados.id is not None
            assert dados.banco == 'Banco do Brasil'


class TestMatriculaModel:
    """Testes do modelo Matricula"""
    
    def test_matricula_creation(self, app, init_database):
        """Testa criação de matrícula"""
        with app.app_context():
            cliente = Cliente(cpf='44455566688', nome_completo='Mat Test')
            db.session.add(cliente)
            db.session.commit()
            
            matricula = Matricula(
                cpf=cliente.cpf,
                matricula='12345678',
                orgao='INSS',
                categoria='Aposentado'
            )
            db.session.add(matricula)
            db.session.commit()
            
            assert matricula.id is not None
            assert matricula.orgao == 'INSS'


class TestRelacionamentos:
    """Testes de relacionamentos entre modelos"""
    
    def test_cliente_telefones(self, app, init_database):
        """Testa relacionamento cliente -> telefones"""
        with app.app_context():
            cliente = Cliente(cpf='77788899900', nome_completo='Test')
            db.session.add(cliente)
            db.session.commit()
            
            tel1 = Telefone(cpf=cliente.cpf, telefone='11111111111')
            tel2 = Telefone(cpf=cliente.cpf, telefone='22222222222')
            db.session.add_all([tel1, tel2])
            db.session.commit()
            
            assert cliente.telefones.count() == 2
    
    def test_cliente_data_nascimento(self, app, init_database):
        """Testa relacionamento 1:1 cliente -> data_nasc"""
        with app.app_context():
            cliente = Cliente(cpf='88899900011', nome_completo='Test')
            db.session.add(cliente)
            db.session.commit()
            
            data_nasc = DataNascimento(
                cpf=cliente.cpf,
                data_nasc='01/01/1990',
                idade=34
            )
            db.session.add(data_nasc)
            db.session.commit()
            
            assert cliente.data_nasc is not None
            assert cliente.data_nasc.idade == 34
    
    def test_cliente_emails(self, app, init_database):
        """Testa relacionamento cliente -> emails"""
        with app.app_context():
            cliente = Cliente(cpf='55544433322', nome_completo='Email Rel Test')
            db.session.add(cliente)
            db.session.commit()
            
            email1 = Email(cpf=cliente.cpf, email='teste1@exemplo.com')
            email2 = Email(cpf=cliente.cpf, email='teste2@exemplo.com')
            db.session.add_all([email1, email2])
            db.session.commit()
            
            assert cliente.emails.count() == 2
    
    def test_cliente_enderecos(self, app, init_database):
        """Testa relacionamento cliente -> enderecos"""
        with app.app_context():
            cliente = Cliente(cpf='33322211199', nome_completo='End Rel Test')
            db.session.add(cliente)
            db.session.commit()
            
            end1 = Endereco(cpf=cliente.cpf, logradouro='Rua 1', cidade='SP')
            end2 = Endereco(cpf=cliente.cpf, logradouro='Rua 2', cidade='RJ')
            db.session.add_all([end1, end2])
            db.session.commit()
            
            assert cliente.enderecos.count() == 2
    
    def test_cliente_dados_bancarios(self, app, init_database):
        """Testa relacionamento cliente -> dados_bancarios"""
        with app.app_context():
            cliente = Cliente(cpf='22211100088', nome_completo='Bank Rel Test')
            db.session.add(cliente)
            db.session.commit()
            
            db1 = DadosBancarios(cpf=cliente.cpf, banco='BB')
            db2 = DadosBancarios(cpf=cliente.cpf, banco='Caixa')
            db.session.add_all([db1, db2])
            db.session.commit()
            
            assert cliente.dados_bancarios.count() == 2
    
    def test_cliente_matriculas(self, app, init_database):
        """Testa relacionamento cliente -> matriculas"""
        with app.app_context():
            cliente = Cliente(cpf='11100099977', nome_completo='Mat Rel Test')
            db.session.add(cliente)
            db.session.commit()
            
            m1 = Matricula(cpf=cliente.cpf, matricula='111', orgao='INSS')
            m2 = Matricula(cpf=cliente.cpf, matricula='222', orgao='Exército')
            db.session.add_all([m1, m2])
            db.session.commit()
            
            assert cliente.matriculas.count() == 2


class TestClientesRoutes:
    """Testes das rotas de clientes"""
    
    def test_clientes_list_requires_login(self, client):
        """Testa que listagem requer login"""
        response = client.get('/clientes/')
        assert response.status_code in [302, 401]
    
    def test_cliente_novo_requires_login(self, client):
        """Testa que criação requer login"""
        response = client.get('/clientes/novo')
        assert response.status_code in [302, 401]
