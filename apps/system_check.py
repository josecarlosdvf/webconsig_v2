# -*- encoding: utf-8 -*-
"""
Verificação de Dependências do Sistema
Verifica se todas as dependências necessárias estão instaladas
"""

import shutil
import subprocess
import platform
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class DependencyStatus:
    """Status de uma dependência"""
    name: str
    description: str
    installed: bool
    version: Optional[str] = None
    install_command: Optional[str] = None
    required_for: Optional[str] = None
    severity: str = 'warning'  # 'warning', 'error', 'info'


class SystemCheck:
    """
    Verifica dependências do sistema necessárias para funcionamento completo.
    """
    
    @staticmethod
    def check_command_exists(command: str) -> bool:
        """Verifica se um comando existe no sistema"""
        return shutil.which(command) is not None
    
    @staticmethod
    def get_command_version(command: str, version_arg: str = '--version') -> Optional[str]:
        """Obtém versão de um comando"""
        try:
            result = subprocess.run(
                [command, version_arg],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Pega primeira linha da saída
                output = result.stdout.strip() or result.stderr.strip()
                return output.split('\n')[0][:50]  # Limita tamanho
            return None
        except Exception:
            return None
    
    @staticmethod
    def check_python_package(package: str) -> tuple:
        """Verifica se um pacote Python está instalado e retorna versão"""
        try:
            import importlib
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'instalado')
            return True, version
        except ImportError:
            return False, None
    
    @classmethod
    def check_all_dependencies(cls) -> List[DependencyStatus]:
        """
        Verifica todas as dependências do sistema.
        
        Returns:
            Lista de DependencyStatus com status de cada dependência
        """
        dependencies = []
        
        # Detecta plataforma para comandos de instalação
        is_windows = platform.system() == 'Windows'
        # ============================================
        # Dependências de Sistema (comandos)
        # ============================================
        
        # poppler-utils (pdftoppm) - necessário para pdf2image
        pdftoppm_installed = cls.check_command_exists('pdftoppm')
        pdftoppm_version = cls.get_command_version('pdftoppm', '-v') if pdftoppm_installed else None
        dependencies.append(DependencyStatus(
            name='poppler-utils (pdftoppm)',
            description='Necessário para converter PDFs em imagens na validação visual de documentos',
            installed=pdftoppm_installed,
            version=pdftoppm_version,
            install_command=(
                'choco install poppler -y' if is_windows else 'sudo apt-get install -y poppler-utils'
            ),
            required_for='Validação visual de PDFs',
            severity='warning'
        ))
        
        # ImageMagick (convert) - útil para manipulação de imagens
        if is_windows:
            # Em Windows o binário padrão é `magick` (convert conflita com utilitário do sistema)
            convert_installed = cls.check_command_exists('magick')
            convert_version = cls.get_command_version('magick', '-version') if convert_installed else None
        else:
            convert_installed = cls.check_command_exists('convert')
            convert_version = cls.get_command_version('convert', '-version') if convert_installed else None
        dependencies.append(DependencyStatus(
            name='ImageMagick',
            description='Útil para manipulação avançada de imagens',
            installed=convert_installed,
            version=convert_version,
            install_command=(
                'choco install imagemagick -y' if is_windows else 'sudo apt-get install -y imagemagick'
            ),
            required_for='Edição avançada de imagens',
            severity='info'
        ))
        
        # Ghostscript - necessário para compressão de PDFs
        if is_windows:
            # Ghostscript em Windows geralmente expõe gswin64c/gswin32c
            gs_cmd = 'gswin64c' if cls.check_command_exists('gswin64c') else (
                'gswin32c' if cls.check_command_exists('gswin32c') else None
            )
            gs_installed = gs_cmd is not None
            gs_version = cls.get_command_version(gs_cmd, '--version') if gs_installed else None
        else:
            gs_installed = cls.check_command_exists('gs')
            gs_version = cls.get_command_version('gs', '--version') if gs_installed else None
        dependencies.append(DependencyStatus(
            name='Ghostscript',
            description='Necessário para compressão de arquivos PDF',
            installed=gs_installed,
            version=gs_version,
            install_command=(
                'choco install ghostscript -y' if is_windows else 'sudo apt-get install -y ghostscript'
            ),
            required_for='Compressão de PDFs',
            severity='warning'
        ))
        
        # FFmpeg - necessário para compressão de vídeos
        ffmpeg_installed = cls.check_command_exists('ffmpeg')
        ffmpeg_version = cls.get_command_version('ffmpeg', '-version') if ffmpeg_installed else None
        dependencies.append(DependencyStatus(
            name='FFmpeg',
            description='Necessário para compressão e conversão de vídeos',
            installed=ffmpeg_installed,
            version=ffmpeg_version,
            install_command=(
                'choco install ffmpeg -y' if is_windows else 'sudo apt-get install -y ffmpeg'
            ),
            required_for='Compressão de vídeos',
            severity='warning'
        ))
        
        # libmagic (file) - para detecção de tipo de arquivo
        if is_windows:
            # Em Windows normalmente não há `file`; usamos python-magic-bin
            magic_ok, _ = cls.check_python_package('magic')
            file_installed = magic_ok
        else:
            file_installed = cls.check_command_exists('file')
        dependencies.append(DependencyStatus(
            name='libmagic (file)',
            description='Detecta tipo real de arquivos para validação de segurança',
            installed=file_installed,
            version=(
                cls.get_command_version('file', '--version') if (not is_windows and file_installed) else None
            ),
            install_command=(
                'pip install python-magic-bin' if is_windows else 'sudo apt-get install -y libmagic1'
            ),
            required_for='Validação de tipo de arquivo',
            severity='warning'
        ))
        
        # ============================================
        # Dependências Python
        # ============================================
        
        # pdf2image
        pdf2image_installed, pdf2image_version = cls.check_python_package('pdf2image')
        dependencies.append(DependencyStatus(
            name='pdf2image (Python)',
            description='Converte PDFs em imagens para processamento',
            installed=pdf2image_installed,
            version=pdf2image_version,
            install_command='pip install pdf2image',
            required_for='Validação visual de PDFs',
            severity='warning'
        ))
        
        # Pillow
        pillow_installed, pillow_version = cls.check_python_package('PIL')
        dependencies.append(DependencyStatus(
            name='Pillow (Python)',
            description='Processamento de imagens',
            installed=pillow_installed,
            version=pillow_version,
            install_command='pip install Pillow',
            required_for='Processamento de imagens',
            severity='error'
        ))
        
        # python-magic
        magic_installed, magic_version = cls.check_python_package('magic')
        dependencies.append(DependencyStatus(
            name='python-magic (Python)',
            description='Detecta tipo MIME real de arquivos',
            installed=magic_installed,
            version=magic_version,
            install_command=('pip install python-magic-bin' if is_windows else 'pip install python-magic'),
            required_for='Validação de tipo de arquivo',
            severity='warning'
        ))
        
        # numpy
        numpy_installed, numpy_version = cls.check_python_package('numpy')
        dependencies.append(DependencyStatus(
            name='NumPy (Python)',
            description='Cálculos numéricos para validação visual',
            installed=numpy_installed,
            version=numpy_version,
            install_command='pip install numpy',
            required_for='Validação visual de documentos',
            severity='warning'
        ))
        
        return dependencies
    
    @classmethod
    def get_missing_dependencies(cls) -> List[DependencyStatus]:
        """Retorna apenas dependências não instaladas"""
        return [d for d in cls.check_all_dependencies() if not d.installed]
    
    @classmethod
    def get_warnings_for_dashboard(cls) -> List[Dict]:
        """
        Retorna avisos formatados para exibição no dashboard.
        
        Returns:
            Lista de dicts com 'type', 'title', 'message', 'action'
        """
        warnings = []
        missing = cls.get_missing_dependencies()
        
        for dep in missing:
            icon = 'alert-triangle' if dep.severity == 'warning' else (
                'alert-circle' if dep.severity == 'error' else 'info-circle'
            )
            color = 'warning' if dep.severity == 'warning' else (
                'danger' if dep.severity == 'error' else 'info'
            )
            
            warnings.append({
                'type': dep.severity,
                'color': color,
                'icon': icon,
                'title': f'{dep.name} não instalado',
                'message': dep.description,
                'required_for': dep.required_for,
                'action': dep.install_command
            })
        
        return warnings
    
    @classmethod
    def get_system_status(cls) -> Dict:
        """
        Retorna status geral do sistema.
        
        Returns:
            Dict com 'healthy', 'total', 'installed', 'missing', 'warnings'
        """
        all_deps = cls.check_all_dependencies()
        missing = [d for d in all_deps if not d.installed]
        critical_missing = [d for d in missing if d.severity == 'error']
        
        return {
            'healthy': len(critical_missing) == 0,
            'total': len(all_deps),
            'installed': len(all_deps) - len(missing),
            'missing': len(missing),
            'critical_missing': len(critical_missing),
            'warnings': cls.get_warnings_for_dashboard()
        }
