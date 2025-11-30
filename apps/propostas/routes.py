# -*- encoding: utf-8 -*-
"""
Rotas de Propostas/Contratos de Empréstimo
CRUD completo de Tabelas, Propostas, RPCs e Boletos
"""

from datetime import datetime

from flask import (
    render_template, request, redirect, url_for,
    flash, jsonify, abort
)
from flask_login import login_required, current_user

from apps import db
from apps.propostas import blueprint
from apps.propostas.models import (
    Tabela, FatoresDiariosTabela, Proposta, RPCProposta, BoletoProposta,
    TipoProposta, PropostaStatus, TipoTabela, TipoRPC, StatusRPC
)
from apps.propostas.forms import (
    TabelaForm, TabelaSearchForm, PropostaForm, PropostaSearchForm,
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
        'propostas/tabelas/list.html',
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
        return redirect(url_for('propostas_blueprint.tabela_view', tabela_id=tabela.id))
    
    return render_template(
        'propostas/tabelas/form.html',
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
        'propostas/tabelas/view.html',
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
        return redirect(url_for('propostas_blueprint.tabela_view', tabela_id=tabela.id))
    
    return render_template(
        'propostas/tabelas/form.html',
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
        return redirect(url_for('propostas_blueprint.tabela_view', tabela_id=tabela.id))
    
    return render_template(
        'propostas/tabelas/fatores.html',
        form=form,
        tabela=tabela,
        fatores=fatores
    )


@blueprint.route('/tabelas/<int:tabela_id>/excluir', methods=['POST'])
@login_required
def tabela_delete(tabela_id):
    """Excluir tabela (soft delete)"""
    tabela = Tabela.query_active().filter_by(id=tabela_id).first_or_404()
    
    # Verifica se tem propostas vinculadas
    if tabela.propostas_count > 0:
        flash('Não é possível excluir tabela com propostas vinculadas.', 'danger')
        return redirect(url_for('propostas_blueprint.tabela_view', tabela_id=tabela.id))
    
    tabela.soft_delete(current_user.id)
    
    AuditLog.log(
        action='delete',
        table_name='tabelas',
        record_id=tabela.id,
        description=f'Tabela excluída: {tabela.nome}'
    )
    db.session.commit()
    
    flash('Tabela excluída com sucesso!', 'success')
    return redirect(url_for('propostas_blueprint.tabelas_list'))


# =============================================================================
# PROPOSTAS / CONTRATOS
# =============================================================================

@blueprint.route('/')
@login_required
def propostas_list():
    """Lista de propostas/contratos"""
    form = PropostaSearchForm(request.args)
    
    query = Proposta.query_active()
    
    # Filtros
    if form.search.data:
        termo = form.search.data.strip()
        cpf_clean = ''.join(filter(str.isdigit, termo))
        query = query.filter(
            db.or_(
                Proposta.cliente_nome_completo.ilike(f'%{termo}%'),
                Proposta.cliente_cpf.like(f'%{cpf_clean}%'),
                Proposta.codigo_unico.ilike(f'%{termo}%')
            )
        )
    
    if form.status.data:
        query = query.filter_by(status=form.status.data)
    
    if form.tipo.data:
        query = query.filter_by(tipo=form.tipo.data)
    
    if form.banco.data:
        query = query.filter(Proposta.banco.ilike(f'%{form.banco.data}%'))
    
    if form.orgao.data:
        query = query.filter(Proposta.orgao.ilike(f'%{form.orgao.data}%'))
    
    if form.data_inicio.data:
        query = query.filter(Proposta.data_proposta >= form.data_inicio.data)
    
    if form.data_fim.data:
        query = query.filter(Proposta.data_proposta <= form.data_fim.data)
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = query.order_by(Proposta.data_proposta.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        'propostas/list.html',
        propostas=pagination.items,
        pagination=pagination,
        form=form,
        PropostaStatus=PropostaStatus
    )


@blueprint.route('/nova', methods=['GET', 'POST'])
@login_required
def proposta_create():
    """Criar nova proposta"""
    form = PropostaForm()
    
    # Carrega tabelas ativas para o select
    tabelas = Tabela.get_ativas()
    form.tabela_id.choices = [(0, 'Selecione...')] + [(t.id, t.display_name) for t in tabelas]
    
    if form.validate_on_submit():
        proposta = Proposta()
        form.populate_obj(proposta)
        
        # Limpa CPF
        proposta.cliente_cpf = ''.join(filter(str.isdigit, form.cliente_cpf.data))
        
        # Define responsável se não informado
        if not proposta.responsavel_usuario:
            proposta.responsavel_usuario = current_user.username
        
        # Define data se não informada
        if not proposta.data_proposta:
            proposta.data_proposta = datetime.utcnow()
        
        # Tabela_id = 0 significa nenhuma selecionada
        if proposta.tabela_id == 0:
            proposta.tabela_id = None
        
        db.session.add(proposta)
        db.session.commit()
        
        AuditLog.log(
            action='create',
            table_name='propostas',
            record_id=proposta.id,
            description=f'Proposta criada: {proposta.cliente_nome_completo}'
        )
        db.session.commit()
        
        flash('Proposta criada com sucesso!', 'success')
        return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=proposta.id))
    
    return render_template(
        'propostas/form.html',
        form=form,
        title='Nova Proposta',
        is_admin=current_user.is_admin
    )


@blueprint.route('/<int:proposta_id>')
@login_required
def proposta_view(proposta_id):
    """Visualizar proposta"""
    proposta = Proposta.query_active().filter_by(id=proposta_id).first_or_404()
    
    # Busca arquivos da proposta
    files = FileService.get_entity_files('proposta', proposta_id)
    missing_files = FileService.get_missing_required('proposta', proposta_id)
    
    # Busca categorias de arquivo disponíveis
    from apps.files.models import FileCategory
    categories = FileCategory.query_active().filter(
        FileCategory.entity_types.contains('proposta')
    ).order_by(FileCategory.display_order).all()
    
    return render_template(
        'propostas/view.html',
        proposta=proposta,
        files=files,
        missing_files=missing_files,
        categories=categories
    )


@blueprint.route('/<int:proposta_id>/editar', methods=['GET', 'POST'])
@login_required
def proposta_edit(proposta_id):
    """Editar proposta"""
    proposta = Proposta.query_active().filter_by(id=proposta_id).first_or_404()
    form = PropostaForm(obj=proposta)
    
    # Carrega tabelas ativas para o select
    tabelas = Tabela.get_ativas()
    form.tabela_id.choices = [(0, 'Selecione...')] + [(t.id, t.display_name) for t in tabelas]
    
    if form.validate_on_submit():
        form.populate_obj(proposta)
        
        # Limpa CPF
        proposta.cliente_cpf = ''.join(filter(str.isdigit, form.cliente_cpf.data))
        
        # Tabela_id = 0 significa nenhuma selecionada
        if proposta.tabela_id == 0:
            proposta.tabela_id = None
        
        db.session.commit()
        
        AuditLog.log(
            action='update',
            table_name='propostas',
            record_id=proposta.id,
            description=f'Proposta atualizada: {proposta.cliente_nome_completo}'
        )
        db.session.commit()
        
        flash('Proposta atualizada com sucesso!', 'success')
        return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=proposta.id))
    
    return render_template(
        'propostas/form.html',
        form=form,
        proposta=proposta,
        title='Editar Proposta',
        is_admin=current_user.is_admin
    )


