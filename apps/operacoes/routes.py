# -*- encoding: utf-8 -*-
"""
Rotas de Operações/Contratos de Empréstimo
CRUD completo de Tabelas, Operações, RPCs e Boletos
"""

from datetime import datetime

from flask import (
    render_template, request, redirect, url_for,
    flash, jsonify, abort
)
from flask_login import login_required, current_user

from apps import db
from apps.operacoes import blueprint
from apps.operacoes.models import (
    Tabela, FatoresDiariosTabela, Operacao, RPCOperacao, BoletoOperacao,
    TipoOperacao, StatusOperacao, TipoTabela, TipoRPC, StatusRPC
)
from apps.operacoes.forms import (
    TabelaForm, TabelaSearchForm, OperacaoForm, OperacaoSearchForm,
    AverbacaoForm, CancelamentoForm, RPCForm, BoletoForm, FatoresDiariosForm
)
from apps.database.models import AuditLog
from apps.files.services import FileService


# =============================================================================
# TABELAS
# =============================================================================

@blueprint.route('/tabelas')
@login_required
def tabelas_list():
    """Lista de tabelas de empréstimo"""
    form = TabelaSearchForm(request.args)
    
    query = Tabela.query_active()
    
    # Filtros
    if form.search.data:
        termo = form.search.data.strip()
        query = query.filter(
            db.or_(
                Tabela.nome.ilike(f'%{termo}%'),
                Tabela.orgao.ilike(f'%{termo}%'),
                Tabela.banco.ilike(f'%{termo}%')
            )
        )
    
    if form.tipo.data:
        query = query.filter_by(tipo=form.tipo.data)
    
    if form.ativa.data:
        query = query.filter_by(ativa=form.ativa.data == '1')
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = query.order_by(Tabela.nome).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        'operacoes/tabelas/list.html',
        tabelas=pagination.items,
        pagination=pagination,
        form=form
    )


@blueprint.route('/tabelas/nova', methods=['GET', 'POST'])
@login_required
def tabela_create():
    """Criar nova tabela"""
    form = TabelaForm()
    
    if form.validate_on_submit():
        tabela = Tabela()
        form.populate_obj(tabela)
        
        db.session.add(tabela)
        db.session.commit()
        
        AuditLog.log(
            action='create',
            table_name='tabelas',
            record_id=tabela.id,
            description=f'Tabela criada: {tabela.nome}'
        )
        db.session.commit()
        
        flash('Tabela criada com sucesso!', 'success')
        return redirect(url_for('operacoes_blueprint.tabela_view', tabela_id=tabela.id))
    
    return render_template(
        'operacoes/tabelas/form.html',
        form=form,
        title='Nova Tabela'
    )


@blueprint.route('/tabelas/<int:tabela_id>')
@login_required
def tabela_view(tabela_id):
    """Visualizar tabela"""
    tabela = Tabela.query_active().filter_by(id=tabela_id).first_or_404()
    fatores = tabela.fatores_diarios.first()
    
    return render_template(
        'operacoes/tabelas/view.html',
        tabela=tabela,
        fatores=fatores
    )


@blueprint.route('/tabelas/<int:tabela_id>/editar', methods=['GET', 'POST'])
@login_required
def tabela_edit(tabela_id):
    """Editar tabela"""
    tabela = Tabela.query_active().filter_by(id=tabela_id).first_or_404()
    form = TabelaForm(obj=tabela)
    
    if form.validate_on_submit():
        form.populate_obj(tabela)
        db.session.commit()
        
        AuditLog.log(
            action='update',
            table_name='tabelas',
            record_id=tabela.id,
            description=f'Tabela atualizada: {tabela.nome}'
        )
        db.session.commit()
        
        flash('Tabela atualizada com sucesso!', 'success')
        return redirect(url_for('operacoes_blueprint.tabela_view', tabela_id=tabela.id))
    
    return render_template(
        'operacoes/tabelas/form.html',
        form=form,
        tabela=tabela,
        title='Editar Tabela'
    )


