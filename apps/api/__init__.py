"""
Rotas de API para serviços utilitários
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from apps.services.viacep import ViaCepService
from apps.services.lemit import LemitService, ConsultaLog

blueprint = Blueprint('api_blueprint', __name__, url_prefix='/api')


@blueprint.route('/cep/<cep>')
@login_required
def buscar_cep(cep):
    """
    Busca endereço pelo CEP via API ViaCEP
    
    Retorna:
        {
            "success": true,
            "data": {
                "cep": "01310-100",
                "logradouro": "Avenida Paulista",
                "bairro": "Bela Vista",
                "localidade": "São Paulo",
                "uf": "SP",
                ...
            }
        }
        
    Ou em caso de erro:
        {
            "success": false,
            "error": "CEP não encontrado"
        }
    """
    address = ViaCepService.get_address_dict(cep)
    
    if address:
        return jsonify({
            'success': True,
            'data': address
        })
    else:
        return jsonify({
            'success': False,
            'error': 'CEP não encontrado'
        }), 404


@blueprint.route('/cep/validar/<cep>')
@login_required
def validar_cep(cep):
    """Valida formato do CEP"""
    is_valid = ViaCepService.validate_cep(cep)
    return jsonify({
        'valid': is_valid
    })


@blueprint.route('/cep/buscar')
@login_required
def buscar_por_endereco():
    """
    Busca CEPs por endereço
    
    Query params:
        uf: Sigla do estado (obrigatório)
        cidade: Nome da cidade (obrigatório)
        logradouro: Nome da rua (mínimo 3 caracteres, obrigatório)
    """
    uf = request.args.get('uf', '')
    cidade = request.args.get('cidade', '')
    logradouro = request.args.get('logradouro', '')
    
    if not all([uf, cidade, logradouro]):
        return jsonify({
            'success': False,
            'error': 'Parâmetros obrigatórios: uf, cidade, logradouro'
        }), 400
    
    if len(logradouro) < 3:
        return jsonify({
            'success': False,
            'error': 'Logradouro deve ter no mínimo 3 caracteres'
        }), 400
    
    addresses = ViaCepService.search_address(uf, cidade, logradouro)
    
    return jsonify({
        'success': True,
        'data': [addr.to_dict() for addr in addresses],
        'count': len(addresses)
    })


# =============================================================================
# ROTAS LEMIT - CONSULTA DE CPF
# =============================================================================

@blueprint.route('/cpf/<cpf>')
@login_required
def consultar_cpf(cpf):
    """
    Consulta dados cadastrais pelo CPF via API Lemit
    
    Retorna:
        {
            "success": true,
            "from_cache": true/false,
            "data": {
                "cpf": "12345678901",
                "nome": "Nome da Pessoa",
                "data_nascimento": "1990-01-15",
                "sexo": "M",
                "nome_mae": "Nome da Mãe",
                "telefone_principal": "(11) 99999-9999",
                "email_principal": "email@exemplo.com",
                ...
            }
        }
        
    Ou em caso de erro:
        {
            "success": false,
            "error": "Mensagem de erro"
        }
    """
    # Parâmetro para forçar nova consulta à API
    force_api = request.args.get('force', '').lower() in ('true', '1', 'yes')
    
    pessoa, erro, from_cache = LemitService.consultar_cpf(
        cpf,
        force_api=force_api,
        user_id=current_user.id if current_user.is_authenticated else None,
        user_name=current_user.username if current_user.is_authenticated else None,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string if request.user_agent else None
    )
    
    if pessoa:
        return jsonify({
            'success': True,
            'from_cache': from_cache,
            'data': pessoa.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'error': erro
        }), 400 if 'inválido' in erro.lower() else 404


@blueprint.route('/cpf/validar/<cpf>')
@login_required
def validar_cpf_api(cpf):
    """Valida formato do CPF"""
    is_valid = LemitService.validate_cpf(cpf)
    return jsonify({
        'valid': is_valid
    })


@blueprint.route('/cpf/estatisticas')
@login_required
def estatisticas_consultas():
    """Retorna estatísticas das consultas Lemit"""
    stats = LemitService.get_estatisticas()
    return jsonify({
        'success': True,
        'data': stats
    })


@blueprint.route('/cpf/historico')
@login_required
def historico_consultas():
    """
    Retorna histórico de consultas
    
    Query params:
        cpf: Filtrar por CPF específico (opcional)
        limit: Limite de registros (default: 50)
        apenas_sucesso: Se true, retorna apenas consultas bem sucedidas
    """
    cpf = request.args.get('cpf', '')
    limit = request.args.get('limit', 50, type=int)
    apenas_sucesso = request.args.get('apenas_sucesso', '').lower() in ('true', '1', 'yes')
    
    consultas = LemitService.get_historico(
        cpf=cpf if cpf else None,
        limit=min(limit, 500),  # Limita a 500
        apenas_sucesso=apenas_sucesso
    )
    
    return jsonify({
        'success': True,
        'data': [{
            'id': c.id,
            'cpf': c.cpf_formatted,
            'nome': c.nome_pessoa,
            'data_consulta': c.data_consulta.isoformat() if c.data_consulta else None,
            'sucesso': c.sucesso,
            'erro': c.erro,
            'from_cache': c.consultas_cache > 0,
            'usuario': c.usuario_nome,
            'ip': c.ip_address
        } for c in consultas],
        'count': len(consultas)
    })
