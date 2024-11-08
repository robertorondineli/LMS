from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

class Notification(models.Model):
    TYPES = [
        ('COURSE', 'Atualização de Curso'),
        ('ACHIEVEMENT', 'Nova Conquista'),
        ('REMINDER', 'Lembrete'),
        ('MENTION', 'Menção'),
        ('DEADLINE', 'Prazo'),
        ('SYSTEM', 'Sistema'),
        ('FEEDBACK', 'Feedback')
    ]
    
    PRIORITIES = [
        ('HIGH', 'Alta'),
        ('MEDIUM', 'Média'),
        ('LOW', 'Baixa')
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITIES, default='MEDIUM')
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Para referência dinâmica a qualquer modelo
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Campos para notificações agendadas
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['type', 'sent']),
        ]

class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    notification_types = models.JSONField(default=dict)  # Configurações por tipo
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    def can_send_notification(self, notification_type):
        if not self.notification_types.get(notification_type, True):
            return False
            
        if self.quiet_hours_start and self.quiet_hours_end:
            current_time = timezone.localtime().time()
            if self.quiet_hours_start <= current_time <= self.quiet_hours_end:
                return False
                
        return True

class NotificationTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=Notification.TYPES)
    subject = models.CharField(max_length=200)
    email_template = models.TextField()
    push_template = models.CharField(max_length=200)
    variables = models.JSONField(default=list)
    active = models.BooleanField(default=True) 