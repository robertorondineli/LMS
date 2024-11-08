from django.db import models
from django.conf import settings

class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses_teaching'
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Enrollment',
        related_name='courses_enrolled'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_mandatory = models.BooleanField(default=False)
    departments = models.JSONField()
    thumbnail = models.ImageField(
        upload_to='course_thumbnails/',
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['-created_at']

class Module(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField()
    
    class Meta:
        ordering = ['order']

class Content(models.Model):
    class ContentType(models.TextChoices):
        VIDEO = 'VIDEO', 'Vídeo'
        PDF = 'PDF', 'PDF'
        TEXT = 'TEXT', 'Texto'
        QUIZ = 'QUIZ', 'Questionário'
    
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='contents'
    )
    title = models.CharField(max_length=200)
    content_type = models.CharField(
        max_length=20,
        choices=ContentType.choices
    )
    content = models.TextField(blank=True)
    file = models.FileField(
        upload_to='course_contents/',
        null=True,
        blank=True
    )
    order = models.IntegerField()
    
    class Meta:
        ordering = ['order']

class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_enrolled = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    progress = models.FloatField(default=0.0) 