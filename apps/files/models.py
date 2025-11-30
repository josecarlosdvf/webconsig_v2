# -*- encoding: utf-8 -*-
"""
Modelos de Gestão de Arquivos
Categorias de arquivos, arquivos e validações
"""

import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

from apps import db
from apps.database.models import BaseModel, audited


# =============================================================================
# CATEGORIA DE ARQUIVO
# =============================================================================

@audited
class FileCategory(db.Model, BaseModel):
    """
    Categoria/Tipo de arquivo permitido no sistema.
    Define regras de validação para cada tipo de documento.
    
    Exemplos: RG, CPF, Comprovante de Residência, Contracheque, Foto 3x4
    """
    
    __tablename__ = 'file_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação
    code = db.Column(
        db.String(50), 
        unique=True, 
        nullable=False,
        index=True,
        comment='Código único da categoria (ex: rg, cpf, contracheque)'
    )
    name = db.Column(
        db.String(100), 
        nullable=False,
        comment='Nome de exibição (ex: Documento de Identidade)'
    )
    description = db.Column(
        db.String(500), 
        nullable=True,
        comment='Descrição detalhada do documento'
    )
    
    # Regras de validação
    allowed_extensions = db.Column(
        db.String(200), 
        nullable=False,
        default='jpg,jpeg,png,pdf',
        comment='Extensões permitidas separadas por vírgula'
    )
    max_size_mb = db.Column(
        db.Float, 
        nullable=False,
        default=5.0,
        comment='Tamanho máximo em MB'
    )
    min_width = db.Column(
        db.Integer, 
        nullable=True,
        comment='Largura mínima para imagens (px)'
    )
    min_height = db.Column(
        db.Integer, 
        nullable=True,
        comment='Altura mínima para imagens (px)'
    )
    max_width = db.Column(
        db.Integer, 
        nullable=True,
        comment='Largura máxima para imagens (px)'
    )
    max_height = db.Column(
        db.Integer, 
        nullable=True,
        comment='Altura máxima para imagens (px)'
    )
    
    # Comportamento
    is_required = db.Column(
        db.Boolean, 
        default=False,
        comment='Se é obrigatório para o cadastro'
    )
    is_active = db.Column(
        db.Boolean, 
        default=True,
        comment='Se a categoria está ativa'
    )
    allow_multiple = db.Column(
        db.Boolean, 
        default=False,
        comment='Permite múltiplos arquivos desta categoria'
    )
    requires_validation = db.Column(
        db.Boolean, 
        default=False,
        comment='Requer validação manual antes de aceitar'
    )
    
    # Contexto de uso
    entity_types = db.Column(
        db.String(200), 
        nullable=True,
        default='employee',
        comment='Tipos de entidade que usam esta categoria (employee,team,user)'
    )
    
    # Ordem de exibição
    display_order = db.Column(
        db.Integer, 
        default=0,
        comment='Ordem de exibição na lista'
    )
    
    # Modelo de referência para validação visual
    reference_model_path = db.Column(
        db.String(500), 
        nullable=True,
        comment='Caminho do arquivo modelo para comparação visual'
    )
    reference_model_embedding = db.Column(
        db.LargeBinary, 
        nullable=True,
        comment='Embedding do modelo de referência (serializado)'
    )
    similarity_threshold = db.Column(
        db.Float, 
        nullable=True,
        default=0.75,
        comment='Limiar de similaridade para considerar documento compatível (0.0-1.0)'
    )
    enable_visual_validation = db.Column(
        db.Boolean, 
        default=False,
        comment='Habilitar validação visual contra modelo de referência'
    )
    
    # Relacionamentos
    files = db.relationship('File', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<FileCategory {self.code}>'
    
    @property
    def allowed_extensions_list(self):
        """Retorna lista de extensões permitidas"""
        return [ext.strip().lower() for ext in self.allowed_extensions.split(',')]
    
    @property
    def max_size_bytes(self):
        """Retorna tamanho máximo em bytes"""
        return int(self.max_size_mb * 1024 * 1024)
    
    @property
    def allowed_mime_types(self):
        """Retorna lista de MIME types permitidos baseado nas extensões"""
        mime_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'txt': 'text/plain',
            'csv': 'text/csv',
        }
        return [mime_map.get(ext, f'application/{ext}') for ext in self.allowed_extensions_list]
    
    def is_extension_allowed(self, filename):
        """Verifica se a extensão do arquivo é permitida"""
        if '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in self.allowed_extensions_list
    
    def is_size_allowed(self, size_bytes):
        """Verifica se o tamanho do arquivo é permitido"""
        return size_bytes <= self.max_size_bytes
    
    def validate_file(self, file):
        """
        Valida um arquivo contra as regras da categoria.
        
        Args:
            file: FileStorage do Werkzeug
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Verifica extensão
        if not self.is_extension_allowed(file.filename):
            return False, f'Extensão não permitida. Use: {self.allowed_extensions}'
        
        # Verifica tamanho
        file.seek(0, 2)  # Vai para o final
        size = file.tell()
        file.seek(0)  # Volta para o início
        
        if not self.is_size_allowed(size):
            return False, f'Arquivo muito grande. Máximo: {self.max_size_mb}MB'
        
        return True, None
    
    @property
    def has_reference_model(self):
        """Verifica se há modelo de referência configurado"""
        return bool(self.reference_model_path and self.enable_visual_validation)
    
    @property
    def reference_model_full_path(self):
        """Retorna caminho completo do modelo de referência"""
        if not self.reference_model_path:
            return None
        from flask import current_app
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        return os.path.join(upload_folder, self.reference_model_path)
    
    @classmethod
    def get_by_code(cls, code):
        """Busca categoria por código"""
        return cls.query_active().filter_by(code=code, is_active=True).first()
    
    @classmethod
    def get_for_entity(cls, entity_type):
        """Retorna categorias disponíveis para um tipo de entidade"""
        return cls.query_active().filter(
            cls.is_active == True,
            cls.entity_types.contains(entity_type)
        ).order_by(cls.display_order).all()


# =============================================================================
# ARQUIVO
# =============================================================================

@audited
class File(db.Model, BaseModel):
    """
    Arquivo armazenado no sistema.
    Vinculado a uma categoria e a uma entidade (funcionário, equipe, etc).
    """
    
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Categoria do arquivo
    category_id = db.Column(
        db.Integer, 
        db.ForeignKey('file_categories.id'),
        nullable=False,
        index=True
    )
    
    # Informações do arquivo original
    original_name = db.Column(
        db.String(255), 
        nullable=False,
        comment='Nome original do arquivo'
    )
    stored_name = db.Column(
        db.String(255), 
        nullable=False,
        unique=True,
        comment='Nome armazenado (UUID)'
    )
    
    # Localização
    path = db.Column(
        db.String(500), 
        nullable=False,
        comment='Caminho relativo no storage'
    )
    
    # Metadados
    size_bytes = db.Column(
        db.Integer, 
        nullable=False,
        comment='Tamanho em bytes'
    )
    mime_type = db.Column(
        db.String(100), 
        nullable=True,
        comment='MIME type do arquivo'
    )
    extension = db.Column(
        db.String(20), 
        nullable=True,
        comment='Extensão do arquivo'
    )
    
    # Dimensões (para imagens)
    width = db.Column(
        db.Integer, 
        nullable=True,
        comment='Largura em pixels (imagens)'
    )
    height = db.Column(
        db.Integer, 
        nullable=True,
        comment='Altura em pixels (imagens)'
    )
    
    # Vinculação com entidade (opcional - pode ser arquivo geral)
    entity_type = db.Column(
        db.String(50), 
        nullable=True,
        index=True,
        comment='Tipo de entidade (employee, team, user, etc) - nulo para arquivos gerais'
    )
    entity_id = db.Column(
        db.Integer, 
        nullable=True,
        index=True,
        comment='ID da entidade vinculada - nulo para arquivos gerais'
    )
    
    # Upload
    uploaded_by_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    uploaded_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow,
        nullable=False
    )
    
    # Validação
    validation_status = db.Column(
        db.String(20), 
        default='pending',
        comment='Status: pending, approved, rejected'
    )
    validated_by_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    validated_at = db.Column(
        db.DateTime, 
        nullable=True
    )
    validation_notes = db.Column(
        db.Text, 
        nullable=True,
        comment='Observações da validação'
    )
    
    # Validação visual (similaridade com modelo)
    visual_similarity_score = db.Column(
        db.Float,
        nullable=True,
        comment='Pontuação de similaridade com modelo de referência (0.0-1.0)'
    )
    visual_validation_passed = db.Column(
        db.Boolean,
        nullable=True,
        comment='Se passou na validação visual contra modelo'
    )
    
    # Hash para detecção de duplicatas
    file_hash = db.Column(
        db.String(64), 
        nullable=True,
        index=True,
        comment='SHA-256 hash do arquivo'
    )
    
    # Versão (para controle de edições)
    version = db.Column(
        db.Integer, 
        default=1,
        comment='Versão do arquivo'
    )
    parent_id = db.Column(
        db.Integer, 
        db.ForeignKey('files.id'),
        nullable=True,
        comment='ID da versão anterior (se editado)'
    )
    
    # Descrição/notas
    description = db.Column(
        db.String(500), 
        nullable=True,
        comment='Descrição ou observações do arquivo'
    )
    
    # Relacionamentos
    uploaded_by = db.relationship(
        'Users', 
        foreign_keys=[uploaded_by_id],
        backref='uploaded_files'
    )
    validated_by = db.relationship(
        'Users', 
        foreign_keys=[validated_by_id]
    )
    versions = db.relationship(
        'File',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    )
    
    def __repr__(self):
        return f'<File {self.original_name}>'
    
    @property
    def size_formatted(self):
        """Retorna tamanho formatado (KB, MB, etc)"""
        if self.size_bytes < 1024:
            return f'{self.size_bytes} B'
        elif self.size_bytes < 1024 * 1024:
            return f'{self.size_bytes / 1024:.1f} KB'
        else:
            return f'{self.size_bytes / (1024 * 1024):.1f} MB'
    
    @property
    def is_image(self):
        """Verifica se é uma imagem"""
        return self.mime_type and self.mime_type.startswith('image/')
    
    @property
    def is_pdf(self):
        """Verifica se é PDF"""
        return self.mime_type == 'application/pdf'
    
    @property
    def icon(self):
        """Retorna ícone baseado no tipo de arquivo"""
        if self.is_image:
            return 'photo'
        elif self.is_pdf:
            return 'file-type-pdf'
        elif self.mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            return 'file-type-doc'
        elif self.mime_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
            return 'file-type-xls'
        elif self.mime_type in ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed']:
            return 'file-zip'
        elif self.mime_type and self.mime_type.startswith('text/'):
            return 'file-text'
        else:
            return 'file'
    
    @property
    def icon_color(self):
        """Retorna cor do ícone baseado no tipo de arquivo"""
        if self.is_image:
            return 'purple'
        elif self.is_pdf:
            return 'red'
        elif self.mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            return 'blue'
        elif self.mime_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
            return 'green'
        elif self.mime_type in ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed']:
            return 'orange'
        else:
            return 'secondary'
    
    @property
    def full_path(self):
        """Retorna caminho completo do arquivo"""
        from flask import current_app
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        return os.path.join(upload_folder, self.path)
    
    @property
    def url(self):
        """Retorna URL para download do arquivo"""
        from flask import url_for
        return url_for('files_blueprint.download', file_id=self.id)
    
    @property
    def thumbnail_url(self):
        """Retorna URL da thumbnail (para imagens)"""
        if self.is_image:
            from flask import url_for
            return url_for('files_blueprint.thumbnail', file_id=self.id)
        return None
    
    def approve(self, user_id, notes=None):
        """Aprova o arquivo"""
        self.validation_status = 'approved'
        self.validated_by_id = user_id
        self.validated_at = datetime.utcnow()
        self.validation_notes = notes
        db.session.commit()
    
    def reject(self, user_id, notes=None):
        """Rejeita o arquivo"""
        self.validation_status = 'rejected'
        self.validated_by_id = user_id
        self.validated_at = datetime.utcnow()
        self.validation_notes = notes
        db.session.commit()
    
    @classmethod
    def get_for_entity(cls, entity_type, entity_id, category_code=None):
        """
        Retorna arquivos de uma entidade.
        
        Args:
            entity_type: Tipo da entidade (employee, team, etc)
            entity_id: ID da entidade
            category_code: Código da categoria (opcional)
        
        Returns:
            List[File]: Lista de arquivos
        """
        query = cls.query_active().filter_by(
            entity_type=entity_type,
            entity_id=entity_id
        )
        
        if category_code:
            query = query.join(FileCategory).filter(FileCategory.code == category_code)
        
        return query.order_by(cls.uploaded_at.desc()).all()
    
    @classmethod
    def create_from_upload(cls, file, category, entity_type=None, entity_id=None, 
                           uploaded_by_id=None, description=None):
        """
        Cria um registro de arquivo a partir de um upload.
        
        Args:
            file: FileStorage do Werkzeug
            category: FileCategory instance
            entity_type: Tipo da entidade (opcional)
            entity_id: ID da entidade (opcional)
            uploaded_by_id: ID do usuário que fez upload
            description: Descrição opcional
        
        Returns:
            File: Instância criada
        """
        import hashlib
        from flask import current_app
        
        # Gera nome único
        original_name = secure_filename(file.filename)
        extension = original_name.rsplit('.', 1)[1].lower() if '.' in original_name else ''
        stored_name = f'{uuid.uuid4().hex}.{extension}'
        
        # Define caminho - se não tem entidade, vai para pasta 'general'
        if entity_type and entity_id:
            relative_path = os.path.join(entity_type, str(entity_id), category.code)
        else:
            relative_path = os.path.join('general', category.code)
        
        # Lê o arquivo para calcular tamanho e hash
        file_content = file.read()
        size_bytes = len(file_content)
        file_hash = hashlib.sha256(file_content).hexdigest()
        file.seek(0)  # Volta ao início
        
        # Obtém MIME type
        mime_type = file.content_type or 'application/octet-stream'
        
        # Dimensões (para imagens)
        width = None
        height = None
        if mime_type.startswith('image/'):
            try:
                from PIL import Image
                from io import BytesIO
                img = Image.open(BytesIO(file_content))
                width, height = img.size
            except Exception:
                pass
        
        # Cria diretório se não existir
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        full_dir = os.path.join(upload_folder, relative_path)
        os.makedirs(full_dir, exist_ok=True)
        
        # Salva o arquivo
        full_path = os.path.join(full_dir, stored_name)
        file.save(full_path)
        
        # Cria registro no banco
        file_record = cls(
            category_id=category.id,
            original_name=original_name,
            stored_name=stored_name,
            path=os.path.join(relative_path, stored_name),
            size_bytes=size_bytes,
            mime_type=mime_type,
            extension=extension,
            width=width,
            height=height,
            entity_type=entity_type,
            entity_id=entity_id,
            uploaded_by_id=uploaded_by_id,
            file_hash=file_hash,
            description=description,
            validation_status='pending' if category.requires_validation else 'approved'
        )
        
        db.session.add(file_record)
        db.session.flush()  # Gera o ID sem commit para permitir mais operações na mesma transação
        
        return file_record


# =============================================================================
# CATEGORIAS PADRÃO
# =============================================================================

DEFAULT_FILE_CATEGORIES = [
    {
        'code': 'foto_3x4',
        'name': 'Foto 3x4',
        'description': 'Foto do funcionário para identificação',
        'allowed_extensions': 'jpg,jpeg,png',
        'max_size_mb': 2.0,
        'min_width': 300,
        'min_height': 400,
        'is_required': True,
        'entity_types': 'employee',
        'display_order': 1
    },
    {
        'code': 'rg_frente',
        'name': 'RG - Frente',
        'description': 'Documento de identidade (frente)',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'is_required': True,
        'requires_validation': True,
        'entity_types': 'employee',
        'display_order': 2
    },
    {
        'code': 'rg_verso',
        'name': 'RG - Verso',
        'description': 'Documento de identidade (verso)',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'is_required': True,
        'requires_validation': True,
        'entity_types': 'employee',
        'display_order': 3
    },
    {
        'code': 'cpf',
        'name': 'CPF',
        'description': 'Cadastro de Pessoa Física',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'is_required': True,
        'requires_validation': True,
        'entity_types': 'employee',
        'display_order': 4
    },
    {
        'code': 'comprovante_residencia',
        'name': 'Comprovante de Residência',
        'description': 'Conta de luz, água, telefone ou similar (últimos 3 meses)',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'is_required': True,
        'requires_validation': True,
        'entity_types': 'employee',
        'display_order': 5
    },
    {
        'code': 'ctps',
        'name': 'Carteira de Trabalho',
        'description': 'CTPS - páginas com foto e qualificação',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 10.0,
        'allow_multiple': True,
        'entity_types': 'employee',
        'display_order': 6
    },
    {
        'code': 'titulo_eleitor',
        'name': 'Título de Eleitor',
        'description': 'Título de eleitor',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'entity_types': 'employee',
        'display_order': 7
    },
    {
        'code': 'certificado_reservista',
        'name': 'Certificado de Reservista',
        'description': 'Certificado de reservista (homens)',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'entity_types': 'employee',
        'display_order': 8
    },
    {
        'code': 'certidao_casamento',
        'name': 'Certidão de Casamento',
        'description': 'Certidão de casamento ou nascimento',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'entity_types': 'employee',
        'display_order': 9
    },
    {
        'code': 'comprovante_escolaridade',
        'name': 'Comprovante de Escolaridade',
        'description': 'Diploma, certificado ou declaração escolar',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 10.0,
        'allow_multiple': True,
        'entity_types': 'employee',
        'display_order': 10
    },
    {
        'code': 'contracheque',
        'name': 'Contracheque',
        'description': 'Contracheque/holerite',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'allow_multiple': True,
        'entity_types': 'employee',
        'display_order': 11
    },
    {
        'code': 'contrato_trabalho',
        'name': 'Contrato de Trabalho',
        'description': 'Contrato de trabalho assinado',
        'allowed_extensions': 'pdf',
        'max_size_mb': 10.0,
        'entity_types': 'employee',
        'display_order': 12
    },
    {
        'code': 'exame_admissional',
        'name': 'Exame Admissional',
        'description': 'Atestado de saúde ocupacional (ASO)',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'entity_types': 'employee',
        'display_order': 13
    },
    {
        'code': 'logo',
        'name': 'Logo',
        'description': 'Logo da equipe/empresa',
        'allowed_extensions': 'jpg,jpeg,png,svg,webp',
        'max_size_mb': 2.0,
        'entity_types': 'team',
        'display_order': 1
    },
    {
        'code': 'contrato_social',
        'name': 'Contrato Social',
        'description': 'Contrato social da empresa',
        'allowed_extensions': 'pdf',
        'max_size_mb': 20.0,
        'entity_types': 'team',
        'display_order': 2
    },
    {
        'code': 'cartao_cnpj',
        'name': 'Cartão CNPJ',
        'description': 'Comprovante de inscrição no CNPJ',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'entity_types': 'team',
        'display_order': 3
    },
]
