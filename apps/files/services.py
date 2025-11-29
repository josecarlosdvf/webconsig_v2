# -*- encoding: utf-8 -*-
"""
Serviços de Gestão de Arquivos
Upload, download, edição de imagem e validação
"""

import os
import io
import zipfile
import hashlib
from datetime import datetime
from typing import List, Tuple, Optional, BinaryIO
from werkzeug.utils import secure_filename
from flask import current_app, send_file, abort

from apps import db
from apps.files.models import File, FileCategory
from apps.database.models import AuditLog


class FileValidationError(Exception):
    """Erro de validação de arquivo"""
    pass


class FileNotFoundError(Exception):
    """Arquivo não encontrado"""
    pass


class FileService:
    """
    Serviço principal de gestão de arquivos.
    Handles upload, download, validation, and storage.
    """
    
    @staticmethod
    def get_upload_folder() -> str:
        """Retorna pasta de upload configurada"""
        return current_app.config.get('UPLOAD_FOLDER', 'uploads')
    
    @staticmethod
    def get_allowed_extensions() -> set:
        """Retorna extensões permitidas globalmente"""
        return current_app.config.get(
            'ALLOWED_EXTENSIONS', 
            {'jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
        )
    
    @staticmethod
    def get_max_file_size() -> int:
        """Retorna tamanho máximo global em bytes"""
        max_mb = current_app.config.get('MAX_FILE_SIZE_MB', 16)
        return max_mb * 1024 * 1024
    
    @classmethod
    def validate_file(cls, file, category: FileCategory) -> Tuple[bool, Optional[str]]:
        """
        Valida um arquivo contra as regras da categoria.
        
        Args:
            file: FileStorage do Werkzeug
            category: FileCategory com as regras
        
        Returns:
            Tuple[bool, str]: (é_válido, mensagem_erro)
        """
        if not file or not file.filename:
            return False, 'Nenhum arquivo selecionado'
        
        # Valida pela categoria
        is_valid, error = category.validate_file(file)
        if not is_valid:
            return False, error
        
        # Valida MIME type real (se python-magic estiver disponível)
        try:
            import magic
            file.seek(0)
            real_mime = magic.from_buffer(file.read(2048), mime=True)
            file.seek(0)
            
            if real_mime not in category.allowed_mime_types:
                return False, f'Tipo de arquivo inválido. Detectado: {real_mime}'
        except ImportError:
            # python-magic não instalado, pula validação
            pass
        
        return True, None
    
    @classmethod
    def upload(cls, file, category_code: str, entity_type: str, entity_id: int,
               uploaded_by_id: int = None, description: str = None) -> File:
        """
        Faz upload de um arquivo.
        
        Args:
            file: FileStorage do Werkzeug
            category_code: Código da categoria do arquivo
            entity_type: Tipo da entidade (employee, team, etc)
            entity_id: ID da entidade
            uploaded_by_id: ID do usuário que fez upload
            description: Descrição opcional
        
        Returns:
            File: Registro do arquivo criado
        
        Raises:
            FileValidationError: Se validação falhar
        """
        # Busca categoria
        category = FileCategory.get_by_code(category_code)
        if not category:
            raise FileValidationError(f'Categoria não encontrada: {category_code}')
        
        # Valida arquivo
        is_valid, error = cls.validate_file(file, category)
        if not is_valid:
            raise FileValidationError(error)
        
        # Verifica se categoria permite múltiplos
        if not category.allow_multiple:
            existing = File.get_for_entity(entity_type, entity_id, category_code)
            if existing:
                # Soft delete do arquivo anterior
                for f in existing:
                    f.soft_delete(uploaded_by_id)
        
        # Cria o arquivo
        file_record = File.create_from_upload(
            file=file,
            category=category,
            entity_type=entity_type,
            entity_id=entity_id,
            uploaded_by_id=uploaded_by_id,
            description=description
        )
        
        # Validação visual contra modelo de referência
        if category.has_reference_model:
            try:
                validation_result = DocumentSimilarityService.validate_against_reference(
                    file_record.full_path,
                    category
                )
                file_record.visual_similarity_score = validation_result['similarity']
                file_record.visual_validation_passed = validation_result['compatible']
                
                # Adiciona informação na descrição
                if not validation_result['compatible']:
                    if file_record.validation_notes:
                        file_record.validation_notes += f"\n{validation_result['message']}"
                    else:
                        file_record.validation_notes = validation_result['message']
                
                db.session.commit()
            except Exception as e:
                current_app.logger.warning(f'Erro na validação visual: {e}')
        
        # Log de auditoria
        AuditLog.log(
            action='file_upload',
            table_name='files',
            record_id=file_record.id,
            description=f'Upload: {file_record.original_name} ({category.name})',
            user_id=uploaded_by_id
        )
        db.session.commit()
        
        return file_record
    
    @classmethod
    def download(cls, file_id: int) -> Tuple[str, str, str]:
        """
        Prepara download de um arquivo.
        
        Args:
            file_id: ID do arquivo
        
        Returns:
            Tuple[str, str, str]: (caminho_completo, nome_original, mime_type)
        
        Raises:
            FileNotFoundError: Se arquivo não existir
        """
        file_record = File.query_active().get(file_id)
        if not file_record:
            raise FileNotFoundError('Arquivo não encontrado')
        
        full_path = file_record.full_path
        if not os.path.exists(full_path):
            raise FileNotFoundError('Arquivo não encontrado no storage')
        
        return full_path, file_record.original_name, file_record.mime_type
    
    @classmethod
    def download_multiple(cls, file_ids: List[int], zip_name: str = 'arquivos.zip') -> BinaryIO:
        """
        Cria um ZIP com múltiplos arquivos para download.
        
        Args:
            file_ids: Lista de IDs dos arquivos
            zip_name: Nome do arquivo ZIP
        
        Returns:
            BytesIO: Buffer com o ZIP
        """
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_id in file_ids:
                try:
                    file_record = File.query_active().get(file_id)
                    if file_record and os.path.exists(file_record.full_path):
                        # Usa nome único no ZIP para evitar conflitos
                        zip_filename = f'{file_record.category.code}_{file_record.original_name}'
                        zf.write(file_record.full_path, zip_filename)
                except Exception:
                    continue
        
        memory_file.seek(0)
        return memory_file
    
    @classmethod
    def delete(cls, file_id: int, deleted_by_id: int = None) -> bool:
        """
        Exclui um arquivo (soft delete).
        
        Args:
            file_id: ID do arquivo
            deleted_by_id: ID do usuário que excluiu
        
        Returns:
            bool: True se excluído com sucesso
        """
        file_record = File.query_active().get(file_id)
        if not file_record:
            return False
        
        file_record.soft_delete(deleted_by_id)
        
        AuditLog.log(
            action='file_delete',
            table_name='files',
            record_id=file_id,
            description=f'Arquivo excluído: {file_record.original_name}',
            user_id=deleted_by_id
        )
        db.session.commit()
        
        return True
    
    @classmethod
    def get_entity_files(cls, entity_type: str, entity_id: int, 
                         include_pending: bool = True) -> dict:
        """
        Retorna todos os arquivos de uma entidade, agrupados por categoria.
        
        Args:
            entity_type: Tipo da entidade
            entity_id: ID da entidade
            include_pending: Incluir arquivos pendentes de validação
        
        Returns:
            dict: {category_code: [files]}
        """
        query = File.query_active().filter_by(
            entity_type=entity_type,
            entity_id=entity_id
        )
        
        if not include_pending:
            query = query.filter_by(validation_status='approved')
        
        files = query.order_by(File.uploaded_at.desc()).all()
        
        result = {}
        for f in files:
            code = f.category.code
            if code not in result:
                result[code] = []
            result[code].append(f)
        
        return result
    
    @classmethod
    def get_missing_required(cls, entity_type: str, entity_id: int) -> List[FileCategory]:
        """
        Retorna categorias obrigatórias que ainda não têm arquivo.
        
        Args:
            entity_type: Tipo da entidade
            entity_id: ID da entidade
        
        Returns:
            List[FileCategory]: Categorias sem arquivo
        """
        # Categorias obrigatórias para o tipo de entidade
        required = FileCategory.query_active().filter(
            FileCategory.is_required == True,
            FileCategory.is_active == True,
            FileCategory.entity_types.contains(entity_type)
        ).all()
        
        # Arquivos existentes
        existing = File.query_active().filter_by(
            entity_type=entity_type,
            entity_id=entity_id
        ).with_entities(File.category_id).distinct().all()
        
        existing_ids = {e[0] for e in existing}
        
        return [cat for cat in required if cat.id not in existing_ids]


class ImageService:
    """
    Serviço de edição de imagens.
    Crop, rotate, resize usando Pillow.
    """
    
    @staticmethod
    def _get_image(file_record: File):
        """Abre imagem do arquivo"""
        from PIL import Image
        
        if not file_record.is_image:
            raise ValueError('Arquivo não é uma imagem')
        
        return Image.open(file_record.full_path)
    
    @classmethod
    def crop(cls, file_id: int, left: int, top: int, right: int, bottom: int,
             user_id: int = None) -> File:
        """
        Recorta uma imagem.
        
        Args:
            file_id: ID do arquivo
            left, top, right, bottom: Coordenadas do recorte
            user_id: ID do usuário que editou
        
        Returns:
            File: Nova versão do arquivo
        """
        from PIL import Image
        
        file_record = File.query_active().get(file_id)
        if not file_record:
            raise FileNotFoundError('Arquivo não encontrado')
        
        img = cls._get_image(file_record)
        cropped = img.crop((left, top, right, bottom))
        
        return cls._save_edited(file_record, cropped, 'crop', user_id)
    
    @classmethod
    def rotate(cls, file_id: int, angle: int, user_id: int = None) -> File:
        """
        Rotaciona uma imagem.
        
        Args:
            file_id: ID do arquivo
            angle: Ângulo de rotação (90, 180, 270)
            user_id: ID do usuário que editou
        
        Returns:
            File: Nova versão do arquivo
        """
        from PIL import Image
        
        file_record = File.query_active().get(file_id)
        if not file_record:
            raise FileNotFoundError('Arquivo não encontrado')
        
        img = cls._get_image(file_record)
        rotated = img.rotate(-angle, expand=True)  # Negativo para rotação horária
        
        return cls._save_edited(file_record, rotated, f'rotate_{angle}', user_id)
    
    @classmethod
    def resize(cls, file_id: int, width: int, height: int = None, 
               maintain_aspect: bool = True, user_id: int = None) -> File:
        """
        Redimensiona uma imagem.
        
        Args:
            file_id: ID do arquivo
            width: Nova largura
            height: Nova altura (calculada se maintain_aspect=True)
            maintain_aspect: Manter proporção
            user_id: ID do usuário que editou
        
        Returns:
            File: Nova versão do arquivo
        """
        from PIL import Image
        
        file_record = File.query_active().get(file_id)
        if not file_record:
            raise FileNotFoundError('Arquivo não encontrado')
        
        img = cls._get_image(file_record)
        
        if maintain_aspect:
            img.thumbnail((width, height or width), Image.Resampling.LANCZOS)
            resized = img
        else:
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
        
        return cls._save_edited(file_record, resized, 'resize', user_id)
    
    @classmethod
    def generate_thumbnail(cls, file_id: int, max_size: int = 200) -> BinaryIO:
        """
        Gera thumbnail de uma imagem.
        
        Args:
            file_id: ID do arquivo
            max_size: Tamanho máximo (largura ou altura)
        
        Returns:
            BytesIO: Buffer com a thumbnail
        """
        from PIL import Image
        
        file_record = File.query_active().get(file_id)
        if not file_record or not file_record.is_image:
            raise FileNotFoundError('Imagem não encontrada')
        
        img = cls._get_image(file_record)
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        format = 'JPEG' if file_record.extension in ('jpg', 'jpeg') else 'PNG'
        img.save(buffer, format=format, quality=85)
        buffer.seek(0)
        
        return buffer
    
    @classmethod
    def _save_edited(cls, original: File, image, operation: str, user_id: int = None) -> File:
        """
        Salva imagem editada como nova versão.
        
        Args:
            original: Arquivo original
            image: Imagem PIL editada
            operation: Nome da operação realizada
            user_id: ID do usuário
        
        Returns:
            File: Novo registro de arquivo
        """
        import uuid
        from PIL import Image
        
        # Define novo nome e caminho
        extension = original.extension
        stored_name = f'{uuid.uuid4().hex}.{extension}'
        relative_path = os.path.dirname(original.path)
        full_path = os.path.join(cls._get_upload_folder(), relative_path, stored_name)
        
        # Salva imagem
        format = 'JPEG' if extension in ('jpg', 'jpeg') else extension.upper()
        image.save(full_path, format=format, quality=95)
        
        # Obtém novo tamanho e dimensões
        size_bytes = os.path.getsize(full_path)
        width, height = image.size
        
        # Calcula hash
        with open(full_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Cria novo registro (nova versão)
        new_file = File(
            category_id=original.category_id,
            original_name=original.original_name,
            stored_name=stored_name,
            path=os.path.join(relative_path, stored_name),
            size_bytes=size_bytes,
            mime_type=original.mime_type,
            extension=extension,
            width=width,
            height=height,
            entity_type=original.entity_type,
            entity_id=original.entity_id,
            uploaded_by_id=user_id,
            file_hash=file_hash,
            description=f'Editado: {operation}',
            validation_status=original.validation_status,
            version=original.version + 1,
            parent_id=original.id
        )
        
        db.session.add(new_file)
        
        # Log de auditoria
        AuditLog.log(
            action='file_edit',
            table_name='files',
            record_id=original.id,
            description=f'Imagem editada ({operation}): {original.original_name}',
            user_id=user_id,
            new_values={'new_file_id': new_file.id, 'operation': operation}
        )
        
        db.session.commit()
        
        return new_file
    
    @staticmethod
    def _get_upload_folder() -> str:
        """Retorna pasta de upload"""
        return current_app.config.get('UPLOAD_FOLDER', 'uploads')


class DocumentValidationService:
    """
    Serviço de validação automática de documentos.
    Validações básicas: CPF, formato, dimensões.
    """
    
    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """
        Valida número de CPF.
        
        Args:
            cpf: Número do CPF (apenas dígitos)
        
        Returns:
            bool: True se válido
        """
        cpf = ''.join(filter(str.isdigit, cpf))
        
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Calcula primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if int(cpf[9]) != digito1:
            return False
        
        # Calcula segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return int(cpf[10]) == digito2
    
    @staticmethod
    def validate_cnpj(cnpj: str) -> bool:
        """
        Valida número de CNPJ.
        
        Args:
            cnpj: Número do CNPJ (apenas dígitos)
        
        Returns:
            bool: True se válido
        """
        cnpj = ''.join(filter(str.isdigit, cnpj))
        
        if len(cnpj) != 14:
            return False
        
        if cnpj == cnpj[0] * 14:
            return False
        
        # Primeiro dígito
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if int(cnpj[12]) != digito1:
            return False
        
        # Segundo dígito
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return int(cnpj[13]) == digito2
    
    @classmethod
    def validate_document_image(cls, file_record: File) -> Tuple[bool, List[str]]:
        """
        Valida imagem de documento.
        
        Args:
            file_record: Registro do arquivo
        
        Returns:
            Tuple[bool, List[str]]: (é_válido, lista_de_problemas)
        """
        issues = []
        
        if not file_record.is_image:
            return True, []  # Não é imagem, pula validação
        
        category = file_record.category
        
        # Verifica dimensões mínimas
        if category.min_width and file_record.width < category.min_width:
            issues.append(f'Largura mínima: {category.min_width}px (atual: {file_record.width}px)')
        
        if category.min_height and file_record.height < category.min_height:
            issues.append(f'Altura mínima: {category.min_height}px (atual: {file_record.height}px)')
        
        # Verifica dimensões máximas
        if category.max_width and file_record.width > category.max_width:
            issues.append(f'Largura máxima: {category.max_width}px (atual: {file_record.width}px)')
        
        if category.max_height and file_record.height > category.max_height:
            issues.append(f'Altura máxima: {category.max_height}px (atual: {file_record.height}px)')
        
        # Verifica se imagem está muito escura ou clara
        try:
            from PIL import Image, ImageStat
            
            img = Image.open(file_record.full_path)
            stat = ImageStat.Stat(img.convert('L'))  # Converte para grayscale
            mean_brightness = stat.mean[0]
            
            if mean_brightness < 30:
                issues.append('Imagem muito escura')
            elif mean_brightness > 230:
                issues.append('Imagem muito clara/estourada')
        except Exception:
            pass
        
        return len(issues) == 0, issues


class DocumentSimilarityService:
    """
    Serviço de validação de similaridade de documentos.
    Compara arquivos enviados com modelos de referência usando
    comparação estrutural/visual.
    
    Funciona para qualquer tipo de documento (PDF, imagem) independente
    de orientação ou resolução.
    """
    
    NORMALIZE_SIZE = (800, 800)  # Tamanho para normalização
    
    @staticmethod
    def file_to_images(file_path: str) -> list:
        """
        Converte qualquer arquivo (PDF ou imagem) para lista de imagens PIL.
        
        Args:
            file_path: Caminho do arquivo
        
        Returns:
            list: Lista de imagens PIL
        """
        from PIL import Image
        
        if file_path.lower().endswith('.pdf'):
            # Tenta converter PDF para imagem
            try:
                from pdf2image import convert_from_path
                pages = convert_from_path(file_path, dpi=150, first_page=1, last_page=1)
                return pages
            except ImportError:
                current_app.logger.warning('pdf2image não disponível. Instale: pip install pdf2image')
                # Fallback: tenta ler como imagem mesmo assim
                try:
                    return [Image.open(file_path)]
                except Exception:
                    return []
            except Exception as e:
                current_app.logger.warning(f'Erro ao converter PDF: {e}')
                return []
        else:
            # É uma imagem
            try:
                img = Image.open(file_path)
                return [img]
            except Exception as e:
                current_app.logger.warning(f'Erro ao abrir imagem: {e}')
                return []
    
    @classmethod
    def normalize_image(cls, img) -> 'Image':
        """
        Normaliza imagem para comparação (tamanho, modo RGB).
        
        Args:
            img: Imagem PIL
        
        Returns:
            Image: Imagem normalizada
        """
        from PIL import Image
        
        # Converte para RGB se necessário
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensiona mantendo proporção
        img.thumbnail(cls.NORMALIZE_SIZE, Image.Resampling.LANCZOS)
        
        # Cria imagem de fundo branco e cola a imagem centralizada
        background = Image.new('RGB', cls.NORMALIZE_SIZE, (255, 255, 255))
        offset = ((cls.NORMALIZE_SIZE[0] - img.width) // 2,
                  (cls.NORMALIZE_SIZE[1] - img.height) // 2)
        background.paste(img, offset)
        
        return background
    
    @staticmethod
    def compute_histogram_similarity(img1, img2) -> float:
        """
        Calcula similaridade baseada em histogramas de cor.
        
        Args:
            img1, img2: Imagens PIL
        
        Returns:
            float: Similaridade (0.0 a 1.0)
        """
        import numpy as np
        
        # Calcula histogramas
        hist1 = img1.histogram()
        hist2 = img2.histogram()
        
        # Normaliza
        hist1 = np.array(hist1, dtype=np.float64)
        hist2 = np.array(hist2, dtype=np.float64)
        
        hist1 = hist1 / (hist1.sum() + 1e-10)
        hist2 = hist2 / (hist2.sum() + 1e-10)
        
        # Correlação (Bhattacharyya coefficient)
        similarity = np.sum(np.sqrt(hist1 * hist2))
        
        return float(similarity)
    
    @staticmethod
    def compute_structural_similarity(img1, img2) -> float:
        """
        Calcula similaridade estrutural (SSIM) entre duas imagens.
        
        Args:
            img1, img2: Imagens PIL
        
        Returns:
            float: SSIM (0.0 a 1.0)
        """
        import numpy as np
        
        # Converte para arrays numpy em escala de cinza
        arr1 = np.array(img1.convert('L'), dtype=np.float64)
        arr2 = np.array(img2.convert('L'), dtype=np.float64)
        
        # Garante que têm o mesmo tamanho
        if arr1.shape != arr2.shape:
            return 0.0
        
        # Parâmetros SSIM
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2
        
        # Médias
        mu1 = arr1.mean()
        mu2 = arr2.mean()
        
        # Variâncias
        sigma1_sq = ((arr1 - mu1) ** 2).mean()
        sigma2_sq = ((arr2 - mu2) ** 2).mean()
        
        # Covariância
        sigma12 = ((arr1 - mu1) * (arr2 - mu2)).mean()
        
        # SSIM
        num = (2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)
        den = (mu1**2 + mu2**2 + C1) * (sigma1_sq + sigma2_sq + C2)
        
        ssim = num / den
        
        return float(max(0.0, ssim))
    
    @staticmethod
    def compute_edge_similarity(img1, img2) -> float:
        """
        Calcula similaridade baseada em detecção de bordas.
        Útil para comparar layout/estrutura de documentos.
        
        Args:
            img1, img2: Imagens PIL
        
        Returns:
            float: Similaridade (0.0 a 1.0)
        """
        import numpy as np
        from PIL import ImageFilter
        
        # Aplica filtro de detecção de bordas
        edges1 = img1.convert('L').filter(ImageFilter.FIND_EDGES)
        edges2 = img2.convert('L').filter(ImageFilter.FIND_EDGES)
        
        # Converte para arrays
        arr1 = np.array(edges1, dtype=np.float64).flatten()
        arr2 = np.array(edges2, dtype=np.float64).flatten()
        
        # Normaliza
        arr1 = arr1 / (np.linalg.norm(arr1) + 1e-10)
        arr2 = arr2 / (np.linalg.norm(arr2) + 1e-10)
        
        # Similaridade por cosseno
        similarity = np.dot(arr1, arr2)
        
        return float(max(0.0, similarity))
    
    @classmethod
    def compute_embedding(cls, img) -> bytes:
        """
        Gera embedding (vetor de características) de uma imagem.
        Usado para comparação rápida de documentos.
        
        Args:
            img: Imagem PIL normalizada
        
        Returns:
            bytes: Embedding serializado
        """
        import numpy as np
        from PIL import Image, ImageFilter
        
        # Reduz para tamanho pequeno para embedding compacto
        small = img.resize((64, 64), resample=Image.Resampling.NEAREST)
        gray = small.convert('L')
        
        # Extrai características simples:
        # 1. Histograma
        hist = np.array(gray.histogram(), dtype=np.float32)
        hist = hist / (hist.sum() + 1e-10)
        
        # 2. Médias por região (divide em 4x4 regiões)
        arr = np.array(gray, dtype=np.float32).reshape(4, 16, 4, 16)
        region_means = arr.mean(axis=(1, 3)).flatten() / 255.0
        
        # 3. Bordas
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_arr = np.array(edges, dtype=np.float32).reshape(4, 16, 4, 16)
        edge_means = edge_arr.mean(axis=(1, 3)).flatten() / 255.0
        
        # Combina em vetor
        embedding = np.concatenate([
            hist[:64],  # Primeiros 64 bins do histograma
            region_means,
            edge_means
        ])
        
        return embedding.tobytes()
    
    @classmethod
    def compare_embeddings(cls, emb1: bytes, emb2: bytes) -> float:
        """
        Compara dois embeddings e retorna similaridade.
        
        Args:
            emb1, emb2: Embeddings serializados
        
        Returns:
            float: Similaridade (0.0 a 1.0)
        """
        import numpy as np
        
        arr1 = np.frombuffer(emb1, dtype=np.float32)
        arr2 = np.frombuffer(emb2, dtype=np.float32)
        
        if len(arr1) != len(arr2):
            return 0.0
        
        # Similaridade por cosseno
        dot = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        
        if norm1 < 1e-10 or norm2 < 1e-10:
            return 0.0
        
        similarity = dot / (norm1 * norm2)
        
        return float(max(0.0, min(1.0, similarity)))
    
    @classmethod
    def validate_against_reference(cls, file_path: str, category: 'FileCategory') -> dict:
        """
        Valida um arquivo contra o modelo de referência da categoria.
        
        Args:
            file_path: Caminho do arquivo a validar
            category: FileCategory com modelo de referência
        
        Returns:
            dict: {
                'compatible': bool,
                'similarity': float,
                'details': dict com métricas detalhadas,
                'message': str
            }
        """
        result = {
            'compatible': True,
            'similarity': 1.0,
            'details': {},
            'message': 'Arquivo aceito'
        }
        
        # Verifica se validação visual está habilitada
        if not category.has_reference_model:
            result['message'] = 'Validação visual não habilitada para esta categoria'
            return result
        
        # Carrega imagem do arquivo enviado
        file_images = cls.file_to_images(file_path)
        if not file_images:
            result['compatible'] = False
            result['similarity'] = 0.0
            result['message'] = 'Não foi possível processar o arquivo enviado'
            return result
        
        # Carrega imagem do modelo de referência
        ref_path = category.reference_model_full_path
        if not ref_path or not os.path.exists(ref_path):
            result['message'] = 'Modelo de referência não encontrado'
            return result
        
        ref_images = cls.file_to_images(ref_path)
        if not ref_images:
            result['message'] = 'Não foi possível processar o modelo de referência'
            return result
        
        # Normaliza imagens
        file_img = cls.normalize_image(file_images[0])
        ref_img = cls.normalize_image(ref_images[0])
        
        # Calcula métricas de similaridade
        try:
            hist_sim = cls.compute_histogram_similarity(file_img, ref_img)
            struct_sim = cls.compute_structural_similarity(file_img, ref_img)
            edge_sim = cls.compute_edge_similarity(file_img, ref_img)
            
            # Se temos embedding salvo, usa para comparação rápida
            if category.reference_model_embedding:
                file_emb = cls.compute_embedding(file_img)
                emb_sim = cls.compare_embeddings(file_emb, category.reference_model_embedding)
            else:
                emb_sim = (hist_sim + struct_sim + edge_sim) / 3
            
            # Pondera as métricas
            # Estrutural e bordas são mais importantes para documentos
            overall_similarity = (
                0.15 * hist_sim +
                0.35 * struct_sim +
                0.35 * edge_sim +
                0.15 * emb_sim
            )
            
            result['details'] = {
                'histogram_similarity': round(hist_sim, 3),
                'structural_similarity': round(struct_sim, 3),
                'edge_similarity': round(edge_sim, 3),
                'embedding_similarity': round(emb_sim, 3)
            }
            result['similarity'] = round(overall_similarity, 3)
            
            # Verifica contra threshold
            threshold = category.similarity_threshold or 0.75
            result['compatible'] = overall_similarity >= threshold
            
            if result['compatible']:
                result['message'] = f'Documento compatível com o modelo ({overall_similarity:.0%} de similaridade)'
            else:
                result['message'] = f'Documento não compatível com o modelo esperado ({overall_similarity:.0%} de similaridade, mínimo: {threshold:.0%})'
        
        except Exception as e:
            current_app.logger.error(f'Erro na validação visual: {e}', exc_info=True)
            result['message'] = 'Erro ao processar validação visual'
            result['details']['error'] = str(e)
            # Em caso de erro técnico, não bloqueia o upload mas marca como não validado
            result['compatible'] = None  # Indica que não foi possível validar
        
        return result
    
    @classmethod
    def save_reference_model(cls, category: 'FileCategory', file) -> str:
        """
        Salva modelo de referência para uma categoria e calcula embedding.
        
        Args:
            category: FileCategory
            file: FileStorage do Werkzeug
        
        Returns:
            str: Caminho relativo do arquivo salvo
        
        Raises:
            ValueError: Se extensão do arquivo não for permitida
        """
        import uuid
        from werkzeug.utils import secure_filename
        
        # Extensões permitidas para modelos de referência
        ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf', 'gif', 'webp'}
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        
        # Define caminho e valida extensão
        original_name = secure_filename(file.filename)
        extension = original_name.rsplit('.', 1)[1].lower() if '.' in original_name else ''
        
        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError(f'Extensão não permitida: {extension}. Use: {", ".join(ALLOWED_EXTENSIONS)}')
        
        stored_name = f'ref_model_{uuid.uuid4().hex}.{extension}'
        relative_path = os.path.join('reference_models', category.code)
        
        # Cria diretório se não existir
        full_dir = os.path.join(upload_folder, relative_path)
        os.makedirs(full_dir, exist_ok=True)
        
        # Salva arquivo
        full_path = os.path.join(full_dir, stored_name)
        file.save(full_path)
        
        # Calcula embedding
        images = cls.file_to_images(full_path)
        if images:
            normalized = cls.normalize_image(images[0])
            embedding = cls.compute_embedding(normalized)
            category.reference_model_embedding = embedding
        
        # Atualiza categoria
        old_ref = category.reference_model_path
        category.reference_model_path = os.path.join(relative_path, stored_name)
        
        # Remove arquivo antigo se existir
        if old_ref:
            old_full = os.path.join(upload_folder, old_ref)
            if os.path.exists(old_full):
                try:
                    os.remove(old_full)
                except Exception:
                    pass
        
        db.session.commit()
        
        return category.reference_model_path
    
    @classmethod
    def remove_reference_model(cls, category: 'FileCategory') -> bool:
        """
        Remove modelo de referência de uma categoria.
        
        Args:
            category: FileCategory
        
        Returns:
            bool: True se removido com sucesso
        """
        if category.reference_model_path:
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            full_path = os.path.join(upload_folder, category.reference_model_path)
            
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except Exception as e:
                    current_app.logger.warning(f'Erro ao remover arquivo: {e}')
        
        category.reference_model_path = None
        category.reference_model_embedding = None
        db.session.commit()
        
        return True
