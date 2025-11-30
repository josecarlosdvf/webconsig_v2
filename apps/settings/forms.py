# -*- encoding: utf-8 -*-
"""
Formulários de Configurações
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
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
    # Upload de imagens
    logo_file = FileField('Logo do Sistema', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'svg', 'gif', 'webp'], 'Apenas imagens são permitidas!')
    ])
    logo_empresa_file = FileField('Logo da Empresa', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'svg', 'gif', 'webp'], 'Apenas imagens são permitidas!')
    ])
    logo_login_file = FileField('Logo do Login', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'svg', 'gif', 'webp'], 'Apenas imagens são permitidas!')
    ])
    logo_dark_file = FileField('Logo (Tema Escuro)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'svg', 'gif', 'webp'], 'Apenas imagens são permitidas!')
    ])
    favicon_file = FileField('Favicon', validators=[
        FileAllowed(['ico', 'png', 'svg'], 'Apenas .ico, .png ou .svg são permitidos!')
    ])
    
    # URLs (hidden, preenchidas após upload)
    logo_url = StringField('Logo URL', validators=[Optional(), Length(max=500)])
    logo_empresa_url = StringField('Logo Empresa URL', validators=[Optional(), Length(max=500)])
    logo_login_url = StringField('Logo Login URL', validators=[Optional(), Length(max=500)])
    logo_dark_url = StringField('Logo (Tema Escuro) URL', validators=[Optional(), Length(max=500)])
    favicon_url = StringField('Favicon URL', validators=[Optional(), Length(max=500)])
    
    # Cores
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


class ApiConsultaForm(FlaskForm):
    """Formulário de configurações de API para consulta de dados cadastrais"""
    api_consulta_provider = SelectField('Provedor da API', choices=[
        ('lemit', 'Lemit'),
        ('cpfcnpj', 'CPF/CNPJ Brasil'),
        ('serpro', 'Serpro'),
        ('bigdata', 'BigData Corp'),
        ('custom', 'Personalizado'),
    ])
    api_consulta_url = StringField('URL da API', validators=[Optional(), Length(max=500)])
    api_consulta_token = StringField('Token de Autenticação', validators=[Optional(), Length(max=500)])
    api_consulta_timeout = StringField('Timeout (segundos)', validators=[Optional()])
    api_consulta_cache_days = StringField('Dias de Cache', validators=[Optional()])
    api_consulta_enabled = BooleanField('API Habilitada')

