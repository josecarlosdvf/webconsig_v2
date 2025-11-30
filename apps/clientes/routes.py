# -*- encoding: utf-8 -*-
"""
Rotas de Gestão de Clientes
CRUD completo de Clientes e entidades relacionadas
"""

import hashlib
from flask import (
    render_template, request, redirect, url_for, 
    flash, jsonify, abort
)
from flask_login import login_required, current_user

from apps import db
from apps.clientes import blueprint
from apps.clientes.models import (
    Cliente, Telefone, Endereco, Email, 
    Identidade, DadosBancarios, Matricula, DataNascimento
)
from apps.clientes.forms import (
    ClienteForm, ClienteSearchForm, TelefoneForm, 
    EnderecoForm, EmailClienteForm, IdentidadeForm,
    DadosBancariosForm, MatriculaForm, DataNascimentoForm
)
from apps.database.models import AuditLog
from apps.files.services import FileService, FileValidationError
from apps.files.models import FileCategory


def cpf_to_entity_id(cpf_clean):
    """
    Converts CPF to a deterministic entity_id for file association.
    Uses SHA256 hash truncated to fit in an integer.
    """
    hash_hex = hashlib.sha256(cpf_clean.encode()).hexdigest()[:9]
    return int(hash_hex, 16) % (10 ** 9)


# =============================================================================
# LISTAGEM E BUSCA
# =============================================================================

@blueprint.route('/')
@login_required
def clientes_list():
    """Lista de clientes"""
    form = ClienteSearchForm(request.args)
    
    query = Cliente.query_active()
    
    # Filtro de busca
    if form.search.data:
        term = form.search.data.strip()
        cpf_term = ''.join(filter(str.isdigit, term))
        if cpf_term and len(cpf_term) >= 3:
            query = query.filter(Cliente.cpf.like(f'%{cpf_term}%'))
        else:
            query = query.filter(Cliente.nome_completo.ilike(f'%{term}%'))
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = query.order_by(Cliente.nome_completo).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        'clientes/list.html',
        clientes=pagination.items,
        pagination=pagination,
        form=form
    )


# =============================================================================
# CRIAR CLIENTE
# =============================================================================

@blueprint.route('/novo', methods=['GET', 'POST'])
@login_required
def cliente_create():
    """Criar novo cliente"""
    form = ClienteForm()
    
    if form.validate_on_submit():
        # Limpa CPF
        cpf = ''.join(filter(str.isdigit, form.cpf.data))
        
        # Verifica se CPF já existe
        existing = Cliente.get_by_cpf(cpf)
        if existing:
            flash('Já existe um cliente com este CPF.', 'danger')
            return render_template('clientes/form.html', form=form, title='Novo Cliente')
        
        cliente = Cliente(
            cpf=cpf,
            nome_completo=form.nome_completo.data
        )
        
        db.session.add(cliente)
        db.session.commit()
        
        AuditLog.log(
            action='create',
            table_name='clientes',
            record_id=None,
            description=f'Cliente criado: {cliente.nome_completo} (CPF: {cliente.cpf_formatted})'
        )
        db.session.commit()
        
        flash('Cliente criado com sucesso!', 'success')
        return redirect(url_for('clientes_blueprint.cliente_view', cpf=cpf))
    
    return render_template(
        'clientes/form.html',
        form=form,
        title='Novo Cliente'
    )


# =============================================================================
# VISUALIZAR CLIENTE
# =============================================================================

