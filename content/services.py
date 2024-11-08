from django.utils import timezone
from django.core.files.storage import default_storage
from django.db import transaction
from .models import (
    Content, ContentVersion, ContentReview,
    ContentComment, ContentAttachment, ContentImport
)
import json
import difflib
import markdown
import bleach
import pandas as pd
from bs4 import BeautifulSoup

class ContentService:
    @staticmethod
    def create_content(data, author):
        """Cria novo conteúdo com versionamento"""
        with transaction.atomic():
            content = Content.objects.create(
                title=data['title'],
                description=data['description'],
                content_type=data['content_type'],
                author=author,
                rich_text=data.get('rich_text', ''),
                media_url=data.get('media_url', ''),
                tags=data.get('tags', []),
                metadata=data.get('metadata', {})
            )
            
            # Cria primeira versão
            ContentVersion.objects.create(
                content=content,
                version_number=1,
                created_by=author,
                change_summary='Versão inicial',
                content_data=ContentService._serialize_content(content)
            )
            
            return content
    
    @staticmethod
    def update_content(content, data, user):
        """Atualiza conteúdo e cria nova versão"""
        with transaction.atomic():
            # Obtém última versão
            last_version = content.versions.first()
            
            # Atualiza conteúdo
            for field, value in data.items():
                if hasattr(content, field):
                    setattr(content, field, value)
            
            content.save()
            
            # Cria nova versão
            new_version = ContentVersion.objects.create(
                content=content,
                version_number=last_version.version_number + 1,
                created_by=user,
                change_summary=data.get('change_summary', 'Atualização'),
                content_data=ContentService._serialize_content(content)
            )
            
            return content, new_version
    
    @staticmethod
    def submit_for_review(content, user):
        """Submete conteúdo para revisão"""
        if content.status != 'DRAFT':
            raise ValueError("Apenas rascunhos podem ser submetidos para revisão")
        
        content.status = 'REVIEW'
        content.save()
        
        ContentReview.objects.create(
            content=content,
            reviewer=user,
            status='PENDING',
            comments='Aguardando revisão'
        )
        
        return content
    
    @staticmethod
    def review_content(content, reviewer, status, comments):
        """Processa revisão de conteúdo"""
        review = ContentReview.objects.create(
            content=content,
            reviewer=reviewer,
            status=status,
            comments=comments
        )
        
        if status == 'APPROVED':
            content.status = 'PUBLISHED'
            content.published_at = timezone.now()
        elif status == 'REJECTED':
            content.status = 'DRAFT'
        
        content.save()
        
        return review
    
    @staticmethod
    def import_content(file, format, user):
        """Importa conteúdo de arquivo"""
        content_import = ContentImport.objects.create(
            file=file,
            format=format,
            created_by=user
        )
        
        try:
            if format == 'csv':
                df = pd.read_csv(file)
            elif format == 'xlsx':
                df = pd.read_excel(file)
            else:
                raise ValueError(f"Formato não suportado: {format}")
            
            imported_content = []
            for _, row in df.iterrows():
                content = Content.objects.create(
                    title=row['title'],
                    description=row['description'],
                    content_type=row['content_type'],
                    author=user,
                    rich_text=row.get('rich_text', ''),
                    tags=json.loads(row.get('tags', '[]')),
                    metadata=json.loads(row.get('metadata', '{}'))
                )
                imported_content.append(content)
            
            content_import.status = 'COMPLETED'
            content_import.processed_at = timezone.now()
            content_import.save()
            
            return imported_content
            
        except Exception as e:
            content_import.status = 'FAILED'
            content_import.error_log = str(e)
            content_import.save()
            raise
    
    @staticmethod
    def export_content(content_ids, format='json'):
        """Exporta conteúdo para arquivo"""
        contents = Content.objects.filter(id__in=content_ids)
        
        if format == 'json':
            data = [ContentService._serialize_content(c) for c in contents]
            return json.dumps(data, indent=2)
        elif format == 'csv':
            df = pd.DataFrame([
                {
                    'title': c.title,
                    'description': c.description,
                    'content_type': c.content_type,
                    'rich_text': c.rich_text,
                    'tags': json.dumps(c.tags),
                    'metadata': json.dumps(c.metadata)
                }
                for c in contents
            ])
            return df.to_csv(index=False)
        else:
            raise ValueError(f"Formato não suportado: {format}")
    
    @staticmethod
    def _serialize_content(content):
        """Serializa conteúdo para versionamento"""
        return {
            'title': content.title,
            'description': content.description,
            'content_type': content.content_type,
            'rich_text': content.rich_text,
            'media_url': content.media_url,
            'tags': content.tags,
            'metadata': content.metadata
        }
    
    @staticmethod
    def _sanitize_html(html):
        """Sanitiza HTML para segurança"""
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'img', 'a', 'table',
            'thead', 'tbody', 'tr', 'th', 'td'
        ]
        allowed_attrs = {
            'img': ['src', 'alt', 'title'],
            'a': ['href', 'title'],
            '*': ['class']
        }
        
        return bleach.clean(
            html,
            tags=allowed_tags,
            attributes=allowed_attrs,
            strip=True
        ) 