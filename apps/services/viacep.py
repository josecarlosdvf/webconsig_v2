"""
Serviço de integração com a API ViaCEP
https://viacep.com.br

Exemplo de uso:
    from apps.services.viacep import ViaCepService
    
    # Buscar endereço por CEP
    address = ViaCepService.get_address('01310100')
    
    # Buscar CEPs por endereço
    ceps = ViaCepService.search_address('SP', 'São Paulo', 'Paulista')
"""

import requests
from typing import Optional, Dict, List
from dataclasses import dataclass
import re


@dataclass
class Address:
    """Representa um endereço retornado pela API ViaCEP"""
    cep: str
    logradouro: str
    complemento: str
    bairro: str
    localidade: str  # cidade
    uf: str
    ibge: str
    gia: str
    ddd: str
    siafi: str
    
    @property
    def cidade(self) -> str:
        """Alias para localidade"""
        return self.localidade
    
    @property
    def estado(self) -> str:
        """Alias para uf"""
        return self.uf
    
    @property
    def rua(self) -> str:
        """Alias para logradouro"""
        return self.logradouro
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'cep': self.cep,
            'logradouro': self.logradouro,
            'complemento': self.complemento,
            'bairro': self.bairro,
            'localidade': self.localidade,
            'uf': self.uf,
            'ibge': self.ibge,
            'gia': self.gia,
            'ddd': self.ddd,
            'siafi': self.siafi,
            # Aliases para facilitar uso no frontend
            'cidade': self.localidade,
            'estado': self.uf,
            'rua': self.logradouro
        }


class ViaCepService:
    """Serviço para consulta de CEP via API ViaCEP"""
    
    BASE_URL = "https://viacep.com.br/ws"
    TIMEOUT = 10  # segundos
    
    @staticmethod
    def _clean_cep(cep: str) -> str:
        """Remove caracteres não numéricos do CEP"""
        return re.sub(r'\D', '', cep)
    
    @staticmethod
    def _format_cep(cep: str) -> str:
        """Formata o CEP com hífen"""
        cep = ViaCepService._clean_cep(cep)
        if len(cep) == 8:
            return f"{cep[:5]}-{cep[5:]}"
        return cep
    
    @staticmethod
    def validate_cep(cep: str) -> bool:
        """Valida se o CEP tem 8 dígitos"""
        cep = ViaCepService._clean_cep(cep)
        return len(cep) == 8 and cep.isdigit()
    
    @classmethod
    def get_address(cls, cep: str) -> Optional[Address]:
        """
        Busca endereço pelo CEP
        
        Args:
            cep: CEP com ou sem formatação (ex: '01310-100' ou '01310100')
            
        Returns:
            Address object ou None se CEP não encontrado
            
        Raises:
            requests.RequestException: Se houver erro de conexão
        """
        cep = cls._clean_cep(cep)
        
        if not cls.validate_cep(cep):
            return None
        
        try:
            response = requests.get(
                f"{cls.BASE_URL}/{cep}/json/",
                timeout=cls.TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            
            # API retorna {"erro": true} quando CEP não existe
            if data.get('erro'):
                return None
            
            return Address(
                cep=data.get('cep', ''),
                logradouro=data.get('logradouro', ''),
                complemento=data.get('complemento', ''),
                bairro=data.get('bairro', ''),
                localidade=data.get('localidade', ''),
                uf=data.get('uf', ''),
                ibge=data.get('ibge', ''),
                gia=data.get('gia', ''),
                ddd=data.get('ddd', ''),
                siafi=data.get('siafi', '')
            )
            
        except requests.RequestException:
            return None
    
    @classmethod
    def get_address_dict(cls, cep: str) -> Optional[Dict]:
        """
        Busca endereço pelo CEP e retorna como dicionário
        
        Args:
            cep: CEP com ou sem formatação
            
        Returns:
            Dicionário com dados do endereço ou None
        """
        address = cls.get_address(cep)
        if address:
            return address.to_dict()
        return None
    
    @classmethod
    def search_address(cls, uf: str, cidade: str, logradouro: str) -> List[Address]:
        """
        Busca CEPs por endereço (logradouro deve ter no mínimo 3 caracteres)
        
        Args:
            uf: Sigla do estado (ex: 'SP')
            cidade: Nome da cidade
            logradouro: Nome da rua (mínimo 3 caracteres)
            
        Returns:
            Lista de Address objects
        """
        if len(logradouro) < 3:
            return []
        
        try:
            response = requests.get(
                f"{cls.BASE_URL}/{uf}/{cidade}/{logradouro}/json/",
                timeout=cls.TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, list):
                return [
                    Address(
                        cep=item.get('cep', ''),
                        logradouro=item.get('logradouro', ''),
                        complemento=item.get('complemento', ''),
                        bairro=item.get('bairro', ''),
                        localidade=item.get('localidade', ''),
                        uf=item.get('uf', ''),
                        ibge=item.get('ibge', ''),
                        gia=item.get('gia', ''),
                        ddd=item.get('ddd', ''),
                        siafi=item.get('siafi', '')
                    )
                    for item in data
                ]
            
            return []
            
        except requests.RequestException:
            return []


# Funções de conveniência para uso direto
def buscar_cep(cep: str) -> Optional[Dict]:
    """
    Função de conveniência para buscar CEP
    
    Exemplo:
        from apps.services.viacep import buscar_cep
        endereco = buscar_cep('01310100')
        print(endereco['logradouro'])  # Avenida Paulista
    """
    return ViaCepService.get_address_dict(cep)


def validar_cep(cep: str) -> bool:
    """Valida formato do CEP (8 dígitos)"""
    return ViaCepService.validate_cep(cep)