@blueprint.route('/<cpf>')
@login_required
def cliente_view(cpf):
    """Visualizar cliente e todas as informações relacionadas"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    cliente = Cliente.get_by_cpf(cpf_clean)
    
    if not cliente:
        abort(404)
    
    # Busca arquivos do cliente usando hash determinístico do CPF
    entity_id = cpf_to_entity_id(cpf_clean)
    files = FileService.get_entity_files('cliente', entity_id)
    missing_files = FileService.get_missing_required('cliente', entity_id)
    
    # Busca categorias de arquivo disponíveis para clientes
    categories = FileCategory.query_active().filter(
        FileCategory.entity_types.contains('cliente')
    ).order_by(FileCategory.display_order).all()
    
    return render_template(
        'clientes/view.html',
        cliente=cliente,
        files=files,
        missing_files=missing_files,
        categories=categories,
        entity_id=entity_id
    )


# =============================================================================
# EDITAR CLIENTE
# =============================================================================

@blueprint.route('/<cpf>/editar', methods=['GET', 'POST'])
@login_required
def cliente_edit(cpf):
    """Editar cliente"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    cliente = Cliente.get_by_cpf(cpf_clean)
    
    if not cliente:
        abort(404)
    
    form = ClienteForm(obj=cliente)
    
    if form.validate_on_submit():
        cliente.nome_completo = form.nome_completo.data
        
        db.session.commit()
        
        AuditLog.log(
            action='update',
            table_name='clientes',
            record_id=None,
            description=f'Cliente atualizado: {cliente.nome_completo}'
        )
        db.session.commit()
        
        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('clientes_blueprint.cliente_view', cpf=cliente.cpf))
    
    return render_template(
        'clientes/form.html',
        form=form,
        cliente=cliente,
        title='Editar Cliente'
    )


# =============================================================================
# EXCLUIR CLIENTE
# =============================================================================

@blueprint.route('/<cpf>/excluir', methods=['POST'])
@login_required
def cliente_delete(cpf):
    """Excluir cliente (soft delete)"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    cliente = Cliente.get_by_cpf(cpf_clean)
    
    if not cliente:
        abort(404)
    
    cliente.soft_delete(current_user.id)
    
    AuditLog.log(
        action='delete',
        table_name='clientes',
        record_id=None,
        description=f'Cliente excluído: {cliente.nome_completo} (CPF: {cliente.cpf_formatted})'
    )
    db.session.commit()
    
    flash('Cliente excluído com sucesso!', 'success')
    return redirect(url_for('clientes_blueprint.clientes_list'))


# =============================================================================
# TELEFONES
# =============================================================================

@blueprint.route('/<cpf>/telefones/novo', methods=['GET', 'POST'])
@login_required
def telefone_create(cpf):
    """Adicionar telefone ao cliente"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    cliente = Cliente.get_by_cpf(cpf_clean)
    
    if not cliente:
        abort(404)
    
    form = TelefoneForm()
    
    if request.method == 'POST':
        telefone = Telefone(
            cpf=cliente.cpf,
            telefone=form.telefone.data,
            tipo=form.tipo.data,
            status=form.status.data,
            ranking=form.ranking.data or 0,
            score=form.score.data or 0
        )
        
        db.session.add(telefone)
        db.session.commit()
        
        flash('Telefone adicionado com sucesso!', 'success')
        return redirect(url_for('clientes_blueprint.cliente_view', cpf=cliente.cpf))
    
    return render_template(
        'clientes/telefone_form.html',
        form=form,
        cliente=cliente,
        title='Novo Telefone'
    )


@blueprint.route('/<cpf>/telefones/<int:tel_id>/excluir', methods=['POST'])
@login_required
def telefone_delete(cpf, tel_id):
    """Excluir telefone"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    telefone = Telefone.query.filter_by(cpf=cpf_clean, id=tel_id).first()
    
    if not telefone:
        abort(404)
    
    db.session.delete(telefone)
    db.session.commit()
    
    flash('Telefone excluído com sucesso!', 'success')
    return redirect(url_for('clientes_blueprint.cliente_view', cpf=cpf_clean))


# =============================================================================
# ENDEREÇOS
# =============================================================================

@blueprint.route('/<cpf>/enderecos/novo', methods=['GET', 'POST'])
@login_required
def endereco_create(cpf):
    """Adicionar endereço ao cliente"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    cliente = Cliente.get_by_cpf(cpf_clean)
    
    if not cliente:
        abort(404)
    
    form = EnderecoForm()
    
    if request.method == 'POST':
        endereco = Endereco(
            cpf=cliente.cpf,
            logradouro=form.logradouro.data,
            numero=form.numero.data,
            complemento=form.complemento.data,
            bairro=form.bairro.data,
            cidade=form.cidade.data,
            uf=form.uf.data,
            cep=form.cep.data
        )
        
        db.session.add(endereco)
        db.session.commit()
        
        flash('Endereço adicionado com sucesso!', 'success')
        return redirect(url_for('clientes_blueprint.cliente_view', cpf=cliente.cpf))
    
    return render_template(
        'clientes/endereco_form.html',
        form=form,
        cliente=cliente,
        title='Novo Endereço'
    )


