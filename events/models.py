from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid

class Event(models.Model):
    TYPES = [
        ('WEBINAR', 'Webinar'),
        ('WORKSHOP', 'Workshop'),
        ('COURSE', 'Curso'),
        ('MEETING', 'Reunião'),
        ('CONFERENCE', 'Conferência')
    ]
    
    STATUS = [
        ('DRAFT', 'Rascunho'),
        ('SCHEDULED', 'Agendado'),
        ('ONGOING', 'Em Andamento'),
        ('COMPLETED', 'Concluído'),
        ('CANCELLED', 'Cancelado')
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=TYPES)
    status = models.CharField(max_length=20, choices=STATUS, default='DRAFT')
    
    # Datas
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    
    # Capacidade e Inscrições
    max_participants = models.IntegerField(null=True, blank=True)
    min_participants = models.IntegerField(default=1)
    current_participants = models.IntegerField(default=0)
    
    # Configurações
    is_online = models.BooleanField(default=True)
    location = models.CharField(max_length=200, blank=True)
    meeting_url = models.URLField(blank=True)
    meeting_password = models.CharField(max_length=50, blank=True)
    
    # Organizador e Apresentadores
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organized_events'
    )
    presenters = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='presenting_events',
        blank=True
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.JSONField(default=list)
    
    def clean(self):
        if self.end_date <= self.start_date:
            raise ValidationError('Data de término deve ser posterior à data de início')
        if self.registration_deadline >= self.start_date:
            raise ValidationError('Prazo de inscrição deve ser anterior ao início do evento')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_full(self):
        if not self.max_participants:
            return False
        return self.current_participants >= self.max_participants
    
    @property
    def available_spots(self):
        if not self.max_participants:
            return None
        return max(0, self.max_participants - self.current_participants)

class EventRegistration(models.Model):
    STATUS = [
        ('PENDING', 'Pendente'),
        ('CONFIRMED', 'Confirmada'),
        ('CANCELLED', 'Cancelada'),
        ('ATTENDED', 'Participou'),
        ('NO_SHOW', 'Não Compareceu')
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    registration_date = models.DateTimeField(auto_now_add=True)
    confirmation_date = models.DateTimeField(null=True, blank=True)
    attended = models.BooleanField(default=False)
    attendance_date = models.DateTimeField(null=True, blank=True)
    certificate_id = models.UUIDField(default=uuid.uuid4, unique=True)
    
    class Meta:
        unique_together = ['event', 'participant']

class EventSession(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    presenter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    materials = models.JSONField(default=list)
    recording_url = models.URLField(blank=True)

class EventFeedback(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['event', 'participant']

class EventMaterial(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='event_materials/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)
    
    @property
    def file_type(self):
        return self.file.name.split('.')[-1].lower()

class EventNotification(models.Model):
    TYPES = [
        ('REMINDER', 'Lembrete'),
        ('UPDATE', 'Atualização'),
        ('CANCELLATION', 'Cancelamento'),
        ('CONFIRMATION', 'Confirmação')
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL) 