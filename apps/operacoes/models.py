# -*- encoding: utf-8 -*-
"""
Modelos de Operações/Contratos de Empréstimo
Tabelas, Operações, RPCs e Boletos
"""

from datetime import datetime
from decimal import Decimal

from apps import db
from apps.database.models import BaseModel, audited


# =============================================================================
# ENUMS E CONSTANTES
# =============================================================================

class TipoOperacao:
    """Tipos de operação"""
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


class StatusOperacao:
    """Status da operação"""
    DIGITACAO = 'digitacao'
    PENDENTE = 'pendente'
    ANALISE = 'analise'
    APROVADA = 'aprovada'
    AVERBADA = 'averbada'
    PAGA = 'paga'
    CANCELADA = 'cancelada'
    RECUSADA = 'recusada'
    
    CHOICES = [
        (DIGITACAO, 'Em Digitação'),
        (PENDENTE, 'Pendente'),
        (ANALISE, 'Em Análise'),
        (APROVADA, 'Aprovada'),
        (AVERBADA, 'Averbada'),
        (PAGA, 'Paga'),
        (CANCELADA, 'Cancelada'),
        (RECUSADA, 'Recusada')
    ]
    
    # Status que indicam operação finalizada
    FINALIZADOS = [PAGA, CANCELADA, RECUSADA]
    
    # Status que indicam sucesso
    SUCESSO = [APROVADA, AVERBADA, PAGA]


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
    operacoes = db.relationship(
        'Operacao',
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
    def operacoes_count(self):
        """Quantidade de operações vinculadas"""
        return self.operacoes.count()
    
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
# OPERAÇÃO / CONTRATO
# =============================================================================

@audited
class Operacao(db.Model, BaseModel):
    """
    Operação de empréstimo consignado.
    Contém todos os dados do contrato, cliente, valores e status.
    """
    
    __tablename__ = 'operacoes'
    
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
        comment='Usuário responsável pela operação'
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
        default=TipoOperacao.NOVO,
        index=True,
        comment='Tipo da operação'
    )
    quitacao = db.Column(
        db.Boolean,
        default=False,
        comment='Se é operação de quitação'
    )
    data_operacao = db.Column(
        db.DateTime,
        nullable=True,
        default=datetime.utcnow,
        comment='Data da operação'
    )
    banco = db.Column(
        db.String(50),
        nullable=True,
        index=True,
        comment='Banco da operação'
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
        comment='Origem da operação (loja, online, etc)'
    )
    
    # =============================
    # STATUS E DOCUMENTAÇÃO
    # =============================
    
    status = db.Column(
        db.String(50),
        nullable=False,
        default=StatusOperacao.DIGITACAO,
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
    
    tabela = db.relationship('Tabela', back_populates='operacoes')
    boletos = db.relationship(
        'BoletoOperacao',
        back_populates='operacao',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    rpcs = db.relationship(
        'RPCOperacao',
        back_populates='operacao',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f'<Operacao {self.id} - {self.cliente_nome_completo}>'
    
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
        for code, name in TipoOperacao.CHOICES:
            if code == self.tipo:
                return name
        return self.tipo
    
    @property
    def status_display(self):
        """Status formatado"""
        for code, name in StatusOperacao.CHOICES:
            if code == self.status:
                return name
        return self.status
    
    @property
    def status_badge_class(self):
        """Classe CSS para badge do status"""
        mapping = {
            StatusOperacao.DIGITACAO: 'bg-secondary',
            StatusOperacao.PENDENTE: 'bg-warning',
            StatusOperacao.ANALISE: 'bg-info',
            StatusOperacao.APROVADA: 'bg-primary',
            StatusOperacao.AVERBADA: 'bg-success',
            StatusOperacao.PAGA: 'bg-success',
            StatusOperacao.CANCELADA: 'bg-danger',
            StatusOperacao.RECUSADA: 'bg-danger'
        }
        return mapping.get(self.status, 'bg-secondary')
    
    @property
    def is_finalizada(self):
        """Verifica se operação está finalizada"""
        return self.status in StatusOperacao.FINALIZADOS
    
    @property
    def is_sucesso(self):
        """Verifica se operação foi bem sucedida"""
        return self.status in StatusOperacao.SUCESSO
    
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
        """Retorna arquivos da operação"""
        from apps.files.models import File, FileCategory
        
        query = File.query_active().filter_by(
            entity_type='operacao',
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
            FileCategory.entity_types.like('%operacao%')
        ).all()
        
        missing = []
        for category in required:
            existing = File.query_active().filter_by(
                entity_type='operacao',
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
        """Marca operação como averbada"""
        self.averbado = True
        self.data_averbacao = datetime.utcnow()
        self.usuario_averbacao = usuario
        self.status = StatusOperacao.AVERBADA
        db.session.commit()
    
    def cancelar(self, motivo, usuario):
        """Cancela a operação"""
        self.status = StatusOperacao.CANCELADA
        self.motivo_cancelamento = motivo
        self.data_cancelamento = datetime.utcnow()
        self.usuario_cancelamento = usuario
        db.session.commit()
    
    def atualizar_status(self, novo_status):
        """Atualiza o status da operação"""
        self.status = novo_status
        db.session.commit()
    
    def verificar_documentos(self):
        """Verifica e atualiza o flag de docs_ok"""
        self.docs_ok = self.documents_complete
        db.session.commit()
        return self.docs_ok
    
    @classmethod
    def get_by_cpf(cls, cpf):
        """Retorna operações de um CPF"""
        cpf_clean = ''.join(filter(str.isdigit, cpf))
        return cls.query_active().filter_by(
            cliente_cpf=cpf_clean
        ).order_by(cls.data_operacao.desc()).all()
    
    @classmethod
    def get_by_status(cls, status, limit=None):
        """Retorna operações por status"""
        query = cls.query_active().filter_by(
            status=status
        ).order_by(cls.data_operacao.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_pendentes(cls, limit=50):
        """Retorna operações pendentes"""
        return cls.query_active().filter(
            cls.status.notin_(StatusOperacao.FINALIZADOS)
        ).order_by(cls.data_operacao.desc()).limit(limit).all()
    
    @classmethod
    def search(cls, termo, limit=50):
        """Busca operações por nome, CPF ou código"""
        cpf_clean = ''.join(filter(str.isdigit, termo))
        
        return cls.query_active().filter(
            db.or_(
                cls.cliente_nome_completo.ilike(f'%{termo}%'),
                cls.cliente_cpf.like(f'%{cpf_clean}%'),
                cls.codigo_unico.ilike(f'%{termo}%')
            )
        ).order_by(cls.data_operacao.desc()).limit(limit).all()


# =============================================================================
# RPC (REFIN/PORT/CARTÃO)
# =============================================================================

@audited
class RPCOperacao(db.Model, BaseModel):
    """
    RPC - Refinanciamento/Portabilidade/Cartão vinculado a uma operação.
    Representa contratos que serão quitados ou refinanciados.
    """
    
    __tablename__ = 'operacoes_rpc'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Vínculo com operação
    operacao_id = db.Column(
        db.Integer,
        db.ForeignKey('operacoes.id', ondelete='CASCADE'),
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
    operacao = db.relationship('Operacao', back_populates='rpcs')
    
    def __repr__(self):
        return f'<RPCOperacao {self.id} - {self.tipo}>'
    
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
# BOLETO DA OPERAÇÃO
# =============================================================================

@audited
class BoletoOperacao(db.Model, BaseModel):
    """
    Boleto de pagamento da operação.
    Contém valores, comissões e controle de pagamento.
    """
    
    __tablename__ = 'operacoes_boletos'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Vínculo com operação
    operacao_id = db.Column(
        db.Integer,
        db.ForeignKey('operacoes.id', ondelete='CASCADE'),
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
    operacao = db.relationship('Operacao', back_populates='boletos')
    
    def __repr__(self):
        return f'<BoletoOperacao {self.id} - R$ {self.valor}>'
    
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
