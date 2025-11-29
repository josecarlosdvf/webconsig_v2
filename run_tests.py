#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para executar testes automatizados.

Este script substitui a necessidade de testes manuais com confirmações.
Os testes são executados automaticamente e mostram resultados claros.

Uso:
    python run_tests.py              # Executa todos os testes
    python run_tests.py -v           # Modo verbose (detalhado)
    python run_tests.py --cov        # Com relatório de cobertura
    python run_tests.py -k login     # Apenas testes que contêm "login"
    python run_tests.py --fast       # Apenas testes rápidos

Exemplos:
    python run_tests.py -v -k auth   # Testes de autenticação detalhados
    python run_tests.py --cov --html # Cobertura com relatório HTML
"""

import sys
import subprocess
import argparse


def run_tests(args):
    """Executa os testes com pytest"""
    
    # Comando base
    cmd = [sys.executable, '-m', 'pytest', 'tests/']
    
    # Verbose
    if args.verbose:
        cmd.append('-v')
    
    # Cobertura de código
    if args.coverage:
        cmd.extend(['--cov=apps', '--cov-report=term-missing'])
        if args.html:
            cmd.append('--cov-report=html')
    
    # Filtro por palavra-chave
    if args.keyword:
        cmd.extend(['-k', args.keyword])
    
    # Excluir testes lentos
    if args.fast:
        cmd.extend(['-m', 'not slow'])
    
    # Parar no primeiro erro
    if args.exitfirst:
        cmd.append('-x')
    
    # Traceback completo
    if args.full_traceback:
        cmd.append('--tb=long')
    else:
        cmd.append('--tb=short')
    
    # Executa
    print("=" * 60)
    print("  EXECUTANDO TESTES AUTOMATIZADOS")
    print("=" * 60)
    print(f"  Comando: {' '.join(cmd)}")
    print("=" * 60)
    print()
    
    result = subprocess.run(cmd)
    
    print()
    print("=" * 60)
    if result.returncode == 0:
        print("  ✅ TODOS OS TESTES PASSARAM!")
    else:
        print("  ❌ ALGUNS TESTES FALHARAM")
    print("=" * 60)
    
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description='Executa testes automatizados do projeto Flask',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s                    Executa todos os testes
  %(prog)s -v                 Modo verbose (detalhado)
  %(prog)s --cov              Com relatório de cobertura
  %(prog)s -k login           Apenas testes que contêm "login"
  %(prog)s -v -k auth         Testes de autenticação detalhados
        """
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Modo verbose - mostra detalhes de cada teste'
    )
    
    parser.add_argument(
        '--cov', '--coverage',
        dest='coverage',
        action='store_true',
        help='Gera relatório de cobertura de código'
    )
    
    parser.add_argument(
        '--html',
        action='store_true',
        help='Gera relatório HTML de cobertura (use com --cov)'
    )
    
    parser.add_argument(
        '-k', '--keyword',
        type=str,
        help='Executa apenas testes que correspondem à palavra-chave'
    )
    
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Executa apenas testes rápidos (exclui testes marcados como slow)'
    )
    
    parser.add_argument(
        '-x', '--exitfirst',
        action='store_true',
        help='Para na primeira falha'
    )
    
    parser.add_argument(
        '--full-traceback',
        action='store_true',
        help='Mostra traceback completo em caso de erro'
    )
    
    args = parser.parse_args()
    
    sys.exit(run_tests(args))


if __name__ == '__main__':
    main()