@blueprint.route('/tabelas/<int:tabela_id>/fatores', methods=['GET', 'POST'])
@login_required
def tabela_fatores(tabela_id):
    """Editar fatores diários da tabela"""
    tabela = Tabela.query_active().filter_by(id=tabela_id).first_or_404()
    fatores = tabela.fatores_diarios.first()
    
    if not fatores:
        fatores = FatoresDiariosTabela(tabela_id=tabela.id)
        db.session.add(fatores)
        db.session.commit()
    
    form = FatoresDiariosForm(obj=fatores)
    
    if form.validate_on_submit():
        form.populate_obj(fatores)
        fatores.usuario_atualizacao = current_user.username
        db.session.commit()
        
        AuditLog.log(
            action='update',
            table_name='fatores_diarios_tabelas',
            record_id=fatores.id,
            description=f'Fatores atualizados para tabela: {tabela.nome}'
        )
        db.session.commit()
        
        flash('Fatores diários atualizados com sucesso!', 'success')
        return redirect(url_for('operacoes_blueprint.tabela_view', tabela_id=tabela.id))
    
    return render_template(
        'operacoes/tabelas/fatores.html',
        form=form,
        tabela=tabela,
        fatores=fatores
    )


@blueprint.route('/tabelas/<int:tabela_id>/excluir', methods=['POST'])
@login_required
def tabela_delete(tabela_id):
    """Excluir tabela (soft delete)"""
    tabela = Tabela.query_active().filter_by(id=tabela_id).first_or_404()
    
    # Verifica se tem operações vinculadas
    if tabela.operacoes_count > 0:
        flash('Não é possível excluir tabela com operações vinculadas.', 'danger')
        return redirect(url_for('operacoes_blueprint.tabela_view', tabela_id=tabela.id))
    
    tabela.soft_delete(current_user.id)
    
    AuditLog.log(
        action='delete',
        table_name='tabelas',
        record_id=tabela.id,
        description=f'Tabela excluída: {tabela.nome}'
    )
    db.session.commit()
    
    flash('Tabela excluída com sucesso!', 'success')
    return redirect(url_for('operacoes_blueprint.tabelas_list'))


# =============================================================================
# OPERAÇÕES / CONTRATOS
# =============================================================================

@blueprint.route('/')
@login_required
def operacoes_list():
    """Lista de operações/contratos"""
    form = OperacaoSearchForm(request.args)
    
    query = Operacao.query_active()
    
    # Filtros
    if form.search.data:
        termo = form.search.data.strip()
        cpf_clean = ''.join(filter(str.isdigit, termo))
        query = query.filter(
            db.or_(
                Operacao.cliente_nome_completo.ilike(f'%{termo}%'),
                Operacao.cliente_cpf.like(f'%{cpf_clean}%'),
                Operacao.codigo_unico.ilike(f'%{termo}%')
            )
        )
    
    if form.status.data:
        query = query.filter_by(status=form.status.data)
    
    if form.tipo.data:
        query = query.filter_by(tipo=form.tipo.data)
    
    if form.banco.data:
        query = query.filter(Operacao.banco.ilike(f'%{form.banco.data}%'))
    
    if form.orgao.data:
        query = query.filter(Operacao.orgao.ilike(f'%{form.orgao.data}%'))
    
    if form.data_inicio.data:
        query = query.filter(Operacao.data_operacao >= form.data_inicio.data)
    
    if form.data_fim.data:
        query = query.filter(Operacao.data_operacao <= form.data_fim.data)
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = query.order_by(Operacao.data_operacao.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        'operacoes/list.html',
        operacoes=pagination.items,
        pagination=pagination,
        form=form,
        StatusOperacao=StatusOperacao
    )


@blueprint.route('/nova', methods=['GET', 'POST'])
@login_required
def operacao_create():
    """Criar nova operação"""
    form = OperacaoForm()
    
    # Carrega tabelas ativas para o select
    tabelas = Tabela.get_ativas()
    form.tabela_id.choices = [(0, 'Selecione...')] + [(t.id, t.display_name) for t in tabelas]
    
    if form.validate_on_submit():
        operacao = Operacao()
        form.populate_obj(operacao)
        
        # Limpa CPF
        operacao.cliente_cpf = ''.join(filter(str.isdigit, form.cliente_cpf.data))
        
        # Define responsável se não informado
        if not operacao.responsavel_usuario:
            operacao.responsavel_usuario = current_user.username
        
        # Define data se não informada
        if not operacao.data_operacao:
            operacao.data_operacao = datetime.utcnow()
        
        # Tabela_id = 0 significa nenhuma selecionada
        if operacao.tabela_id == 0:
            operacao.tabela_id = None
        
        db.session.add(operacao)
        db.session.commit()
        
        AuditLog.log(
            action='create',
            table_name='operacoes',
            record_id=operacao.id,
            description=f'Operação criada: {operacao.cliente_nome_completo}'
        )
        db.session.commit()
        
        flash('Operação criada com sucesso!', 'success')
        return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=operacao.id))
    
    return render_template(
        'operacoes/form.html',
        form=form,
        title='Nova Operação'
    )


