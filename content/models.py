from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import json

class Content(models.Model):
    TYPES = [
        ('TEXT', 'Texto'),
        ('VIDEO', 'Vídeo'),
        ('AUDIO', 'Áudio'),
        ('PDF', 'PDF'),
        ('PRESENTATION', 'Apresentação'),
        ('INTERACTIVE', 'Interativo')
    ]
    
    STATUS = [
        ('DRAFT', 'Rascunho'),
        ('REVIEW', 'Em Revisão'),
        ('PUBLISHED', 'Publicado'),
        ('ARCHIVED', 'Arquivado')
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    content_type = models.CharField(max_length=20, choices=TYPES)
    status = models.CharField(max_length=20, choices=STATUS, default='DRAFT')
    
    # Metadados
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Conteúdo
    rich_text = models.TextField(blank=True)
    media_url = models.URLField(blank=True)
    file = models.FileField(upload_to='content_files/', blank=True)
    
    # Metadados adicionais
    tags = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['content_type', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class ContentVersion(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    change_summary = models.TextField()
    content_data = models.JSONField()
    
    class Meta:
        unique_together = ['content', 'version_number']
        ordering = ['-version_number']

class ContentReview(models.Model):
    STATUSES = [
        ('PENDING', 'Pendente'),
        ('APPROVED', 'Aprovado'),
        ('REJECTED', 'Rejeitado'),
        ('CHANGES_REQUESTED', 'Alterações Solicitadas')
    ]
    
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='PENDING')
    comments = models.TextField()
    reviewed_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-reviewed_at']

class ContentComment(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['created_at']

class ContentAttachment(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='content_attachments/')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file_type = models.CharField(max_length=50)
    size = models.IntegerField()  # em bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']

class ContentImport(models.Model):
    STATUSES = [
        ('PENDING', 'Pendente'),
        ('PROCESSING', 'Processando'),
        ('COMPLETED', 'Concluído'),
        ('FAILED', 'Falhou')
    ]
    
    file = models.FileField(upload_to='content_imports/')
    format = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUSES, default='PENDING')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True)
    error_log = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at'] 