# -*- encoding: utf-8 -*-
"""
Modelos de Propostas/Contratos de Empréstimo
Tabelas, Propostas, RPCs e Boletos
"""

from datetime import datetime
from decimal import Decimal

from apps import db
from apps.database.models import BaseModel, audited


# =============================================================================
# STATUS DE PROPOSTA (Conforme especificação)
# =============================================================================

# Configuração de status - definida fora da classe para ser acessível
_STATUS_CONFIG = {
    'AGUARD_DIGITACAO':   {'seq': 1,  'ativo': True,  'desc': 'AGUARD. DIGITAÇÃO',    'etapa': 1, 'etapa_fin': 1, 'cor': 'AMARELO',    'css': 'warning'},
    'AGUARD_LIB_MARGEM':  {'seq': 2,  'ativo': True,  'desc': 'AGUARD. LIB. MARGEM',  'etapa': 1, 'etapa_fin': 3, 'cor': 'VERDE CL',   'css': 'success-lt'},
    'NOVO_QUITACAO':      {'seq': 3,  'ativo': False, 'desc': 'NOVO/QUITAÇÃO',        'etapa': 1, 'etapa_fin': 0, 'cor': None,         'css': 'secondary'},
    'SALDO_PAGO':         {'seq': 4,  'ativo': True,  'desc': 'SALDO PAGO',           'etapa': 1, 'etapa_fin': 4, 'cor': 'VERDE',      'css': 'success'},
    'REPASSE':            {'seq': 5,  'ativo': False, 'desc': 'REPASSE',              'etapa': 1, 'etapa_fin': 0, 'cor': None,         'css': 'secondary'},
    'AGUARD_CIP':         {'seq': 6,  'ativo': True,  'desc': 'AGUARD. CIP',          'etapa': 1, 'etapa_fin': 3, 'cor': 'VERDE CL',   'css': 'success-lt'},
    'INTEGRACAO_PROPOSTA':{'seq': 7,  'ativo': False, 'desc': 'INTEGRAÇÃO PROPOSTA',  'etapa': 1, 'etapa_fin': 0, 'cor': None,         'css': 'secondary'},
    'REFIN_DIGITADO':     {'seq': 8,  'ativo': False, 'desc': 'REFIN DIGITADO',       'etapa': 1, 'etapa_fin': 0, 'cor': None,         'css': 'secondary'},
    'CANCELADA':          {'seq': 9,  'ativo': True,  'desc': 'CANCELADA',            'etapa': 0, 'etapa_fin': 0, 'cor': 'VERME ESC',  'css': 'danger'},
    'DIGITADO_BANCO':     {'seq': 10, 'ativo': True,  'desc': 'DIGITADO NO BANCO',    'etapa': 1, 'etapa_fin': 2, 'cor': 'LARANJA',    'css': 'orange'},
    'AVERBADO':           {'seq': 11, 'ativo': True,  'desc': 'AVERBADO',             'etapa': 2, 'etapa_fin': 5, 'cor': 'VERDE ESC',  'css': 'green'},
    'PAGO_BANCO':         {'seq': 12, 'ativo': True,  'desc': 'PAGO PELO BANCO',      'etapa': 3, 'etapa_fin': 6, 'cor': 'AZUL',       'css': 'primary'},
    'COMISSAO_PAGA':      {'seq': 13, 'ativo': True,  'desc': 'COMISSÃO PAGA',        'etapa': 3, 'etapa_fin': 7, 'cor': 'AZUL ESC',   'css': 'blue'},
    'PENDENTE':           {'seq': 14, 'ativo': True,  'desc': 'PENDENTE',             'etapa': 1, 'etapa_fin': 3, 'cor': 'VERME CL',   'css': 'danger-lt'},
    'INTENCAO_CEF':       {'seq': 15, 'ativo': True,  'desc': 'INTENÇÃO CEF',         'etapa': 1, 'etapa_fin': 1, 'cor': 'AMARELO ES', 'css': 'warning-lt'},
    'AGUARD_ANAL_CEF':    {'seq': 16, 'ativo': True,  'desc': 'AGUARD. ANAL. CEF',    'etapa': 1, 'etapa_fin': 1, 'cor': 'AMAR CL',    'css': 'warning-lt'},
    'CTT_CEF_GERADO':     {'seq': 17, 'ativo': True,  'desc': 'CTT CEF GERADO',       'etapa': 1, 'etapa_fin': 1, 'cor': None,         'css': 'secondary'},
    'AVERB_PARCIAL':      {'seq': 18, 'ativo': True,  'desc': 'AVERB. PARCIAL',       'etapa': 1, 'etapa_fin': 4, 'cor': None,         'css': 'success-lt'},
}


