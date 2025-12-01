# -*- encoding: utf-8 -*-
"""
Rotas de Autenticação
"""

from flask import render_template, redirect, request, url_for, flash, session, jsonify, make_response, current_app
from flask_login import current_user, login_user, logout_user, login_required

from apps import db
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm, ProfileForm, ChangePasswordForm
from apps.authentication.models import Users
from apps.messages import Messages


@blueprint.route('/debug-session')
def debug_session():
    """Debug: mostra estado da sessão"""
    return jsonify({
        'session_keys': list(session.keys()),
        'session_token': session.get('session_token', 'NOT SET')[:20] + '...' if session.get('session_token') else 'NOT SET',
        'is_authenticated': current_user.is_authenticated,
        'user_id': current_user.id if current_user.is_authenticated else None,
        'cookies': dict(request.cookies)
    })


@blueprint.route('/')
def route_default():
    """Rota padrão - redireciona para login ou dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('home_blueprint.dashboard'))
    return redirect(url_for('authentication_blueprint.login'))


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    
    # Se já está logado, redireciona
    if current_user.is_authenticated:
        return redirect(url_for('home_blueprint.dashboard'))
    
    form = LoginForm()
    msg = None
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Busca usuário por username ou e-mail
        user = Users.query.filter(
            (Users.username == username) | (Users.email == username)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                msg = Messages.get('account_inactive')
            else:
                # Atualiza último login
                user.update_last_login()
                
                # Realiza o login
                login_user(user, remember=form.remember.data)
                
                # Redireciona para a página solicitada ou dashboard
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('home_blueprint.dashboard'))
        else:
            msg = Messages.get('login_failed')
    
    return render_template(
        'accounts/login.html',
        form=form,
        msg=msg
    )


@blueprint.route('/registrar', methods=['GET', 'POST'])
def register():
    """Página de registro"""
    
    # Se já está logado, redireciona
    if current_user.is_authenticated:
        return redirect(url_for('home_blueprint.dashboard'))
    
    form = CreateAccountForm()
    msg = None
    success = False
    
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        
        # Verifica se username já existe
        if Users.query.filter_by(username=username).first():
            msg = Messages.get('username_exists')
        
        # Verifica se e-mail já existe
        elif Users.query.filter_by(email=email).first():
            msg = Messages.get('email_exists')
        
        else:
            # Cria novo usuário
            user = Users(
                username=username,
                email=email,
                password=password
            )
            
            if user.save():
                msg = Messages.get('register_success')
                success = True
            else:
                msg = Messages.get('register_failed')
    
    return render_template(
        'accounts/register.html',
        form=form,
        msg=msg,
        success=success
    )


@blueprint.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    # Invalida o token de sessão
    if current_user.is_authenticated:
        current_user.invalidate_session()
    
    # Limpa a sessão
    session.pop('session_token', None)
    
    logout_user()
    flash(Messages.get('logout_success'), 'info')
    return redirect(url_for('authentication_blueprint.login'))


@blueprint.route('/verificar-sessao')
@login_required
def check_session():
    """API para verificar se a sessão ainda é válida (via JavaScript)"""
    session_token = session.get('session_token')
    
    if not session_token or not current_user.verify_session_token(session_token):
        return jsonify({
            'valid': False,
            'message': 'Sua sessão foi encerrada pois você fez login em outro dispositivo.'
        })
    
    return jsonify({'valid': True})


@blueprint.route('/sessao-expirada')
def session_expired():
    """Página exibida quando a sessão expira por login em outro dispositivo"""
    # Limpa qualquer sessão residual
    session.pop('session_token', None)
    logout_user()
    
    return render_template(
        'accounts/session-expired.html'
    )


@blueprint.route('/perfil', methods=['GET', 'POST'])
@login_required
def profile():
    """Página de perfil do usuário"""
    form = ProfileForm()
    password_form = ChangePasswordForm()
    
    if request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.phone.data = current_user.phone
        form.bio.data = current_user.bio
    
    if form.validate_on_submit() and 'save_profile' in request.form:
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('authentication_blueprint.profile'))
    
    return render_template(
        'accounts/profile.html',
        segment='profile',
        form=form,
        password_form=password_form
    )


@blueprint.route('/alterar-senha', methods=['POST'])
@login_required
def change_password():
    """Alteração de senha"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Senha atual incorreta.', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Senha alterada com sucesso!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')
    
    return redirect(url_for('authentication_blueprint.profile'))


