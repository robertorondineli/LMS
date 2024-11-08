from django.db.models.signals import post_save
from django.dispatch import receiver
from courses.models import CourseCompletion
from assessments.models import QuizAttempt
from .services import GamificationService

@receiver(post_save, sender=CourseCompletion)
def award_course_completion_points(sender, instance, created, **kwargs):
    if created:
        GamificationService.award_points(
            user=instance.user,
            amount=100,
            point_type='COURSE_COMPLETE',
            description=f"Conclusão do curso: {instance.course.title}"
        )

@receiver(post_save, sender=QuizAttempt)
def award_quiz_points(sender, instance, created, **kwargs):
    if instance.is_passed:
        points = 50 if instance.score >= 90 else 30
        GamificationService.award_points(
            user=instance.user,
            amount=points,
            point_type='QUIZ_PASS',
            description=f"Quiz concluído com {instance.score}%: {instance.quiz.title}"
        ) 