@blueprint.route('/<int:operacao_id>')
@login_required
def operacao_view(operacao_id):
    """Visualizar operação"""
    operacao = Operacao.query_active().filter_by(id=operacao_id).first_or_404()
    
    # Busca arquivos da operação
    files = FileService.get_entity_files('operacao', operacao_id)
    missing_files = FileService.get_missing_required('operacao', operacao_id)
    
    # Busca categorias de arquivo disponíveis
    from apps.files.models import FileCategory
    categories = FileCategory.query_active().filter(
        FileCategory.entity_types.contains('operacao')
    ).order_by(FileCategory.display_order).all()
    
    return render_template(
        'operacoes/view.html',
        operacao=operacao,
        files=files,
        missing_files=missing_files,
        categories=categories
    )


@blueprint.route('/<int:operacao_id>/editar', methods=['GET', 'POST'])
@login_required
def operacao_edit(operacao_id):
    """Editar operação"""
    operacao = Operacao.query_active().filter_by(id=operacao_id).first_or_404()
    form = OperacaoForm(obj=operacao)
    
    # Carrega tabelas ativas para o select
    tabelas = Tabela.get_ativas()
    form.tabela_id.choices = [(0, 'Selecione...')] + [(t.id, t.display_name) for t in tabelas]
    
    if form.validate_on_submit():
        form.populate_obj(operacao)
        
        # Limpa CPF
        operacao.cliente_cpf = ''.join(filter(str.isdigit, form.cliente_cpf.data))
        
        # Tabela_id = 0 significa nenhuma selecionada
        if operacao.tabela_id == 0:
            operacao.tabela_id = None
        
        db.session.commit()
        
        AuditLog.log(
            action='update',
            table_name='operacoes',
            record_id=operacao.id,
            description=f'Operação atualizada: {operacao.cliente_nome_completo}'
        )
        db.session.commit()
        
        flash('Operação atualizada com sucesso!', 'success')
        return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=operacao.id))
    
    return render_template(
        'operacoes/form.html',
        form=form,
        operacao=operacao,
        title='Editar Operação'
    )


@blueprint.route('/<int:operacao_id>/averbar', methods=['GET', 'POST'])
@login_required
def operacao_averbar(operacao_id):
    """Averbar operação"""
    operacao = Operacao.query_active().filter_by(id=operacao_id).first_or_404()
    
    if operacao.averbado:
        flash('Esta operação já está averbada.', 'warning')
        return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=operacao.id))
    
    form = AverbacaoForm()
    
    if form.validate_on_submit():
        operacao.averbar(current_user.username)
        
        if form.obs.data:
            if operacao.obs:
                operacao.obs += f'\n\nAverbação: {form.obs.data}'
            else:
                operacao.obs = f'Averbação: {form.obs.data}'
            db.session.commit()
        
        AuditLog.log(
            action='averbar',
            table_name='operacoes',
            record_id=operacao.id,
            description=f'Operação averbada: {operacao.cliente_nome_completo}'
        )
        db.session.commit()
        
        flash('Operação averbada com sucesso!', 'success')
        return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=operacao.id))
    
    return render_template(
        'operacoes/averbar.html',
        form=form,
        operacao=operacao
    )


