from django.db.models import Avg, Count, Sum, F
from django.utils import timezone
from datetime import timedelta
from .models import (
    UserActivity, CourseProgress, LearningMetrics,
    EngagementMetrics, ContentPerformance
)

class AnalyticsService:
    @staticmethod
    def track_activity(user, action, content_type, content_id, extra_data=None):
        return UserActivity.objects.create(
            user=user,
            action=action,
            content_type=content_type,
            content_id=content_id,
            extra_data=extra_data
        )
    
    @staticmethod
    def update_course_progress(user, course):
        total_items = course.get_total_items()
        completed_items = course.get_completed_items(user)
        
        progress = (completed_items / total_items * 100) if total_items > 0 else 0
        
        progress_obj, created = CourseProgress.objects.get_or_create(
            user=user,
            course=course,
            defaults={'progress_percentage': progress}
        )
        
        if not created:
            progress_obj.progress_percentage = progress
            if progress == 100 and not progress_obj.completed_at:
                progress_obj.completed_at = timezone.now()
            progress_obj.save()
        
        return progress_obj
    
    @staticmethod
    def update_learning_metrics(user, course):
        metrics, _ = LearningMetrics.objects.get_or_create(
            user=user,
            course=course
        )
        
        # Atualiza tempo total
        activities = UserActivity.objects.filter(
            user=user,
            content_type='lesson',
            content_id__in=course.get_lesson_ids()
        )
        
        total_time = timedelta()
        for activity in activities:
            if activity.extra_data and 'time_spent' in activity.extra_data:
                total_time += timedelta(seconds=activity.extra_data['time_spent'])
        
        metrics.total_time_spent = total_time
        
        # Atualiza média de quiz
        quiz_scores = UserActivity.objects.filter(
            user=user,
            content_type='quiz',
            content_id__in=course.get_quiz_ids()
        ).values_list('extra_data__score', flat=True)
        
        if quiz_scores:
            metrics.quiz_average_score = sum(quiz_scores) / len(quiz_scores)
        
        # Atualiza assignments completados
        metrics.assignments_completed = UserActivity.objects.filter(
            user=user,
            content_type='assignment',
            content_id__in=course.get_assignment_ids(),
            action='completed'
        ).count()
        
        metrics.save()
        return metrics
    
    @staticmethod
    def calculate_engagement_metrics(date=None):
        if not date:
            date = timezone.now().date()
        
        activities = UserActivity.objects.filter(
            created_at__date=date
        )
        
        active_users = activities.values('user').distinct().count()
        total_sessions = activities.values('user').annotate(
            sessions=Count('id', distinct=True)
        ).count()
        
        # Calcula duração média da sessão
        session_durations = []
        for user_activities in activities.values('user').annotate(
            first_activity=F('created_at__min'),
            last_activity=F('created_at__max')
        ):
            duration = user_activities['last_activity'] - user_activities['first_activity']
            session_durations.append(duration)
        
        avg_duration = sum(session_durations, timedelta()) / len(session_durations) if session_durations else timedelta()
        
        # Calcula taxa de rejeição
        bounce_sessions = activities.values('user').annotate(
            activity_count=Count('id')
        ).filter(activity_count=1).count()
        
        bounce_rate = (bounce_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        metrics, _ = EngagementMetrics.objects.get_or_create(
            date=date,
            defaults={
                'active_users': active_users,
                'total_sessions': total_sessions,
                'avg_session_duration': avg_duration,
                'bounce_rate': bounce_rate
            }
        )
        
        return metrics
    
    @staticmethod
    def update_content_performance(content_type, content_id):
        activities = UserActivity.objects.filter(
            content_type=content_type,
            content_id=content_id
        )
        
        views = activities.filter(action='view').count()
        
        # Calcula tempo médio gasto
        time_spent = []
        for activity in activities.filter(action='view'):
            if activity.extra_data and 'time_spent' in activity.extra_data:
                time_spent.append(activity.extra_data['time_spent'])
        
        avg_time = sum(time_spent) / len(time_spent) if time_spent else 0
        avg_time_duration = timedelta(seconds=avg_time)
        
        # Calcula taxa de conclusão
        total_users = activities.values('user').distinct().count()
        completed_users = activities.filter(
            action='completed'
        ).values('user').distinct().count()
        
        completion_rate = (completed_users / total_users * 100) if total_users > 0 else 0
        
        # Calcula média de feedback
        feedback_scores = activities.filter(
            action='feedback'
        ).values_list('extra_data__score', flat=True)
        
        feedback_avg = sum(feedback_scores) / len(feedback_scores) if feedback_scores else None
        
        performance, _ = ContentPerformance.objects.get_or_create(
            content_type=content_type,
            content_id=content_id,
            defaults={
                'views': views,
                'avg_time_spent': avg_time_duration,
                'completion_rate': completion_rate,
                'feedback_score': feedback_avg
            }
        )
        
        return performance 