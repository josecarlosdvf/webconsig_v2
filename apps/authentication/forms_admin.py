# -*- encoding: utf-8 -*-
"""
Formulários de Administração de Usuários e Grupos
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, TextAreaField,
    SelectField, SelectMultipleField, HiddenField, EmailField
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError

from apps.authentication.models import Users, UserGroup, LoginTypeAllowed


class UserForm(FlaskForm):
    """Formulário de Cadastro/Edição de Usuário"""
    
    id = HiddenField()
    
    username = StringField(
        'Usuário',
        validators=[
            DataRequired(message='Informe o nome de usuário.'),
            Length(min=3, max=64, message='O usuário deve ter entre 3 e 64 caracteres.')
        ],
        render_kw={'placeholder': 'Nome de usuário'}
    )
    
    email = EmailField(
        'E-mail',
        validators=[
            DataRequired(message='Informe o e-mail.'),
            Email(message='E-mail inválido.')
        ],
        render_kw={'placeholder': 'email@exemplo.com'}
    )
    
    first_name = StringField(
        'Nome',
        validators=[Optional(), Length(max=64)],
        render_kw={'placeholder': 'Nome'}
    )
    
    last_name = StringField(
        'Sobrenome',
        validators=[Optional(), Length(max=64)],
        render_kw={'placeholder': 'Sobrenome'}
    )
    
    phone = StringField(
        'Telefone',
        validators=[Optional(), Length(max=20)],
        render_kw={'placeholder': '(00) 00000-0000'}
    )
    
    password = PasswordField(
        'Senha',
        validators=[
            Optional(),
            Length(min=6, message='A senha deve ter pelo menos 6 caracteres.')
        ],
        render_kw={'placeholder': 'Digite uma senha (deixe vazio para manter)'}
    )
    
    confirm_password = PasswordField(
        'Confirmar Senha',
        validators=[
            EqualTo('password', message='As senhas não conferem.')
        ],
        render_kw={'placeholder': 'Confirme a senha'}
    )
    
    login_type_allowed = SelectField(
        'Tipo de Login Permitido',
        choices=LoginTypeAllowed.CHOICES,
        default=LoginTypeAllowed.BOTH
    )
    
    is_active = BooleanField('Usuário Ativo', default=True)
    
    is_admin = BooleanField('Administrador')
    
    groups = SelectMultipleField(
        'Grupos',
        coerce=int,
        validators=[Optional()]
    )
    
    employee_id = SelectField(
        'Funcionário Vinculado',
        coerce=int,
        validators=[Optional()],
        choices=[]
    )
    
    team_id = SelectField(
        'Equipe/Corban',
        coerce=int,
        validators=[Optional()],
        choices=[]
    )
    
    bio = TextAreaField(
        'Observações',
        validators=[Optional(), Length(max=500)],
        render_kw={'placeholder': 'Observações sobre o usuário...', 'rows': 3}
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Carrega grupos disponíveis
        self.groups.choices = [
            (g.id, g.name) for g in UserGroup.get_active()
        ]
        # employee_id será preenchido na view
    
    def validate_username(self, field):
        """Valida se username é único"""
        user = Users.find_by_username(field.data)
        if user and (not self.id.data or int(self.id.data) != user.id):
            raise ValidationError('Este nome de usuário já está em uso.')
    
    def validate_email(self, field):
        """Valida se email é único"""
        user = Users.find_by_email(field.data)
        if user and (not self.id.data or int(self.id.data) != user.id):
            raise ValidationError('Este e-mail já está cadastrado.')


class UserGroupForm(FlaskForm):
    """Formulário de Cadastro/Edição de Grupo"""
    
    id = HiddenField()
    
    name = StringField(
        'Nome do Grupo',
        validators=[
            DataRequired(message='Informe o nome do grupo.'),
            Length(min=2, max=64, message='O nome deve ter entre 2 e 64 caracteres.')
        ],
        render_kw={'placeholder': 'Nome do grupo'}
    )
    
    description = TextAreaField(
        'Descrição',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'Descrição do grupo...', 'rows': 2}
    )
    
    is_active = BooleanField('Grupo Ativo', default=True)
    
    permissions = SelectMultipleField(
        'Permissões',
        coerce=int,
        validators=[Optional()]
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Permissões serão carregadas na view agrupadas por módulo
    
    def validate_name(self, field):
        """Valida se nome é único"""
        group = UserGroup.query.filter_by(name=field.data).first()
        if group and (not self.id.data or int(self.id.data) != group.id):
            raise ValidationError('Já existe um grupo com este nome.')


class InvitationForm(FlaskForm):
    """Formulário de Convite de Usuário"""
    
    email = EmailField(
        'E-mail do Convidado',
        validators=[
            DataRequired(message='Informe o e-mail.'),
            Email(message='E-mail inválido.')
        ],
        render_kw={'placeholder': 'email@exemplo.com'}
    )
    
    name = StringField(
        'Nome (opcional)',
        validators=[Optional(), Length(max=100)],
        render_kw={'placeholder': 'Nome do convidado'}
    )
    
    group_id = SelectField(
        'Grupo Inicial',
        coerce=int,
        validators=[Optional()]
    )
    
    employee_id = SelectField(
        'Vincular a Funcionário',
        coerce=int,
        validators=[Optional()],
        choices=[(0, '-- Selecione --')]
    )
    
    message = TextAreaField(
        'Mensagem Personalizada',
        validators=[Optional(), Length(max=1000)],
        render_kw={'placeholder': 'Mensagem que aparecerá no convite...', 'rows': 3}
    )
    
    expires_hours = SelectField(
        'Validade do Convite',
        coerce=int,
        choices=[
            (24, '24 horas'),
            (48, '48 horas'),
            (72, '72 horas'),
            (168, '7 dias'),
            (720, '30 dias')
        ],
        default=72
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_id.choices = [(0, '-- Selecione --')] + [
            (g.id, g.name) for g in UserGroup.get_active()
        ]
    
    def validate_email(self, field):
        """Verifica se já existe usuário com este e-mail"""
        user = Users.find_by_email(field.data)
        if user:
            raise ValidationError('Já existe um usuário cadastrado com este e-mail.')


class UnlockUserForm(FlaskForm):
    """Formulário para desbloquear usuário"""
    user_id = HiddenField(validators=[DataRequired()])


class ResetPasswordAdminForm(FlaskForm):
    """Formulário para admin resetar senha de usuário"""
    
    user_id = HiddenField(validators=[DataRequired()])
    
    new_password = PasswordField(
        'Nova Senha',
        validators=[
            DataRequired(message='Informe a nova senha.'),
            Length(min=6, message='A senha deve ter pelo menos 6 caracteres.')
        ],
        render_kw={'placeholder': 'Nova senha'}
    )
    
    confirm_password = PasswordField(
        'Confirmar Senha',
        validators=[
            DataRequired(message='Confirme a senha.'),
            EqualTo('new_password', message='As senhas não conferem.')
        ],
        render_kw={'placeholder': 'Confirme a nova senha'}
    )
    
    send_email = BooleanField('Enviar nova senha por e-mail', default=True)


class UserSearchForm(FlaskForm):
    """Formulário de busca de usuários"""
    
    search = StringField(
        'Buscar',
        validators=[Optional()],
        render_kw={'placeholder': 'Buscar por nome, usuário ou e-mail...'}
    )
    
    status = SelectField(
        'Status',
        choices=[
            ('', 'Todos'),
            ('active', 'Ativos'),
            ('inactive', 'Inativos'),
            ('locked', 'Bloqueados')
        ],
        default=''
    )
    
    group_id = SelectField(
        'Grupo',
        coerce=int,
        choices=[],
        default=0
    )
    
    is_admin = SelectField(
        'Tipo',
        choices=[
            ('', 'Todos'),
            ('1', 'Administradores'),
            ('0', 'Usuários comuns')
        ],
        default=''
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_id.choices = [(0, 'Todos os grupos')] + [
            (g.id, g.name) for g in UserGroup.get_active()
        ]


class CompleteRegistrationForm(FlaskForm):
    """Formulário para completar registro via convite"""
    
    token = HiddenField(validators=[DataRequired()])
    
    username = StringField(
        'Nome de Usuário',
        validators=[
            DataRequired(message='Escolha um nome de usuário.'),
            Length(min=3, max=64, message='O usuário deve ter entre 3 e 64 caracteres.')
        ],
        render_kw={'placeholder': 'Escolha um nome de usuário'}
    )
    
    password = PasswordField(
        'Senha',
        validators=[
            DataRequired(message='Escolha uma senha.'),
            Length(min=6, message='A senha deve ter pelo menos 6 caracteres.')
        ],
        render_kw={'placeholder': 'Escolha uma senha segura'}
    )
    
    confirm_password = PasswordField(
        'Confirmar Senha',
        validators=[
            DataRequired(message='Confirme a senha.'),
            EqualTo('password', message='As senhas não conferem.')
        ],
        render_kw={'placeholder': 'Digite a senha novamente'}
    )
    
    first_name = StringField(
        'Nome',
        validators=[Optional(), Length(max=64)],
        render_kw={'placeholder': 'Seu nome'}
    )
    
    last_name = StringField(
        'Sobrenome',
        validators=[Optional(), Length(max=64)],
        render_kw={'placeholder': 'Seu sobrenome'}
    )
    
    agree_terms = BooleanField(
        'Li e aceito os termos de uso',
        validators=[DataRequired(message='Você deve aceitar os termos de uso.')]
    )
    
    def validate_username(self, field):
        """Valida se username é único"""
        user = Users.find_by_username(field.data)
        if user:
            raise ValidationError('Este nome de usuário já está em uso.')