@blueprint.route('/<int:operacao_id>/cancelar', methods=['GET', 'POST'])
@login_required
def operacao_cancelar(operacao_id):
    """Cancelar operação"""
    operacao = Operacao.query_active().filter_by(id=operacao_id).first_or_404()
    
    if operacao.status == StatusOperacao.CANCELADA:
        flash('Esta operação já está cancelada.', 'warning')
        return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=operacao.id))
    
    form = CancelamentoForm()
    
    if form.validate_on_submit():
        operacao.cancelar(form.motivo_cancelamento.data, current_user.username)
        
        AuditLog.log(
            action='cancelar',
            table_name='operacoes',
            record_id=operacao.id,
            description=f'Operação cancelada: {operacao.cliente_nome_completo}',
            new_values={'motivo': form.motivo_cancelamento.data}
        )
        db.session.commit()
        
        flash('Operação cancelada.', 'success')
        return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=operacao.id))
    
    return render_template(
        'operacoes/cancelar.html',
        form=form,
        operacao=operacao
    )


@blueprint.route('/<int:operacao_id>/excluir', methods=['POST'])
@login_required
def operacao_delete(operacao_id):
    """Excluir operação (soft delete)"""
    operacao = Operacao.query_active().filter_by(id=operacao_id).first_or_404()
    
    operacao.soft_delete(current_user.id)
    
    AuditLog.log(
        action='delete',
        table_name='operacoes',
        record_id=operacao.id,
        description=f'Operação excluída: {operacao.cliente_nome_completo}'
    )
    db.session.commit()
    
    flash('Operação excluída com sucesso!', 'success')
    return redirect(url_for('operacoes_blueprint.operacoes_list'))


@blueprint.route('/<int:operacao_id>/upload', methods=['POST'])
@login_required
def operacao_upload_document(operacao_id):
    """Upload de documento da operação"""
    operacao = Operacao.query_active().filter_by(id=operacao_id).first_or_404()
    
    file = request.files.get('file')
    category_code = request.form.get('category', 'DOC_OUTROS')
    description = request.form.get('description', '')
    
    if not file or not file.filename:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=operacao_id))
    
    try:
        file_record = FileService.upload(
            file=file,
            category_code=category_code,
            entity_type='operacao',
            entity_id=operacao_id,
            uploaded_by_id=current_user.id,
            description=description or f'Documento da operação #{operacao.id}'
        )
        
        # Atualiza flag de documentos
        operacao.verificar_documentos()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'file': {
                    'id': file_record.id,
                    'name': file_record.original_name,
                    'category': file_record.category.name if file_record.category else None,
                    'size': file_record.size_formatted
                }
            })
        
        flash('Documento enviado com sucesso!', 'success')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(f'Erro ao enviar documento: {str(e)}', 'danger')
    
    return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=operacao_id))


# =============================================================================
# RPCs
# =============================================================================

@blueprint.route('/<int:operacao_id>/rpc/novo', methods=['GET', 'POST'])
@login_required
def rpc_create(operacao_id):
    """Criar novo RPC"""
    operacao = Operacao.query_active().filter_by(id=operacao_id).first_or_404()
    form = RPCForm()
    
    if form.validate_on_submit():
        rpc = RPCOperacao()
        form.populate_obj(rpc)
        rpc.operacao_id = operacao_id
        
        db.session.add(rpc)
        db.session.commit()
        
        AuditLog.log(
            action='create',
            table_name='operacoes_rpc',
            record_id=rpc.id,
            description=f'RPC criado para operação #{operacao_id}'
        )
        db.session.commit()
        
        flash('RPC adicionado com sucesso!', 'success')
        return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=operacao_id))
    
    return render_template(
        'operacoes/rpc_form.html',
        form=form,
        operacao=operacao,
        title='Novo RPC'
    )


@blueprint.route('/rpc/<int:rpc_id>/editar', methods=['GET', 'POST'])
@login_required
def rpc_edit(rpc_id):
    """Editar RPC"""
    rpc = RPCOperacao.query_active().filter_by(id=rpc_id).first_or_404()
    operacao = rpc.operacao
    form = RPCForm(obj=rpc)
    
    if form.validate_on_submit():
        form.populate_obj(rpc)
        db.session.commit()
        
        AuditLog.log(
            action='update',
            table_name='operacoes_rpc',
            record_id=rpc.id,
            description=f'RPC atualizado: #{rpc.id}'
        )
        db.session.commit()
        
        flash('RPC atualizado com sucesso!', 'success')
        return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=operacao.id))
    
    return render_template(
        'operacoes/rpc_form.html',
        form=form,
        operacao=operacao,
        rpc=rpc,
        title='Editar RPC'
    )


