# -*- encoding: utf-8 -*-
"""
Modelos de Recursos Humanos
Funcionários, Equipes e Corbans
"""

from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from apps import db
from apps.database.models import BaseModel, audited

# Import lazy para evitar importação circular
def get_file_category():
    from apps.files.models import FileCategory
    return FileCategory


# =============================================================================
# ENUMS E CONSTANTES
# =============================================================================

class TeamType:
    """Tipos de equipe"""
    TEAM = 'team'       # Equipe interna
    CORBAN = 'corban'   # Correspondente bancário parceiro
    
    CHOICES = [
        (TEAM, 'Equipe'),
        (CORBAN, 'Corban')
    ]


class EmployeeStatus:
    """Status do funcionário"""
    ACTIVE = 'active'           # Ativo
    INACTIVE = 'inactive'       # Inativo
    VACATION = 'vacation'       # Férias
    LEAVE = 'leave'             # Licença/Afastamento
    TERMINATED = 'terminated'   # Demitido
    
    CHOICES = [
        (ACTIVE, 'Ativo'),
        (INACTIVE, 'Inativo'),
        (VACATION, 'Férias'),
        (LEAVE, 'Licença'),
        (TERMINATED, 'Desligado')
    ]


class ContractType:
    """Tipos de contrato"""
    CLT = 'clt'
    PJ = 'pj'
    TEMPORARY = 'temporary'
    INTERN = 'intern'
    APPRENTICE = 'apprentice'
    
    CHOICES = [
        (CLT, 'CLT'),
        (PJ, 'PJ'),
        (TEMPORARY, 'Temporário'),
        (INTERN, 'Estagiário'),
        (APPRENTICE, 'Aprendiz')
    ]


class Gender:
    """Gênero"""
    MALE = 'M'
    FEMALE = 'F'
    OTHER = 'O'
    
    CHOICES = [
        (MALE, 'Masculino'),
        (FEMALE, 'Feminino'),
        (OTHER, 'Outro')
    ]


class MaritalStatus:
    """Estado civil"""
    SINGLE = 'single'
    MARRIED = 'married'
    DIVORCED = 'divorced'
    WIDOWED = 'widowed'
    SEPARATED = 'separated'
    UNION = 'union'
    
    CHOICES = [
        (SINGLE, 'Solteiro(a)'),
        (MARRIED, 'Casado(a)'),
        (DIVORCED, 'Divorciado(a)'),
        (WIDOWED, 'Viúvo(a)'),
        (SEPARATED, 'Separado(a)'),
        (UNION, 'União Estável')
    ]


class EducationLevel:
    """Grau de instrução"""
    NONE = 'none'
    ELEMENTARY_INCOMPLETE = 'elementary_incomplete'
    ELEMENTARY = 'elementary'
    HIGH_SCHOOL_INCOMPLETE = 'high_school_incomplete'
    HIGH_SCHOOL = 'high_school'
    TECHNICAL = 'technical'
    COLLEGE_INCOMPLETE = 'college_incomplete'
    COLLEGE = 'college'
    POST_GRADUATE = 'post_graduate'
    MASTERS = 'masters'
    DOCTORATE = 'doctorate'
    
    CHOICES = [
        (NONE, 'Sem escolaridade'),
        (ELEMENTARY_INCOMPLETE, 'Fundamental Incompleto'),
        (ELEMENTARY, 'Fundamental Completo'),
        (HIGH_SCHOOL_INCOMPLETE, 'Médio Incompleto'),
        (HIGH_SCHOOL, 'Médio Completo'),
        (TECHNICAL, 'Técnico'),
        (COLLEGE_INCOMPLETE, 'Superior Incompleto'),
        (COLLEGE, 'Superior Completo'),
        (POST_GRADUATE, 'Pós-Graduação'),
        (MASTERS, 'Mestrado'),
        (DOCTORATE, 'Doutorado')
    ]


# =============================================================================
# EQUIPE / CORBAN
# =============================================================================

