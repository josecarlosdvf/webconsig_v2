/**
 * Sistema de Notificações Padronizado
 * Usa Notyf para toasts e SweetAlert2 para modais
 */

// Instância global do Notyf
const notyf = new Notyf({
    duration: 4000,
    position: {
        x: 'right',
        y: 'top'
    },
    dismissible: true,
    ripple: true,
    types: [
        {
            type: 'info',
            background: '#0d6efd',
            icon: {
                className: 'fas fa-info-circle',
                tagName: 'i'
            }
        },
        {
            type: 'warning',
            background: '#ffc107',
            icon: {
                className: 'fas fa-exclamation-triangle',
                tagName: 'i'
            }
        }
    ]
});

// SweetAlert2 com estilo Bootstrap (do volt.js)
const SwalBootstrap = Swal.mixin({
    customClass: {
        confirmButton: 'btn btn-primary me-3',
        cancelButton: 'btn btn-gray',
        denyButton: 'btn btn-danger me-3'
    },
    buttonsStyling: false
});

/**
 * Sistema de Notificações
 */
const Notify = {
    /**
     * Toast de sucesso
     * @param {string} message - Mensagem a exibir
     */
    success(message) {
        notyf.success(message);
    },

    /**
     * Toast de erro
     * @param {string} message - Mensagem a exibir
     */
    error(message) {
        notyf.error(message);
    },

    /**
     * Toast de informação
     * @param {string} message - Mensagem a exibir
     */
    info(message) {
        notyf.open({
            type: 'info',
            message: message
        });
    },

    /**
     * Toast de aviso
     * @param {string} message - Mensagem a exibir
     */
    warning(message) {
        notyf.open({
            type: 'warning',
            message: message
        });
    },

    /**
     * Modal de alerta simples
     * @param {string} title - Título do modal
     * @param {string} text - Texto do modal
     * @param {string} icon - Ícone (success, error, warning, info, question)
     */
    alert(title, text, icon = 'info') {
        return SwalBootstrap.fire({
            title: title,
            text: text,
            icon: icon
        });
    },

    /**
     * Modal de confirmação
     * @param {string} title - Título
     * @param {string} text - Texto
     * @param {string} confirmText - Texto do botão confirmar
     * @param {string} cancelText - Texto do botão cancelar
     * @returns {Promise}
     */
    confirm(title, text, confirmText = 'Confirmar', cancelText = 'Cancelar') {
        return SwalBootstrap.fire({
            title: title,
            text: text,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: confirmText,
            cancelButtonText: cancelText,
            reverseButtons: true
        });
    },

    /**
     * Modal de confirmação de exclusão
     * @param {string} itemName - Nome do item a ser excluído
     * @returns {Promise}
     */
    confirmDelete(itemName = 'este item') {
        return SwalBootstrap.fire({
            title: 'Confirmar Exclusão',
            html: `Tem certeza que deseja excluir <strong>${itemName}</strong>?<br><small class="text-muted">Esta ação não pode ser desfeita.</small>`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: '<i class="fas fa-trash me-2"></i>Excluir',
            cancelButtonText: 'Cancelar',
            reverseButtons: true,
            customClass: {
                confirmButton: 'btn btn-danger me-3',
                cancelButton: 'btn btn-gray'
            }
        });
    },

    /**
     * Modal com input
     * @param {string} title - Título
     * @param {string} inputPlaceholder - Placeholder do input
     * @param {string} inputType - Tipo do input (text, email, password, etc)
     * @returns {Promise}
     */
    prompt(title, inputPlaceholder = '', inputType = 'text') {
        return SwalBootstrap.fire({
            title: title,
            input: inputType,
            inputPlaceholder: inputPlaceholder,
            showCancelButton: true,
            confirmButtonText: 'Confirmar',
            cancelButtonText: 'Cancelar',
            reverseButtons: true,
            inputValidator: (value) => {
                if (!value) {
                    return 'Este campo é obrigatório';
                }
            }
        });
    },

    /**
     * Modal de loading
     * @param {string} title - Título
     * @param {string} text - Texto
     */
    loading(title = 'Aguarde', text = 'Processando...') {
        return SwalBootstrap.fire({
            title: title,
            text: text,
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false,
            willOpen: () => {
                Swal.showLoading();
            }
        });
    },

    /**
     * Fecha modal de loading
     */
    closeLoading() {
        Swal.close();
    },

    /**
     * Modal de erro detalhado
     * @param {string} title - Título
     * @param {string} message - Mensagem de erro
     * @param {string} details - Detalhes técnicos (opcional)
     */
    errorDetails(title, message, details = null) {
        let html = `<p>${message}</p>`;
        if (details) {
            html += `<details class="text-start mt-3"><summary class="text-muted">Detalhes técnicos</summary><pre class="bg-light p-2 mt-2 small">${details}</pre></details>`;
        }
        
        return SwalBootstrap.fire({
            title: title,
            html: html,
            icon: 'error'
        });
    },

    /**
     * Modal de sucesso com redirect
     * @param {string} title - Título
     * @param {string} text - Texto
     * @param {string} redirectUrl - URL para redirecionamento
     * @param {number} timer - Tempo em ms antes do redirect (0 = sem auto-redirect)
     */
    successAndRedirect(title, text, redirectUrl, timer = 2000) {
        return SwalBootstrap.fire({
            title: title,
            text: text,
            icon: 'success',
            timer: timer > 0 ? timer : undefined,
            timerProgressBar: timer > 0,
            showConfirmButton: timer === 0,
            confirmButtonText: 'Continuar',
            willClose: () => {
                window.location.href = redirectUrl;
            }
        });
    }
};

/**
 * Verificador de Sessão
 * Verifica periodicamente se a sessão ainda é válida
 */
const SessionChecker = {
    interval: null,
    checkIntervalMs: 30000, // 30 segundos

    start() {
        // Primeira verificação após 5 segundos
        setTimeout(() => this.check(), 5000);
        
        // Verificações periódicas
        this.interval = setInterval(() => this.check(), this.checkIntervalMs);
    },

    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    },

    async check() {
        try {
            const response = await fetch('/verificar-sessao', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                
                if (!data.valid) {
                    this.stop();
                    this.showSessionExpiredModal(data.message);
                }
            }
        } catch (error) {
            console.warn('Erro ao verificar sessão:', error);
        }
    },

    showSessionExpiredModal(message) {
        SwalBootstrap.fire({
            title: 'Sessão Encerrada',
            html: `
                <p>${message || 'Sua sessão foi encerrada.'}</p>
                <p class="text-muted small">Você será redirecionado para a tela de login.</p>
            `,
            icon: 'warning',
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: true,
            confirmButtonText: 'Ir para Login',
            willClose: () => {
                window.location.href = '/sessao-expirada';
            }
        });
    }
};

// Inicia verificador de sessão apenas se o usuário estiver logado
document.addEventListener('DOMContentLoaded', function() {
    // Verifica se existe o elemento de usuário logado (sidebar, navigation, etc)
    const userLoggedIn = document.querySelector('[data-user-logged-in="true"]') || 
                         document.querySelector('.sidebar-inner');
    
    if (userLoggedIn && !window.location.pathname.includes('/login') && 
        !window.location.pathname.includes('/registrar')) {
        SessionChecker.start();
    }
});

// Exporta para uso global
window.Notify = Notify;
window.SessionChecker = SessionChecker;
window.SwalBootstrap = SwalBootstrap;
