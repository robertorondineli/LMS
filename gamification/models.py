from django.db import models
from django.conf import settings
from django.utils import timezone
from courses.models import Course, Lesson

class Achievement(models.Model):
    TYPES = [
        ('COURSE', 'Conclusão de Curso'),
        ('STREAK', 'Sequência de Dias'),
        ('QUIZ', 'Desempenho em Quiz'),
        ('SOCIAL', 'Interação Social'),
        ('CONTENT', 'Criação de Conteúdo'),
        ('SPECIAL', 'Conquista Especial')
    ]
    
    LEVELS = [
        ('BRONZE', 'Bronze'),
        ('SILVER', 'Prata'),
        ('GOLD', 'Ouro'),
        ('PLATINUM', 'Platina')
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=TYPES)
    level = models.CharField(max_length=20, choices=LEVELS)
    icon = models.CharField(max_length=50)  # FontAwesome icon class
    points = models.IntegerField(default=0)
    requirement = models.JSONField()  # Critérios para conquistar
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class UserAchievement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    progress = models.JSONField(default=dict)  # Progresso atual

class Streak(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity = models.DateTimeField(null=True)
    
    def update_streak(self):
        now = timezone.now()
        if not self.last_activity:
            self.current_streak = 1
        else:
            days_diff = (now.date() - self.last_activity.date()).days
            if days_diff == 1:  # Atividade em dias consecutivos
                self.current_streak += 1
                self.longest_streak = max(self.current_streak, self.longest_streak)
            elif days_diff > 1:  # Quebrou a sequência
                self.current_streak = 1
        
        self.last_activity = now
        self.save()

class Level(models.Model):
    number = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    points_required = models.IntegerField()
    icon = models.CharField(max_length=50)
    
    class Meta:
        ordering = ['number']

class UserLevel(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    current_points = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    
    def add_points(self, points):
        self.total_points += points
        self.current_points += points
        
        # Verifica se subiu de nível
        next_level = Level.objects.filter(
            points_required__gt=self.total_points
        ).order_by('points_required').first()
        
        if next_level and self.level.number < next_level.number:
            self.level = next_level
            self.current_points = self.total_points - next_level.points_required
        
        self.save()

class Quest(models.Model):
    TYPES = [
        ('DAILY', 'Diária'),
        ('WEEKLY', 'Semanal'),
        ('SPECIAL', 'Especial')
    ]
    
    title = models.CharField(max_length=100)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=TYPES)
    points = models.IntegerField()
    requirement = models.JSONField()
    expires_at = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)

class UserQuest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    progress = models.JSONField(default=dict)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True)
    
    class Meta:
        unique_together = ['user', 'quest']