@blueprint.route('/<int:proposta_id>/averbar', methods=['GET', 'POST'])
@login_required
def proposta_averbar(proposta_id):
    """Averbar proposta"""
    proposta = Proposta.query_active().filter_by(id=proposta_id).first_or_404()
    
    if proposta.averbado:
        flash('Esta proposta já está averbada.', 'warning')
        return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=proposta.id))
    
    form = AverbacaoForm()
    
    if form.validate_on_submit():
        proposta.averbar(current_user.username)
        
        if form.obs.data:
            if proposta.obs:
                proposta.obs += f'\n\nAverbação: {form.obs.data}'
            else:
                proposta.obs = f'Averbação: {form.obs.data}'
            db.session.commit()
        
        AuditLog.log(
            action='averbar',
            table_name='propostas',
            record_id=proposta.id,
            description=f'Proposta averbada: {proposta.cliente_nome_completo}'
        )
        db.session.commit()
        
        flash('Proposta averbada com sucesso!', 'success')
        return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=proposta.id))
    
    return render_template(
        'propostas/averbar.html',
        form=form,
        proposta=proposta
    )


@blueprint.route('/<int:proposta_id>/cancelar', methods=['GET', 'POST'])
@login_required
def proposta_cancelar(proposta_id):
    """Cancelar proposta"""
    proposta = Proposta.query_active().filter_by(id=proposta_id).first_or_404()
    
    if proposta.status == PropostaStatus.CANCELADA:
        flash('Esta proposta já está cancelada.', 'warning')
        return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=proposta.id))
    
    form = CancelamentoForm()
    
    if form.validate_on_submit():
        proposta.cancelar(form.motivo_cancelamento.data, current_user.username)
        
        AuditLog.log(
            action='cancelar',
            table_name='propostas',
            record_id=proposta.id,
            description=f'Proposta cancelada: {proposta.cliente_nome_completo}',
            new_values={'motivo': form.motivo_cancelamento.data}
        )
        db.session.commit()
        
        flash('Proposta cancelada.', 'success')
        return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=proposta.id))
    
    return render_template(
        'propostas/cancelar.html',
        form=form,
        proposta=proposta
    )


