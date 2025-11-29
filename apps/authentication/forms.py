# -*- encoding: utf-8 -*-
"""
Formulários de Autenticação
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


class LoginForm(FlaskForm):
    """Formulário de Login"""
    
    username = StringField(
        'Usuário',
        id='username_login',
        validators=[
            DataRequired(message='Informe o usuário ou e-mail.')
        ],
        render_kw={'placeholder': 'Digite seu usuário ou e-mail'}
    )
    
    password = PasswordField(
        'Senha',
        id='pwd_login',
        validators=[
            DataRequired(message='Informe a senha.')
        ],
        render_kw={'placeholder': 'Digite sua senha'}
    )
    
    remember = BooleanField('Lembrar-me')


class CreateAccountForm(FlaskForm):
    """Formulário de Criação de Conta"""
    
    username = StringField(
        'Usuário',
        id='username_create',
        validators=[
            DataRequired(message='Informe o nome de usuário.'),
            Length(min=3, max=64, message='O usuário deve ter entre 3 e 64 caracteres.')
        ],
        render_kw={'placeholder': 'Escolha um nome de usuário'}
    )
    
    email = StringField(
        'E-mail',
        id='email_create',
        validators=[
            DataRequired(message='Informe o e-mail.'),
            Email(message='E-mail inválido.')
        ],
        render_kw={'placeholder': 'seu@email.com'}
    )
    
    password = PasswordField(
        'Senha',
        id='pwd_create',
        validators=[
            DataRequired(message='Informe a senha.'),
            Length(min=6, message='A senha deve ter pelo menos 6 caracteres.')
        ],
        render_kw={'placeholder': 'Digite uma senha segura'}
    )
    
    confirm_password = PasswordField(
        'Confirmar Senha',
        id='pwd_confirm',
        validators=[
            DataRequired(message='Confirme a senha.'),
            EqualTo('password', message='As senhas não conferem.')
        ],
        render_kw={'placeholder': 'Digite a senha novamente'}
    )
    
    agree_terms = BooleanField(
        'Li e aceito os termos de uso',
        validators=[DataRequired(message='Você deve aceitar os termos de uso.')]
    )


class ForgotPasswordForm(FlaskForm):
    """Formulário de Recuperação de Senha"""
    
    email = StringField(
        'E-mail',
        validators=[
            DataRequired(message='Informe o e-mail.'),
            Email(message='E-mail inválido.')
        ],
        render_kw={'placeholder': 'Digite seu e-mail cadastrado'}
    )


class ResetPasswordForm(FlaskForm):
    """Formulário de Redefinição de Senha"""
    
    password = PasswordField(
        'Nova Senha',
        validators=[
            DataRequired(message='Informe a nova senha.'),
            Length(min=6, message='A senha deve ter pelo menos 6 caracteres.')
        ],
        render_kw={'placeholder': 'Digite a nova senha'}
    )
    
    confirm_password = PasswordField(
        'Confirmar Nova Senha',
        validators=[
            DataRequired(message='Confirme a nova senha.'),
            EqualTo('password', message='As senhas não conferem.')
        ],
        render_kw={'placeholder': 'Digite a nova senha novamente'}
    )


class ProfileForm(FlaskForm):
    """Formulário de Perfil do Usuário"""
    
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
    
    phone = StringField(
        'Telefone',
        validators=[Optional(), Length(max=20)],
        render_kw={'placeholder': '(00) 00000-0000'}
    )
    
    bio = TextAreaField(
        'Sobre mim',
        validators=[Optional(), Length(max=500)],
        render_kw={'placeholder': 'Conte um pouco sobre você...', 'rows': 4}
    )


class ChangePasswordForm(FlaskForm):
    """Formulário de Alteração de Senha"""
    
    current_password = PasswordField(
        'Senha Atual',
        validators=[
            DataRequired(message='Informe a senha atual.')
        ],
        render_kw={'placeholder': 'Digite sua senha atual'}
    )
    
    new_password = PasswordField(
        'Nova Senha',
        validators=[
            DataRequired(message='Informe a nova senha.'),
            Length(min=6, message='A senha deve ter pelo menos 6 caracteres.')
        ],
        render_kw={'placeholder': 'Digite a nova senha'}
    )
    
    confirm_password = PasswordField(
        'Confirmar Nova Senha',
        validators=[
            DataRequired(message='Confirme a nova senha.'),
            EqualTo('new_password', message='As senhas não conferem.')
        ],
        render_kw={'placeholder': 'Digite a nova senha novamente'}
    )
