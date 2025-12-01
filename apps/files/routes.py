# -*- encoding: utf-8 -*-
"""
Rotas de Gestão de Arquivos
Upload, download, edição e validação
"""

import io
import os
from flask import (
    render_template, request, jsonify, send_file, 
    current_app, abort, flash, redirect, url_for
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

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
        query = query.filter(File.original_name.ilike(f'%{search}%'))
    
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


@blueprint.route('/validacao-pendente')
@login_required
def pending_validation():
    """Lista de documentos aguardando validação"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Busca arquivos pendentes de validação
    query = File.query_active().filter_by(validation_status='pending')
    
    # Filtro por categoria
    category_id = request.args.get('category_id', type=int)
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Filtro por tipo de entidade
    entity_type = request.args.get('entity_type')
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    
    # Filtro por validação visual (se falhou)
    visual_failed = request.args.get('visual_failed')
    if visual_failed == 'true':
        query = query.filter_by(visual_validation_passed=False)
    
    # Ordena por data de upload
    pagination = query.order_by(File.uploaded_at.desc()).paginate(page=page, per_page=per_page)
    
    # Categorias para filtro
    categories = FileCategory.query_active().filter_by(requires_validation=True).all()
    
    # Contadores
    total_pending = File.query_active().filter_by(validation_status='pending').count()
    visual_failed_count = File.query_active().filter_by(
        validation_status='pending',
        visual_validation_passed=False
    ).count()
    
    return render_template(
        'files/pending_validation.html',
        files=pagination.items,
        pagination=pagination,
        categories=categories,
        total_pending=total_pending,
        visual_failed_count=visual_failed_count
    )


@blueprint.route('/entity/<entity_type>/<int:entity_id>')
@login_required
def entity_files(entity_type, entity_id):
    """Lista arquivos de uma entidade específica"""
    # Obtém a entidade
    entity = None
    if entity_type == 'employee':
        from apps.hr.models import Employee
        entity = Employee.query_active().filter_by(id=entity_id).first_or_404()
    elif entity_type == 'team':
        from apps.hr.models import Team
        entity = Team.query_active().filter_by(id=entity_id).first_or_404()
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
    category = FileCategory.query_active().filter_by(id=id).first_or_404()
    
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
    category = FileCategory.query_active().filter_by(id=id).first_or_404()
    
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


@blueprint.route('/compress')
@login_required
def compress_page():
    """Página de compressão de arquivos"""
    files = File.query_active().order_by(File.created_at.desc()).limit(100).all()
    
    # Verifica se há um arquivo pré-selecionado
    selected_file_id = request.args.get('file_id', type=int)
    
    return render_template(
        'files/compress.html',
        files=files,
        selected_file_id=selected_file_id,
        recent_compressions=[]  # TODO: implementar histórico
    )


@blueprint.route('/compress', methods=['POST'])
@login_required
def compress_file():
    """Comprime um arquivo"""
    import subprocess
    import tempfile
    import shutil
    from PIL import Image
    
    source_type = request.form.get('source_type', 'existing')
    save_mode = request.form.get('save_mode', 'copy')
    
    try:
        # Obtém o arquivo
        if source_type == 'existing':
            file_id = request.form.get('file_id', type=int)
            if not file_id:
                flash('Selecione um arquivo.', 'warning')
                return redirect(url_for('files_blueprint.compress_page'))
            
            file = File.query_active().filter_by(id=file_id).first_or_404()
            file_path = file.full_path
            mime_type = file.mime_type
            original_name = file.original_name
            original_size = file.size_bytes
        else:
            # Upload novo
            uploaded = request.files.get('file')
            if not uploaded or not uploaded.filename:
                flash('Selecione um arquivo para upload.', 'warning')
                return redirect(url_for('files_blueprint.compress_page'))
            
            # Salva temporariamente
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, secure_filename(uploaded.filename))
            uploaded.save(file_path)
            mime_type = uploaded.content_type
            original_name = uploaded.filename
            original_size = os.path.getsize(file_path)
            file = None
        
        # Processa baseado no tipo
        compressed_path = None
        new_size = original_size
        
        if mime_type.startswith('image/'):
            compressed_path, new_size = compress_image(
                file_path,
                quality=int(request.form.get('image_quality', 80)),
                max_width=int(request.form.get('image_resize') or 0),
                strip_metadata=request.form.get('strip_metadata') == 'on'
            )
        elif mime_type == 'application/pdf':
            compressed_path, new_size = compress_pdf(
                file_path,
                level=request.form.get('pdf_level', 'ebook')
            )
        elif mime_type.startswith('video/'):
            compressed_path, new_size = compress_video(
                file_path,
                resolution=request.form.get('video_resolution'),
                crf=int(request.form.get('video_crf', 23)),
                remove_audio=request.form.get('remove_audio') == 'on'
            )
        else:
            flash('Tipo de arquivo não suportado para compressão.', 'warning')
            return redirect(url_for('files_blueprint.compress_page'))
        
        if not compressed_path:
            flash('Erro ao comprimir arquivo.', 'danger')
            return redirect(url_for('files_blueprint.compress_page'))
        
        # Calcula redução
        reduction = round((1 - new_size / original_size) * 100, 1)
        
        # Se não houve redução, avisa o usuário
        if reduction <= 0:
            flash(f'O arquivo já está otimizado e não pode ser reduzido mais.', 'info')
            # Limpa arquivos temporários
            if compressed_path and compressed_path != file_path and os.path.exists(compressed_path):
                os.remove(compressed_path)
            return redirect(url_for('files_blueprint.index'))
        
        if save_mode == 'replace' and file:
            # Substitui o original
            shutil.copy2(compressed_path, file.full_path)
            file.size_bytes = new_size
            db.session.commit()
            
            AuditLog.log(
                action='compress',
                table_name='files',
                record_id=file.id,
                description=f'Arquivo comprimido: {original_size} → {new_size} bytes ({reduction}% redução)'
            )
            db.session.commit()
            
            flash(f'Arquivo comprimido com sucesso! Redução de {reduction}%', 'success')
        else:
            # Salva como novo arquivo
            new_name = f"compressed_{original_name}"
            
            # Busca categoria padrão se não tiver arquivo de referência
            if file and file.category:
                category = file.category
            else:
                category = FileCategory.query.filter_by(code='outros').first()
                if not category:
                    # Cria categoria 'outros' se não existir
                    category = FileCategory(
                        code='outros',
                        name='Outros',
                        description='Arquivos diversos'
                    )
                    db.session.add(category)
                    db.session.flush()
            
            # Cria objeto file-like para o upload
            from werkzeug.datastructures import FileStorage
            from io import BytesIO
            
            with open(compressed_path, 'rb') as f:
                file_content = f.read()
            
            file_storage = FileStorage(
                stream=BytesIO(file_content),
                filename=new_name,
                content_type=mime_type
            )
            
            new_file = File.create_from_upload(
                file=file_storage,
                category=category,
                entity_type=file.entity_type if file else None,
                entity_id=file.entity_id if file else None,
                uploaded_by_id=current_user.id,
                description=f'Comprimido de {original_name}'
            )
            
            db.session.commit()
            
            flash(f'Arquivo comprimido salvo como "{new_name}"! Redução de {reduction}%', 'success')
        
        # Limpa arquivos temporários
        if compressed_path and os.path.exists(compressed_path):
            os.remove(compressed_path)
        
        return redirect(url_for('files_blueprint.index'))
        
    except Exception as e:
        current_app.logger.error(f'Erro ao comprimir arquivo: {e}')
        import traceback
        traceback.print_exc()
        flash('Erro ao comprimir arquivo.', 'danger')
        return redirect(url_for('files_blueprint.compress_page'))


def compress_image(file_path, quality=80, max_width=0, strip_metadata=True):
    """Comprime uma imagem"""
    from PIL import Image
    import tempfile
    
    try:
        img = Image.open(file_path)
        
        # Remove metadados EXIF se solicitado
        if strip_metadata:
            data = list(img.getdata())
            img_no_exif = Image.new(img.mode, img.size)
            img_no_exif.putdata(data)
            img = img_no_exif
        
        # Redimensiona se necessário
        if max_width > 0 and img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)
        
        # Converte RGBA para RGB se necessário
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        
        # Salva comprimido
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        img.save(temp_file.name, 'JPEG', quality=quality, optimize=True)
        
        new_size = os.path.getsize(temp_file.name)
        return temp_file.name, new_size
        
    except Exception as e:
        current_app.logger.error(f'Erro ao comprimir imagem: {e}')
        return None, 0


def compress_pdf(file_path, level='ebook'):
    """Comprime um PDF usando Ghostscript"""
    import subprocess
    import tempfile
    
    original_size = os.path.getsize(file_path)
    
    # Mapeia níveis para configurações do Ghostscript
    # screen: 72 dpi (menor)
    # ebook: 150 dpi
    # printer: 300 dpi
    # prepress: 300 dpi com preservação de cores
    gs_settings = {
        'screen': '/screen',
        'ebook': '/ebook',
        'printer': '/printer',
        'prepress': '/prepress'
    }
    
    setting = gs_settings.get(level, '/ebook')
    
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        
        # Comando Ghostscript com opções adicionais para garantir compressão
        cmd = [
            'gs', 
            '-sDEVICE=pdfwrite', 
            '-dCompatibilityLevel=1.4',
            f'-dPDFSETTINGS={setting}',
            '-dNOPAUSE', 
            '-dQUIET', 
            '-dBATCH',
            '-dDetectDuplicateImages=true',
            '-dCompressFonts=true',
            '-dSubsetFonts=true',
            '-dColorImageDownsampleType=/Bicubic',
            '-dGrayImageDownsampleType=/Bicubic',
            '-dMonoImageDownsampleType=/Bicubic',
            '-dDownsampleColorImages=true',
            '-dDownsampleGrayImages=true',
            '-dDownsampleMonoImages=true',
            f'-sOutputFile={temp_file.name}',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            current_app.logger.error(f'Ghostscript error: {result.stderr}')
            return None, 0
        
        new_size = os.path.getsize(temp_file.name)
        
        # Se o arquivo comprimido ficou maior, tenta com configurações mais agressivas
        if new_size >= original_size and level != 'screen':
            current_app.logger.info(f'PDF ficou maior ({new_size} >= {original_size}), tentando compressão mais agressiva')
            os.unlink(temp_file.name)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            
            # Tenta com configurações mais agressivas
            cmd_aggressive = [
                'gs', 
                '-sDEVICE=pdfwrite', 
                '-dCompatibilityLevel=1.4',
                '-dPDFSETTINGS=/screen',
                '-dNOPAUSE', 
                '-dQUIET', 
                '-dBATCH',
                '-dDetectDuplicateImages=true',
                '-dCompressFonts=true',
                '-dSubsetFonts=true',
                '-dColorImageResolution=72',
                '-dGrayImageResolution=72',
                '-dMonoImageResolution=72',
                '-dDownsampleColorImages=true',
                '-dDownsampleGrayImages=true',
                '-dDownsampleMonoImages=true',
                f'-sOutputFile={temp_file.name}',
                file_path
            ]
            
            result = subprocess.run(cmd_aggressive, capture_output=True, text=True)
            new_size = os.path.getsize(temp_file.name)
            
            # Se ainda ficou maior, retorna o original
            if new_size >= original_size:
                current_app.logger.warning(f'PDF não pode ser reduzido significativamente. Original: {original_size}, Comprimido: {new_size}')
                # Retorna o arquivo original se não conseguiu reduzir
                return file_path, original_size
        
        return temp_file.name, new_size
        
    except FileNotFoundError:
        current_app.logger.error('Ghostscript não encontrado. Instale com: apt install ghostscript')
        return None, 0
    except Exception as e:
        current_app.logger.error(f'Erro ao comprimir PDF: {e}')
        return None, 0


def compress_video(file_path, resolution=None, crf=23, remove_audio=False):
    """Comprime um vídeo usando FFmpeg"""
    import subprocess
    import tempfile
    
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        
        # Comando FFmpeg
        cmd = ['ffmpeg', '-i', file_path, '-y']
        
        # Codec de vídeo
        cmd.extend(['-c:v', 'libx264', '-crf', str(crf)])
        
        # Resolução
        if resolution:
            cmd.extend(['-vf', f'scale=-2:{resolution}'])
        
        # Áudio
        if remove_audio:
            cmd.extend(['-an'])
        else:
            cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
        
        # Preset para velocidade
        cmd.extend(['-preset', 'medium'])
        
        cmd.append(temp_file.name)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            current_app.logger.error(f'FFmpeg error: {result.stderr}')
            return None, 0
        
        new_size = os.path.getsize(temp_file.name)
        return temp_file.name, new_size
        
    except FileNotFoundError:
        current_app.logger.error('FFmpeg não encontrado. Instale com: apt install ffmpeg')
        return None, 0
    except Exception as e:
        current_app.logger.error(f'Erro ao comprimir vídeo: {e}')
        return None, 0


@blueprint.route('/edit-image/<int:id>')
@login_required
def edit_image(id):
    """Editor de imagem"""
    file = File.query_active().filter_by(id=id).first_or_404()
    
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
    """Salvar imagem editada com suporte a crop via Cropper.js"""
    import json
    import base64
    from PIL import Image
    import os
    
    file = File.query_active().filter_by(id=id).first_or_404()
    
    if not file.is_image:
        return jsonify({'success': False, 'error': 'Arquivo não é uma imagem'}), 400
    
    try:
        save_mode = request.form.get('save_mode', 'overwrite')
        image_data = request.form.get('image_data', '')
        
        # Se recebeu dados de imagem em base64 (do Cropper.js)
        if image_data and image_data.startswith('data:image'):
            # Extrai o base64 da string data URL
            header, encoded = image_data.split(',', 1)
            image_bytes = base64.b64decode(encoded)
            
            # Abre a imagem dos bytes
            img = Image.open(io.BytesIO(image_bytes))
            
            # Converte RGBA para RGB se necessário (para JPEG)
            if img.mode == 'RGBA' and file.mime_type == 'image/jpeg':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
        else:
            # Fallback para o método antigo com transformações JSON
            transformations = json.loads(request.form.get('transformations', '{}'))
            
            # Abre a imagem original
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
            save_kwargs = {'quality': 95}
            if file.mime_type == 'image/png':
                save_kwargs = {'optimize': True}
            
            img.save(file.full_path, **save_kwargs)
            
            # Atualiza tamanho do arquivo
            file.size = os.path.getsize(file.full_path)
            
            # Regenera thumbnail
            if file.thumbnail_path and os.path.exists(file.thumbnail_path):
                os.remove(file.thumbnail_path)
            ImageService.create_thumbnail(file.full_path, file)
            
            db.session.commit()
            
            flash('Imagem salva com sucesso!', 'success')
        else:
            # Salva como cópia
            new_filename = f"copia_{file.original_name}"
            
            # Salva em buffer
            buffer = io.BytesIO()
            save_kwargs = {'quality': 95}
            if file.mime_type == 'image/png':
                img.save(buffer, format='PNG', optimize=True)
            else:
                img.save(buffer, format='JPEG', **save_kwargs)
            buffer.seek(0)
            
            # Cria novo arquivo
            new_file = File.create_from_upload(
                file=type('obj', (object,), {
                    'filename': new_filename,
                    'read': lambda: buffer.read(),
                    'seek': lambda x: buffer.seek(x),
                    'stream': buffer
                })(),
                category_code=file.category.code if file.category else 'outros',
                entity_type=file.entity_type,
                entity_id=file.entity_id,
                uploaded_by_id=current_user.id
            )
            
            flash(f'Cópia salva como: {new_filename}', 'success')
        
        return redirect(url_for('files_blueprint.index'))
    
    except Exception as e:
        current_app.logger.error(f'Erro ao salvar imagem editada: {e}')
        import traceback
        traceback.print_exc()
        flash('Erro ao salvar imagem.', 'danger')
        return redirect(url_for('files_blueprint.edit_image', id=id))


@blueprint.route('/serve/<int:id>')
@login_required
def serve(id):
    """Servir arquivo"""
    file = File.query_active().filter_by(id=id).first_or_404()
    
    return send_file(
        file.full_path,
        mimetype=file.mime_type,
        as_attachment=False,
        download_name=file.original_name
    )


@blueprint.route('/serve/<int:id>/thumbnail')
@login_required
def serve_thumbnail(id):
    """Servir thumbnail"""
    file = File.query_active().filter_by(id=id).first_or_404()
    
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
            zf.write(f.full_path, f.original_name)
    
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


@blueprint.route('/<int:file_id>/rename', methods=['POST'])
@login_required
def rename_file(file_id):
    """Renomear arquivo"""
    file = File.query_active().filter_by(id=file_id).first_or_404()
    
    new_name = request.form.get('new_name', '').strip()
    
    if not new_name:
        if request.headers.get('Accept', '').find('application/json') != -1:
            return jsonify({'success': False, 'error': 'Nome é obrigatório'}), 400
        flash('Nome é obrigatório.', 'danger')
        return redirect(url_for('files_blueprint.index'))
    
    # Mantém a extensão original se não foi incluída
    import os
    old_ext = os.path.splitext(file.original_name)[1].lower()
    new_ext = os.path.splitext(new_name)[1].lower()
    
    if not new_ext:
        new_name = new_name + old_ext
    
    old_name = file.original_name
    file.original_name = new_name
    
    db.session.commit()
    
    AuditLog.log(
        action='update',
        table_name='files',
        record_id=file.id,
        description=f'Arquivo renomeado: {old_name} → {new_name}'
    )
    db.session.commit()
    
    if request.headers.get('Accept', '').find('application/json') != -1:
        return jsonify({'success': True, 'new_name': new_name})
    
    flash('Arquivo renomeado com sucesso!', 'success')
    return redirect(url_for('files_blueprint.index'))


# =============================================================================
# ROTAS DE UPLOAD
# =============================================================================

@blueprint.route('/upload', methods=['POST'])
@login_required
def upload():
    """
    Upload de arquivo via AJAX ou form tradicional.
    
    Expects:
        - file: Arquivo
        - category: Código da categoria OU category_id: ID da categoria
        - entity_type: Tipo da entidade
        - entity_id: ID da entidade
        - description: Descrição (opcional)
        - redirect_url: URL para redirecionamento (opcional, para forms tradicionais)
    
    Returns:
        JSON com resultado do upload ou redirect
    """
    try:
        # Valida campos obrigatórios
        if 'file' not in request.files:
            if request.headers.get('Accept', '').find('application/json') != -1:
                return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400
            flash('Nenhum arquivo enviado', 'danger')
            return redirect(request.form.get('redirect_url', url_for('files_blueprint.index')))
        
        file = request.files['file']
        if not file or not file.filename:
            if request.headers.get('Accept', '').find('application/json') != -1:
                return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.form.get('redirect_url', url_for('files_blueprint.index')))
        
        # Aceita category (código) ou category_id (ID)
        category_code = request.form.get('category')
        category_id = request.form.get('category_id')
        entity_type = request.form.get('entity_type') or None
        entity_id = request.form.get('entity_id') or None
        description = request.form.get('description')
        redirect_url = request.form.get('redirect_url')
        
        # Se category_id foi fornecido, busca o código
        if category_id and not category_code:
            category = FileCategory.query.get(int(category_id))
            if category:
                category_code = category.code
        
        # Categoria é obrigatória, entidade é opcional
        if not category_code:
            error_msg = 'Categoria é obrigatória'
            if request.headers.get('Accept', '').find('application/json') != -1:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'danger')
            return redirect(redirect_url or url_for('files_blueprint.index'))
        
        # Se entity_type foi fornecido, entity_id também é necessário
        if entity_type and not entity_id:
            error_msg = 'Entidade é obrigatória quando tipo de entidade é selecionado'
            if request.headers.get('Accept', '').find('application/json') != -1:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'danger')
            return redirect(redirect_url or url_for('files_blueprint.index'))
        
        # Faz upload
        file_record = FileService.upload(
            file=file,
            category_code=category_code,
            entity_type=entity_type,
            entity_id=int(entity_id) if entity_id else None,
            uploaded_by_id=current_user.id,
            description=description
        )
        
        # Se é uma requisição AJAX, retorna JSON
        if request.headers.get('Accept', '').find('application/json') != -1 or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
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
        
        # Caso contrário, redireciona
        flash('Arquivo enviado com sucesso!', 'success')
        return redirect(redirect_url or url_for('files_blueprint.index'))
    
    except FileValidationError as e:
        error_msg = str(e)
        if request.headers.get('Accept', '').find('application/json') != -1:
            return jsonify({'success': False, 'error': error_msg}), 400
        flash(error_msg, 'danger')
        return redirect(request.form.get('redirect_url', url_for('files_blueprint.index')))
    
    except Exception as e:
        current_app.logger.error(f'Erro no upload: {e}')
        error_msg = 'Erro interno no upload'
        if request.headers.get('Accept', '').find('application/json') != -1:
            return jsonify({'success': False, 'error': error_msg}), 500
        flash(error_msg, 'danger')
        return redirect(request.form.get('redirect_url', url_for('files_blueprint.index')))


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
        
        response = send_file(
            buffer,
            mimetype='image/jpeg',
            as_attachment=False
        )
        
        # Adiciona headers de cache para evitar requisições duplicadas
        response.headers['Cache-Control'] = 'private, max-age=3600'
        response.headers['ETag'] = f'thumb-{file_id}-{size}'
        
        return response
    
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
        file_record = File.query_active().filter_by(id=file_id).first()
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
