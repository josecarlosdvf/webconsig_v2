# -*- encoding: utf-8 -*-
"""
Seeder de Categorias de Arquivos para RH
Define as categorias de documentos necessários para funcionários
"""

from apps import db
from apps.files.models import FileCategory
from apps.logs import log_info


# Categorias de documentos de funcionários
EMPLOYEE_FILE_CATEGORIES = [
    # ============================
    # FOTO
    # ============================
    {
        'code': 'FOTO_3X4',
        'name': 'Foto 3x4',
        'description': 'Foto para identificação do funcionário (tipo documento)',
        'allowed_extensions': 'jpg,jpeg,png',
        'max_size_mb': 5.0,
        'min_width': 300,
        'min_height': 400,
        'is_required': True,
        'allow_multiple': False,
        'entity_types': 'employee',
        'display_order': 1
    },
    
    # ============================
    # DOCUMENTOS PESSOAIS
    # ============================
    {
        'code': 'DOC_RG',
        'name': 'RG - Documento de Identidade',
        'description': 'Cópia do RG (frente e verso)',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 10.0,
        'is_required': True,
        'allow_multiple': True,
        'entity_types': 'employee',
        'display_order': 10
    },
    {
        'code': 'DOC_CPF',
        'name': 'CPF',
        'description': 'Cópia do CPF',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'is_required': True,
        'allow_multiple': False,
        'entity_types': 'employee',
        'display_order': 11
    },
    {
        'code': 'DOC_CNH',
        'name': 'CNH - Carteira de Motorista',
        'description': 'Cópia da CNH (frente e verso)',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 10.0,
        'is_required': False,
        'allow_multiple': True,
        'entity_types': 'employee',
        'display_order': 12
    },
    {
        'code': 'DOC_TITULO_ELEITOR',
        'name': 'Título de Eleitor',
        'description': 'Cópia do título de eleitor',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'is_required': False,
        'allow_multiple': False,
        'entity_types': 'employee',
        'display_order': 13
    },
    {
        'code': 'DOC_CERTIDAO_NASCIMENTO',
        'name': 'Certidão de Nascimento',
        'description': 'Cópia da certidão de nascimento',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 10.0,
        'is_required': False,
        'allow_multiple': False,
        'entity_types': 'employee',
        'display_order': 14
    },
    {
        'code': 'DOC_CERTIDAO_CASAMENTO',
        'name': 'Certidão de Casamento',
        'description': 'Cópia da certidão de casamento (se aplicável)',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 10.0,
        'is_required': False,
        'allow_multiple': False,
        'entity_types': 'employee',
        'display_order': 15
    },
    {
        'code': 'DOC_RESERVISTA',
        'name': 'Certificado de Reservista',
        'description': 'Certificado de reservista (para homens)',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'is_required': False,
        'allow_multiple': False,
        'entity_types': 'employee',
        'display_order': 16
    },
    
    # ============================
    # DOCUMENTOS TRABALHISTAS
    # ============================
    {
        'code': 'DOC_CTPS',
        'name': 'CTPS - Carteira de Trabalho',
        'description': 'Cópia da CTPS (página de identificação e contrato)',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 10.0,
        'is_required': True,
        'allow_multiple': True,
        'entity_types': 'employee',
        'display_order': 20
    },
    {
        'code': 'DOC_PIS',
        'name': 'Comprovante PIS/PASEP',
        'description': 'Comprovante do número do PIS/PASEP',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'is_required': False,
        'allow_multiple': False,
        'entity_types': 'employee',
        'display_order': 21
    },
    
    # ============================
    # COMPROVANTES
    # ============================
    {
        'code': 'DOC_COMP_RESIDENCIA',
        'name': 'Comprovante de Residência',
        'description': 'Comprovante de residência recente (últimos 3 meses)',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 10.0,
        'is_required': True,
        'allow_multiple': False,
        'entity_types': 'employee',
        'display_order': 30
    },
    {
        'code': 'DOC_COMP_ESCOLARIDADE',
        'name': 'Comprovante de Escolaridade',
        'description': 'Diploma, certificado ou histórico escolar',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 10.0,
        'is_required': False,
        'allow_multiple': True,
        'entity_types': 'employee',
        'display_order': 31
    },
    {
        'code': 'DOC_COMP_BANCARIO',
        'name': 'Comprovante Bancário',
        'description': 'Comprovante de conta bancária para depósito salarial',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'is_required': False,
        'allow_multiple': False,
        'entity_types': 'employee',
        'display_order': 32
    },
    
    # ============================
    # EXAMES E SAÚDE
    # ============================
    {
        'code': 'DOC_ASO_ADMISSIONAL',
        'name': 'ASO Admissional',
        'description': 'Atestado de Saúde Ocupacional de admissão',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 10.0,
        'is_required': True,
        'allow_multiple': False,
        'entity_types': 'employee',
        'display_order': 40
    },
    {
        'code': 'DOC_ASO_PERIODICO',
        'name': 'ASO Periódico',
        'description': 'Atestado de Saúde Ocupacional periódico',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 10.0,
        'is_required': False,
        'allow_multiple': True,
        'entity_types': 'employee',
        'display_order': 41
    },
    {
        'code': 'DOC_ASO_DEMISSIONAL',
        'name': 'ASO Demissional',
        'description': 'Atestado de Saúde Ocupacional de desligamento',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 10.0,
        'is_required': False,
        'allow_multiple': False,
        'entity_types': 'employee',
        'display_order': 42
    },
    {
        'code': 'DOC_ATESTADO_MEDICO',
        'name': 'Atestado Médico',
        'description': 'Atestados médicos (afastamento, licença, etc)',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 10.0,
        'is_required': False,
        'allow_multiple': True,
        'entity_types': 'employee',
        'display_order': 43
    },
    
    # ============================
    # CONTRATOS E TERMOS
    # ============================
    {
        'code': 'DOC_CONTRATO_TRABALHO',
        'name': 'Contrato de Trabalho',
        'description': 'Contrato de trabalho assinado',
        'allowed_extensions': 'pdf',
        'max_size_mb': 20.0,
        'is_required': True,
        'allow_multiple': True,
        'entity_types': 'employee',
        'display_order': 50
    },
    {
        'code': 'DOC_TERMO_RESPONSABILIDADE',
        'name': 'Termo de Responsabilidade',
        'description': 'Termos de responsabilidade assinados',
        'allowed_extensions': 'pdf',
        'max_size_mb': 10.0,
        'is_required': False,
        'allow_multiple': True,
        'entity_types': 'employee',
        'display_order': 51
    },
    {
        'code': 'DOC_REGULAMENTO_INTERNO',
        'name': 'Regulamento Interno',
        'description': 'Ciência do regulamento interno assinada',
        'allowed_extensions': 'pdf',
        'max_size_mb': 10.0,
        'is_required': False,
        'allow_multiple': False,
        'entity_types': 'employee',
        'display_order': 52
    },
    
    # ============================
    # FÉRIAS E RECIBOS
    # ============================
    {
        'code': 'DOC_AVISO_FERIAS',
        'name': 'Aviso de Férias',
        'description': 'Aviso de férias assinado',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'is_required': False,
        'allow_multiple': True,
        'entity_types': 'employee',
        'display_order': 60
    },
    {
        'code': 'DOC_RECIBO_FERIAS',
        'name': 'Recibo de Férias',
        'description': 'Recibo de pagamento de férias',
        'allowed_extensions': 'jpg,jpeg,png,pdf',
        'max_size_mb': 5.0,
        'is_required': False,
        'allow_multiple': True,
        'entity_types': 'employee',
        'display_order': 61
    },
    
    # ============================
    # DESLIGAMENTO
    # ============================
    {
        'code': 'DOC_CARTA_DEMISSAO',
        'name': 'Carta de Demissão/Dispensa',
        'description': 'Carta de demissão ou comunicado de dispensa',
        'allowed_extensions': 'pdf',
        'max_size_mb': 5.0,
        'is_required': False,
        'allow_multiple': False,
        'entity_types': 'employee',
        'display_order': 70
    },
    {
        'code': 'DOC_TERMO_RESCISAO',
        'name': 'Termo de Rescisão',
        'description': 'TRCT - Termo de Rescisão de Contrato de Trabalho',
        'allowed_extensions': 'pdf',
        'max_size_mb': 10.0,
        'is_required': False,
        'allow_multiple': False,
        'entity_types': 'employee',
        'display_order': 71
    },
    {
        'code': 'DOC_GRRF',
        'name': 'GRRF',
        'description': 'Guia de Recolhimento Rescisório do FGTS',
        'allowed_extensions': 'pdf',
        'max_size_mb': 5.0,
        'is_required': False,
        'allow_multiple': False,
        'entity_types': 'employee',
        'display_order': 72
    },
    
    # ============================
    # OUTROS
    # ============================
    {
        'code': 'DOC_OUTROS',
        'name': 'Outros Documentos',
        'description': 'Outros documentos relacionados ao funcionário',
        'allowed_extensions': 'jpg,jpeg,png,pdf,doc,docx,xls,xlsx',
        'max_size_mb': 20.0,
        'is_required': False,
        'allow_multiple': True,
        'entity_types': 'employee',
        'display_order': 99
    },
]


def seed_employee_file_categories():
    """
    Popula as categorias de arquivos para funcionários.
    Só cria categorias que não existem (baseado no código).
    """
    created_count = 0
    updated_count = 0
    
    for cat_data in EMPLOYEE_FILE_CATEGORIES:
        # Verifica se já existe
        existing = FileCategory.query.filter_by(code=cat_data['code']).first()
        
        if existing:
            # Atualiza campos se necessário
            for key, value in cat_data.items():
                if hasattr(existing, key) and getattr(existing, key) != value:
                    setattr(existing, key, value)
                    updated_count += 1
        else:
            # Cria nova categoria
            category = FileCategory(**cat_data)
            db.session.add(category)
            created_count += 1
    
    if created_count > 0 or updated_count > 0:
        db.session.commit()
        log_info(f'Seed HR Files: {created_count} categorias criadas, {updated_count} atualizadas')
    
    return created_count, updated_count


def run_seed():
    """Executa o seeder"""
    return seed_employee_file_categories()