@blueprint.route('/<int:proposta_id>/excluir', methods=['POST'])
@login_required
def proposta_delete(proposta_id):
    """Excluir proposta (soft delete)"""
    proposta = Proposta.query_active().filter_by(id=proposta_id).first_or_404()
    
    proposta.soft_delete(current_user.id)
    
    AuditLog.log(
        action='delete',
        table_name='propostas',
        record_id=proposta.id,
        description=f'Proposta excluída: {proposta.cliente_nome_completo}'
    )
    db.session.commit()
    
    flash('Proposta excluída com sucesso!', 'success')
    return redirect(url_for('propostas_blueprint.propostas_list'))


@blueprint.route('/<int:proposta_id>/upload', methods=['POST'])
@login_required
def proposta_upload_document(proposta_id):
    """Upload de documento da proposta"""
    proposta = Proposta.query_active().filter_by(id=proposta_id).first_or_404()
    
    file = request.files.get('file')
    category_code = request.form.get('category', 'DOC_OUTROS')
    description = request.form.get('description', '')
    
    if not file or not file.filename:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=proposta_id))
    
    try:
        file_record = FileService.upload(
            file=file,
            category_code=category_code,
            entity_type='proposta',
            entity_id=proposta_id,
            uploaded_by_id=current_user.id,
            description=description or f'Documento da proposta #{proposta.id}'
        )
        
        # Atualiza flag de documentos
        proposta.verificar_documentos()
        
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
    
    return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=proposta_id))


# =============================================================================
# RPCs
# =============================================================================

@blueprint.route('/<int:proposta_id>/rpc/novo', methods=['GET', 'POST'])
@login_required
def rpc_create(proposta_id):
    """Criar novo RPC"""
    proposta = Proposta.query_active().filter_by(id=proposta_id).first_or_404()
    form = RPCForm()
    
    if form.validate_on_submit():
        rpc = RPCProposta()
        form.populate_obj(rpc)
        rpc.proposta_id = proposta_id
        
        db.session.add(rpc)
        db.session.commit()
        
        AuditLog.log(
            action='create',
            table_name='propostas_rpc',
            record_id=rpc.id,
            description=f'RPC criado para proposta #{proposta_id}'
        )
        db.session.commit()
        
        flash('RPC adicionado com sucesso!', 'success')
        return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=proposta_id))
    
    return render_template(
        'propostas/rpc_form.html',
        form=form,
        proposta=proposta,
        title='Novo RPC'
    )


@blueprint.route('/rpc/<int:rpc_id>/editar', methods=['GET', 'POST'])
@login_required
def rpc_edit(rpc_id):
    """Editar RPC"""
    rpc = RPCProposta.query_active().filter_by(id=rpc_id).first_or_404()
    proposta = rpc.proposta
    form = RPCForm(obj=rpc)
    
    if form.validate_on_submit():
        form.populate_obj(rpc)
        db.session.commit()
        
        AuditLog.log(
            action='update',
            table_name='propostas_rpc',
            record_id=rpc.id,
            description=f'RPC atualizado: #{rpc.id}'
        )
        db.session.commit()
        
        flash('RPC atualizado com sucesso!', 'success')
        return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=proposta.id))
    
    return render_template(
        'propostas/rpc_form.html',
        form=form,
        proposta=proposta,
        rpc=rpc,
        title='Editar RPC'
    )


@blueprint.route('/rpc/<int:rpc_id>/excluir', methods=['POST'])
@login_required
def rpc_delete(rpc_id):
    """Excluir RPC"""
    rpc = RPCProposta.query_active().filter_by(id=rpc_id).first_or_404()
    proposta_id = rpc.proposta_id
    
    rpc.soft_delete(current_user.id)
    
    AuditLog.log(
        action='delete',
        table_name='propostas_rpc',
        record_id=rpc.id,
        description=f'RPC excluído: #{rpc.id}'
    )
    db.session.commit()
    
    flash('RPC excluído com sucesso!', 'success')
    return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=proposta_id))


