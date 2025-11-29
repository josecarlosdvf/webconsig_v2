#!/usr/bin/env python
"""Script para verificar o erro 500 do dashboard"""
import requests
import re

BASE_URL = "http://127.0.0.1:5000"

s = requests.Session()

# Pegar CSRF token
csrf_resp = s.get(f'{BASE_URL}/login')
match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', csrf_resp.text)
csrf_token = match.group(1) if match else None

# Login sem redirect
login = s.post(f'{BASE_URL}/login', data={
    'username': 'admin',
    'password': 'admin123',
    'csrf_token': csrf_token
}, allow_redirects=False)

print(f"Login: {login.status_code}")
print(f"Location: {login.headers.get('Location', 'N/A')}")

# Testar Dashboard
dash = s.get(f'{BASE_URL}/dashboard')
print(f"\nDashboard: {dash.status_code}")

if dash.status_code == 500:
    # Extrair traceback do HTML de debug
    html = dash.text
    
    # Procurar pela classe 'traceback' ou div com erro
    if 'Traceback' in html:
        # Procurar o traceback
        start = html.find('File &quot;')
        if start > 0:
            end = html.find('</div>', start)
            error_section = html[start:end] if end > start else html[start:start+3000]
            # Limpar HTML
            error_section = error_section.replace('&quot;', '"')
            error_section = error_section.replace('&lt;', '<')
            error_section = error_section.replace('&gt;', '>')
            error_section = error_section.replace('<span class="ws">', '')
            error_section = error_section.replace('</span>', '')
            error_section = error_section.replace('<br>', '\n')
            print(f"\nTraceback:\n{error_section[:3000]}")
    
    # Buscar exception name
    if 'exc-divider' in html:
        exc_start = html.find('exc-divider')
        exc_end = html.find('</h2>', exc_start)
        if exc_end > exc_start:
            exc_section = html[exc_start:exc_end+5]
            print(f"\nException: {exc_section}")
    
    # Tentar pegar só a última parte do erro
    if 'frame-info' in html:
        import re
        frames = re.findall(r'frame-info.*?</div>', html, re.DOTALL)
        if frames:
            last_frame = frames[-1] if frames else ''
            last_frame = last_frame.replace('&quot;', '"')
            last_frame = last_frame.replace('&lt;', '<')
            last_frame = last_frame.replace('&gt;', '>')
            print(f"\nLast frame:\n{last_frame[:1000]}")