@blueprint.route('/rpc/<int:rpc_id>/excluir', methods=['POST'])
@login_required
def rpc_delete(rpc_id):
    """Excluir RPC"""
    rpc = RPCOperacao.query_active().filter_by(id=rpc_id).first_or_404()
    operacao_id = rpc.operacao_id
    
    rpc.soft_delete(current_user.id)
    
    AuditLog.log(
        action='delete',
        table_name='operacoes_rpc',
        record_id=rpc.id,
        description=f'RPC excluído: #{rpc.id}'
    )
    db.session.commit()
    
    flash('RPC excluído com sucesso!', 'success')
    return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=operacao_id))


@blueprint.route('/rpc/<int:rpc_id>/upload', methods=['POST'])
@login_required
def rpc_upload_boleto(rpc_id):
    """Upload do boleto do RPC"""
    rpc = RPCOperacao.query_active().filter_by(id=rpc_id).first_or_404()
    
    file = request.files.get('file')
    if not file or not file.filename:
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=rpc.operacao_id))
    
    try:
        file_record = FileService.upload(
            file=file,
            category_code='BOLETO_RPC',
            entity_type='rpc',
            entity_id=rpc.id,
            uploaded_by_id=current_user.id,
            description=f'Boleto RPC #{rpc.id}'
        )
        
        rpc.boleto_img = str(file_record.id)
        db.session.commit()
        
        flash('Boleto do RPC enviado com sucesso!', 'success')
        
    except Exception as e:
        flash(f'Erro ao enviar boleto: {str(e)}', 'danger')
    
    return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=rpc.operacao_id))


# =============================================================================
# BOLETOS
# =============================================================================

@blueprint.route('/<int:operacao_id>/boleto/novo', methods=['GET', 'POST'])
@login_required
def boleto_create(operacao_id):
    """Criar novo boleto"""
    operacao = Operacao.query_active().filter_by(id=operacao_id).first_or_404()
    form = BoletoForm()
    
    if form.validate_on_submit():
        boleto = BoletoOperacao()
        form.populate_obj(boleto)
        boleto.operacao_id = operacao_id
        
        db.session.add(boleto)
        db.session.commit()
        
        AuditLog.log(
            action='create',
            table_name='operacoes_boletos',
            record_id=boleto.id,
            description=f'Boleto criado para operação #{operacao_id}'
        )
        db.session.commit()
        
        flash('Boleto adicionado com sucesso!', 'success')
        return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=operacao_id))
    
    return render_template(
        'operacoes/boleto_form.html',
        form=form,
        operacao=operacao,
        title='Novo Boleto'
    )


@blueprint.route('/boleto/<int:boleto_id>/editar', methods=['GET', 'POST'])
@login_required
def boleto_edit(boleto_id):
    """Editar boleto"""
    boleto = BoletoOperacao.query_active().filter_by(id=boleto_id).first_or_404()
    operacao = boleto.operacao
    form = BoletoForm(obj=boleto)
    
    if form.validate_on_submit():
        form.populate_obj(boleto)
        db.session.commit()
        
        AuditLog.log(
            action='update',
            table_name='operacoes_boletos',
            record_id=boleto.id,
            description=f'Boleto atualizado: #{boleto.id}'
        )
        db.session.commit()
        
        flash('Boleto atualizado com sucesso!', 'success')
        return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=operacao.id))
    
    return render_template(
        'operacoes/boleto_form.html',
        form=form,
        operacao=operacao,
        boleto=boleto,
        title='Editar Boleto'
    )


@blueprint.route('/boleto/<int:boleto_id>/excluir', methods=['POST'])
@login_required
def boleto_delete(boleto_id):
    """Excluir boleto"""
    boleto = BoletoOperacao.query_active().filter_by(id=boleto_id).first_or_404()
    operacao_id = boleto.operacao_id
    
    boleto.soft_delete(current_user.id)
    
    AuditLog.log(
        action='delete',
        table_name='operacoes_boletos',
        record_id=boleto.id,
        description=f'Boleto excluído: #{boleto.id}'
    )
    db.session.commit()
    
    flash('Boleto excluído com sucesso!', 'success')
    return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=operacao_id))