class PropostaStatus:
    """
    Status das propostas com sequência, cores, etapas comercial/financeiro
    """
    
    # Constantes de status
    AGUARD_DIGITACAO = 'AGUARD_DIGITACAO'
    AGUARD_LIB_MARGEM = 'AGUARD_LIB_MARGEM'
    NOVO_QUITACAO = 'NOVO_QUITACAO'
    SALDO_PAGO = 'SALDO_PAGO'
    REPASSE = 'REPASSE'
    AGUARD_CIP = 'AGUARD_CIP'
    INTEGRACAO_PROPOSTA = 'INTEGRACAO_PROPOSTA'
    REFIN_DIGITADO = 'REFIN_DIGITADO'
    CANCELADA = 'CANCELADA'
    DIGITADO_BANCO = 'DIGITADO_BANCO'
    AVERBADO = 'AVERBADO'
    PAGO_BANCO = 'PAGO_BANCO'
    COMISSAO_PAGA = 'COMISSAO_PAGA'
    PENDENTE = 'PENDENTE'
    INTENCAO_CEF = 'INTENCAO_CEF'
    AGUARD_ANAL_CEF = 'AGUARD_ANAL_CEF'
    CTT_CEF_GERADO = 'CTT_CEF_GERADO'
    AVERB_PARCIAL = 'AVERB_PARCIAL'
    
    # Referência ao dicionário de configuração
    STATUS_CONFIG = _STATUS_CONFIG
    
    # Choices para SelectField (ordenado por sequência)
    CHOICES = sorted(
        [(k, v['desc']) for k, v in _STATUS_CONFIG.items()],
        key=lambda x: _STATUS_CONFIG[x[0]]['seq']
    )
    
    # Apenas status ativos
    CHOICES_ATIVOS = sorted(
        [(k, v['desc']) for k, v in _STATUS_CONFIG.items() if v['ativo']],
        key=lambda x: _STATUS_CONFIG[x[0]]['seq']
    )
    
    # Agrupamentos
    ETAPA_COMERCIAL = [k for k, v in _STATUS_CONFIG.items() if v['etapa'] == 1]
    ETAPA_AVERBACAO = [k for k, v in _STATUS_CONFIG.items() if v['etapa'] == 2]
    ETAPA_FINANCEIRO = [k for k, v in _STATUS_CONFIG.items() if v['etapa'] == 3]
    
    # Finalizados
    FINALIZADOS = ['CANCELADA', 'PAGO_BANCO', 'COMISSAO_PAGA']
    
    # Sucesso
    SUCESSO = ['AVERBADO', 'PAGO_BANCO', 'COMISSAO_PAGA', 'AVERB_PARCIAL']
    
    @classmethod
    def get_config(cls, status):
        """Retorna configuração de um status"""
        return cls.STATUS_CONFIG.get(status, {
            'seq': 0, 'ativo': False, 'desc': status, 
            'etapa': 0, 'etapa_fin': 0, 'cor': None, 'css': 'secondary'
        })
    
    @classmethod
    def get_badge_class(cls, status):
        """Retorna classe CSS do badge"""
        config = cls.get_config(status)
        css = config.get('css', 'secondary')
        return f'bg-{css}'
    
    @classmethod
    def get_display(cls, status):
        """Retorna nome para exibição"""
        config = cls.get_config(status)
        return config.get('desc', status)
    
    @classmethod
    def get_sequencia(cls, status):
        """Retorna sequência para ordenação"""
        config = cls.get_config(status)
        return config.get('seq', 0)
    
    @classmethod
    def get_etapa_comercial(cls, status):
        """Retorna etapa comercial"""
        config = cls.get_config(status)
        return config.get('etapa', 0)
    
    @classmethod
    def get_etapa_financeiro(cls, status):
        """Retorna etapa financeira"""
        config = cls.get_config(status)
        return config.get('etapa_fin', 0)
    
    @classmethod
    def is_ativo(cls, status):
        """Verifica se status está ativo"""
        config = cls.get_config(status)
        return config.get('ativo', False)


# =============================================================================
# ENUMS E CONSTANTES
# =============================================================================