@audited
class Team(db.Model, BaseModel):
    """
    Equipe ou Correspondente Bancário (Corban).
    Funcionários podem ser vinculados a equipes ou corbans.
    """
    
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação básica
    name = db.Column(
        db.String(100), 
        nullable=False,
        comment='Nome da equipe/corban'
    )
    acronym = db.Column(
        db.String(20), 
        nullable=True,
        comment='Sigla'
    )
    type = db.Column(
        db.String(20), 
        nullable=False,
        default=TeamType.TEAM,
        index=True,
        comment='Tipo: team ou corban'
    )
    
    # Dados da empresa (para corbans)
    cnpj = db.Column(
        db.String(14), 
        nullable=True,
        unique=True,
        comment='CNPJ (apenas números)'
    )
    legal_name = db.Column(
        db.String(150), 
        nullable=True,
        comment='Razão social'
    )
    trade_name = db.Column(
        db.String(150), 
        nullable=True,
        comment='Nome fantasia'
    )
    
    # Contato
    email = db.Column(
        db.String(120), 
        nullable=True,
        comment='E-mail de contato'
    )
    phone = db.Column(
        db.String(20), 
        nullable=True,
        comment='Telefone'
    )
    
    # Financeiro
    pix = db.Column(
        db.String(100), 
        nullable=True,
        comment='Chave PIX'
    )
    
    # Comissão para corbans (percentual sobre comissão externos das tabelas)
    # Ex: 110 = 110% (10% a mais), 90 = 90% (10% a menos)
    comissao_fator_percentual = db.Column(
        db.Numeric(5, 2),
        nullable=True,
        default=100.00,
        comment='Fator percentual sobre comissão externos (ex: 110 = 110%)'
    )
    
    # Localização
    location = db.Column(
        db.String(200), 
        nullable=True,
        comment='Localização/Endereço'
    )
    
    # Configurações
    vacancies = db.Column(
        db.Integer, 
        nullable=True,
        default=0,
        comment='Número de vagas disponíveis'
    )
    color = db.Column(
        db.String(7), 
        nullable=True,
        default='#206bc4',
        comment='Cor de identificação (hex)'
    )
    
    # Status
    is_active = db.Column(
        db.Boolean, 
        default=True,
        index=True,
        comment='Se está ativo'
    )
    
    # Observações
    notes = db.Column(
        db.Text, 
        nullable=True,
        comment='Observações gerais'
    )
    
    # Relacionamentos
    employees = db.relationship(
        'Employee', 
        backref='team', 
        lazy='dynamic',
        foreign_keys='Employee.team_id'
    )
    
    def __repr__(self):
        return f'<Team {self.name}>'
    
    @property
    def cnpj_formatted(self):
        """CNPJ formatado"""
        if not self.cnpj:
            return None
        cnpj = self.cnpj.zfill(14)
        return f'{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}'
    
    @property
    def display_name(self):
        """Nome para exibição"""
        if self.acronym:
            return f'{self.acronym} - {self.name}'
        return self.name
    
    @property
    def employee_count(self):
        """Número de funcionários ativos"""
        return self.employees.filter(
            Employee.deleted_at.is_(None),
            Employee.status == EmployeeStatus.ACTIVE
        ).count()
    
    @property
    def team_type(self):
        """Alias para compatibilidade com templates"""
        return self.type
    
    @property
    def is_team(self):
        return self.type == TeamType.TEAM
    
    @property
    def is_corban(self):
        return self.type == TeamType.CORBAN
    
    @classmethod
    def get_active(cls, team_type=None):
        """Retorna equipes/corbans ativos"""
        query = cls.query_active().filter_by(is_active=True)
        if team_type:
            query = query.filter_by(type=team_type)
        return query.order_by(cls.name).all()
    
    @classmethod
    def get_teams(cls):
        """Retorna apenas equipes"""
        return cls.get_active(TeamType.TEAM)
    
    @classmethod
    def get_corbans(cls):
        """Retorna apenas corbans"""
        return cls.get_active(TeamType.CORBAN)
    
    @classmethod
    def get_next_color(cls):
        """Gera uma cor diferente das existentes"""
        import random
        # Cores base para equipes (harmoniosas)
        base_colors = [
            '#206bc4', '#4299e1', '#0ca678', '#2fb344', '#ae3ec9',
            '#d63939', '#f76707', '#fab005', '#74b816', '#17a2b8',
            '#6f42c1', '#e83e8c', '#fd7e14', '#20c997', '#6610f2',
            '#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8'
        ]
        
        # Busca cores já usadas
        used_colors = [t.color for t in cls.query_active().all() if t.color]
        
        # Encontra uma cor não usada
        for color in base_colors:
            if color not in used_colors:
                return color
        
        # Se todas as cores base foram usadas, gera uma aleatória
        return '#{:06x}'.format(random.randint(0, 0xFFFFFF))