@blueprint.route('/rpc/<int:rpc_id>/upload', methods=['POST'])
@login_required
def rpc_upload_boleto(rpc_id):
    """Upload do boleto do RPC"""
    rpc = RPCProposta.query_active().filter_by(id=rpc_id).first_or_404()
    
    file = request.files.get('file')
    if not file or not file.filename:
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=rpc.proposta_id))
    
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
    
    return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=rpc.proposta_id))


# =============================================================================
# BOLETOS
# =============================================================================

@blueprint.route('/<int:proposta_id>/boleto/novo', methods=['GET', 'POST'])
@login_required
def boleto_create(proposta_id):
    """Criar novo boleto"""
    proposta = Proposta.query_active().filter_by(id=proposta_id).first_or_404()
    form = BoletoForm()
    
    if form.validate_on_submit():
        boleto = BoletoProposta()
        form.populate_obj(boleto)
        boleto.proposta_id = proposta_id
        
        db.session.add(boleto)
        db.session.commit()
        
        AuditLog.log(
            action='create',
            table_name='propostas_boletos',
            record_id=boleto.id,
            description=f'Boleto criado para proposta #{proposta_id}'
        )
        db.session.commit()
        
        flash('Boleto adicionado com sucesso!', 'success')
        return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=proposta_id))
    
    return render_template(
        'propostas/boleto_form.html',
        form=form,
        proposta=proposta,
        title='Novo Boleto'
    )


@blueprint.route('/boleto/<int:boleto_id>/editar', methods=['GET', 'POST'])
@login_required
def boleto_edit(boleto_id):
    """Editar boleto"""
    boleto = BoletoProposta.query_active().filter_by(id=boleto_id).first_or_404()
    proposta = boleto.proposta
    form = BoletoForm(obj=boleto)
    
    if form.validate_on_submit():
        form.populate_obj(boleto)
        db.session.commit()
        
        AuditLog.log(
            action='update',
            table_name='propostas_boletos',
            record_id=boleto.id,
            description=f'Boleto atualizado: #{boleto.id}'
        )
        db.session.commit()
        
        flash('Boleto atualizado com sucesso!', 'success')
        return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=proposta.id))
    
    return render_template(
        'propostas/boleto_form.html',
        form=form,
        proposta=proposta,
        boleto=boleto,
        title='Editar Boleto'
    )


@blueprint.route('/boleto/<int:boleto_id>/excluir', methods=['POST'])
@login_required
def boleto_delete(boleto_id):
    """Excluir boleto"""
    boleto = BoletoProposta.query_active().filter_by(id=boleto_id).first_or_404()
    proposta_id = boleto.proposta_id
    
    boleto.soft_delete(current_user.id)
    
    AuditLog.log(
        action='delete',
        table_name='propostas_boletos',
        record_id=boleto.id,
        description=f'Boleto excluído: #{boleto.id}'
    )
    db.session.commit()
    
    flash('Boleto excluído com sucesso!', 'success')
    return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=proposta_id))


@blueprint.route('/boleto/<int:boleto_id>/confirmar', methods=['POST'])
@login_required
def boleto_confirmar(boleto_id):
    """Confirmar depósito do boleto"""
    boleto = BoletoProposta.query_active().filter_by(id=boleto_id).first_or_404()
    
    boleto.confirmar_deposito()
    
    AuditLog.log(
        action='confirmar',
        table_name='propostas_boletos',
        record_id=boleto.id,
        description=f'Depósito confirmado: #{boleto.id}'
    )
    db.session.commit()
    
    flash('Depósito confirmado!', 'success')
    return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=boleto.proposta_id))


@blueprint.route('/boleto/<int:boleto_id>/pagar-comissao', methods=['POST'])
@login_required
def boleto_pagar_comissao(boleto_id):
    """Marcar comissão como paga"""
    boleto = BoletoProposta.query_active().filter_by(id=boleto_id).first_or_404()
    
    boleto.pagar_comissao()
    
    AuditLog.log(
        action='pagar_comissao',
        table_name='propostas_boletos',
        record_id=boleto.id,
        description=f'Comissão paga: #{boleto.id}'
    )
    db.session.commit()
    
    flash('Comissão marcada como paga!', 'success')
    return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=boleto.proposta_id))