class TipoProposta:
    """Tipos de proposta"""
    NOVO = 'novo'
    PORTABILIDADE = 'portabilidade'
    REFINANCIAMENTO = 'refinanciamento'
    MARGEM = 'margem'
    CARTAO = 'cartao'
    SAQUE = 'saque'
    
    CHOICES = [
        (NOVO, 'Novo'),
        (PORTABILIDADE, 'Portabilidade'),
        (REFINANCIAMENTO, 'Refinanciamento'),
        (MARGEM, 'Margem'),
        (CARTAO, 'Cartão'),
        (SAQUE, 'Saque')
    ]


class TipoRPC:
    """Tipos de RPC (Refin/Port/Cartão)"""
    REFIN = 'refin'
    PORT = 'port'
    CARTAO = 'cartao'
    SAQUE = 'saque'
    
    CHOICES = [
        (REFIN, 'Refinanciamento'),
        (PORT, 'Portabilidade'),
        (CARTAO, 'Cartão'),
        (SAQUE, 'Saque')
    ]


class StatusRPC:
    """Status do RPC"""
    PENDENTE = 'pendente'
    QUITADO = 'quitado'
    CANCELADO = 'cancelado'
    
    CHOICES = [
        (PENDENTE, 'Pendente'),
        (QUITADO, 'Quitado'),
        (CANCELADO, 'Cancelado')
    ]


class TipoTabela:
    """Tipos de tabela de empréstimo"""
    NOVO = 'novo'
    REFIN = 'refin'
    PORT = 'port'
    MARGEM = 'margem'
    CARTAO = 'cartao'
    
    CHOICES = [
        (NOVO, 'Novo'),
        (REFIN, 'Refinanciamento'),
        (PORT, 'Portabilidade'),
        (MARGEM, 'Margem'),
        (CARTAO, 'Cartão')
    ]


# =============================================================================
# TABELA DE EMPRÉSTIMO
# =============================================================================