# =============================================================================
# FUNCIONÁRIO
# =============================================================================

@audited
class Employee(db.Model, BaseModel):
    """
    Funcionário do sistema.
    Contém todos os dados pessoais, profissionais e documentos.
    Pode ser vinculado a um usuário do sistema.
    """
    
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # =============================
    # DADOS PESSOAIS
    # =============================
    
    cpf = db.Column(
        db.String(11), 
        unique=True, 
        nullable=False,
        index=True,
        comment='CPF (apenas números)'
    )
    name = db.Column(
        db.String(100), 
        nullable=False,
        comment='Nome completo'
    )
    birth_date = db.Column(
        db.Date, 
        nullable=False,
        comment='Data de nascimento'
    )
    gender = db.Column(
        db.String(1), 
        nullable=True,
        comment='Sexo: M, F, O'
    )
    
    # Contato
    phone = db.Column(
        db.String(20), 
        nullable=True,
        comment='Telefone principal'
    )
    phone_secondary = db.Column(
        db.String(20), 
        nullable=True,
        comment='Telefone secundário'
    )
    email = db.Column(
        db.String(120), 
        nullable=True,
        comment='E-mail pessoal'
    )
    
    # Foto (path do arquivo)
    photo_path = db.Column(
        db.String(500), 
        nullable=True,
        comment='Caminho da foto do funcionário'
    )
    
    # Naturalidade
    birthplace_city = db.Column(
        db.String(100), 
        nullable=True,
        comment='Cidade de nascimento'
    )
    birthplace_state = db.Column(
        db.String(2), 
        nullable=True,
        comment='UF de nascimento'
    )
    nationality = db.Column(
        db.String(50), 
        nullable=True,
        default='Brasileira',
        comment='Nacionalidade'
    )
    
    # Estado civil e família
    marital_status = db.Column(
        db.String(20), 
        nullable=True,
        comment='Estado civil'
    )
    father_name = db.Column(
        db.String(100), 
        nullable=True,
        comment='Nome do pai'
    )
    mother_name = db.Column(
        db.String(100), 
        nullable=True,
        comment='Nome da mãe'
    )
    
    # =============================
    # DOCUMENTOS
    # =============================
    
    # RG
    rg_number = db.Column(
        db.String(20), 
        nullable=True,
        comment='Número do RG'
    )
    rg_issuer = db.Column(
        db.String(20), 
        nullable=True,
        comment='Órgão emissor do RG'
    )
    rg_state = db.Column(
        db.String(2), 
        nullable=True,
        comment='UF do RG'
    )
    rg_issue_date = db.Column(
        db.Date, 
        nullable=True,
        comment='Data de emissão do RG'
    )
    
    # PIS/PASEP
    pis = db.Column(
        db.String(20), 
        nullable=True,
        comment='Número do PIS/PASEP'
    )
    
    # Título de Eleitor
    voter_id = db.Column(
        db.String(20), 
        nullable=True,
        comment='Número do título de eleitor'
    )
    voter_zone = db.Column(
        db.String(10), 
        nullable=True,
        comment='Zona eleitoral'
    )
    voter_section = db.Column(
        db.String(10), 
        nullable=True,
        comment='Seção eleitoral'
    )
    
    # CTPS
    ctps_number = db.Column(
        db.String(20), 
        nullable=True,
        comment='Número da CTPS'
    )
    ctps_series = db.Column(
        db.String(10), 
        nullable=True,
        comment='Série da CTPS'
    )
    ctps_state = db.Column(
        db.String(2), 
        nullable=True,
        comment='UF da CTPS'
    )
    ctps_issue_date = db.Column(
        db.Date, 
        nullable=True,
        comment='Data de emissão da CTPS'
    )
    
    # Escolaridade
    education_level = db.Column(
        db.String(30), 
        nullable=True,
        comment='Grau de instrução'
    )
    
    # =============================
    # ENDEREÇO
    # =============================
    
    address_street = db.Column(
        db.String(200), 
        nullable=True,
        comment='Logradouro'
    )
    address_number = db.Column(
        db.String(20), 
        nullable=True,
        comment='Número'
    )
    address_complement = db.Column(
        db.String(100), 
        nullable=True,
        comment='Complemento'
    )
    address_neighborhood = db.Column(
        db.String(100), 
        nullable=True,
        comment='Bairro'
    )
    address_city = db.Column(
        db.String(100), 
        nullable=True,
        comment='Cidade'
    )
    address_state = db.Column(
        db.String(2), 
        nullable=True,
        comment='UF'
    )
    address_zipcode = db.Column(
        db.String(8), 
        nullable=True,
        comment='CEP (apenas números)'
    )
    
    # =============================
    # DADOS PROFISSIONAIS
    # =============================
    
    # Vínculo com equipe/corban
    team_id = db.Column(
        db.Integer, 
        db.ForeignKey('teams.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment='ID da equipe/corban'
    )
    
    # Admissão
    admission_date = db.Column(
        db.Date, 
        nullable=True,
        comment='Data de admissão'
    )
    admission_origin = db.Column(
        db.String(50), 
        nullable=True,
        comment='Origem da admissão (indicação, anúncio, etc)'
    )
    
    # Cargo e contrato
    position = db.Column(
        db.String(100), 
        nullable=True,
        comment='Cargo'
    )
    department = db.Column(
        db.String(100), 
        nullable=True,
        comment='Departamento/Setor'
    )
    contract_type = db.Column(
        db.String(20), 
        nullable=True,
        default=ContractType.CLT,
        comment='Tipo de contrato'
    )
    
    # Status
    status = db.Column(
        db.String(20), 
        nullable=False,
        default=EmployeeStatus.ACTIVE,
        index=True,
        comment='Status do funcionário'
    )
    
    # Vendedor
    is_salesperson = db.Column(
        db.Boolean, 
        default=False,
        comment='Se é vendedor (tem metas de vendas)'
    )
    
    # =============================
    # REMUNERAÇÃO
    # =============================
    
    salary = db.Column(
        db.Numeric(10, 2), 
        nullable=True,
        comment='Salário base'
    )
    bonus = db.Column(
        db.Numeric(10, 2), 
        nullable=True,
        default=0,
        comment='Bônus/Comissão'
    )
    transport_allowance = db.Column(
        db.Numeric(10, 2), 
        nullable=True,
        default=0,
        comment='Vale transporte'
    )
    meal_allowance = db.Column(
        db.Numeric(10, 2), 
        nullable=True,
        default=0,
        comment='Vale refeição/alimentação'
    )
    
    # =============================
    # DADOS BANCÁRIOS
    # =============================
    
    bank_name = db.Column(
        db.String(50), 
        nullable=True,
        comment='Nome do banco'
    )
    bank_code = db.Column(
        db.String(10), 
        nullable=True,
        comment='Código do banco'
    )
    bank_agency = db.Column(
        db.String(20), 
        nullable=True,
        comment='Agência'
    )
    bank_account = db.Column(
        db.String(20), 
        nullable=True,
        comment='Conta corrente'
    )
    bank_account_type = db.Column(
        db.String(20), 
        nullable=True,
        default='checking',
        comment='Tipo de conta: checking, savings'
    )
    pix_key = db.Column(
        db.String(100), 
        nullable=True,
        comment='Chave PIX'
    )
    
    # =============================
    # FÉRIAS E DEMISSÃO
    # =============================
    
    vacation_limit_date = db.Column(
        db.Date, 
        nullable=True,
        comment='Data limite para próximas férias'
    )
    last_vacation_date = db.Column(
        db.Date, 
        nullable=True,
        comment='Data das últimas férias'
    )
    
    termination_date = db.Column(
        db.Date, 
        nullable=True,
        comment='Data de demissão/desligamento'
    )
    termination_reason = db.Column(
        db.String(100), 
        nullable=True,
        comment='Motivo do desligamento'
    )
    
    # =============================
    # OUTROS
    # =============================
    
    notes = db.Column(
        db.Text, 
        nullable=True,
        comment='Observações gerais'
    )
    
    # Vínculo com usuário do sistema
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        unique=True,
        comment='ID do usuário vinculado (se tiver acesso ao sistema)'
    )
    
    # Relacionamentos
    user = db.relationship(
        'Users', 
        backref=db.backref('employee', uselist=False),
        foreign_keys=[user_id]
    )
    
    def __repr__(self):
        return f'<Employee {self.name}>'
    
    # =============================
    # PROPRIEDADES CALCULADAS
    # =============================
    
    @property
    def age(self):
        """Calcula idade em anos"""
        if not self.birth_date:
            return None
        today = date.today()
        return relativedelta(today, self.birth_date).years
    
    @property
    def service_time(self):
        """
        Calcula tempo de serviço.
        Retorna dict com anos, meses e dias.
        """
        if not self.admission_date:
            return None
        
        end_date = self.termination_date or date.today()
        delta = relativedelta(end_date, self.admission_date)
        
        return {
            'years': delta.years,
            'months': delta.months,
            'days': delta.days,
            'total_months': delta.years * 12 + delta.months,
            'formatted': self._format_service_time(delta)
        }
    
    def _format_service_time(self, delta):
        """Formata tempo de serviço para exibição"""
        parts = []
        if delta.years:
            parts.append(f'{delta.years} ano{"s" if delta.years > 1 else ""}')
        if delta.months:
            parts.append(f'{delta.months} {"meses" if delta.months > 1 else "mês"}')
        if not parts and delta.days:
            parts.append(f'{delta.days} dia{"s" if delta.days > 1 else ""}')
        return ' e '.join(parts) if parts else 'Menos de 1 mês'
    
    @property
    def cpf_formatted(self):
        """CPF formatado"""
        if not self.cpf:
            return None
        cpf = self.cpf.zfill(11)
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    
    @property
    def phone_formatted(self):
        """Telefone formatado"""
        if not self.phone:
            return None
        phone = ''.join(filter(str.isdigit, self.phone))
        if len(phone) == 11:
            return f'({phone[:2]}) {phone[2:7]}-{phone[7:]}'
        elif len(phone) == 10:
            return f'({phone[:2]}) {phone[2:6]}-{phone[6:]}'
        return self.phone
    
    @property
    def zipcode_formatted(self):
        """CEP formatado"""
        if not self.address_zipcode:
            return None
        cep = self.address_zipcode.zfill(8)
        return f'{cep[:5]}-{cep[5:]}'
    
    @property
    def full_address(self):
        """Endereço completo formatado"""
        parts = []
        if self.address_street:
            addr = self.address_street
            if self.address_number:
                addr += f', {self.address_number}'
            if self.address_complement:
                addr += f' - {self.address_complement}'
            parts.append(addr)
        
        if self.address_neighborhood:
            parts.append(self.address_neighborhood)
        
        if self.address_city:
            city = self.address_city
            if self.address_state:
                city += f'/{self.address_state}'
            parts.append(city)
        
        if self.address_zipcode:
            parts.append(f'CEP: {self.zipcode_formatted}')
        
        return ' - '.join(parts) if parts else None
    
    @property
    def first_name(self):
        """Primeiro nome"""
        return self.name.split()[0] if self.name else None
    
    @property
    def full_name(self):
        """Alias para name (compatibilidade)"""
        return self.name
    
    @property
    def photo_url(self):
        """URL da foto do funcionário"""
        from flask import url_for
        
        # Se tiver caminho de foto definido, usa ele
        if self.photo_path:
            return url_for('files_blueprint.serve_file', file_id=self.photo_file_id) if self.photo_file_id else None
        
        # Busca foto na tabela de arquivos
        photo = self.get_photo()
        if photo:
            return url_for('files_blueprint.serve_file', file_id=photo.id)
        
        # Retorna avatar padrão
        return None
    
    @property
    def photo_file_id(self):
        """ID do arquivo da foto"""
        photo = self.get_photo()
        return photo.id if photo else None
    
    def get_photo(self):
        """Retorna o arquivo de foto do funcionário"""
        from apps.files.models import File, FileCategory
        return File.query_active().filter_by(
            entity_type='employee',
            entity_id=self.id
        ).join(File.category).filter(
            FileCategory.code == 'FOTO_3X4'
        ).first()
    
    def get_files(self, category_code=None):
        """Retorna arquivos do funcionário, opcionalmente filtrados por categoria"""
        from apps.files.models import File, FileCategory
        
        query = File.query_active().filter_by(
            entity_type='employee',
            entity_id=self.id
        )
        
        if category_code:
            query = query.join(File.category).filter(
                FileCategory.code == category_code
            )
        
        return query.order_by(File.created_at.desc()).all()
    
    def get_files_by_category(self):
        """Retorna arquivos agrupados por categoria"""
        from apps.files.models import File, FileCategory
        
        files = File.query_active().filter_by(
            entity_type='employee',
            entity_id=self.id
        ).order_by(File.category_id, File.created_at.desc()).all()
        
        # Agrupa por categoria
        grouped = {}
        for file in files:
            cat_name = file.category.name if file.category else 'Outros'
            if cat_name not in grouped:
                grouped[cat_name] = []
            grouped[cat_name].append(file)
        
        return grouped
    
    def get_missing_documents(self):
        """Retorna categorias de documentos obrigatórios que estão faltando"""
        from apps.files.models import File, FileCategory
        
        # Busca categorias obrigatórias para funcionários
        required_categories = FileCategory.query_active().filter(
            FileCategory.is_required == True,
            FileCategory.entity_types.like('%employee%')
        ).all()
        
        missing = []
        for category in required_categories:
            existing = File.query_active().filter_by(
                entity_type='employee',
                entity_id=self.id,
                category_id=category.id
            ).first()
            
            if not existing:
                missing.append(category)
        
        return missing
    
    @property
    def documents_complete(self):
        """Verifica se todos os documentos obrigatórios foram enviados"""
        return len(self.get_missing_documents()) == 0
    
    @property
    def is_active(self):
        """Verifica se está ativo"""
        return self.status == EmployeeStatus.ACTIVE
    
    @property
    def is_terminated(self):
        """Verifica se foi desligado"""
        return self.status == EmployeeStatus.TERMINATED
    
    @property
    def total_compensation(self):
        """Remuneração total (salário + benefícios)"""
        total = float(self.salary or 0)
        total += float(self.bonus or 0)
        total += float(self.transport_allowance or 0)
        total += float(self.meal_allowance or 0)
        return total
    
    # =============================
    # MÉTODOS DE CLASSE
    # =============================
    
    @classmethod
    def get_active(cls):
        """Retorna funcionários ativos"""
        return cls.query_active().filter_by(
            status=EmployeeStatus.ACTIVE
        ).order_by(cls.name).all()
    
    @classmethod
    def get_by_team(cls, team_id, include_inactive=False):
        """Retorna funcionários de uma equipe"""
        query = cls.query_active().filter_by(team_id=team_id)
        if not include_inactive:
            query = query.filter_by(status=EmployeeStatus.ACTIVE)
        return query.order_by(cls.name).all()
    
    @classmethod
    def get_by_cpf(cls, cpf):
        """Busca funcionário por CPF"""
        cpf_clean = ''.join(filter(str.isdigit, cpf))
        return cls.query_active().filter_by(cpf=cpf_clean).first()
    
    @classmethod
    def search(cls, term, limit=20):
        """Busca funcionários por nome ou CPF"""
        term = term.strip()
        cpf_term = ''.join(filter(str.isdigit, term))
        
        query = cls.query_active()
        
        if cpf_term and len(cpf_term) >= 3:
            query = query.filter(cls.cpf.like(f'%{cpf_term}%'))
        else:
            query = query.filter(cls.name.ilike(f'%{term}%'))
        
        return query.order_by(cls.name).limit(limit).all()
    
    # =============================
    # MÉTODOS DE INSTÂNCIA
    # =============================
    
    def terminate(self, date=None, reason=None, user_id=None):
        """Realiza desligamento do funcionário"""
        self.status = EmployeeStatus.TERMINATED
        self.termination_date = date or datetime.utcnow().date()
        self.termination_reason = reason
        
        # Desvincula usuário se existir
        if self.user_id:
            from apps.authentication.models import Users
            user = Users.query.get(self.user_id)
            if user:
                user.is_active = False
        
        db.session.commit()
    
    def reactivate(self):
        """Reativa funcionário desligado"""
        self.status = EmployeeStatus.ACTIVE
        self.termination_date = None
        self.termination_reason = None
        db.session.commit()
    
    def link_user(self, user_id):
        """Vincula funcionário a um usuário do sistema"""
        self.user_id = user_id
        db.session.commit()
    
    def unlink_user(self):
        """Desvincula funcionário do usuário"""
        self.user_id = None
        db.session.commit()
