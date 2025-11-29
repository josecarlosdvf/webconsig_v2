/**
 * Tabler Theme JavaScript
 * Funcionalidades personalizadas para o template Tabler
 */

(function() {
    'use strict';

    // =========================================
    // Theme Switcher (Dark/Light Mode)
    // =========================================
    
    const THEME_KEY = 'tabler-theme';
    
    /**
     * Obtém o tema atual salvo ou o padrão do sistema
     */
    function getStoredTheme() {
        return localStorage.getItem(THEME_KEY);
    }
    
    /**
     * Salva o tema escolhido
     */
    function setStoredTheme(theme) {
        localStorage.setItem(THEME_KEY, theme);
    }
    
    /**
     * Detecta a preferência do sistema
     */
    function getPreferredTheme() {
        const storedTheme = getStoredTheme();
        if (storedTheme) {
            return storedTheme;
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    
    /**
     * Aplica o tema ao documento
     */
    function setTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        
        // Atualiza ícones de tema
        const darkIcon = document.querySelector('.hide-theme-dark');
        const lightIcon = document.querySelector('.hide-theme-light');
        
        if (darkIcon && lightIcon) {
            if (theme === 'dark') {
                darkIcon.style.display = 'none';
                lightIcon.style.display = '';
            } else {
                darkIcon.style.display = '';
                lightIcon.style.display = 'none';
            }
        }
        
        // Dispara evento customizado
        document.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }
    
    /**
     * Alterna entre temas
     */
    window.toggleTheme = function() {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setStoredTheme(newTheme);
        setTheme(newTheme);
    };
    
    // Aplica tema ao carregar
    setTheme(getPreferredTheme());
    
    // Observa mudanças na preferência do sistema
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!getStoredTheme()) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    });

    // =========================================
    // Sidebar Toggle (Mobile)
    // =========================================
    
    document.addEventListener('DOMContentLoaded', function() {
        
        // Toggle sidebar no mobile
        const sidebarToggle = document.querySelector('[data-bs-toggle="sidebar"]');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', function() {
                document.body.classList.toggle('sidebar-open');
            });
        }
        
        // Fecha sidebar ao clicar fora
        document.addEventListener('click', function(e) {
            if (document.body.classList.contains('sidebar-open')) {
                const sidebar = document.querySelector('.navbar-vertical');
                const toggle = document.querySelector('[data-bs-toggle="sidebar"]');
                
                if (sidebar && !sidebar.contains(e.target) && toggle && !toggle.contains(e.target)) {
                    document.body.classList.remove('sidebar-open');
                }
            }
        });

        // =========================================
        // Tooltips Initialization
        // =========================================
        
        // Bootstrap vem incluído no Tabler Core
        const bs = window.bootstrap;
        
        if (bs) {
            const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            tooltipTriggerList.forEach(function(tooltipTriggerEl) {
                new bs.Tooltip(tooltipTriggerEl);
            });

            // =========================================
            // Popovers Initialization
            // =========================================
            
            const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
            popoverTriggerList.forEach(function(popoverTriggerEl) {
                new bs.Popover(popoverTriggerEl);
            });

            // =========================================
            // Auto-dismiss Alerts
            // =========================================
            
            const alerts = document.querySelectorAll('.alert-dismissible');
            alerts.forEach(function(alert) {
                // Auto fecha após 5 segundos se não for erro
                if (!alert.classList.contains('alert-danger')) {
                    setTimeout(function() {
                        const bsAlert = bs.Alert.getOrCreateInstance(alert);
                        if (bsAlert) {
                            bsAlert.close();
                        }
                    }, 5000);
                }
            });
        }

        // =========================================
        // Dropdown Menu Improvements
        // =========================================
        
        // Evita que dropdown feche ao clicar dentro
        const dropdownMenus = document.querySelectorAll('.dropdown-menu.dropdown-menu-card');
        dropdownMenus.forEach(function(menu) {
            menu.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        });

        // =========================================
        // Active State for Sidebar Links
        // =========================================
        
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        
        navLinks.forEach(function(link) {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
                
                // Expande parent dropdown se existir
                const parentDropdown = link.closest('.nav-item.dropdown');
                if (parentDropdown) {
                    const toggle = parentDropdown.querySelector('.dropdown-toggle');
                    const menu = parentDropdown.querySelector('.dropdown-menu');
                    if (toggle && menu) {
                        toggle.setAttribute('aria-expanded', 'true');
                        menu.classList.add('show');
                    }
                }
            }
        });

        // =========================================
        // Form Validation Feedback
        // =========================================
        
        const forms = document.querySelectorAll('.needs-validation');
        forms.forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });

        // =========================================
        // Loading State for Buttons
        // =========================================
        
        const allForms = document.querySelectorAll('form');
        allForms.forEach(function(form) {
            form.addEventListener('submit', function() {
                const btn = form.querySelector('button[type="submit"]');
                if (btn) {
                    btn.classList.add('btn-loading');
                    // Desabilita após um pequeno delay para permitir o submit
                    setTimeout(function() {
                        btn.disabled = true;
                    }, 10);
                    
                    // Restaura após 10 segundos como fallback
                    setTimeout(function() {
                        btn.classList.remove('btn-loading');
                        btn.disabled = false;
                    }, 10000);
                }
            });
        });

        // =========================================
        // Smooth Scroll
        // =========================================
        
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const targetId = this.getAttribute('href');
                if (targetId !== '#') {
                    const target = document.querySelector(targetId);
                    if (target) {
                        e.preventDefault();
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                }
            });
        });

        // =========================================
        // Console Welcome Message
        // =========================================
        
        console.log(
            '%c🎨 Tabler UI Framework',
            'font-size: 20px; font-weight: bold; color: #206bc4;'
        );
        console.log(
            '%cMigrado com sucesso do Volt!',
            'font-size: 12px; color: #6c757d;'
        );
        
    });

})();
