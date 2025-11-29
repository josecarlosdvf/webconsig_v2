# -*- encoding: utf-8 -*-
"""
Rotas de Gestão de Arquivos
Upload, download, edição e validação
"""

import io
from flask import (
    render_template, request, jsonify, send_file, 
    current_app, abort, flash, redirect, url_for
)
from flask_login import login_required, current_user

from apps import db
from apps.files import blueprint
from apps.files.models import File, FileCategory
from apps.files.services import FileService, ImageService, FileValidationError
from apps.database.models import AuditLog


# =============================================================================
# ROTAS DE LISTAGEM (VIEWS)
# =============================================================================

@blueprint.route('/')
@login_required
def index():
    """Lista de arquivos do usuário"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = File.query_active()
    
    # Filtros
    search = request.args.get('search')
    if search:
        query = query.filter(File.original_filename.ilike(f'%{search}%'))
    
    category_id = request.args.get('category_id', type=int)
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    file_type = request.args.get('file_type')
    if file_type == 'image':
        query = query.filter(File.mime_type.like('image/%'))
    elif file_type == 'document':
        query = query.filter(File.mime_type.in_(['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']))
    elif file_type == 'spreadsheet':
        query = query.filter(File.mime_type.in_(['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']))
    elif file_type == 'pdf':
        query = query.filter_by(mime_type='application/pdf')
    
    pagination = query.order_by(File.created_at.desc()).paginate(page=page, per_page=per_page)
    
    categories = FileCategory.query_active().filter_by(is_active=True).all()
    
    return render_template(
        'files/index.html',
        files=pagination.items,
        pagination=pagination,
        categories=categories
    )


@blueprint.route('/entity/<entity_type>/<int:entity_id>')
@login_required
def entity_files(entity_type, entity_id):
    """Lista arquivos de uma entidade específica"""
    # Obtém a entidade
    entity = None
    if entity_type == 'employee':
        from apps.hr.models import Employee
        entity = Employee.query_active().get_or_404(entity_id)
    elif entity_type == 'team':
        from apps.hr.models import Team
        entity = Team.query_active().get_or_404(entity_id)
    else:
        abort(404)
    
    # Filtro por categoria
    category_id = request.args.get('category_id', type=int)
    
    query = File.query_active().filter_by(
        entity_type=entity_type,
        entity_id=entity_id
    )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    files = query.order_by(File.created_at.desc()).all()
    
    # Categorias aplicáveis
    categories = FileCategory.get_for_entity(entity_type)
    
    return render_template(
        'files/entity_files.html',
        entity_type=entity_type,
        entity=entity,
        files=files,
        categories=categories
    )


@blueprint.route('/categories/manage')
@login_required  
def categories():
    """Gerenciar categorias de arquivos"""
    categories = FileCategory.query_active().order_by(FileCategory.display_order).all()
    
    return render_template(
        'files/categories.html',
        categories=categories
    )


@blueprint.route('/categories/create', methods=['POST'])
@login_required
def category_create():
    """Criar nova categoria"""
    name = request.form.get('name')
    code = request.form.get('code', '').upper().replace(' ', '_')
    
    if not name or not code:
        flash('Nome e código são obrigatórios.', 'danger')
        return redirect(url_for('files_blueprint.categories'))
    
    category = FileCategory(
        name=name,
        code=code,
        description=request.form.get('description'),
        entity_type=request.form.get('entity_type'),
        allowed_extensions=request.form.get('allowed_extensions'),
        max_size_mb=int(request.form.get('max_size_mb', 10)),
        is_required='is_required' in request.form,
        is_active='is_active' in request.form
    )
    
    db.session.add(category)
    db.session.commit()
    
    AuditLog.log(
        action='create',
        table_name='file_categories',
        record_id=category.id,
        description=f'Categoria criada: {category.name}'
    )
    db.session.commit()
    
    flash('Categoria criada com sucesso!', 'success')
    return redirect(url_for('files_blueprint.categories'))


@blueprint.route('/categories/<int:id>/edit', methods=['POST'])
@login_required
def category_edit(id):
    """Editar categoria"""
    category = FileCategory.query_active().get_or_404(id)
    
    category.name = request.form.get('name', category.name)
    category.code = request.form.get('code', category.code).upper().replace(' ', '_')
    category.description = request.form.get('description')
    category.entity_type = request.form.get('entity_type')
    category.allowed_extensions = request.form.get('allowed_extensions')
    category.max_size_mb = int(request.form.get('max_size_mb', 10))
    category.is_required = 'is_required' in request.form
    category.is_active = 'is_active' in request.form
    
    db.session.commit()
    
    AuditLog.log(
        action='update',
        table_name='file_categories',
        record_id=category.id,
        description=f'Categoria atualizada: {category.name}'
    )
    db.session.commit()
    
    flash('Categoria atualizada com sucesso!', 'success')
    return redirect(url_for('files_blueprint.categories'))


@blueprint.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
def category_delete(id):
    """Excluir categoria"""
    category = FileCategory.query_active().get_or_404(id)
    
    category.soft_delete(current_user.id)
    
    AuditLog.log(
        action='delete',
        table_name='file_categories',
        record_id=category.id,
        description=f'Categoria excluída: {category.name}'
    )
    db.session.commit()
    
    flash('Categoria excluída com sucesso!', 'success')
    return redirect(url_for('files_blueprint.categories'))


@blueprint.route('/edit-image/<int:id>')
@login_required
def edit_image(id):
    """Editor de imagem"""
    file = File.query_active().get_or_404(id)
    
    if not file.is_image:
        flash('Este arquivo não é uma imagem.', 'warning')
        return redirect(url_for('files_blueprint.index'))
    
    return render_template(
        'files/edit_image.html',
        file=file
    )


@blueprint.route('/edit-image/<int:id>/save', methods=['POST'])
@login_required
def save_edited_image(id):
    """Salvar imagem editada"""
    import json
    from PIL import Image
    import os
    
    file = File.query_active().get_or_404(id)
    
    if not file.is_image:
        return jsonify({'success': False, 'error': 'Arquivo não é uma imagem'}), 400
    
    try:
        transformations = json.loads(request.form.get('transformations', '{}'))
        save_mode = request.form.get('save_mode', 'overwrite')
        
        # Abre a imagem
        img = Image.open(file.full_path)
        
        # Aplica transformações
        if transformations.get('rotate'):
            img = img.rotate(-transformations['rotate'], expand=True)
        
        if transformations.get('flipH'):
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        
        if transformations.get('flipV'):
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        
        if transformations.get('crop'):
            crop = transformations['crop']
            img = img.crop((crop['x'], crop['y'], crop['x'] + crop['width'], crop['y'] + crop['height']))
        
        if save_mode == 'overwrite':
            # Salva sobre o original
            img.save(file.full_path, quality=95)
            
            # Atualiza dimensões
            file.width = img.width
            file.height = img.height
            
            # Regenera thumbnail
            if file.thumbnail_path and os.path.exists(file.thumbnail_path):
                os.remove(file.thumbnail_path)
            ImageService.create_thumbnail(file.full_path, file)
            
            db.session.commit()
            
            flash('Imagem salva com sucesso!', 'success')
        else:
            # Salva como cópia
            new_filename = f"copia_{file.original_filename}"
            new_file = FileService.save_file(
                file_data=img,
                original_filename=new_filename,
                entity_type=file.entity_type,
                entity_id=file.entity_id,
                category_id=file.category_id,
                uploaded_by_id=current_user.id
            )
            
            flash(f'Cópia salva como: {new_filename}', 'success')
        
        return redirect(url_for('files_blueprint.index'))
    
    except Exception as e:
        current_app.logger.error(f'Erro ao salvar imagem editada: {e}')
        flash('Erro ao salvar imagem.', 'danger')
        return redirect(url_for('files_blueprint.edit_image', id=id))


@blueprint.route('/serve/<int:id>')
@login_required
def serve(id):
    """Servir arquivo"""
    file = File.query_active().get_or_404(id)
    
    return send_file(
        file.full_path,
        mimetype=file.mime_type,
        as_attachment=False,
        download_name=file.original_filename
    )


@blueprint.route('/serve/<int:id>/thumbnail')
@login_required
def serve_thumbnail(id):
    """Servir thumbnail"""
    file = File.query_active().get_or_404(id)
    
    if file.thumbnail_path:
        return send_file(
            file.thumbnail_path,
            mimetype='image/jpeg',
            as_attachment=False
        )
    else:
        return send_file(
            file.full_path,
            mimetype=file.mime_type,
            as_attachment=False
        )


@blueprint.route('/bulk-download')
@login_required
def bulk_download():
    """Download em lote"""
    import zipfile
    import tempfile
    
    ids = request.args.get('ids', '').split(',')
    if not ids or ids == ['']:
        abort(400)
    
    files = File.query_active().filter(File.id.in_(ids)).all()
    
    if not files:
        abort(404)
    
    # Cria ZIP
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    
    with zipfile.ZipFile(temp_file.name, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f.full_path, f.original_filename)
    
    return send_file(
        temp_file.name,
        mimetype='application/zip',
        as_attachment=True,
        download_name='arquivos.zip'
    )


@blueprint.route('/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    """Exclusão em lote"""
    ids = request.form.get('ids', '').split(',')
    
    if not ids or ids == ['']:
        flash('Nenhum arquivo selecionado.', 'warning')
        return redirect(url_for('files_blueprint.index'))
    
    files = File.query_active().filter(File.id.in_(ids)).all()
    
    for f in files:
        f.soft_delete(current_user.id)
    
    db.session.commit()
    
    flash(f'{len(files)} arquivo(s) excluído(s) com sucesso!', 'success')
    return redirect(url_for('files_blueprint.index'))


# =============================================================================
# ROTAS DE UPLOAD
# =============================================================================

@blueprint.route('/upload', methods=['POST'])
@login_required
def upload():
    """
    Upload de arquivo via AJAX.
    
    Expects:
        - file: Arquivo
        - category: Código da categoria
        - entity_type: Tipo da entidade
        - entity_id: ID da entidade
        - description: Descrição (opcional)
    
    Returns:
        JSON com resultado do upload
    """
    try:
        # Valida campos obrigatórios
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        category_code = request.form.get('category')
        entity_type = request.form.get('entity_type')
        entity_id = request.form.get('entity_id')
        description = request.form.get('description')
        
        if not all([category_code, entity_type, entity_id]):
            return jsonify({'success': False, 'error': 'Parâmetros obrigatórios faltando'}), 400
        
        # Faz upload
        file_record = FileService.upload(
            file=file,
            category_code=category_code,
            entity_type=entity_type,
            entity_id=int(entity_id),
            uploaded_by_id=current_user.id,
            description=description
        )
        
        return jsonify({
            'success': True,
            'file': {
                'id': file_record.id,
                'name': file_record.original_name,
                'size': file_record.size_formatted,
                'url': file_record.url,
                'thumbnail_url': file_record.thumbnail_url,
                'validation_status': file_record.validation_status
            }
        })
    
    except FileValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    
    except Exception as e:
        current_app.logger.error(f'Erro no upload: {e}')
        return jsonify({'success': False, 'error': 'Erro interno no upload'}), 500


@blueprint.route('/upload-multiple', methods=['POST'])
@login_required
def upload_multiple():
    """
    Upload de múltiplos arquivos.
    
    Returns:
        JSON com resultado dos uploads
    """
    files = request.files.getlist('files')
    category_code = request.form.get('category')
    entity_type = request.form.get('entity_type')
    entity_id = request.form.get('entity_id')
    
    if not all([category_code, entity_type, entity_id]):
        return jsonify({'success': False, 'error': 'Parâmetros obrigatórios faltando'}), 400
    
    results = []
    
    for file in files:
        try:
            file_record = FileService.upload(
                file=file,
                category_code=category_code,
                entity_type=entity_type,
                entity_id=int(entity_id),
                uploaded_by_id=current_user.id
            )
            results.append({
                'success': True,
                'name': file.filename,
                'file_id': file_record.id
            })
        except FileValidationError as e:
            results.append({
                'success': False,
                'name': file.filename,
                'error': str(e)
            })
    
    success_count = sum(1 for r in results if r['success'])
    
    return jsonify({
        'success': True,
        'total': len(results),
        'success_count': success_count,
        'results': results
    })


# =============================================================================
# ROTAS DE DOWNLOAD
# =============================================================================

@blueprint.route('/download/<int:file_id>')
@login_required
def download(file_id):
    """Download de arquivo"""
    try:
        path, original_name, mime_type = FileService.download(file_id)
        
        # Log de download
        AuditLog.log(
            action='file_download',
            table_name='files',
            record_id=file_id,
            description=f'Download: {original_name}'
        )
        db.session.commit()
        
        return send_file(
            path,
            download_name=original_name,
            mimetype=mime_type,
            as_attachment=True
        )
    
    except Exception as e:
        current_app.logger.error(f'Erro no download: {e}')
        abort(404)


@blueprint.route('/view/<int:file_id>')
@login_required
def view(file_id):
    """Visualização de arquivo (inline)"""
    try:
        path, original_name, mime_type = FileService.download(file_id)
        
        return send_file(
            path,
            download_name=original_name,
            mimetype=mime_type,
            as_attachment=False  # Inline
        )
    
    except Exception as e:
        current_app.logger.error(f'Erro na visualização: {e}')
        abort(404)


@blueprint.route('/thumbnail/<int:file_id>')
@login_required
def thumbnail(file_id):
    """Retorna thumbnail de uma imagem"""
    try:
        size = request.args.get('size', 200, type=int)
        buffer = ImageService.generate_thumbnail(file_id, max_size=size)
        
        return send_file(
            buffer,
            mimetype='image/jpeg',
            as_attachment=False
        )
    
    except Exception as e:
        current_app.logger.error(f'Erro ao gerar thumbnail: {e}')
        abort(404)


@blueprint.route('/download-zip', methods=['POST'])
@login_required
def download_zip():
    """
    Download de múltiplos arquivos como ZIP.
    
    Expects:
        - file_ids: Lista de IDs dos arquivos (JSON)
    """
    try:
        data = request.get_json()
        file_ids = data.get('file_ids', [])
        
        if not file_ids:
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
        
        zip_buffer = FileService.download_multiple(file_ids)
        
        # Log
        AuditLog.log(
            action='file_download_zip',
            table_name='files',
            description=f'Download ZIP: {len(file_ids)} arquivos',
            new_values={'file_ids': file_ids}
        )
        db.session.commit()
        
        return send_file(
            zip_buffer,
            download_name='arquivos.zip',
            mimetype='application/zip',
            as_attachment=True
        )
    
    except Exception as e:
        current_app.logger.error(f'Erro no download ZIP: {e}')
        return jsonify({'success': False, 'error': 'Erro ao gerar arquivo'}), 500


# =============================================================================
# ROTAS DE EDIÇÃO DE IMAGEM
# =============================================================================

@blueprint.route('/edit/<int:file_id>/crop', methods=['POST'])
@login_required
def crop_image(file_id):
    """
    Recorta uma imagem.
    
    Expects JSON:
        - left, top, right, bottom: Coordenadas do recorte
    """
    try:
        data = request.get_json()
        
        new_file = ImageService.crop(
            file_id=file_id,
            left=int(data['left']),
            top=int(data['top']),
            right=int(data['right']),
            bottom=int(data['bottom']),
            user_id=current_user.id
        )
        
        return jsonify({
            'success': True,
            'file': {
                'id': new_file.id,
                'url': new_file.url,
                'thumbnail_url': new_file.thumbnail_url,
                'width': new_file.width,
                'height': new_file.height
            }
        })
    
    except Exception as e:
        current_app.logger.error(f'Erro ao recortar: {e}')
        return jsonify({'success': False, 'error': str(e)}), 400


@blueprint.route('/edit/<int:file_id>/rotate', methods=['POST'])
@login_required
def rotate_image(file_id):
    """
    Rotaciona uma imagem.
    
    Expects JSON:
        - angle: Ângulo de rotação (90, 180, 270)
    """
    try:
        data = request.get_json()
        angle = int(data.get('angle', 90))
        
        if angle not in (90, 180, 270):
            return jsonify({'success': False, 'error': 'Ângulo inválido'}), 400
        
        new_file = ImageService.rotate(
            file_id=file_id,
            angle=angle,
            user_id=current_user.id
        )
        
        return jsonify({
            'success': True,
            'file': {
                'id': new_file.id,
                'url': new_file.url,
                'thumbnail_url': new_file.thumbnail_url,
                'width': new_file.width,
                'height': new_file.height
            }
        })
    
    except Exception as e:
        current_app.logger.error(f'Erro ao rotacionar: {e}')
        return jsonify({'success': False, 'error': str(e)}), 400


@blueprint.route('/edit/<int:file_id>/resize', methods=['POST'])
@login_required
def resize_image(file_id):
    """
    Redimensiona uma imagem.
    
    Expects JSON:
        - width: Nova largura
        - height: Nova altura (opcional)
        - maintain_aspect: Manter proporção (default: true)
    """
    try:
        data = request.get_json()
        
        new_file = ImageService.resize(
            file_id=file_id,
            width=int(data['width']),
            height=int(data.get('height', data['width'])),
            maintain_aspect=data.get('maintain_aspect', True),
            user_id=current_user.id
        )
        
        return jsonify({
            'success': True,
            'file': {
                'id': new_file.id,
                'url': new_file.url,
                'thumbnail_url': new_file.thumbnail_url,
                'width': new_file.width,
                'height': new_file.height
            }
        })
    
    except Exception as e:
        current_app.logger.error(f'Erro ao redimensionar: {e}')
        return jsonify({'success': False, 'error': str(e)}), 400


# =============================================================================
# ROTAS DE EXCLUSÃO
# =============================================================================

@blueprint.route('/delete/<int:file_id>', methods=['DELETE', 'POST'])
@login_required
def delete_file(file_id):
    """Exclui um arquivo (soft delete)"""
    try:
        success = FileService.delete(file_id, current_user.id)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Arquivo não encontrado'}), 404
    
    except Exception as e:
        current_app.logger.error(f'Erro ao excluir: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# ROTAS DE VALIDAÇÃO
# =============================================================================

@blueprint.route('/validate/<int:file_id>', methods=['POST'])
@login_required
def validate_file(file_id):
    """
    Aprova ou rejeita um arquivo.
    
    Expects JSON:
        - action: 'approve' ou 'reject'
        - notes: Observações (opcional)
    """
    try:
        file_record = File.query_active().get(file_id)
        if not file_record:
            return jsonify({'success': False, 'error': 'Arquivo não encontrado'}), 404
        
        data = request.get_json()
        action = data.get('action')
        notes = data.get('notes')
        
        if action == 'approve':
            file_record.approve(current_user.id, notes)
        elif action == 'reject':
            file_record.reject(current_user.id, notes)
        else:
            return jsonify({'success': False, 'error': 'Ação inválida'}), 400
        
        AuditLog.log(
            action=f'file_{action}',
            table_name='files',
            record_id=file_id,
            description=f'Arquivo {action}d: {file_record.original_name}',
            new_values={'notes': notes}
        )
        db.session.commit()
        
        return jsonify({
            'success': True,
            'status': file_record.validation_status
        })
    
    except Exception as e:
        current_app.logger.error(f'Erro na validação: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# ROTAS DE CONSULTA
# =============================================================================

@blueprint.route('/list/<entity_type>/<int:entity_id>')
@login_required
def list_files(entity_type, entity_id):
    """
    Lista arquivos de uma entidade.
    
    Returns:
        JSON com arquivos agrupados por categoria
    """
    try:
        include_pending = request.args.get('include_pending', 'true').lower() == 'true'
        
        files = FileService.get_entity_files(
            entity_type=entity_type,
            entity_id=entity_id,
            include_pending=include_pending
        )
        
        # Formata para JSON
        result = {}
        for category_code, file_list in files.items():
            result[category_code] = [{
                'id': f.id,
                'name': f.original_name,
                'size': f.size_formatted,
                'url': f.url,
                'thumbnail_url': f.thumbnail_url,
                'validation_status': f.validation_status,
                'uploaded_at': f.uploaded_at.isoformat()
            } for f in file_list]
        
        return jsonify({
            'success': True,
            'files': result
        })
    
    except Exception as e:
        current_app.logger.error(f'Erro ao listar arquivos: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@blueprint.route('/missing/<entity_type>/<int:entity_id>')
@login_required
def missing_files(entity_type, entity_id):
    """
    Lista categorias obrigatórias sem arquivo.
    
    Returns:
        JSON com categorias faltantes
    """
    try:
        missing = FileService.get_missing_required(entity_type, entity_id)
        
        return jsonify({
            'success': True,
            'missing': [{
                'code': cat.code,
                'name': cat.name,
                'description': cat.description
            } for cat in missing]
        })
    
    except Exception as e:
        current_app.logger.error(f'Erro ao verificar arquivos faltantes: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@blueprint.route('/categories')
@login_required
def list_categories():
    """
    Lista categorias de arquivo disponíveis.
    
    Query params:
        - entity_type: Filtrar por tipo de entidade
    """
    try:
        entity_type = request.args.get('entity_type')
        
        if entity_type:
            categories = FileCategory.get_for_entity(entity_type)
        else:
            categories = FileCategory.query_active().filter_by(
                is_active=True
            ).order_by(FileCategory.display_order).all()
        
        return jsonify({
            'success': True,
            'categories': [{
                'code': cat.code,
                'name': cat.name,
                'description': cat.description,
                'allowed_extensions': cat.allowed_extensions_list,
                'max_size_mb': cat.max_size_mb,
                'is_required': cat.is_required,
                'allow_multiple': cat.allow_multiple,
                'requires_validation': cat.requires_validation
            } for cat in categories]
        })
    
    except Exception as e:
        current_app.logger.error(f'Erro ao listar categorias: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500