@blueprint.route('/<cpf>/enderecos/<int:end_id>/excluir', methods=['POST'])
@login_required
def endereco_delete(cpf, end_id):
    """Excluir endereço"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    endereco = Endereco.query.filter_by(cpf=cpf_clean, id=end_id).first()
    
    if not endereco:
        abort(404)
    
    db.session.delete(endereco)
    db.session.commit()
    
    flash('Endereço excluído com sucesso!', 'success')
    return redirect(url_for('clientes_blueprint.cliente_view', cpf=cpf_clean))


# =============================================================================
# EMAILS
# =============================================================================

@blueprint.route('/<cpf>/emails/novo', methods=['GET', 'POST'])
@login_required
def email_create(cpf):
    """Adicionar email ao cliente"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    cliente = Cliente.get_by_cpf(cpf_clean)
    
    if not cliente:
        abort(404)
    
    form = EmailClienteForm()
    
    if request.method == 'POST':
        email = Email(
            cpf=cliente.cpf,
            email=form.email.data,
            status=form.status.data
        )
        
        db.session.add(email)
        db.session.commit()
        
        flash('Email adicionado com sucesso!', 'success')
        return redirect(url_for('clientes_blueprint.cliente_view', cpf=cliente.cpf))
    
    return render_template(
        'clientes/email_form.html',
        form=form,
        cliente=cliente,
        title='Novo Email'
    )


@blueprint.route('/<cpf>/emails/<int:email_id>/excluir', methods=['POST'])
@login_required
def email_delete(cpf, email_id):
    """Excluir email"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    email = Email.query.filter_by(cpf=cpf_clean, id=email_id).first()
    
    if not email:
        abort(404)
    
    db.session.delete(email)
    db.session.commit()
    
    flash('Email excluído com sucesso!', 'success')
    return redirect(url_for('clientes_blueprint.cliente_view', cpf=cpf_clean))


# =============================================================================
# IDENTIDADES
# =============================================================================

@blueprint.route('/<cpf>/identidades/novo', methods=['GET', 'POST'])
@login_required
def identidade_create(cpf):
    """Adicionar identidade ao cliente"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    cliente = Cliente.get_by_cpf(cpf_clean)
    
    if not cliente:
        abort(404)
    
    form = IdentidadeForm()
    
    if request.method == 'POST':
        identidade = Identidade(
            cpf=cliente.cpf,
            rg=form.rg.data,
            orgao_emissor=form.orgao_emissor.data,
            data_emissao=form.data_emissao.data,
            nacionalidade=form.nacionalidade.data,
            naturalidade=form.naturalidade.data,
            profissao=form.profissao.data,
            estado_civil=form.estado_civil.data,
            sexo=form.sexo.data,
            nome_pai=form.nome_pai.data,
            nome_mae=form.nome_mae.data
        )
        
        db.session.add(identidade)
        db.session.commit()
        
        flash('Identidade adicionada com sucesso!', 'success')
        return redirect(url_for('clientes_blueprint.cliente_view', cpf=cliente.cpf))
    
    return render_template(
        'clientes/identidade_form.html',
        form=form,
        cliente=cliente,
        title='Nova Identidade'
    )


