from django.db import models
from django.conf import settings
from courses.models import Course, Lesson
from django.core.validators import MinValueValidator, MaxValueValidator
import random

class Question(models.Model):
    TYPES = [
        ('MULTIPLE_CHOICE', 'Múltipla Escolha'),
        ('TRUE_FALSE', 'Verdadeiro ou Falso'),
        ('ESSAY', 'Dissertativa'),
        ('CODING', 'Programação'),
        ('MATCHING', 'Associação')
    ]
    
    DIFFICULTY = [
        ('EASY', 'Fácil'),
        ('MEDIUM', 'Médio'),
        ('HARD', 'Difícil')
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    type = models.CharField(max_length=20, choices=TYPES)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY)
    points = models.IntegerField(default=10)
    explanation = models.TextField(blank=True)
    tags = models.JSONField(default=list)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['type', 'difficulty']),
        ]

class QuestionOption(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    content = models.TextField()
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']

class Assessment(models.Model):
    TYPES = [
        ('QUIZ', 'Quiz'),
        ('EXAM', 'Prova'),
        ('PRACTICE', 'Prática'),
        ('DIAGNOSTIC', 'Diagnóstico')
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=TYPES)
    questions = models.ManyToManyField(Question, through='AssessmentQuestion')
    time_limit = models.IntegerField(null=True, blank=True, help_text="Tempo em minutos")
    passing_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=70
    )
    attempts_allowed = models.IntegerField(default=1)
    randomize_questions = models.BooleanField(default=False)
    show_answers = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_total_points(self):
        return sum(aq.question.points for aq in self.assessmentquestion_set.all())
    
    def generate_question_set(self):
        questions = list(self.assessmentquestion_set.all())
        if self.randomize_questions:
            random.shuffle(questions)
        return questions

class AssessmentQuestion(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = ['assessment', 'question']

class UserAssessment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True)
    time_spent = models.DurationField(null=True)
    attempt_number = models.IntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=[
            ('IN_PROGRESS', 'Em Andamento'),
            ('COMPLETED', 'Concluído'),
            ('TIMED_OUT', 'Tempo Esgotado')
        ],
        default='IN_PROGRESS'
    )
    
    class Meta:
        unique_together = ['user', 'assessment', 'attempt_number']

class UserAnswer(models.Model):
    user_assessment = models.ForeignKey(UserAssessment, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_options = models.ManyToManyField(QuestionOption, blank=True)
    text_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(null=True)
    points_earned = models.FloatField(default=0)
    feedback = models.TextField(blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user_assessment', 'question']

class AutomatedFeedback(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    condition = models.JSONField(help_text="Condições para este feedback")
    feedback_text = models.TextField()
    suggestions = models.TextField()
    
    def apply_feedback(self, user_answer):
        # Implementa lógica de feedback automatizado
        pass