@blueprint.route('/boleto/<int:boleto_id>/upload', methods=['POST'])
@login_required
def boleto_upload_comprovante(boleto_id):
    """Upload do comprovante do boleto"""
    boleto = BoletoProposta.query_active().filter_by(id=boleto_id).first_or_404()
    
    file = request.files.get('file')
    if not file or not file.filename:
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=boleto.proposta_id))
    
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
    
    return redirect(url_for('propostas_blueprint.proposta_view', proposta_id=boleto.proposta_id))


# =============================================================================
# API / AJAX
# =============================================================================

@blueprint.route('/api/buscar')
@login_required
def api_proposta_search():
    """Busca de propostas (autocomplete)"""
    term = request.args.get('term', '')
    limit = request.args.get('limit', 50, type=int)
    
    if len(term) < 2:
        propostas = Proposta.get_pendentes(limit=limit)
    else:
        propostas = Proposta.search(term, limit=limit)
    
    return jsonify({
        'results': [{
            'id': p.id,
            'text': f'{p.cliente_nome_completo} - {p.cpf_formatted}',
            'cpf': p.cpf_formatted,
            'nome': p.cliente_nome_completo,
            'status': p.status_display,
            'tipo': p.tipo_display,
            'valor': p.valor_liquido
        } for p in propostas]
    })


@blueprint.route('/api/buscar-cliente')
@login_required
def api_buscar_cliente():
    """Busca cliente por CPF para preenchimento automático"""
    cpf = request.args.get('cpf', '')
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    
    if len(cpf_clean) < 11:
        return jsonify({'found': False, 'message': 'CPF incompleto'})
    
    # Busca no módulo de clientes
    try:
        from apps.clientes.models import Cliente
        
        cliente = Cliente.query_active().filter_by(cpf=cpf_clean).first()
        
        if cliente:
            # Busca telefone principal
            telefone_principal = None
            if cliente.telefones:
                telefones = [t for t in cliente.telefones if not t.excluido_em]
                if telefones:
                    telefone_principal = telefones[0].telefone
            
            # Busca email principal
            email_principal = None
            if cliente.emails:
                emails = [e for e in cliente.emails if not e.excluido_em]
                if emails:
                    email_principal = emails[0].email
            
            # Busca primeira matrícula
            matricula_info = None
            if cliente.matriculas:
                matriculas = [m for m in cliente.matriculas if not m.excluido_em]
                if matriculas:
                    mat = matriculas[0]
                    matricula_info = {
                        'matricula': mat.matricula,
                        'orgao': mat.orgao
                    }
            
            return jsonify({
                'found': True,
                'cliente': {
                    'cpf': cliente.cpf,
                    'nome_completo': cliente.nome_completo,
                    'telefone': telefone_principal,
                    'email': email_principal,
                    'matricula': matricula_info.get('matricula') if matricula_info else None,
                    'orgao': matricula_info.get('orgao') if matricula_info else None,
                    'view_url': url_for('clientes_blueprint.cliente_view', cpf=cliente.cpf)
                }
            })
        else:
            return jsonify({
                'found': False,
                'message': 'Cliente não encontrado',
                'create_url': url_for('clientes_blueprint.cliente_create', cpf=cpf_clean)
            })
    
    except Exception as e:
        return jsonify({'found': False, 'error': str(e)})


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
    """Estatísticas das propostas"""
    # Contagem por status
    stats = {}
    for status, config in PropostaStatus.STATUS_CONFIG.items():
        if config['ativo']:
            stats[status] = Proposta.query_active().filter_by(status=status).count()
    
    # Total geral
    stats['total'] = Proposta.query_active().count()
    
    # Total pendentes
    stats['pendentes'] = Proposta.query_active().filter(
        Proposta.status.notin_(PropostaStatus.FINALIZADOS)
    ).count()
    
    # Por etapa comercial
    stats['etapa_comercial'] = Proposta.query_active().filter(
        Proposta.status.in_(PropostaStatus.ETAPA_COMERCIAL)
    ).count()
    
    stats['etapa_averbacao'] = Proposta.query_active().filter(
        Proposta.status.in_(PropostaStatus.ETAPA_AVERBACAO)
    ).count()
    
    stats['etapa_financeiro'] = Proposta.query_active().filter(
        Proposta.status.in_(PropostaStatus.ETAPA_FINANCEIRO)
    ).count()
    
    return jsonify(stats)
