# -*- encoding: utf-8 -*-
"""
Mensagens do Sistema em pt-BR
"""


class Messages:
    """Mensagens padronizadas do sistema"""
    
    message = {
        # Autenticação
        'login_success': 'Login realizado com sucesso!',
        'login_failed': 'Usuário ou senha incorretos.',
        'logout_success': 'Você saiu do sistema.',
        'register_success': 'Conta criada com sucesso! Faça login para continuar.',
        'register_failed': 'Erro ao criar conta. Tente novamente.',
        'username_exists': 'Este nome de usuário já está em uso.',
        'email_exists': 'Este e-mail já está cadastrado.',
        'password_mismatch': 'As senhas não conferem.',
        'password_weak': 'A senha deve ter pelo menos 6 caracteres, incluindo uma letra maiúscula e um número.',
        'invalid_email': 'E-mail inválido.',
        'account_inactive': 'Sua conta está inativa. Entre em contato com o administrador.',
        'account_suspended': 'Sua conta foi suspensa.',
        
        # Permissões
        'access_denied': 'Acesso negado.',
        'permission_required': 'Você não tem permissão para realizar esta ação.',
        'login_required': 'Por favor, faça login para acessar esta página.',
        
        # CRUD
        'created_success': 'Registro criado com sucesso!',
        'updated_success': 'Registro atualizado com sucesso!',
        'deleted_success': 'Registro excluído com sucesso!',
        'create_failed': 'Erro ao criar registro.',
        'update_failed': 'Erro ao atualizar registro.',
        'delete_failed': 'Erro ao excluir registro.',
        'not_found': 'Registro não encontrado.',
        
        # Validação
        'required_field': 'Este campo é obrigatório.',
        'invalid_format': 'Formato inválido.',
        'invalid_currency': 'Moeda inválida.',
        'invalid_payment_method': 'Método de pagamento inválido.',
        'invalid_state': 'Estado inválido.',
        
        # Sistema
        'settings_updated': 'Configurações atualizadas com sucesso!',
        'settings_failed': 'Erro ao atualizar configurações.',
        'upload_success': 'Arquivo enviado com sucesso!',
        'upload_failed': 'Erro ao enviar arquivo.',
        'file_too_large': 'Arquivo muito grande. Tamanho máximo: 16MB.',
        'file_type_not_allowed': 'Tipo de arquivo não permitido.',
        
        # Erros HTTP
        'error_400': 'Requisição inválida.',
        'error_401': 'Não autorizado.',
        'error_403': 'Acesso proibido.',
        'error_404': 'Página não encontrada.',
        'error_500': 'Erro interno do servidor.',
    }
    
    @classmethod
    def get(cls, key: str, default: str = '') -> str:
        """Retorna mensagem pelo código"""
        return cls.message.get(key, default)
