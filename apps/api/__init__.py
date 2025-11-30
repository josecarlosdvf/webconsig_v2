"""
Rotas de API para serviços utilitários
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required

from apps.services.viacep import ViaCepService

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
