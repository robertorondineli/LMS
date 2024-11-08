from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrador')
        INSTRUCTOR = 'INSTRUCTOR', _('Instrutor')
        STUDENT = 'STUDENT', _('Aluno')
    
    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.STUDENT
    )
    department = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50, unique=True)
    profile_picture = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True
    )
    bio = models.TextField(blank=True)
    points = models.IntegerField(default=0)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}" 