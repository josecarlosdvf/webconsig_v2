/**
 * Serviço de busca de CEP via API ViaCEP
 * 
 * Uso básico:
 *   CepService.init();  // Inicializa com configuração padrão
 * 
 * Uso customizado:
 *   CepService.init({
 *     cepInput: '#meu_cep',
 *     streetInput: '#minha_rua',
 *     neighborhoodInput: '#meu_bairro',
 *     cityInput: '#minha_cidade',
 *     stateInput: '#meu_estado'
 *   });
 * 
 * Busca manual:
 *   const endereco = await CepService.buscar('01310100');
 */

const CepService = {
    // URL da API interna (passa pelo backend para evitar CORS)
    apiUrl: '/api/cep/',
    
    // Configuração padrão de campos
    defaultConfig: {
        cepInput: '#address_zipcode',
        streetInput: '#address_street',
        numberInput: '#address_number',
        complementInput: '#address_complement',
        neighborhoodInput: '#address_neighborhood',
        cityInput: '#address_city',
        stateInput: '#address_state'
    },

    /**
     * Limpa o CEP removendo caracteres não numéricos
     */
    limparCep(cep) {
        return cep.replace(/\D/g, '');
    },

    /**
     * Formata o CEP com hífen
     */
    formatarCep(cep) {
        cep = this.limparCep(cep);
        if (cep.length === 8) {
            return cep.replace(/(\d{5})(\d{3})/, '$1-$2');
        }
        return cep;
    },

    /**
     * Valida se o CEP tem 8 dígitos
     */
    validarCep(cep) {
        cep = this.limparCep(cep);
        return cep.length === 8 && /^\d+$/.test(cep);
    },

    /**
     * Busca endereço pelo CEP
     * @param {string} cep - CEP com ou sem formatação
     * @returns {Promise<Object|null>} Dados do endereço ou null
     */
    async buscar(cep) {
        cep = this.limparCep(cep);
        
        if (!this.validarCep(cep)) {
            return null;
        }

        try {
            // Tenta usar a API interna primeiro
            const response = await fetch(`${this.apiUrl}${cep}`);
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    return result.data;
                }
            }
            
            // Fallback: acessa ViaCEP diretamente
            const viaCepResponse = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
            if (viaCepResponse.ok) {
                const data = await viaCepResponse.json();
                if (!data.erro) {
                    return data;
                }
            }
            
            return null;
        } catch (error) {
            console.error('Erro ao buscar CEP:', error);
            return null;
        }
    },

    /**
     * Preenche os campos do formulário com os dados do endereço
     * @param {Object} endereco - Dados do endereço
     * @param {Object} config - Configuração dos seletores de campos
     */
    preencherCampos(endereco, config = {}) {
        const cfg = { ...this.defaultConfig, ...config };
        
        const campos = {
            [cfg.streetInput]: endereco.logradouro,
            [cfg.neighborhoodInput]: endereco.bairro,
            [cfg.cityInput]: endereco.localidade,
            [cfg.stateInput]: endereco.uf
        };

        for (const [selector, valor] of Object.entries(campos)) {
            const elemento = document.querySelector(selector);
            if (elemento && valor) {
                elemento.value = valor;
                // Dispara evento de change para atualizar validações
                elemento.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }

        // Foca no campo de número após preencher
        const numeroInput = document.querySelector(cfg.numberInput);
        if (numeroInput) {
            numeroInput.focus();
        }
    },

    /**
     * Limpa os campos de endereço
     * @param {Object} config - Configuração dos seletores de campos
     */
    limparCampos(config = {}) {
        const cfg = { ...this.defaultConfig, ...config };
        
        const campos = [
            cfg.streetInput,
            cfg.numberInput,
            cfg.complementInput,
            cfg.neighborhoodInput,
            cfg.cityInput,
            cfg.stateInput
        ];

        for (const selector of campos) {
            const elemento = document.querySelector(selector);
            if (elemento) {
                elemento.value = '';
            }
        }
    },

    /**
     * Mostra indicador de carregamento no campo de CEP
     */
    mostrarLoading(cepInput) {
        const elemento = document.querySelector(cepInput);
        if (elemento) {
            elemento.classList.add('is-loading');
            elemento.style.backgroundImage = 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'24\' height=\'24\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'%236c757d\' stroke-width=\'2\' stroke-linecap=\'round\' stroke-linejoin=\'round\'%3E%3Cpath d=\'M21 12a9 9 0 1 1-6.219-8.56\'/%3E%3C/svg%3E")';
            elemento.style.backgroundRepeat = 'no-repeat';
            elemento.style.backgroundPosition = 'right 10px center';
            elemento.style.backgroundSize = '20px';
        }
    },

    /**
     * Remove indicador de carregamento
     */
    esconderLoading(cepInput) {
        const elemento = document.querySelector(cepInput);
        if (elemento) {
            elemento.classList.remove('is-loading');
            elemento.style.backgroundImage = '';
        }
    },

    /**
     * Mostra feedback visual de sucesso
     */
    mostrarSucesso(cepInput) {
        const elemento = document.querySelector(cepInput);
        if (elemento) {
            elemento.classList.remove('is-invalid');
            elemento.classList.add('is-valid');
            setTimeout(() => elemento.classList.remove('is-valid'), 2000);
        }
    },

    /**
     * Mostra feedback visual de erro
     */
    mostrarErro(cepInput, mensagem = 'CEP não encontrado') {
        const elemento = document.querySelector(cepInput);
        if (elemento) {
            elemento.classList.remove('is-valid');
            elemento.classList.add('is-invalid');
            
            // Mostra mensagem de erro se houver container
            let feedback = elemento.parentElement.querySelector('.invalid-feedback');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                elemento.parentElement.appendChild(feedback);
            }
            feedback.textContent = mensagem;
        }
    },

    /**
     * Inicializa o serviço de CEP com máscara e busca automática
     * @param {Object} config - Configuração personalizada
     */
    init(config = {}) {
        const cfg = { ...this.defaultConfig, ...config };
        const cepInput = document.querySelector(cfg.cepInput);
        
        if (!cepInput) {
            console.warn('CepService: Campo de CEP não encontrado:', cfg.cepInput);
            return;
        }

        // Aplica máscara de CEP
        cepInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 8) {
                value = value.slice(0, 8);
            }
            if (value.length > 5) {
                value = value.replace(/(\d{5})(\d)/, '$1-$2');
            }
            e.target.value = value;
        });

        // Busca CEP ao perder foco ou ao digitar 8 números
        const buscarEndereco = async () => {
            const cep = this.limparCep(cepInput.value);
            
            if (cep.length !== 8) {
                return;
            }

            // Remove classe de erro anterior
            cepInput.classList.remove('is-invalid', 'is-valid');

            this.mostrarLoading(cfg.cepInput);

            const endereco = await this.buscar(cep);

            this.esconderLoading(cfg.cepInput);

            if (endereco) {
                this.preencherCampos(endereco, cfg);
                this.mostrarSucesso(cfg.cepInput);
            } else {
                this.mostrarErro(cfg.cepInput, 'CEP não encontrado');
            }
        };

        // Busca ao perder foco
        cepInput.addEventListener('blur', buscarEndereco);

        // Busca automática quando digitar 9 caracteres (8 + hífen)
        cepInput.addEventListener('input', (e) => {
            const cep = this.limparCep(e.target.value);
            if (cep.length === 8) {
                buscarEndereco();
            }
        });

        // Permite buscar ao pressionar Enter
        cepInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                buscarEndereco();
            }
        });

        console.log('CepService: Inicializado com sucesso');
    }
};

// Inicializa automaticamente quando o DOM estiver pronto
// Apenas se houver campos de endereço na página
document.addEventListener('DOMContentLoaded', function() {
    // Verifica se existe um campo de CEP padrão
    if (document.querySelector('#address_zipcode')) {
        CepService.init();
    }
});

// Exporta para uso global
window.CepService = CepService;
