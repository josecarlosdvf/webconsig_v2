# -*- encoding: utf-8 -*-
"""
Formulários de Gestão de Clientes
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, 
    IntegerField, SubmitField, FieldList, FormField
)
from wtforms.validators import DataRequired, Optional, Length, Email


class TelefoneForm(FlaskForm):
    """Formulário de telefone"""
    telefone = StringField('Telefone', validators=[Optional(), Length(max=20)])
    tipo = SelectField('Tipo', choices=[
        ('', 'Selecione...'),
        ('celular', 'Celular'),
        ('fixo', 'Fixo'),
        ('comercial', 'Comercial'),
        ('recado', 'Recado'),
    ], validators=[Optional()])
    status = StringField('Status', validators=[Optional(), Length(max=30)])
    ranking = IntegerField('Ranking', validators=[Optional()], default=0)
    score = IntegerField('Score', validators=[Optional()], default=0)
    
    class Meta:
        csrf = False


class EnderecoForm(FlaskForm):
    """Formulário de endereço"""
    logradouro = StringField('Logradouro', validators=[Optional(), Length(max=150)])
    numero = StringField('Número', validators=[Optional(), Length(max=20)])
    complemento = StringField('Complemento', validators=[Optional(), Length(max=50)])
    bairro = StringField('Bairro', validators=[Optional(), Length(max=100)])
    cidade = StringField('Cidade', validators=[Optional(), Length(max=100)])
    uf = SelectField('UF', choices=[
        ('', 'Selecione...'),
        ('AC', 'AC'), ('AL', 'AL'), ('AP', 'AP'), ('AM', 'AM'), ('BA', 'BA'),
        ('CE', 'CE'), ('DF', 'DF'), ('ES', 'ES'), ('GO', 'GO'), ('MA', 'MA'),
        ('MT', 'MT'), ('MS', 'MS'), ('MG', 'MG'), ('PA', 'PA'), ('PB', 'PB'),
        ('PR', 'PR'), ('PE', 'PE'), ('PI', 'PI'), ('RJ', 'RJ'), ('RN', 'RN'),
        ('RS', 'RS'), ('RO', 'RO'), ('RR', 'RR'), ('SC', 'SC'), ('SP', 'SP'),
        ('SE', 'SE'), ('TO', 'TO'),
    ], validators=[Optional()])
    cep = StringField('CEP', validators=[Optional(), Length(max=20)])
    
    class Meta:
        csrf = False


class EmailClienteForm(FlaskForm):
    """Formulário de email"""
    email = StringField('Email', validators=[Optional(), Email(), Length(max=255)])
    status = StringField('Status', validators=[Optional(), Length(max=30)])
    
    class Meta:
        csrf = False


class IdentidadeForm(FlaskForm):
    """Formulário de identidade"""
    rg = StringField('RG', validators=[Optional(), Length(max=30)])
    orgao_emissor = StringField('Órgão Emissor', validators=[Optional(), Length(max=50)])
    data_emissao = StringField('Data Emissão', validators=[Optional(), Length(max=20)])
    nacionalidade = StringField('Nacionalidade', validators=[Optional(), Length(max=50)])
    naturalidade = StringField('Naturalidade', validators=[Optional(), Length(max=50)])
    profissao = StringField('Profissão', validators=[Optional(), Length(max=50)])
    estado_civil = SelectField('Estado Civil', choices=[
        ('', 'Selecione...'),
        ('Solteiro', 'Solteiro(a)'),
        ('Casado', 'Casado(a)'),
        ('Divorciado', 'Divorciado(a)'),
        ('Viúvo', 'Viúvo(a)'),
        ('Separado', 'Separado(a)'),
        ('União Estável', 'União Estável'),
    ], validators=[Optional()])
    sexo = SelectField('Sexo', choices=[
        ('', 'Selecione...'),
        ('M', 'Masculino'),
        ('F', 'Feminino'),
    ], validators=[Optional()])
    nome_pai = StringField('Nome do Pai', validators=[Optional(), Length(max=150)])
    nome_mae = StringField('Nome da Mãe', validators=[Optional(), Length(max=150)])
    
    class Meta:
        csrf = False


class DadosBancariosForm(FlaskForm):
    """Formulário de dados bancários"""
    numero_banco = StringField('Código Banco', validators=[Optional(), Length(max=10)])
    banco = StringField('Nome do Banco', validators=[Optional(), Length(max=150)])
    agencia = StringField('Agência', validators=[Optional(), Length(max=20)])
    conta = StringField('Conta', validators=[Optional(), Length(max=30)])
    data_abertura = StringField('Data Abertura', validators=[Optional(), Length(max=20)])
    chave_pix = StringField('Chave PIX', validators=[Optional(), Length(max=100)])
    
    class Meta:
        csrf = False


class MatriculaForm(FlaskForm):
    """Formulário de matrícula"""
    orgao = StringField('Órgão', validators=[Optional(), Length(max=50)])
    matricula = StringField('Matrícula', validators=[Optional(), Length(max=50)])
    cod_categoria = StringField('Cód. Categoria', validators=[Optional(), Length(max=10)])
    categoria = StringField('Categoria', validators=[Optional(), Length(max=80)])
    indicativo = StringField('Indicativo', validators=[Optional(), Length(max=20)])
    patente = StringField('Patente', validators=[Optional(), Length(max=50)])
    
    class Meta:
        csrf = False


class DataNascimentoForm(FlaskForm):
    """Formulário de data de nascimento"""
    data_nasc = StringField('Data de Nascimento', validators=[Optional(), Length(max=20)])
    idade = IntegerField('Idade', validators=[Optional()])
    obito = StringField('Óbito', validators=[Optional(), Length(max=10)])
    
    class Meta:
        csrf = False


class ClienteForm(FlaskForm):
    """Formulário principal de Cliente"""
    cpf = StringField('CPF', validators=[DataRequired(), Length(max=14)])
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(max=150)])
    
    submit = SubmitField('Salvar')


class ClienteSearchForm(FlaskForm):
    """Formulário de busca de clientes"""
    search = StringField('Buscar', validators=[Optional()])
    
    class Meta:
        csrf = False
