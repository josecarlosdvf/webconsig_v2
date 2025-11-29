# -*- encoding: utf-8 -*-
"""
Formulários de Configurações
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Optional, Length


class SettingForm(FlaskForm):
    """Formulário para edição de configuração individual"""
    value = StringField('Valor', validators=[Optional(), Length(max=500)])


class SystemInfoForm(FlaskForm):
    """Formulário de informações do sistema"""
    app_name = StringField('Nome do Sistema', validators=[DataRequired(), Length(max=100)])
    app_description = TextAreaField('Descrição', validators=[Optional(), Length(max=500)])
    app_version = StringField('Versão', validators=[Optional(), Length(max=20)])


class CompanyForm(FlaskForm):
    """Formulário de dados da empresa"""
    company_name = StringField('Nome da Empresa', validators=[DataRequired(), Length(max=200)])
    company_cnpj = StringField('CNPJ', validators=[Optional(), Length(max=20)])
    company_address = TextAreaField('Endereço', validators=[Optional(), Length(max=500)])
    company_phone = StringField('Telefone', validators=[Optional(), Length(max=20)])
    company_email = StringField('E-mail', validators=[Optional(), Length(max=100)])


class DeveloperForm(FlaskForm):
    """Formulário de dados do desenvolvedor"""
    developer_name = StringField('Nome da Desenvolvedora', validators=[DataRequired(), Length(max=200)])
    developer_url = StringField('Site', validators=[Optional(), Length(max=200)])
    developer_email = StringField('E-mail', validators=[Optional(), Length(max=100)])


class AppearanceForm(FlaskForm):
    """Formulário de aparência"""
    logo_url = StringField('Logo', validators=[Optional(), Length(max=500)])
    logo_dark_url = StringField('Logo (Tema Escuro)', validators=[Optional(), Length(max=500)])
    favicon_url = StringField('Favicon', validators=[Optional(), Length(max=500)])
    primary_color = StringField('Cor Primária', validators=[Optional(), Length(max=10)])
    secondary_color = StringField('Cor Secundária', validators=[Optional(), Length(max=10)])


class LocalizationForm(FlaskForm):
    """Formulário de localização"""
    language = SelectField('Idioma', choices=[
        ('pt-BR', 'Português (Brasil)'),
        ('en-US', 'English (US)'),
        ('es-ES', 'Español'),
    ])
    timezone = SelectField('Fuso Horário', choices=[
        ('America/Sao_Paulo', 'Brasília (GMT-3)'),
        ('America/Manaus', 'Manaus (GMT-4)'),
        ('America/Rio_Branco', 'Rio Branco (GMT-5)'),
        ('America/Noronha', 'Fernando de Noronha (GMT-2)'),
    ])
    date_format = SelectField('Formato de Data', choices=[
        ('DD/MM/YYYY', 'DD/MM/AAAA'),
        ('MM/DD/YYYY', 'MM/DD/AAAA'),
        ('YYYY-MM-DD', 'AAAA-MM-DD'),
    ])
    currency = SelectField('Moeda', choices=[
        ('BRL', 'Real Brasileiro (R$)'),
        ('USD', 'Dólar Americano ($)'),
        ('EUR', 'Euro (€)'),
    ])


class SecurityForm(FlaskForm):
    """Formulário de segurança"""
    session_timeout = StringField('Tempo de Sessão (segundos)', validators=[Optional()])
    max_login_attempts = StringField('Tentativas de Login', validators=[Optional()])
    password_min_length = StringField('Tamanho Mínimo da Senha', validators=[Optional()])
    maintenance_mode = BooleanField('Modo Manutenção')
