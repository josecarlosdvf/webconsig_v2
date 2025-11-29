#!/usr/bin/env python
"""Script para debugar problema de login"""
import requests
import re

BASE_URL = "http://127.0.0.1:5000"

s = requests.Session()

# Pegar CSRF token
print("1. Pegando CSRF token...")
csrf_resp = s.get(f'{BASE_URL}/login')
match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', csrf_resp.text)
csrf_token = match.group(1) if match else None
print(f'   CSRF Token: {csrf_token[:30] if csrf_token else "N/A"}...')

# Login com redirect habilitado
print("\n2. Fazendo login...")
login = s.post(f'{BASE_URL}/login', data={
    'username': 'admin',
    'password': 'admin123',
    'csrf_token': csrf_token
}, allow_redirects=True)
print(f'   Status final: {login.status_code}')
print(f'   URL final: {login.url}')
print(f'   Cookies: {dict(s.cookies)}')

# Se o login resultou em 500, mostrar o erro
if login.status_code == 500:
    print("\n3. ERRO 500 durante o login!")
    # Tentar encontrar a mensagem de erro
    if '<pre' in login.text:
        import re
        pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', login.text, re.DOTALL)
        if pre_match:
            print(f"   Erro: {pre_match.group(1)[:500]}")
    else:
        print(f"   Resposta: {login.text[:1000]}")
else:
    # Testar Dashboard
    print("\n3. Testando Dashboard...")
    dash = s.get(f'{BASE_URL}/')
    print(f'   Dashboard: {dash.status_code}')
    
    if dash.status_code == 500:
        # Mostrar erro
        if '<pre' in dash.text:
            import re
            pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', dash.text, re.DOTALL)
            if pre_match:
                print(f"   Erro: {pre_match.group(1)[:800]}")
        else:
            print(f"   Resposta: {dash.text[:1000]}")
    elif dash.status_code == 200:
        print("   Dashboard OK!")
    else:
        print(f"   Resposta: {dash.text[:500]}")