@blueprint.route('/<cpf>/identidades/<int:id_id>/excluir', methods=['POST'])
@login_required
def identidade_delete(cpf, id_id):
    """Excluir identidade"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    identidade = Identidade.query.filter_by(cpf=cpf_clean, id=id_id).first()
    
    if not identidade:
        abort(404)
    
    db.session.delete(identidade)
    db.session.commit()
    
    flash('Identidade excluída com sucesso!', 'success')
    return redirect(url_for('clientes_blueprint.cliente_view', cpf=cpf_clean))


# =============================================================================
# DADOS BANCÁRIOS
# =============================================================================

@blueprint.route('/<cpf>/dados-bancarios/novo', methods=['GET', 'POST'])
@login_required
def dados_bancarios_create(cpf):
    """Adicionar dados bancários ao cliente"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    cliente = Cliente.get_by_cpf(cpf_clean)
    
    if not cliente:
        abort(404)
    
    form = DadosBancariosForm()
    
    if request.method == 'POST':
        dados = DadosBancarios(
            cpf=cliente.cpf,
            numero_banco=form.numero_banco.data,
            banco=form.banco.data,
            agencia=form.agencia.data,
            conta=form.conta.data,
            data_abertura=form.data_abertura.data,
            chave_pix=form.chave_pix.data
        )
        
        db.session.add(dados)
        db.session.commit()
        
        flash('Dados bancários adicionados com sucesso!', 'success')
        return redirect(url_for('clientes_blueprint.cliente_view', cpf=cliente.cpf))
    
    return render_template(
        'clientes/dados_bancarios_form.html',
        form=form,
        cliente=cliente,
        title='Novos Dados Bancários'
    )


@blueprint.route('/<cpf>/dados-bancarios/<int:db_id>/excluir', methods=['POST'])
@login_required
def dados_bancarios_delete(cpf, db_id):
    """Excluir dados bancários"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    dados = DadosBancarios.query.filter_by(cpf=cpf_clean, id=db_id).first()
    
    if not dados:
        abort(404)
    
    db.session.delete(dados)
    db.session.commit()
    
    flash('Dados bancários excluídos com sucesso!', 'success')
    return redirect(url_for('clientes_blueprint.cliente_view', cpf=cpf_clean))


# =============================================================================
# MATRÍCULAS
# =============================================================================

@blueprint.route('/<cpf>/matriculas/novo', methods=['GET', 'POST'])
@login_required
def matricula_create(cpf):
    """Adicionar matrícula ao cliente"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    cliente = Cliente.get_by_cpf(cpf_clean)
    
    if not cliente:
        abort(404)
    
    form = MatriculaForm()
    
    if request.method == 'POST':
        matricula = Matricula(
            cpf=cliente.cpf,
            orgao=form.orgao.data,
            matricula=form.matricula.data,
            cod_categoria=form.cod_categoria.data,
            categoria=form.categoria.data,
            indicativo=form.indicativo.data,
            patente=form.patente.data
        )
        
        db.session.add(matricula)
        db.session.commit()
        
        flash('Matrícula adicionada com sucesso!', 'success')
        return redirect(url_for('clientes_blueprint.cliente_view', cpf=cliente.cpf))
    
    return render_template(
        'clientes/matricula_form.html',
        form=form,
        cliente=cliente,
        title='Nova Matrícula'
    )


@blueprint.route('/<cpf>/matriculas/<int:mat_id>/excluir', methods=['POST'])
@login_required
def matricula_delete(cpf, mat_id):
    """Excluir matrícula"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    matricula = Matricula.query.filter_by(cpf=cpf_clean, id=mat_id).first()
    
    if not matricula:
        abort(404)
    
    db.session.delete(matricula)
    db.session.commit()
    
    flash('Matrícula excluída com sucesso!', 'success')
    return redirect(url_for('clientes_blueprint.cliente_view', cpf=cpf_clean))


# =============================================================================
# DATA DE NASCIMENTO
# =============================================================================

@blueprint.route('/<cpf>/nascimento/editar', methods=['GET', 'POST'])
@login_required
def data_nascimento_edit(cpf):
    """Editar/criar data de nascimento do cliente"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    cliente = Cliente.get_by_cpf(cpf_clean)
    
    if not cliente:
        abort(404)
    
    form = DataNascimentoForm(obj=cliente.data_nasc)
    
    if request.method == 'POST':
        if cliente.data_nasc:
            # Atualiza existente
            cliente.data_nasc.data_nasc = form.data_nasc.data
            cliente.data_nasc.idade = form.idade.data
            cliente.data_nasc.obito = form.obito.data
        else:
            # Cria novo
            data_nasc = DataNascimento(
                cpf=cliente.cpf,
                data_nasc=form.data_nasc.data,
                idade=form.idade.data,
                obito=form.obito.data
            )
            db.session.add(data_nasc)
        
        db.session.commit()
        
        flash('Data de nascimento atualizada com sucesso!', 'success')
        return redirect(url_for('clientes_blueprint.cliente_view', cpf=cliente.cpf))
    
    return render_template(
        'clientes/data_nascimento_form.html',
        form=form,
        cliente=cliente,
        title='Data de Nascimento'
    )


