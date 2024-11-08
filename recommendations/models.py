from django.db import models
from django.conf import settings
from courses.models import Course, Lesson
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import numpy as np

class UserPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    preferred_categories = models.JSONField(default=list)
    learning_style = models.CharField(max_length=50)
    difficulty_preference = models.CharField(max_length=20)
    time_availability = models.IntegerField(help_text="Minutos por dia")
    interests = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UserInteraction(models.Model):
    INTERACTION_TYPES = [
        ('VIEW', 'Visualização'),
        ('COMPLETE', 'Conclusão'),
        ('LIKE', 'Curtida'),
        ('BOOKMARK', 'Favorito'),
        ('SHARE', 'Compartilhamento'),
        ('COMMENT', 'Comentário')
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', 'interaction_type'])
        ]

class ContentSimilarity(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id_1 = models.PositiveIntegerField()
    object_id_2 = models.PositiveIntegerField()
    similarity_score = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['content_type', 'object_id_1', 'object_id_2']
        indexes = [
            models.Index(fields=['content_type', 'object_id_1']),
            models.Index(fields=['similarity_score'])
        ]

class PersonalizedRecommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    score = models.FloatField()
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    is_dismissed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-score']
        indexes = [
            models.Index(fields=['user', 'score']),
            models.Index(fields=['content_type', 'object_id'])
        ] 