@audited
class Tabela(db.Model, BaseModel):
    """
    Tabela de empréstimo consignado.
    Contém as configurações de prazo, taxas e comissões.
    """
    
    __tablename__ = 'tabelas'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação
    nome = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        comment='Nome da tabela'
    )
    tipo = db.Column(
        db.String(20),
        nullable=False,
        default=TipoTabela.NOVO,
        index=True,
        comment='Tipo: novo, refin, port, margem, cartao'
    )
    
    # Vínculo
    orgao = db.Column(
        db.String(50),
        nullable=True,
        index=True,
        comment='Órgão (INSS, Exército, etc)'
    )
    banco = db.Column(
        db.String(50),
        nullable=True,
        index=True,
        comment='Banco'
    )
    
    # Parâmetros
    num_parcelas = db.Column(
        db.Integer,
        nullable=True,
        comment='Número de parcelas'
    )
    fator = db.Column(
        db.Float,
        nullable=True,
        comment='Fator de conversão'
    )
    idade_max = db.Column(
        db.Integer,
        nullable=True,
        comment='Idade máxima permitida'
    )
    
    # Comissões
    comissao_total = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Comissão total (%)'
    )
    comissao_empresa = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Comissão empresa (%)'
    )
    comissao_externos = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Comissão externos (%)'
    )
    comissao_bonus = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Comissão bônus (%)'
    )
    comissao_incidencia = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Incidência de comissão'
    )
    
    # Status
    ativa = db.Column(
        db.Boolean,
        default=True,
        index=True,
        comment='Se a tabela está ativa'
    )
    externos = db.Column(
        db.Boolean,
        default=False,
        comment='Se aceita operações de externos/corbans'
    )
    
    # Observações
    observacoes = db.Column(
        db.Text,
        nullable=True,
        comment='Observações gerais'
    )
    
    # Relacionamentos
    fatores_diarios = db.relationship(
        'FatoresDiariosTabela',
        back_populates='tabela',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    propostas = db.relationship(
        'Proposta',
        back_populates='tabela',
        lazy='dynamic'
    )
    
    def __repr__(self):
        return f'<Tabela {self.nome}>'
    
    @property
    def display_name(self):
        """Nome para exibição"""
        parts = [self.nome]
        if self.banco:
            parts.insert(0, self.banco)
        if self.orgao:
            parts.insert(0, self.orgao)
        return ' - '.join(parts)
    
    @property
    def tipo_display(self):
        """Tipo formatado"""
        for code, name in TipoTabela.CHOICES:
            if code == self.tipo:
                return name
        return self.tipo
    
    @property
    def propostas_count(self):
        """Quantidade de propostas vinculadas"""
        return self.propostas.count()
    
    def get_fator_dia(self, dia):
        """Retorna o fator para um dia específico do mês"""
        fatores = self.fatores_diarios.first()
        if not fatores:
            return self.fator
        
        campo = f'dia_{str(dia).zfill(2)}'
        valor = getattr(fatores, campo, None)
        return valor or self.fator
    
    @classmethod
    def get_ativas(cls, tipo=None, orgao=None, banco=None):
        """Retorna tabelas ativas com filtros opcionais"""
        query = cls.query_active().filter_by(ativa=True)
        
        if tipo:
            query = query.filter_by(tipo=tipo)
        if orgao:
            query = query.filter_by(orgao=orgao)
        if banco:
            query = query.filter_by(banco=banco)
        
        return query.order_by(cls.nome).all()
    
    @classmethod
    def search(cls, termo, limit=20):
        """Busca tabelas por nome, órgão ou banco"""
        return cls.query_active().filter(
            db.or_(
                cls.nome.ilike(f'%{termo}%'),
                cls.orgao.ilike(f'%{termo}%'),
                cls.banco.ilike(f'%{termo}%')
            )
        ).order_by(cls.nome).limit(limit).all()


# =============================================================================
# FATORES DIÁRIOS DA TABELA
# =============================================================================

@audited
class FatoresDiariosTabela(db.Model, BaseModel):
    """
    Fatores diários para cálculo de empréstimo.
    Cada dia do mês pode ter um fator diferente.
    """
    
    __tablename__ = 'fatores_diarios_tabelas'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Vínculo com tabela
    tabela_id = db.Column(
        db.Integer,
        db.ForeignKey('tabelas.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Fatores por dia (1 a 31)
    dia_01 = db.Column(db.Float, nullable=True)
    dia_02 = db.Column(db.Float, nullable=True)
    dia_03 = db.Column(db.Float, nullable=True)
    dia_04 = db.Column(db.Float, nullable=True)
    dia_05 = db.Column(db.Float, nullable=True)
    dia_06 = db.Column(db.Float, nullable=True)
    dia_07 = db.Column(db.Float, nullable=True)
    dia_08 = db.Column(db.Float, nullable=True)
    dia_09 = db.Column(db.Float, nullable=True)
    dia_10 = db.Column(db.Float, nullable=True)
    dia_11 = db.Column(db.Float, nullable=True)
    dia_12 = db.Column(db.Float, nullable=True)
    dia_13 = db.Column(db.Float, nullable=True)
    dia_14 = db.Column(db.Float, nullable=True)
    dia_15 = db.Column(db.Float, nullable=True)
    dia_16 = db.Column(db.Float, nullable=True)
    dia_17 = db.Column(db.Float, nullable=True)
    dia_18 = db.Column(db.Float, nullable=True)
    dia_19 = db.Column(db.Float, nullable=True)
    dia_20 = db.Column(db.Float, nullable=True)
    dia_21 = db.Column(db.Float, nullable=True)
    dia_22 = db.Column(db.Float, nullable=True)
    dia_23 = db.Column(db.Float, nullable=True)
    dia_24 = db.Column(db.Float, nullable=True)
    dia_25 = db.Column(db.Float, nullable=True)
    dia_26 = db.Column(db.Float, nullable=True)
    dia_27 = db.Column(db.Float, nullable=True)
    dia_28 = db.Column(db.Float, nullable=True)
    dia_29 = db.Column(db.Float, nullable=True)
    dia_30 = db.Column(db.Float, nullable=True)
    dia_31 = db.Column(db.Float, nullable=True)
    
    # Auditoria adicional
    usuario_criacao = db.Column(db.String(50), nullable=True)
    usuario_atualizacao = db.Column(db.String(50), nullable=True)
    
    # Relacionamento
    tabela = db.relationship('Tabela', back_populates='fatores_diarios')
    
    def __repr__(self):
        return f'<FatoresDiariosTabela tabela_id={self.tabela_id}>'
    
    def get_fator(self, dia):
        """Retorna fator para o dia especificado"""
        campo = f'dia_{str(dia).zfill(2)}'
        return getattr(self, campo, None)
    
    def set_fator(self, dia, valor):
        """Define fator para o dia especificado"""
        campo = f'dia_{str(dia).zfill(2)}'
        setattr(self, campo, valor)
    
    def to_dict(self):
        """Retorna dicionário com todos os fatores"""
        return {
            f'dia_{str(i).zfill(2)}': getattr(self, f'dia_{str(i).zfill(2)}')
            for i in range(1, 32)
        }


# =============================================================================
# PROPOSTA / CONTRATO
# =============================================================================

@audited
class Proposta(db.Model, BaseModel):
    """
    Proposta de empréstimo consignado.
    Contém todos os dados do contrato, cliente, valores e status.
    """
    
    __tablename__ = 'propostas'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # =============================
    # DADOS DO CLIENTE
    # =============================
    
    cliente_cpf = db.Column(
        db.String(11),
        nullable=False,
        index=True,
        comment='CPF do cliente'
    )
    cliente_nome_completo = db.Column(
        db.String(200),
        nullable=False,
        comment='Nome completo do cliente'
    )
    
    # Contato
    telefone = db.Column(
        db.String(20),
        nullable=True,
        comment='Telefone de contato'
    )
    email = db.Column(
        db.String(200),
        nullable=True,
        comment='E-mail de contato'
    )
    
    # =============================
    # RESPONSÁVEL
    # =============================
    
    responsavel_usuario = db.Column(
        db.String(60),
        nullable=True,
        index=True,
        comment='Usuário responsável pela proposta'
    )
    responsavel_ponto = db.Column(
        db.String(50),
        nullable=True,
        comment='Ponto de venda responsável'
    )
    
    # =============================
    # VÍNCULO COM TABELA
    # =============================
    
    tabela_id = db.Column(
        db.Integer,
        db.ForeignKey('tabelas.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # =============================
    # DADOS DO CONTRATO
    # =============================
    
    orgao = db.Column(
        db.String(50),
        nullable=True,
        index=True,
        comment='Órgão pagador'
    )
    matricula = db.Column(
        db.String(50),
        nullable=True,
        comment='Matrícula do cliente'
    )
    senha = db.Column(
        db.String(50),
        nullable=True,
        comment='Senha do cliente (se necessário)'
    )
    
    tipo = db.Column(
        db.String(20),
        nullable=False,
        default=TipoProposta.NOVO,
        index=True,
        comment='Tipo da proposta'
    )
    quitacao = db.Column(
        db.Boolean,
        default=False,
        comment='Se é proposta de quitação'
    )
    data_proposta = db.Column(
        db.DateTime,
        nullable=True,
        default=datetime.utcnow,
        comment='Data da proposta'
    )
    banco = db.Column(
        db.String(50),
        nullable=True,
        index=True,
        comment='Banco da proposta'
    )
    prazo = db.Column(
        db.Integer,
        nullable=True,
        comment='Prazo em meses'
    )
    margem = db.Column(
        db.Float,
        nullable=True,
        comment='Margem disponível'
    )
    
    # =============================
    # VALORES
    # =============================
    
    valor_parcela = db.Column(
        db.Float,
        nullable=True,
        comment='Valor da parcela'
    )
    valor_af = db.Column(
        db.Float,
        nullable=True,
        comment='Valor AF (autorização financeira)'
    )
    valor_liquido = db.Column(
        db.Float,
        nullable=True,
        comment='Valor líquido para o cliente'
    )
    saldo = db.Column(
        db.Float,
        nullable=True,
        comment='Saldo devedor'
    )
    taxa = db.Column(
        db.Float,
        nullable=True,
        comment='Taxa de juros (%)'
    )
    
    # =============================
    # IDENTIFICAÇÃO
    # =============================
    
    codigo_unico = db.Column(
        db.String(100),
        nullable=True,
        unique=True,
        comment='Código único do contrato'
    )
    origem = db.Column(
        db.String(50),
        nullable=True,
        comment='Origem da proposta (loja, online, etc)'
    )
    
    # =============================
    # STATUS E DOCUMENTAÇÃO
    # =============================
    
    status = db.Column(
        db.String(50),
        nullable=False,
        default=PropostaStatus.AGUARD_DIGITACAO,
        index=True,
        comment='Status atual'
    )
    docs_ok = db.Column(
        db.Boolean,
        default=False,
        comment='Se a documentação está completa'
    )
    
    # Averbação
    averbado = db.Column(
        db.Boolean,
        default=False,
        comment='Se foi averbado'
    )
    data_averbacao = db.Column(
        db.DateTime,
        nullable=True,
        comment='Data da averbação'
    )
    usuario_averbacao = db.Column(
        db.String(50),
        nullable=True,
        comment='Usuário que averbou'
    )
    
    # Cancelamento
    motivo_cancelamento = db.Column(
        db.String(200),
        nullable=True,
        comment='Motivo do cancelamento'
    )
    data_cancelamento = db.Column(
        db.DateTime,
        nullable=True,
        comment='Data do cancelamento'
    )
    usuario_cancelamento = db.Column(
        db.String(50),
        nullable=True,
        comment='Usuário que cancelou'
    )
    
    # =============================
    # OBSERVAÇÕES
    # =============================
    
    obs = db.Column(
        db.Text,
        nullable=True,
        comment='Observações gerais'
    )
    
    # =============================
    # RELACIONAMENTOS
    # =============================
    
    tabela = db.relationship('Tabela', back_populates='propostas')
    boletos = db.relationship(
        'BoletoProposta',
        back_populates='proposta',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    rpcs = db.relationship(
        'RPCProposta',
        back_populates='proposta',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f'<Proposta {self.id} - {self.cliente_nome_completo}>'
    
    # =============================
    # PROPRIEDADES
    # =============================
    
    @property
    def cpf_formatted(self):
        """CPF formatado"""
        if not self.cliente_cpf:
            return None
        cpf = self.cliente_cpf.zfill(11)
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    
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
    
    @property
    def tipo_display(self):
        """Tipo formatado"""
        for code, name in TipoProposta.CHOICES:
            if code == self.tipo:
                return name
        return self.tipo
    
    @property
    def status_display(self):
        """Status formatado"""
        return PropostaStatus.get_display(self.status)
    
    @property
    def status_badge_class(self):
        """Classe CSS para badge do status"""
        return PropostaStatus.get_badge_class(self.status)
    
    @property
    def status_sequencia(self):
        """Sequência do status para ordenação"""
        return PropostaStatus.get_sequencia(self.status)
    
    @property
    def etapa_comercial(self):
        """Etapa comercial do status"""
        return PropostaStatus.get_etapa_comercial(self.status)
    
    @property
    def etapa_financeiro(self):
        """Etapa financeira do status"""
        return PropostaStatus.get_etapa_financeiro(self.status)
    
    @property
    def is_finalizada(self):
        """Verifica se proposta está finalizada"""
        return self.status in PropostaStatus.FINALIZADOS
    
    @property
    def is_sucesso(self):
        """Verifica se proposta foi bem sucedida"""
        return self.status in PropostaStatus.SUCESSO
    
    @property
    def total_boletos(self):
        """Soma dos valores dos boletos"""
        return sum(b.valor or 0 for b in self.boletos)
    
    @property
    def total_comissoes(self):
        """Soma das comissões dos boletos"""
        total = 0
        for b in self.boletos:
            total += b.comissao_empresa or 0
            total += b.comissao_bonus or 0
            total += b.comissao_corretor or 0
            total += b.comissao_ger_equipe or 0
            total += b.comissao_ger_geral1 or 0
            total += b.comissao_ger_geral2 or 0
            total += b.comissao_ger_adm or 0
            total += b.comissao_adm1 or 0
            total += b.comissao_adm2 or 0
            total += b.comissao_lider1 or 0
            total += b.comissao_lider2 or 0
        return total
    
    @property
    def rpcs_count(self):
        """Quantidade de RPCs"""
        return self.rpcs.count()
    
    @property
    def boletos_count(self):
        """Quantidade de boletos"""
        return self.boletos.count()
    
    @property
    def primeiro_nome_cliente(self):
        """Primeiro nome do cliente"""
        return self.cliente_nome_completo.split()[0] if self.cliente_nome_completo else ''
    
    def get_files(self, category_code=None):
        """Retorna arquivos da proposta"""
        from apps.files.models import File, FileCategory
        
        query = File.query_active().filter_by(
            entity_type='proposta',
            entity_id=self.id
        )
        
        if category_code:
            query = query.join(File.category).filter(
                FileCategory.code == category_code
            )
        
        return query.order_by(File.created_at.desc()).all()
    
    def get_missing_documents(self):
        """Retorna categorias de documentos obrigatórios que estão faltando"""
        from apps.files.models import File, FileCategory
        
        required = FileCategory.query_active().filter(
            FileCategory.is_required == True,
            FileCategory.entity_types.like('%proposta%')
        ).all()
        
        missing = []
        for category in required:
            existing = File.query_active().filter_by(
                entity_type='proposta',
                entity_id=self.id,
                category_id=category.id
            ).first()
            
            if not existing:
                missing.append(category)
        
        return missing
    
    @property
    def documents_complete(self):
        """Verifica se todos os documentos obrigatórios foram enviados"""
        return len(self.get_missing_documents()) == 0
    
    # =============================
    # MÉTODOS
    # =============================
    
    def averbar(self, usuario):
        """Marca proposta como averbada"""
        self.averbado = True
        self.data_averbacao = datetime.utcnow()
        self.usuario_averbacao = usuario
        self.status = PropostaStatus.AVERBADO
        db.session.commit()
    
    def cancelar(self, motivo, usuario):
        """Cancela a proposta"""
        self.status = PropostaStatus.CANCELADA
        self.motivo_cancelamento = motivo
        self.data_cancelamento = datetime.utcnow()
        self.usuario_cancelamento = usuario
        db.session.commit()
    
    def atualizar_status(self, novo_status):
        """Atualiza o status da proposta"""
        self.status = novo_status
        db.session.commit()
    
    def verificar_documentos(self):
        """Verifica e atualiza o flag de docs_ok"""
        self.docs_ok = self.documents_complete
        db.session.commit()
        return self.docs_ok
    
    @classmethod
    def get_by_cpf(cls, cpf):
        """Retorna propostas de um CPF"""
        cpf_clean = ''.join(filter(str.isdigit, cpf))
        return cls.query_active().filter_by(
            cliente_cpf=cpf_clean
        ).order_by(cls.data_proposta.desc()).all()
    
    @classmethod
    def get_by_status(cls, status, limit=None):
        """Retorna propostas por status"""
        query = cls.query_active().filter_by(
            status=status
        ).order_by(cls.data_proposta.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_pendentes(cls, limit=50):
        """Retorna propostas pendentes"""
        return cls.query_active().filter(
            cls.status.notin_(PropostaStatus.FINALIZADOS)
        ).order_by(cls.data_proposta.desc()).limit(limit).all()
    
    @classmethod
    def search(cls, termo, limit=50):
        """Busca propostas por nome, CPF ou código"""
        cpf_clean = ''.join(filter(str.isdigit, termo))
        
        return cls.query_active().filter(
            db.or_(
                cls.cliente_nome_completo.ilike(f'%{termo}%'),
                cls.cliente_cpf.like(f'%{cpf_clean}%'),
                cls.codigo_unico.ilike(f'%{termo}%')
            )
        ).order_by(cls.data_proposta.desc()).limit(limit).all()


# =============================================================================
# RPC (REFIN/PORT/CARTÃO)
# =============================================================================

@audited
class RPCProposta(db.Model, BaseModel):
    """
    RPC - Refinanciamento/Portabilidade/Cartão vinculado a uma proposta.
    Representa contratos que serão quitados ou refinanciados.
    """
    
    __tablename__ = 'propostas_rpc'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Vínculo com proposta
    proposta_id = db.Column(
        db.Integer,
        db.ForeignKey('propostas.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Dados do contrato a ser quitado
    tipo = db.Column(
        db.String(20),
        nullable=True,
        comment='Tipo: refin, port, cartao, saque'
    )
    banco = db.Column(
        db.String(50),
        nullable=True,
        comment='Banco do contrato original'
    )
    valor_parcela = db.Column(
        db.Float,
        nullable=True,
        comment='Valor da parcela atual'
    )
    restantes = db.Column(
        db.Integer,
        nullable=True,
        comment='Parcelas restantes'
    )
    saldo_devedor = db.Column(
        db.Float,
        nullable=True,
        comment='Saldo devedor total'
    )
    
    # Identificação
    codigo_unico = db.Column(
        db.String(100),
        nullable=True,
        comment='Código único do contrato original'
    )
    
    # Status
    status = db.Column(
        db.String(50),
        nullable=False,
        default=StatusRPC.PENDENTE,
        comment='Status do RPC'
    )
    
    # Boleto de quitação
    boleto_img = db.Column(
        db.String(255),
        nullable=True,
        comment='Caminho/ID do arquivo do boleto'
    )
    boleto_vencimento = db.Column(
        db.DateTime,
        nullable=True,
        comment='Vencimento do boleto'
    )
    
    # Observações
    obs = db.Column(
        db.Text,
        nullable=True,
        comment='Observações'
    )
    
    # Relacionamento
    proposta = db.relationship('Proposta', back_populates='rpcs')
    
    def __repr__(self):
        return f'<RPCProposta {self.id} - {self.tipo}>'
    
    @property
    def tipo_display(self):
        """Tipo formatado"""
        for code, name in TipoRPC.CHOICES:
            if code == self.tipo:
                return name
        return self.tipo
    
    @property
    def status_display(self):
        """Status formatado"""
        for code, name in StatusRPC.CHOICES:
            if code == self.status:
                return name
        return self.status
    
    @property
    def status_badge_class(self):
        """Classe CSS para badge do status"""
        mapping = {
            StatusRPC.PENDENTE: 'bg-warning',
            StatusRPC.QUITADO: 'bg-success',
            StatusRPC.CANCELADO: 'bg-danger'
        }
        return mapping.get(self.status, 'bg-secondary')
    
    def get_file(self):
        """Retorna arquivo anexo do RPC (boleto)"""
        from apps.files.models import File
        
        if self.boleto_img:
            # Se é um ID numérico
            try:
                file_id = int(self.boleto_img)
                return File.query_active().filter_by(id=file_id).first()
            except ValueError:
                pass
        
        # Busca por entity
        return File.query_active().filter_by(
            entity_type='rpc',
            entity_id=self.id
        ).first()
    
    def quitar(self):
        """Marca RPC como quitado"""
        self.status = StatusRPC.QUITADO
        db.session.commit()
    
    def cancelar(self):
        """Cancela o RPC"""
        self.status = StatusRPC.CANCELADO
        db.session.commit()


# =============================================================================
# BOLETO DA PROPOSTA
# =============================================================================

@audited
class BoletoProposta(db.Model, BaseModel):
    """
    Boleto de pagamento da proposta.
    Contém valores, comissões e controle de pagamento.
    """
    
    __tablename__ = 'propostas_boletos'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Vínculo com proposta
    proposta_id = db.Column(
        db.Integer,
        db.ForeignKey('propostas.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Dados do boleto
    data = db.Column(
        db.DateTime,
        nullable=True,
        comment='Data do boleto/pagamento'
    )
    banco = db.Column(
        db.String(50),
        nullable=True,
        comment='Banco do boleto'
    )
    valor = db.Column(
        db.Float,
        nullable=True,
        comment='Valor do boleto'
    )
    comprovante = db.Column(
        db.String(255),
        nullable=True,
        comment='Caminho/ID do arquivo do comprovante'
    )
    
    # Comissões
    comissao_empresa = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Comissão da empresa'
    )
    comissao_bonus = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Comissão bônus'
    )
    comissao_corretor = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Comissão do corretor'
    )
    comissao_ger_equipe = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Comissão gerente de equipe'
    )
    comissao_ger_geral1 = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Comissão gerente geral 1'
    )
    comissao_ger_geral2 = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Comissão gerente geral 2'
    )
    comissao_ger_adm = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Comissão gerente administrativo'
    )
    comissao_adm1 = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Comissão administrativa 1'
    )
    comissao_adm2 = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Comissão administrativa 2'
    )
    comissao_lider1 = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Comissão líder 1'
    )
    comissao_lider2 = db.Column(
        db.Float,
        nullable=True,
        default=0,
        comment='Comissão líder 2'
    )
    
    # Controle de pagamento
    deposito_confirmado = db.Column(
        db.Boolean,
        default=False,
        comment='Se o depósito foi confirmado'
    )
    deposito_comissao_paga = db.Column(
        db.Boolean,
        default=False,
        comment='Se a comissão foi paga'
    )
    
    # Relacionamento
    proposta = db.relationship('Proposta', back_populates='boletos')
    
    def __repr__(self):
        return f'<BoletoProposta {self.id} - R$ {self.valor}>'
    
    @property
    def total_comissoes(self):
        """Total de comissões do boleto"""
        return sum([
            self.comissao_empresa or 0,
            self.comissao_bonus or 0,
            self.comissao_corretor or 0,
            self.comissao_ger_equipe or 0,
            self.comissao_ger_geral1 or 0,
            self.comissao_ger_geral2 or 0,
            self.comissao_ger_adm or 0,
            self.comissao_adm1 or 0,
            self.comissao_adm2 or 0,
            self.comissao_lider1 or 0,
            self.comissao_lider2 or 0
        ])
    
    @property
    def valor_formatted(self):
        """Valor formatado em reais"""
        if self.valor is None:
            return 'R$ 0,00'
        return f'R$ {self.valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    
    def get_comprovante(self):
        """Retorna arquivo do comprovante"""
        from apps.files.models import File
        
        if self.comprovante:
            try:
                file_id = int(self.comprovante)
                return File.query_active().filter_by(id=file_id).first()
            except ValueError:
                pass
        
        return File.query_active().filter_by(
            entity_type='boleto',
            entity_id=self.id
        ).first()
    
    def confirmar_deposito(self):
        """Confirma o depósito do boleto"""
        self.deposito_confirmado = True
        db.session.commit()
    
    def pagar_comissao(self):
        """Marca comissão como paga"""
        self.deposito_comissao_paga = True
        db.session.commit()
