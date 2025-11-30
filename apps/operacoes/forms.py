# -*- encoding: utf-8 -*-
"""
Formulários de Operações/Contratos
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, TextAreaField, BooleanField,
    FloatField, IntegerField, DateField, DateTimeField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange

from apps.operacoes.models import (
    TipoOperacao, StatusOperacao, TipoTabela, TipoRPC, StatusRPC
)


class TabelaForm(FlaskForm):
    """Formulário de tabela de empréstimo"""
    
    nome = StringField(
        'Nome',
        validators=[DataRequired(), Length(max=100)],
        render_kw={'placeholder': 'Nome da tabela'}
    )
    tipo = SelectField(
        'Tipo',
        choices=TipoTabela.CHOICES,
        validators=[DataRequired()]
    )
    orgao = StringField(
        'Órgão',
        validators=[Optional(), Length(max=50)],
        render_kw={'placeholder': 'INSS, Exército, etc'}
    )
    banco = StringField(
        'Banco',
        validators=[Optional(), Length(max=50)],
        render_kw={'placeholder': 'Nome do banco'}
    )
    num_parcelas = IntegerField(
        'Nº Parcelas',
        validators=[Optional(), NumberRange(min=1, max=999)],
        render_kw={'placeholder': '84'}
    )
    fator = FloatField(
        'Fator',
        validators=[Optional()],
        render_kw={'placeholder': '0.0000', 'step': '0.0001'}
    )
    idade_max = IntegerField(
        'Idade Máxima',
        validators=[Optional(), NumberRange(min=18, max=120)],
        render_kw={'placeholder': '80'}
    )
    
    # Comissões
    comissao_total = FloatField(
        'Comissão Total (%)',
        validators=[Optional()],
        render_kw={'placeholder': '0.00', 'step': '0.01'}
    )
    comissao_empresa = FloatField(
        'Comissão Empresa (%)',
        validators=[Optional()],
        render_kw={'placeholder': '0.00', 'step': '0.01'}
    )
    comissao_externos = FloatField(
        'Comissão Externos (%)',
        validators=[Optional()],
        render_kw={'placeholder': '0.00', 'step': '0.01'}
    )
    comissao_bonus = FloatField(
        'Comissão Bônus (%)',
        validators=[Optional()],
        render_kw={'placeholder': '0.00', 'step': '0.01'}
    )
    comissao_incidencia = FloatField(
        'Incidência',
        validators=[Optional()],
        render_kw={'placeholder': '0.00', 'step': '0.01'}
    )
    
    # Status
    ativa = BooleanField('Tabela Ativa', default=True)
    externos = BooleanField('Aceita Externos', default=False)
    
    # Observações
    observacoes = TextAreaField(
        'Observações',
        validators=[Optional()],
        render_kw={'rows': 3}
    )


class TabelaSearchForm(FlaskForm):
    """Formulário de busca de tabelas"""
    
    search = StringField(
        'Buscar',
        render_kw={'placeholder': 'Nome, órgão ou banco...'}
    )
    tipo = SelectField(
        'Tipo',
        choices=[('', 'Todos')] + TipoTabela.CHOICES,
        validators=[Optional()]
    )
    ativa = SelectField(
        'Status',
        choices=[('', 'Todos'), ('1', 'Ativas'), ('0', 'Inativas')],
        validators=[Optional()]
    )


class OperacaoForm(FlaskForm):
    """Formulário de operação/contrato"""
    
    # Cliente
    cliente_cpf = StringField(
        'CPF',
        validators=[DataRequired(), Length(max=14)],
        render_kw={'placeholder': '000.000.000-00', 'class': 'cpf-mask'}
    )
    cliente_nome_completo = StringField(
        'Nome Completo',
        validators=[DataRequired(), Length(max=200)],
        render_kw={'placeholder': 'Nome do cliente'}
    )
    telefone = StringField(
        'Telefone',
        validators=[Optional(), Length(max=20)],
        render_kw={'placeholder': '(00) 00000-0000', 'class': 'phone-mask'}
    )
    email = StringField(
        'E-mail',
        validators=[Optional(), Length(max=200)],
        render_kw={'placeholder': 'email@exemplo.com'}
    )
    
    # Responsável
    responsavel_usuario = StringField(
        'Responsável',
        validators=[Optional(), Length(max=60)]
    )
    responsavel_ponto = StringField(
        'Ponto de Venda',
        validators=[Optional(), Length(max=50)]
    )
    
    # Contrato
    tabela_id = SelectField(
        'Tabela',
        coerce=int,
        validators=[Optional()]
    )
    orgao = StringField(
        'Órgão',
        validators=[Optional(), Length(max=50)],
        render_kw={'placeholder': 'INSS, Exército, etc'}
    )
    matricula = StringField(
        'Matrícula',
        validators=[Optional(), Length(max=50)]
    )
    senha = StringField(
        'Senha',
        validators=[Optional(), Length(max=50)]
    )
    
    tipo = SelectField(
        'Tipo',
        choices=TipoOperacao.CHOICES,
        validators=[DataRequired()]
    )
    quitacao = BooleanField('Operação de Quitação', default=False)
    
    data_operacao = DateField(
        'Data da Operação',
        validators=[Optional()],
        format='%Y-%m-%d'
    )
    banco = StringField(
        'Banco',
        validators=[Optional(), Length(max=50)]
    )
    prazo = IntegerField(
        'Prazo (meses)',
        validators=[Optional(), NumberRange(min=1, max=999)]
    )
    margem = FloatField(
        'Margem',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    
    # Valores
    valor_parcela = FloatField(
        'Valor Parcela',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    valor_af = FloatField(
        'Valor AF',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    valor_liquido = FloatField(
        'Valor Líquido',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    saldo = FloatField(
        'Saldo',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    taxa = FloatField(
        'Taxa (%)',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    
    # Identificação
    codigo_unico = StringField(
        'Código Único',
        validators=[Optional(), Length(max=100)]
    )
    origem = StringField(
        'Origem',
        validators=[Optional(), Length(max=50)]
    )
    
    # Status
    status = SelectField(
        'Status',
        choices=StatusOperacao.CHOICES,
        validators=[DataRequired()]
    )
    
    # Observações
    obs = TextAreaField(
        'Observações',
        validators=[Optional()],
        render_kw={'rows': 3}
    )


class OperacaoSearchForm(FlaskForm):
    """Formulário de busca de operações"""
    
    search = StringField(
        'Buscar',
        render_kw={'placeholder': 'Nome, CPF ou código...'}
    )
    status = SelectField(
        'Status',
        choices=[('', 'Todos')] + StatusOperacao.CHOICES,
        validators=[Optional()]
    )
    tipo = SelectField(
        'Tipo',
        choices=[('', 'Todos')] + TipoOperacao.CHOICES,
        validators=[Optional()]
    )
    banco = StringField(
        'Banco',
        validators=[Optional()]
    )
    orgao = StringField(
        'Órgão',
        validators=[Optional()]
    )
    data_inicio = DateField(
        'De',
        validators=[Optional()],
        format='%Y-%m-%d'
    )
    data_fim = DateField(
        'Até',
        validators=[Optional()],
        format='%Y-%m-%d'
    )


class AverbacaoForm(FlaskForm):
    """Formulário de averbação"""
    
    data_averbacao = DateField(
        'Data da Averbação',
        validators=[DataRequired()],
        format='%Y-%m-%d'
    )
    obs = TextAreaField(
        'Observações',
        validators=[Optional()],
        render_kw={'rows': 3}
    )


class CancelamentoForm(FlaskForm):
    """Formulário de cancelamento"""
    
    motivo_cancelamento = TextAreaField(
        'Motivo do Cancelamento',
        validators=[DataRequired(), Length(max=200)],
        render_kw={'rows': 3, 'placeholder': 'Informe o motivo do cancelamento'}
    )


class RPCForm(FlaskForm):
    """Formulário de RPC"""
    
    tipo = SelectField(
        'Tipo',
        choices=TipoRPC.CHOICES,
        validators=[DataRequired()]
    )
    banco = StringField(
        'Banco',
        validators=[Optional(), Length(max=50)]
    )
    valor_parcela = FloatField(
        'Valor Parcela',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    restantes = IntegerField(
        'Parcelas Restantes',
        validators=[Optional(), NumberRange(min=0)]
    )
    saldo_devedor = FloatField(
        'Saldo Devedor',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    codigo_unico = StringField(
        'Código Único',
        validators=[Optional(), Length(max=100)]
    )
    boleto_vencimento = DateField(
        'Vencimento do Boleto',
        validators=[Optional()],
        format='%Y-%m-%d'
    )
    obs = TextAreaField(
        'Observações',
        validators=[Optional()],
        render_kw={'rows': 2}
    )


class BoletoForm(FlaskForm):
    """Formulário de boleto"""
    
    data = DateField(
        'Data',
        validators=[Optional()],
        format='%Y-%m-%d'
    )
    banco = StringField(
        'Banco',
        validators=[Optional(), Length(max=50)]
    )
    valor = FloatField(
        'Valor',
        validators=[DataRequired()],
        render_kw={'step': '0.01'}
    )
    
    # Comissões
    comissao_empresa = FloatField(
        'Comissão Empresa',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    comissao_bonus = FloatField(
        'Comissão Bônus',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    comissao_corretor = FloatField(
        'Comissão Corretor',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    comissao_ger_equipe = FloatField(
        'Comissão Ger. Equipe',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    comissao_ger_geral1 = FloatField(
        'Comissão Ger. Geral 1',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    comissao_ger_geral2 = FloatField(
        'Comissão Ger. Geral 2',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    comissao_ger_adm = FloatField(
        'Comissão Ger. ADM',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    comissao_adm1 = FloatField(
        'Comissão ADM 1',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    comissao_adm2 = FloatField(
        'Comissão ADM 2',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    comissao_lider1 = FloatField(
        'Comissão Líder 1',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    comissao_lider2 = FloatField(
        'Comissão Líder 2',
        validators=[Optional()],
        render_kw={'step': '0.01'}
    )
    
    # Controle
    deposito_confirmado = BooleanField('Depósito Confirmado', default=False)
    deposito_comissao_paga = BooleanField('Comissão Paga', default=False)


class FatoresDiariosForm(FlaskForm):
    """Formulário de fatores diários"""
    
    dia_01 = FloatField('Dia 01', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_02 = FloatField('Dia 02', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_03 = FloatField('Dia 03', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_04 = FloatField('Dia 04', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_05 = FloatField('Dia 05', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_06 = FloatField('Dia 06', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_07 = FloatField('Dia 07', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_08 = FloatField('Dia 08', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_09 = FloatField('Dia 09', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_10 = FloatField('Dia 10', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_11 = FloatField('Dia 11', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_12 = FloatField('Dia 12', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_13 = FloatField('Dia 13', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_14 = FloatField('Dia 14', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_15 = FloatField('Dia 15', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_16 = FloatField('Dia 16', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_17 = FloatField('Dia 17', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_18 = FloatField('Dia 18', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_19 = FloatField('Dia 19', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_20 = FloatField('Dia 20', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_21 = FloatField('Dia 21', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_22 = FloatField('Dia 22', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_23 = FloatField('Dia 23', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_24 = FloatField('Dia 24', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_25 = FloatField('Dia 25', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_26 = FloatField('Dia 26', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_27 = FloatField('Dia 27', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_28 = FloatField('Dia 28', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_29 = FloatField('Dia 29', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_30 = FloatField('Dia 30', validators=[Optional()], render_kw={'step': '0.0001'})
    dia_31 = FloatField('Dia 31', validators=[Optional()], render_kw={'step': '0.0001'})
