# -*- encoding: utf-8 -*-
"""
Formulários de Recursos Humanos
Funcionários e Equipes
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, BooleanField,
    DateField, DecimalField, IntegerField, HiddenField
)
from wtforms.validators import (
    DataRequired, Email, Optional, Length, ValidationError, Regexp
)

from apps.hr.models import (
    TeamType, EmployeeStatus, ContractType, 
    Gender, MaritalStatus, EducationLevel
)


# =============================================================================
# VALIDADORES CUSTOMIZADOS
# =============================================================================

def validate_cpf(form, field):
    """Valida CPF"""
    if not field.data:
        return
    
    cpf = ''.join(filter(str.isdigit, field.data))
    
    if len(cpf) != 11:
        raise ValidationError('CPF deve ter 11 dígitos')
    
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido')
    
    # Calcula primeiro dígito
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    d1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[9]) != d1:
        raise ValidationError('CPF inválido')
    
    # Calcula segundo dígito
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    d2 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[10]) != d2:
        raise ValidationError('CPF inválido')


def validate_cnpj(form, field):
    """Valida CNPJ"""
    if not field.data:
        return
    
    cnpj = ''.join(filter(str.isdigit, field.data))
    
    if len(cnpj) != 14:
        raise ValidationError('CNPJ deve ter 14 dígitos')
    
    if cnpj == cnpj[0] * 14:
        raise ValidationError('CNPJ inválido')
    
    # Primeiro dígito
    pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos[i] for i in range(12))
    resto = soma % 11
    d1 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj[12]) != d1:
        raise ValidationError('CNPJ inválido')
    
    # Segundo dígito
    pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos[i] for i in range(13))
    resto = soma % 11
    d2 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj[13]) != d2:
        raise ValidationError('CNPJ inválido')


# =============================================================================
# FORMULÁRIO DE EQUIPE/CORBAN
# =============================================================================

class TeamForm(FlaskForm):
    """Formulário de Equipe/Corban"""
    
    # Identificação
    name = StringField(
        'Nome',
        validators=[DataRequired(message='Nome é obrigatório'), Length(max=100)]
    )
    acronym = StringField(
        'Sigla',
        validators=[Optional(), Length(max=20)]
    )
    type = SelectField(
        'Tipo',
        choices=TeamType.CHOICES,
        default=TeamType.TEAM
    )
    
    # Dados da empresa
    cnpj = StringField(
        'CNPJ',
        validators=[Optional(), validate_cnpj]
    )
    legal_name = StringField(
        'Razão Social',
        validators=[Optional(), Length(max=150)]
    )
    trade_name = StringField(
        'Nome Fantasia',
        validators=[Optional(), Length(max=150)]
    )
    
    # Contato
    email = StringField(
        'E-mail',
        validators=[Optional(), Email(message='E-mail inválido'), Length(max=120)]
    )
    phone = StringField(
        'Telefone',
        validators=[Optional(), Length(max=20)]
    )
    
    # Financeiro
    pix = StringField(
        'Chave PIX',
        validators=[Optional(), Length(max=100)]
    )
    
    # Localização
    location = StringField(
        'Localização',
        validators=[Optional(), Length(max=200)]
    )
    
    # Configurações
    vacancies = IntegerField(
        'Vagas',
        validators=[Optional()],
        default=0
    )
    color = StringField(
        'Cor',
        validators=[Optional(), Length(max=7)],
        default='#206bc4'
    )
    
    # Status
    is_active = BooleanField(
        'Ativo',
        default=True
    )
    
    # Observações
    notes = TextAreaField(
        'Observações',
        validators=[Optional()]
    )


# =============================================================================
# FORMULÁRIO DE FUNCIONÁRIO
# =============================================================================

class EmployeeForm(FlaskForm):
    """Formulário completo de Funcionário"""
    
    # =============================
    # DADOS PESSOAIS
    # =============================
    
    cpf = StringField(
        'CPF',
        validators=[DataRequired(message='CPF é obrigatório'), validate_cpf]
    )
    name = StringField(
        'Nome Completo',
        validators=[DataRequired(message='Nome é obrigatório'), Length(max=100)]
    )
    birth_date = DateField(
        'Data de Nascimento',
        validators=[DataRequired(message='Data de nascimento é obrigatória')],
        format='%Y-%m-%d'
    )
    gender = SelectField(
        'Sexo',
        choices=[('', 'Selecione...')] + Gender.CHOICES,
        validators=[Optional()]
    )
    
    # Contato
    phone = StringField(
        'Telefone',
        validators=[Optional(), Length(max=20)]
    )
    phone_secondary = StringField(
        'Telefone Secundário',
        validators=[Optional(), Length(max=20)]
    )
    email = StringField(
        'E-mail',
        validators=[Optional(), Email(message='E-mail inválido'), Length(max=120)]
    )
    
    # Naturalidade
    birthplace_city = StringField(
        'Cidade de Nascimento',
        validators=[Optional(), Length(max=100)]
    )
    birthplace_state = SelectField(
        'UF de Nascimento',
        choices=[('', '')] + [(uf, uf) for uf in [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]],
        validators=[Optional()]
    )
    nationality = StringField(
        'Nacionalidade',
        validators=[Optional(), Length(max=50)],
        default='Brasileira'
    )
    
    # Estado civil e família
    marital_status = SelectField(
        'Estado Civil',
        choices=[('', 'Selecione...')] + MaritalStatus.CHOICES,
        validators=[Optional()]
    )
    father_name = StringField(
        'Nome do Pai',
        validators=[Optional(), Length(max=100)]
    )
    mother_name = StringField(
        'Nome da Mãe',
        validators=[Optional(), Length(max=100)]
    )
    
    # =============================
    # DOCUMENTOS
    # =============================
    
    # RG
    rg_number = StringField(
        'Número do RG',
        validators=[Optional(), Length(max=20)]
    )
    rg_issuer = StringField(
        'Órgão Emissor',
        validators=[Optional(), Length(max=20)]
    )
    rg_state = SelectField(
        'UF do RG',
        choices=[('', '')] + [(uf, uf) for uf in [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]],
        validators=[Optional()]
    )
    rg_issue_date = DateField(
        'Data de Emissão',
        validators=[Optional()],
        format='%Y-%m-%d'
    )
    
    # PIS
    pis = StringField(
        'PIS/PASEP',
        validators=[Optional(), Length(max=20)]
    )
    
    # Título de Eleitor
    voter_id = StringField(
        'Título de Eleitor',
        validators=[Optional(), Length(max=20)]
    )
    voter_zone = StringField(
        'Zona',
        validators=[Optional(), Length(max=10)]
    )
    voter_section = StringField(
        'Seção',
        validators=[Optional(), Length(max=10)]
    )
    
    # CTPS
    ctps_number = StringField(
        'Número da CTPS',
        validators=[Optional(), Length(max=20)]
    )
    ctps_series = StringField(
        'Série',
        validators=[Optional(), Length(max=10)]
    )
    ctps_state = SelectField(
        'UF da CTPS',
        choices=[('', '')] + [(uf, uf) for uf in [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]],
        validators=[Optional()]
    )
    ctps_issue_date = DateField(
        'Data de Emissão',
        validators=[Optional()],
        format='%Y-%m-%d'
    )
    
    # Escolaridade
    education_level = SelectField(
        'Grau de Instrução',
        choices=[('', 'Selecione...')] + EducationLevel.CHOICES,
        validators=[Optional()]
    )
    
    # =============================
    # ENDEREÇO
    # =============================
    
    address_zipcode = StringField(
        'CEP',
        validators=[Optional(), Length(max=8)]
    )
    address_street = StringField(
        'Logradouro',
        validators=[Optional(), Length(max=200)]
    )
    address_number = StringField(
        'Número',
        validators=[Optional(), Length(max=20)]
    )
    address_complement = StringField(
        'Complemento',
        validators=[Optional(), Length(max=100)]
    )
    address_neighborhood = StringField(
        'Bairro',
        validators=[Optional(), Length(max=100)]
    )
    address_city = StringField(
        'Cidade',
        validators=[Optional(), Length(max=100)]
    )
    address_state = SelectField(
        'UF',
        choices=[('', '')] + [(uf, uf) for uf in [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]],
        validators=[Optional()]
    )
    
    # =============================
    # DADOS PROFISSIONAIS
    # =============================
    
    team_id = SelectField(
        'Equipe/Corban',
        coerce=int,
        validators=[Optional()]
    )
    
    admission_date = DateField(
        'Data de Admissão',
        validators=[Optional()],
        format='%Y-%m-%d'
    )
    admission_origin = StringField(
        'Origem da Admissão',
        validators=[Optional(), Length(max=50)]
    )
    
    position = StringField(
        'Cargo',
        validators=[Optional(), Length(max=100)]
    )
    department = StringField(
        'Departamento',
        validators=[Optional(), Length(max=100)]
    )
    contract_type = SelectField(
        'Tipo de Contrato',
        choices=ContractType.CHOICES,
        default=ContractType.CLT
    )
    
    status = SelectField(
        'Status',
        choices=EmployeeStatus.CHOICES,
        default=EmployeeStatus.ACTIVE
    )
    
    is_salesperson = BooleanField(
        'É vendedor',
        default=False
    )
    
    # =============================
    # REMUNERAÇÃO
    # =============================
    
    salary = DecimalField(
        'Salário',
        validators=[Optional()],
        places=2
    )
    bonus = DecimalField(
        'Bônus/Comissão',
        validators=[Optional()],
        places=2
    )
    transport_allowance = DecimalField(
        'Vale Transporte',
        validators=[Optional()],
        places=2
    )
    meal_allowance = DecimalField(
        'Vale Refeição',
        validators=[Optional()],
        places=2
    )
    
    # =============================
    # DADOS BANCÁRIOS
    # =============================
    
    bank_name = StringField(
        'Banco',
        validators=[Optional(), Length(max=50)]
    )
    bank_code = StringField(
        'Código do Banco',
        validators=[Optional(), Length(max=10)]
    )
    bank_agency = StringField(
        'Agência',
        validators=[Optional(), Length(max=20)]
    )
    bank_account = StringField(
        'Conta',
        validators=[Optional(), Length(max=20)]
    )
    bank_account_type = SelectField(
        'Tipo de Conta',
        choices=[
            ('checking', 'Corrente'),
            ('savings', 'Poupança')
        ],
        default='checking'
    )
    pix_key = StringField(
        'Chave PIX',
        validators=[Optional(), Length(max=100)]
    )
    
    # =============================
    # FÉRIAS
    # =============================
    
    vacation_limit_date = DateField(
        'Data Limite Férias',
        validators=[Optional()],
        format='%Y-%m-%d'
    )
    last_vacation_date = DateField(
        'Últimas Férias',
        validators=[Optional()],
        format='%Y-%m-%d'
    )
    
    # =============================
    # OBSERVAÇÕES
    # =============================
    
    notes = TextAreaField(
        'Observações',
        validators=[Optional()]
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Carrega equipes para o select
        from apps.hr.models import Team
        teams = Team.get_active()
        self.team_id.choices = [('', 'Selecione...')] + [
            (t.id, t.display_name) for t in teams
        ]


class EmployeeSearchForm(FlaskForm):
    """Formulário de busca de funcionários"""
    
    search = StringField(
        'Buscar',
        validators=[Optional()]
    )
    team_id = SelectField(
        'Equipe',
        coerce=int,
        validators=[Optional()]
    )
    status = SelectField(
        'Status',
        choices=[('', 'Todos')] + EmployeeStatus.CHOICES,
        validators=[Optional()]
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.hr.models import Team
        teams = Team.get_active()
        self.team_id.choices = [('', 'Todas')] + [
            (t.id, t.display_name) for t in teams
        ]


class TerminationForm(FlaskForm):
    """Formulário de desligamento"""
    
    termination_date = DateField(
        'Data de Desligamento',
        validators=[DataRequired(message='Data é obrigatória')],
        format='%Y-%m-%d'
    )
    termination_reason = StringField(
        'Motivo',
        validators=[DataRequired(message='Motivo é obrigatório'), Length(max=100)]
    )
    notes = TextAreaField(
        'Observações',
        validators=[Optional()]
    )
