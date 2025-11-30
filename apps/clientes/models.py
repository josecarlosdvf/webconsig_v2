# -*- encoding: utf-8 -*-
"""
Modelos de Gestão de Clientes
Entidade principal: Cliente
Tabelas relacionadas: telefones, enderecos, matriculas, identidades, datas_nasc, emails, dados_bancarios
"""

from datetime import datetime

from apps import db
from apps.database.models import BaseModel


# =============================================================================
# CLIENTE (Entidade Principal)
# =============================================================================

# Note: Cliente não usa @audited porque usa CPF como chave primária (não id)
class Cliente(db.Model, BaseModel):
    """
    Cliente do sistema.
    Entidade principal com CPF como chave primária.
    """
    
    __tablename__ = 'clientes'
    
    cpf = db.Column(
        db.String(11), 
        primary_key=True,
        comment='CPF do cliente (apenas números)'
    )
    nome_completo = db.Column(
        db.String(150), 
        nullable=False,
        comment='Nome completo do cliente'
    )
    
    # Relacionamentos (1:N)
    telefones = db.relationship(
        'Telefone', 
        back_populates='cliente', 
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    enderecos = db.relationship(
        'Endereco', 
        back_populates='cliente', 
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    emails = db.relationship(
        'Email', 
        back_populates='cliente', 
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    identidades = db.relationship(
        'Identidade', 
        back_populates='cliente', 
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    dados_bancarios = db.relationship(
        'DadosBancarios', 
        back_populates='cliente', 
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    matriculas = db.relationship(
        'Matricula', 
        back_populates='cliente', 
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    # Relacionamento 1:1 com data de nascimento
    data_nasc = db.relationship(
        'DataNascimento', 
        back_populates='cliente', 
        uselist=False,
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f'<Cliente {self.cpf}: {self.nome_completo}>'
    
    @property
    def cpf_formatted(self):
        """CPF formatado"""
        if not self.cpf:
            return None
        cpf = self.cpf.zfill(11)
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    
    @property
    def primeiro_nome(self):
        """Retorna o primeiro nome"""
        return self.nome_completo.split()[0] if self.nome_completo else None
    
    @property
    def telefone_principal(self):
        """Retorna o telefone com melhor ranking"""
        return self.telefones.order_by(Telefone.ranking.desc()).first()
    
    @property
    def endereco_principal(self):
        """Retorna o primeiro endereço"""
        return self.enderecos.first()
    
    @property
    def email_principal(self):
        """Retorna o primeiro email"""
        return self.emails.first()
    
    @property
    def identidade_principal(self):
        """Retorna a primeira identidade"""
        return self.identidades.first()
    
    @property
    def dados_bancarios_principal(self):
        """Retorna os primeiros dados bancários"""
        return self.dados_bancarios.first()
    
    @classmethod
    def get_by_cpf(cls, cpf):
        """Busca cliente por CPF"""
        cpf_clean = ''.join(filter(str.isdigit, cpf))
        return cls.query_active().filter_by(cpf=cpf_clean).first()
    
    @classmethod
    def search(cls, term, limit=20):
        """Busca clientes por nome ou CPF"""
        term = term.strip()
        cpf_term = ''.join(filter(str.isdigit, term))
        
        query = cls.query_active()
        
        if cpf_term and len(cpf_term) >= 3:
            query = query.filter(cls.cpf.like(f'%{cpf_term}%'))
        else:
            query = query.filter(cls.nome_completo.ilike(f'%{term}%'))
        
        return query.order_by(cls.nome_completo).limit(limit).all()


# =============================================================================
# TELEFONE
# =============================================================================

class Telefone(db.Model, BaseModel):
    """
    Telefones do cliente (vários por CPF)
    """
    
    __tablename__ = 'telefones'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cpf = db.Column(
        db.String(11), 
        db.ForeignKey('clientes.cpf', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    telefone = db.Column(
        db.String(20),
        nullable=True,
        comment='Número do telefone'
    )
    tipo = db.Column(
        db.String(20),
        nullable=True,
        comment='Tipo: celular, fixo, comercial'
    )
    status = db.Column(
        db.String(30),
        nullable=True,
        comment='Status do telefone'
    )
    ranking = db.Column(
        db.Integer,
        nullable=True,
        default=0,
        comment='Ranking de prioridade'
    )
    score = db.Column(
        db.Integer,
        nullable=True,
        default=0,
        comment='Score de qualidade'
    )
    
    cliente = db.relationship('Cliente', back_populates='telefones')
    
    def __repr__(self):
        return f'<Telefone {self.telefone}>'
    
    @property
    def telefone_formatted(self):
        """Telefone formatado"""
        if not self.telefone:
            return None
        phone = ''.join(filter(str.isdigit, self.telefone))
        if len(phone) == 11:
            return f'({phone[:2]}) {phone[2:7]}-{phone[7:]}'
        elif len(phone) == 10:
            return f'({phone[:2]}) {phone[2:6]}-{phone[6:]}'
        return self.telefone


# =============================================================================
# ENDEREÇO
# =============================================================================

class Endereco(db.Model, BaseModel):
    """
    Endereços do cliente (vários por CPF)
    """
    
    __tablename__ = 'enderecos'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cpf = db.Column(
        db.String(11), 
        db.ForeignKey('clientes.cpf', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    logradouro = db.Column(
        db.String(150),
        nullable=True,
        comment='Rua, Avenida, etc.'
    )
    numero = db.Column(
        db.String(20),
        nullable=True,
        comment='Número do endereço'
    )
    complemento = db.Column(
        db.String(50),
        nullable=True,
        comment='Apartamento, bloco, etc.'
    )
    bairro = db.Column(
        db.String(100),
        nullable=True,
        comment='Bairro'
    )
    cidade = db.Column(
        db.String(100),
        nullable=True,
        comment='Cidade'
    )
    uf = db.Column(
        db.String(2),
        nullable=True,
        comment='Unidade Federativa'
    )
    cep = db.Column(
        db.String(20),
        nullable=True,
        comment='CEP'
    )
    
    cliente = db.relationship('Cliente', back_populates='enderecos')
    
    def __repr__(self):
        return f'<Endereco {self.logradouro}, {self.cidade}/{self.uf}>'
    
    @property
    def cep_formatted(self):
        """CEP formatado"""
        if not self.cep:
            return None
        cep = ''.join(filter(str.isdigit, self.cep))
        if len(cep) == 8:
            return f'{cep[:5]}-{cep[5:]}'
        return self.cep
    
    @property
    def endereco_completo(self):
        """Endereço completo formatado"""
        parts = []
        if self.logradouro:
            addr = self.logradouro
            if self.numero:
                addr += f', {self.numero}'
            if self.complemento:
                addr += f' - {self.complemento}'
            parts.append(addr)
        
        if self.bairro:
            parts.append(self.bairro)
        
        if self.cidade:
            city = self.cidade
            if self.uf:
                city += f'/{self.uf}'
            parts.append(city)
        
        if self.cep:
            parts.append(f'CEP: {self.cep_formatted}')
        
        return ' - '.join(parts) if parts else None


# =============================================================================
# EMAIL
# =============================================================================

class Email(db.Model, BaseModel):
    """
    Emails do cliente (vários por CPF)
    """
    
    __tablename__ = 'emails'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cpf = db.Column(
        db.String(11), 
        db.ForeignKey('clientes.cpf', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    email = db.Column(
        db.String(255),
        nullable=True,
        comment='Endereço de email'
    )
    status = db.Column(
        db.String(30),
        nullable=True,
        comment='Status do email'
    )
    
    cliente = db.relationship('Cliente', back_populates='emails')
    
    def __repr__(self):
        return f'<Email {self.email}>'


# =============================================================================
# IDENTIDADE
# =============================================================================

class Identidade(db.Model, BaseModel):
    """
    Identidades/RG do cliente (pode ter várias)
    """
    
    __tablename__ = 'identidades'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cpf = db.Column(
        db.String(11), 
        db.ForeignKey('clientes.cpf', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    rg = db.Column(
        db.String(30),
        nullable=True,
        comment='Número do RG'
    )
    orgao_emissor = db.Column(
        db.String(50),
        nullable=True,
        comment='Órgão emissor do RG'
    )
    data_emissao = db.Column(
        db.String(20),
        nullable=True,
        comment='Data de emissão'
    )
    nacionalidade = db.Column(
        db.String(50),
        nullable=True,
        comment='Nacionalidade'
    )
    naturalidade = db.Column(
        db.String(50),
        nullable=True,
        comment='Naturalidade'
    )
    profissao = db.Column(
        db.String(50),
        nullable=True,
        comment='Profissão'
    )
    estado_civil = db.Column(
        db.String(30),
        nullable=True,
        comment='Estado civil'
    )
    sexo = db.Column(
        db.String(10),
        nullable=True,
        comment='Sexo'
    )
    nome_pai = db.Column(
        db.String(150),
        nullable=True,
        comment='Nome do pai'
    )
    nome_mae = db.Column(
        db.String(150),
        nullable=True,
        comment='Nome da mãe'
    )
    
    cliente = db.relationship('Cliente', back_populates='identidades')
    
    def __repr__(self):
        return f'<Identidade RG: {self.rg}>'


# =============================================================================
# DADOS BANCÁRIOS
# =============================================================================

class DadosBancarios(db.Model, BaseModel):
    """
    Dados bancários do cliente (vários bancos por CPF)
    """
    
    __tablename__ = 'dados_bancarios'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cpf = db.Column(
        db.String(11), 
        db.ForeignKey('clientes.cpf', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    numero_banco = db.Column(
        db.String(10),
        nullable=True,
        comment='Número do banco'
    )
    banco = db.Column(
        db.String(150),
        nullable=True,
        comment='Nome do banco'
    )
    agencia = db.Column(
        db.String(20),
        nullable=True,
        comment='Número da agência'
    )
    conta = db.Column(
        db.String(30),
        nullable=True,
        comment='Número da conta'
    )
    data_abertura = db.Column(
        db.String(20),
        nullable=True,
        comment='Data de abertura da conta'
    )
    chave_pix = db.Column(
        db.String(100),
        nullable=True,
        comment='Chave PIX'
    )
    
    cliente = db.relationship('Cliente', back_populates='dados_bancarios')
    
    def __repr__(self):
        return f'<DadosBancarios {self.banco} - Ag: {self.agencia} Conta: {self.conta}>'


# =============================================================================
# MATRÍCULA
# =============================================================================

class Matricula(db.Model, BaseModel):
    """
    Matrículas do cliente (podem existir várias por CPF)
    """
    
    __tablename__ = 'matriculas'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cpf = db.Column(
        db.String(11), 
        db.ForeignKey('clientes.cpf', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    orgao = db.Column(
        db.String(50),
        nullable=True,
        comment='Órgão da matrícula'
    )
    matricula = db.Column(
        db.String(50),
        nullable=True,
        comment='Número da matrícula'
    )
    cod_categoria = db.Column(
        db.String(10),
        nullable=True,
        comment='Código da categoria'
    )
    categoria = db.Column(
        db.String(80),
        nullable=True,
        comment='Nome da categoria'
    )
    indicativo = db.Column(
        db.String(20),
        nullable=True,
        comment='Indicativo'
    )
    patente = db.Column(
        db.String(50),
        nullable=True,
        comment='Patente'
    )
    
    cliente = db.relationship('Cliente', back_populates='matriculas')
    
    def __repr__(self):
        return f'<Matricula {self.matricula} - {self.orgao}>'


# =============================================================================
# DATA DE NASCIMENTO (1:1)
# =============================================================================

class DataNascimento(db.Model, BaseModel):
    """
    Data de nascimento do cliente (1:1)
    """
    
    __tablename__ = 'datas_nasc'
    
    cpf = db.Column(
        db.String(11), 
        db.ForeignKey('clientes.cpf', ondelete='CASCADE'),
        primary_key=True
    )
    
    data_nasc = db.Column(
        db.String(20),
        nullable=True,
        comment='Data de nascimento'
    )
    idade = db.Column(
        db.Integer,
        nullable=True,
        comment='Idade calculada'
    )
    obito = db.Column(
        db.String(10),
        nullable=True,
        comment='Indicador de óbito'
    )
    
    cliente = db.relationship('Cliente', back_populates='data_nasc')
    
    def __repr__(self):
        return f'<DataNascimento {self.data_nasc}>'
