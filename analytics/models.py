from django.db import models
from django.conf import settings
from courses.models import Course, Module, Lesson

class UserActivity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    content_type = models.CharField(max_length=50)
    content_id = models.IntegerField()
    extra_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'content_type', 'content_id']),
            models.Index(fields=['created_at']),
        ]

class CourseProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    last_activity = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'course']

class LearningMetrics(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    total_time_spent = models.DurationField(default=0)
    quiz_average_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    assignments_completed = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

class EngagementMetrics(models.Model):
    date = models.DateField()
    active_users = models.IntegerField()
    total_sessions = models.IntegerField()
    avg_session_duration = models.DurationField()
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        ordering = ['-date']

class ContentPerformance(models.Model):
    content_type = models.CharField(max_length=50)
    content_id = models.IntegerField()
    views = models.IntegerField(default=0)
    avg_time_spent = models.DurationField()
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2)
    feedback_score = models.DecimalField(max_digits=3, decimal_places=2, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['content_type', 'content_id'] 