@blueprint.route('/boleto/<int:boleto_id>/confirmar', methods=['POST'])
@login_required
def boleto_confirmar(boleto_id):
    """Confirmar depósito do boleto"""
    boleto = BoletoOperacao.query_active().filter_by(id=boleto_id).first_or_404()
    
    boleto.confirmar_deposito()
    
    AuditLog.log(
        action='confirmar',
        table_name='operacoes_boletos',
        record_id=boleto.id,
        description=f'Depósito confirmado: #{boleto.id}'
    )
    db.session.commit()
    
    flash('Depósito confirmado!', 'success')
    return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=boleto.operacao_id))


@blueprint.route('/boleto/<int:boleto_id>/pagar-comissao', methods=['POST'])
@login_required
def boleto_pagar_comissao(boleto_id):
    """Marcar comissão como paga"""
    boleto = BoletoOperacao.query_active().filter_by(id=boleto_id).first_or_404()
    
    boleto.pagar_comissao()
    
    AuditLog.log(
        action='pagar_comissao',
        table_name='operacoes_boletos',
        record_id=boleto.id,
        description=f'Comissão paga: #{boleto.id}'
    )
    db.session.commit()
    
    flash('Comissão marcada como paga!', 'success')
    return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=boleto.operacao_id))


@blueprint.route('/boleto/<int:boleto_id>/upload', methods=['POST'])
@login_required
def boleto_upload_comprovante(boleto_id):
    """Upload do comprovante do boleto"""
    boleto = BoletoOperacao.query_active().filter_by(id=boleto_id).first_or_404()
    
    file = request.files.get('file')
    if not file or not file.filename:
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=boleto.operacao_id))
    
    try:
        file_record = FileService.upload(
            file=file,
            category_code='COMPROVANTE',
            entity_type='boleto',
            entity_id=boleto.id,
            uploaded_by_id=current_user.id,
            description=f'Comprovante boleto #{boleto.id}'
        )
        
        boleto.comprovante = str(file_record.id)
        db.session.commit()
        
        flash('Comprovante enviado com sucesso!', 'success')
        
    except Exception as e:
        flash(f'Erro ao enviar comprovante: {str(e)}', 'danger')
    
    return redirect(url_for('operacoes_blueprint.operacao_view', operacao_id=boleto.operacao_id))


# =============================================================================
# API / AJAX
# =============================================================================

@blueprint.route('/api/buscar')
@login_required
def api_operacao_search():
    """Busca de operações (autocomplete)"""
    term = request.args.get('term', '')
    limit = request.args.get('limit', 50, type=int)
    
    if len(term) < 2:
        operacoes = Operacao.get_pendentes(limit=limit)
    else:
        operacoes = Operacao.search(term, limit=limit)
    
    return jsonify({
        'results': [{
            'id': o.id,
            'text': f'{o.cliente_nome_completo} - {o.cpf_formatted}',
            'cpf': o.cpf_formatted,
            'nome': o.cliente_nome_completo,
            'status': o.status_display,
            'tipo': o.tipo_display,
            'valor': o.valor_liquido
        } for o in operacoes]
    })


@blueprint.route('/api/tabelas')
@login_required
def api_tabelas_list():
    """Lista de tabelas para selects"""
    tipo = request.args.get('tipo')
    orgao = request.args.get('orgao')
    banco = request.args.get('banco')
    
    tabelas = Tabela.get_ativas(tipo=tipo, orgao=orgao, banco=banco)
    
    return jsonify({
        'results': [{
            'id': t.id,
            'text': t.display_name,
            'nome': t.nome,
            'tipo': t.tipo,
            'orgao': t.orgao,
            'banco': t.banco,
            'fator': t.fator,
            'num_parcelas': t.num_parcelas
        } for t in tabelas]
    })


@blueprint.route('/api/stats')
@login_required
def api_stats():
    """Estatísticas das operações"""
    # Contagem por status
    stats = {}
    for status, _ in StatusOperacao.CHOICES:
        stats[status] = Operacao.query_active().filter_by(status=status).count()
    
    # Total geral
    stats['total'] = Operacao.query_active().count()
    
    # Total pendentes
    stats['pendentes'] = Operacao.query_active().filter(
        Operacao.status.notin_(StatusOperacao.FINALIZADOS)
    ).count()
    
    return jsonify(stats)