@blueprint.route('/perfil/avatar', methods=['POST'])
@login_required
def update_avatar():
    """Upload/atualização de foto do perfil"""
    import os
    from werkzeug.utils import secure_filename
    
    # Extensões permitidas para avatar
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    
    if 'avatar' not in request.files:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('authentication_blueprint.profile'))
    
    file = request.files['avatar']
    
    if not file or file.filename == '':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Arquivo inválido'}), 400
        flash('Arquivo inválido.', 'danger')
        return redirect(url_for('authentication_blueprint.profile'))
    
    # Verifica extensão
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Formato não permitido. Use: PNG, JPG, GIF ou WebP'}), 400
        flash('Formato não permitido. Use: PNG, JPG, GIF ou WebP', 'danger')
        return redirect(url_for('authentication_blueprint.profile'))
    
    # Verifica tamanho
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    
    if size > MAX_SIZE:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Arquivo muito grande. Máximo: 5MB'}), 400
        flash('Arquivo muito grande. Máximo: 5MB', 'danger')
        return redirect(url_for('authentication_blueprint.profile'))
    
    try:
        # Define pasta de avatars
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        avatar_folder = os.path.join(upload_folder, 'avatars')
        os.makedirs(avatar_folder, exist_ok=True)
        
        # Nome do arquivo: user_{id}_{timestamp}.{ext}
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"user_{current_user.id}_{timestamp}.{ext}"
        filepath = os.path.join(avatar_folder, filename)
        
        # Remove avatar anterior se existir
        if current_user.avatar_url:
            old_filename = current_user.avatar_url.split('/')[-1]
            old_filepath = os.path.join(avatar_folder, old_filename)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)
        
        # Salva novo arquivo
        file.save(filepath)
        
        # Atualiza URL no usuário
        current_user.avatar_url = f"/uploads/avatars/{filename}"
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'avatar_url': current_user.avatar_url,
                'message': 'Foto atualizada com sucesso!'
            })
        
        flash('Foto atualizada com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao atualizar avatar: {e}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Erro ao salvar arquivo'}), 500
        flash('Erro ao salvar arquivo.', 'danger')
    
    return redirect(url_for('authentication_blueprint.profile'))


@blueprint.route('/perfil/avatar/remover', methods=['POST'])
@login_required
def remove_avatar():
    """Remove a foto do perfil"""
    import os
    
    try:
        if current_user.avatar_url:
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            filename = current_user.avatar_url.split('/')[-1]
            filepath = os.path.join(upload_folder, 'avatars', filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
            
            current_user.avatar_url = None
            db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Foto removida com sucesso!'})
        
        flash('Foto removida com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao remover avatar: {e}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Erro ao remover foto'}), 500
        flash('Erro ao remover foto.', 'danger')
    
    return redirect(url_for('authentication_blueprint.profile'))


# ===========================================
# Handlers de Erro
# ===========================================

@blueprint.app_errorhandler(403)
def access_forbidden(error):
    """Acesso negado"""
    return render_template('errors/403.html'), 403


@blueprint.app_errorhandler(404)
def not_found_error(error):
    """Página não encontrada"""
    return render_template('errors/404.html'), 404


@blueprint.app_errorhandler(500)
def internal_error(error):
    """Erro interno do servidor"""
    db.session.rollback()
    return render_template('errors/500.html'), 500