# =============================================================================
# DOCUMENTOS/ARQUIVOS
# =============================================================================

@blueprint.route('/<cpf>/documentos/upload', methods=['POST'])
@login_required
def documento_upload(cpf):
    """Upload de documento para o cliente"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    cliente = Cliente.get_by_cpf(cpf_clean)
    
    if not cliente:
        abort(404)
    
    if 'file' not in request.files:
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('clientes_blueprint.cliente_view', cpf=cpf_clean))
    
    file = request.files['file']
    category_code = request.form.get('category_code')
    description = request.form.get('description', '')
    
    if not category_code:
        flash('Selecione uma categoria de documento.', 'danger')
        return redirect(url_for('clientes_blueprint.cliente_view', cpf=cpf_clean))
    
    try:
        # Usa hash determinístico do CPF como entity_id
        entity_id = cpf_to_entity_id(cpf_clean)
        
        file_record = FileService.upload(
            file=file,
            category_code=category_code,
            entity_type='cliente',
            entity_id=entity_id,
            uploaded_by_id=current_user.id,
            description=description
        )
        
        flash(f'Documento "{file_record.original_name}" enviado com sucesso!', 'success')
        
    except FileValidationError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash(f'Erro ao enviar documento: {str(e)}', 'danger')
    
    return redirect(url_for('clientes_blueprint.cliente_view', cpf=cpf_clean))


@blueprint.route('/<cpf>/documentos/<int:file_id>/excluir', methods=['POST'])
@login_required
def documento_delete(cpf, file_id):
    """Excluir documento do cliente"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    cliente = Cliente.get_by_cpf(cpf_clean)
    
    if not cliente:
        abort(404)
    
    try:
        FileService.delete(file_id, current_user.id)
        flash('Documento excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir documento: {str(e)}', 'danger')
    
    return redirect(url_for('clientes_blueprint.cliente_view', cpf=cpf_clean))


@blueprint.route('/<cpf>/documentos/<int:file_id>/download')
@login_required
def documento_download(cpf, file_id):
    """Download de documento do cliente"""
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    cliente = Cliente.get_by_cpf(cpf_clean)
    
    if not cliente:
        abort(404)
    
    try:
        return FileService.download(file_id)
    except Exception as e:
        flash(f'Erro ao baixar documento: {str(e)}', 'danger')
        return redirect(url_for('clientes_blueprint.cliente_view', cpf=cpf_clean))


# =============================================================================
# API / AJAX
# =============================================================================

@blueprint.route('/api/buscar')
@login_required
def api_cliente_search():
    """Busca de clientes (autocomplete)"""
    term = request.args.get('term', '')
    limit = request.args.get('limit', 10, type=int)
    
    if len(term) < 2:
        return jsonify([])
    
    clientes = Cliente.search(term, limit=limit)
    
    return jsonify([{
        'cpf': c.cpf,
        'cpf_formatted': c.cpf_formatted,
        'nome': c.nome_completo,
        'telefone': c.telefone_principal.telefone_formatted if c.telefone_principal else None,
        'email': c.email_principal.email if c.email_principal else None
    } for c in clientes])
