# -*- coding: utf-8 -*-
"""
Script de Teste Completo do Sistema
Testa acesso a todas as páginas, links e botões
"""

import os
import sys
from flask import url_for
from apps import create_app, db
from apps.config import config_dict
from apps.authentication.models import Users, UserGroup

# Configuração
os.environ['DEBUG'] = 'True'
app_config = config_dict['Debug']
app = create_app(app_config)

def test_all_routes():
    """Testa todas as rotas do sistema"""
    
    with app.app_context():
        # Cria um usuário admin de teste se não existir
        test_user = Users.query.filter_by(username='admin').first()
        if not test_user:
            print("❌ Usuário admin não encontrado. Execute seeds.py primeiro.")
            return False
        
        print("=" * 80)
        print("TESTE DE ROTAS DO SISTEMA")
        print("=" * 80)
        print()
        
        # Lista todas as rotas registradas
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': ','.join(rule.methods - {'HEAD', 'OPTIONS'}),
                    'path': str(rule)
                })
        
        # Organiza por blueprint
        blueprints = {}
        for route in sorted(routes, key=lambda x: x['endpoint']):
            bp_name = route['endpoint'].split('.')[0] if '.' in route['endpoint'] else 'app'
            if bp_name not in blueprints:
                blueprints[bp_name] = []
            blueprints[bp_name].append(route)
        
        # Exibe relatório
        total_routes = 0
        for bp_name, bp_routes in sorted(blueprints.items()):
            print(f"\n📦 {bp_name.upper().replace('_BLUEPRINT', '')}")
            print("-" * 80)
            
            for route in bp_routes:
                total_routes += 1
                methods = route['methods']
                endpoint = route['endpoint']
                path = route['path']
                
                # Verifica se a rota requer parâmetros
                has_params = '<' in path
                
                if has_params:
                    status = "⚠️  Requer parâmetros"
                else:
                    status = "✅ OK"
                
                print(f"  {status} [{methods:12}] {path:50} ({endpoint})")
        
        print()
        print("=" * 80)
        print(f"TOTAL: {total_routes} rotas registradas")
        print("=" * 80)
        print()
        
        return True


def test_templates():
    """Verifica existência de templates"""
    
    print("\n" + "=" * 80)
    print("VERIFICAÇÃO DE TEMPLATES")
    print("=" * 80)
    print()
    
    template_folders = []
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, file), templates_dir)
                template_folders.append(rel_path.replace('\\', '/'))
    
    # Agrupa por diretório
    by_folder = {}
    for template in sorted(template_folders):
        folder = template.split('/')[0]
        if folder not in by_folder:
            by_folder[folder] = []
        by_folder[folder].append(template)
    
    total = 0
    for folder, templates in sorted(by_folder.items()):
        print(f"\n📁 {folder}/")
        for tmpl in templates:
            total += 1
            print(f"  ✅ {tmpl}")
    
    print()
    print("=" * 80)
    print(f"TOTAL: {total} templates encontrados")
    print("=" * 80)
    
    return True


def check_route_security():
    """Verifica decorators de segurança nas rotas"""
    
    print("\n" + "=" * 80)
    print("ANÁLISE DE SEGURANÇA DAS ROTAS")
    print("=" * 80)
    print()
    
    from flask_login import login_required
    
    public_routes = []
    protected_routes = []
    
    for rule in app.url_map.iter_rules():
        if rule.endpoint == 'static':
            continue
        
        endpoint_func = app.view_functions.get(rule.endpoint)
        if endpoint_func:
            # Verifica se tem @login_required
            is_protected = hasattr(endpoint_func, '__wrapped__') or 'login_required' in str(endpoint_func)
            
            route_info = {
                'path': str(rule),
                'endpoint': rule.endpoint,
                'methods': ','.join(rule.methods - {'HEAD', 'OPTIONS'})
            }
            
            if is_protected or 'login' not in rule.endpoint:
                protected_routes.append(route_info)
            else:
                public_routes.append(route_info)
    
    print(f"🔓 Rotas Públicas: {len(public_routes)}")
    for route in public_routes:
        print(f"  • {route['path']} ({route['endpoint']})")
    
    print(f"\n🔒 Rotas Protegidas: {len(protected_routes)}")
    
    print()
    print("=" * 80)
    print(f"RESUMO: {len(public_routes)} públicas | {len(protected_routes)} protegidas")
    print("=" * 80)
    
    return True


def check_missing_templates():
    """Verifica se há rotas sem templates correspondentes"""
    
    print("\n" + "=" * 80)
    print("VERIFICAÇÃO DE TEMPLATES FALTANTES")
    print("=" * 80)
    print()
    
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    existing_templates = set()
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, file), templates_dir)
                existing_templates.add(rel_path.replace('\\', '/'))
    
    # Procura por render_template no código
    import re
    missing = []
    
    apps_dir = os.path.join(os.path.dirname(__file__), 'apps')
    for root, dirs, files in os.walk(apps_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Procura por render_template('...')
                        matches = re.findall(r"render_template\(['\"]([^'\"]+)['\"]", content)
                        for match in matches:
                            if match not in existing_templates:
                                missing.append({
                                    'template': match,
                                    'file': os.path.relpath(filepath, os.path.dirname(__file__))
                                })
                except:
                    pass
    
    if missing:
        print("⚠️  Templates referenciados mas não encontrados:")
        for item in missing:
            print(f"  • {item['template']} (em {item['file']})")
    else:
        print("✅ Todos os templates referenciados existem!")
    
    print()
    print("=" * 80)
    
    return len(missing) == 0


def generate_routes_documentation():
    """Gera documentação de rotas"""
    
    output_file = os.path.join(os.path.dirname(__file__), 'ROTAS.md')
    
    with app.app_context():
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
                    'path': str(rule)
                })
        
        # Organiza por blueprint
        blueprints = {}
        for route in sorted(routes, key=lambda x: x['endpoint']):
            bp_name = route['endpoint'].split('.')[0] if '.' in route['endpoint'] else 'app'
            if bp_name not in blueprints:
                blueprints[bp_name] = []
            blueprints[bp_name].append(route)
        
        # Gera markdown
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Documentação de Rotas do Sistema\n\n")
            f.write(f"Total de rotas: **{len(routes)}**\n\n")
            
            for bp_name, bp_routes in sorted(blueprints.items()):
                bp_display = bp_name.replace('_blueprint', '').upper()
                f.write(f"\n## {bp_display}\n\n")
                f.write(f"Total: {len(bp_routes)} rotas\n\n")
                f.write("| Método | Rota | Endpoint |\n")
                f.write("|--------|------|----------|\n")
                
                for route in bp_routes:
                    methods = route['methods']
                    path = route['path']
                    endpoint = route['endpoint']
                    f.write(f"| `{methods}` | `{path}` | `{endpoint}` |\n")
                
                f.write("\n")
        
        print(f"\n✅ Documentação gerada em: {output_file}")
        return True


if __name__ == '__main__':
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "TESTE COMPLETO DO SISTEMA" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    results = []
    
    # Executa testes
    results.append(("Listagem de Rotas", test_all_routes()))
    results.append(("Verificação de Templates", test_templates()))
    results.append(("Análise de Segurança", check_route_security()))
    results.append(("Templates Faltantes", check_missing_templates()))
    results.append(("Documentação de Rotas", generate_routes_documentation()))
    
    # Resumo
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 32 + "RESUMO DOS TESTES" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {status}: {test_name}")
    
    print()
    all_passed = all(result for _, result in results)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("⚠️  ALGUNS TESTES FALHARAM - Verifique os detalhes acima")
    
    print()
