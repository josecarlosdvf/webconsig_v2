#!/usr/bin/env python
"""Script para testar todas as rotas do sistema"""
import requests
import re

BASE_URL = "http://127.0.0.1:5000"

def get_csrf_token(session, url):
    """Extrai o CSRF token da página"""
    resp = session.get(url)
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', resp.text)
    if match:
        return match.group(1)
    return None

def test_routes():
    s = requests.Session()
    
    # Login
    print("=" * 50)
    print("Testando Login...")
    
    # Primeiro pegar a página de login para obter CSRF token
    csrf_token = get_csrf_token(s, f'{BASE_URL}/login')
    if not csrf_token:
        print("  ERRO: Não foi possível obter CSRF token")
        return
    
    login = s.post(f'{BASE_URL}/login', data={
        'username': 'admin', 
        'password': 'admin123',
        'csrf_token': csrf_token
    }, allow_redirects=False)
    print(f'  POST /login: {login.status_code}')
    
    if login.status_code != 302:
        print(f"  ERRO: Login falhou! Response: {login.text[:500]}")
        return
    
    print("  Login OK - Sessão iniciada")
    print()
    
    # Teste de rotas
    routes = [
        ('Dashboard', '/'),
        ('Admin - Usuarios', '/admin/usuarios'),
        ('Admin - Grupos', '/admin/grupos'),
        ('Admin - Permissoes', '/admin/permissoes'),
        ('Admin - Auditoria', '/admin/auditoria'),
        ('HR - Funcionarios', '/rh/funcionarios'),
        ('HR - Equipes', '/rh/equipes'),
        ('Arquivos', '/files'),
        ('Configuracoes', '/admin/settings'),
        # Mensageria WhatsApp
        ('Mensagens - Dashboard', '/mensagens'),
        ('Mensagens - Conexoes', '/mensagens/conexoes'),
        ('Mensagens - Enviar', '/mensagens/enviar'),
        ('Mensagens - Historico', '/mensagens/historico'),
        ('Mensagens - Contatos', '/mensagens/contatos'),
        ('Mensagens - Templates', '/mensagens/templates'),
    ]
    
    results = []
    for name, path in routes:
        try:
            resp = s.get(f'{BASE_URL}{path}')
            status = "OK" if resp.status_code == 200 else f"ERRO ({resp.status_code})"
            results.append((name, path, resp.status_code, status))
            
            if resp.status_code != 200:
                # Mostrar erro
                print(f'  {name}: {status}')
                if 'error' in resp.text.lower() or resp.status_code == 500:
                    # Tentar pegar a mensagem de erro
                    start = resp.text.find('<pre>')
                    end = resp.text.find('</pre>')
                    if start > 0 and end > start:
                        error_msg = resp.text[start+5:end][:300]
                        print(f"    Erro: {error_msg}")
            else:
                print(f'  {name}: OK')
        except Exception as e:
            results.append((name, path, 0, f"EXCEPTION: {e}"))
            print(f'  {name}: EXCEPTION - {e}')
    
    print()
    print("=" * 50)
    print("RESUMO:")
    print("=" * 50)
    ok_count = sum(1 for r in results if r[2] == 200)
    print(f"  Total: {len(results)} rotas")
    print(f"  OK: {ok_count}")
    print(f"  Erros: {len(results) - ok_count}")

if __name__ == '__main__':
    test_routes()
