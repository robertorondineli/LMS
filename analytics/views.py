from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from .models import (
    UserActivity, CourseProgress, LearningMetrics,
    EngagementMetrics, ContentPerformance
)
from courses.models import Course

class AnalyticsDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'analytics/dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Período de análise
        period = self.request.GET.get('period', '30')  # dias
        start_date = timezone.now() - timedelta(days=int(period))
        
        # Métricas gerais
        context['total_users'] = UserActivity.objects.filter(
            created_at__gte=start_date
        ).values('user').distinct().count()
        
        context['total_courses'] = Course.objects.count()
        
        context['avg_completion_rate'] = CourseProgress.objects.filter(
            last_activity__gte=start_date
        ).aggregate(avg=Avg('progress_percentage'))['avg'] or 0
        
        # Engajamento ao longo do tempo
        engagement_metrics = EngagementMetrics.objects.filter(
            date__gte=start_date
        ).order_by('date')
        
        context['engagement_data'] = {
            'dates': [m.date.strftime('%d/%m') for m in engagement_metrics],
            'active_users': [m.active_users for m in engagement_metrics],
            'bounce_rate': [float(m.bounce_rate) for m in engagement_metrics]
        }
        
        # Top cursos
        context['top_courses'] = Course.objects.annotate(
            students=Count('students'),
            avg_progress=Avg('courseprogress__progress_percentage')
        ).order_by('-students')[:5]
        
        # Distribuição de progresso
        progress_distribution = CourseProgress.objects.filter(
            last_activity__gte=start_date
        ).values('progress_percentage').annotate(
            count=Count('id')
        ).order_by('progress_percentage')
        
        context['progress_distribution'] = {
            'labels': ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%'],
            'data': [0, 0, 0, 0, 0]  # Inicializa com zeros
        }
        
        for progress in progress_distribution:
            index = int(float(progress['progress_percentage']) // 20)
            if 0 <= index <= 4:
                context['progress_distribution']['data'][index] += progress['count']
        
        return context

class CourseAnalyticsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'analytics/course_analytics.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = Course.objects.get(id=self.kwargs['course_id'])
        context['course'] = course
        
        # Métricas do curso
        metrics = LearningMetrics.objects.filter(course=course)
        
        context['avg_time_spent'] = metrics.aggregate(
            avg=Avg('total_time_spent')
        )['avg'] or timedelta()
        
        context['avg_quiz_score'] = metrics.aggregate(
            avg=Avg('quiz_average_score')
        )['avg'] or 0
        
        # Performance do conteúdo
        content_performance = ContentPerformance.objects.filter(
            content_type__in=['lesson', 'quiz', 'assignment'],
            content_id__in=course.get_content_ids()
        ).order_by('-views')
        
        context['content_performance'] = content_performance
        
        # Progresso dos alunos
        student_progress = CourseProgress.objects.filter(
            course=course
        ).select_related('user')
        
        context['student_progress'] = student_progress
        
        return context

class StudentAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/student_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Progresso geral
        context['course_progress'] = CourseProgress.objects.filter(
            user=user
        ).select_related('course')
        
        # Métricas de aprendizado
        context['learning_metrics'] = LearningMetrics.objects.filter(
            user=user
        ).select_related('course')
        
        # Atividade recente
        context['recent_activity'] = UserActivity.objects.filter(
            user=user
        ).select_related('content_type')[:10]
        
        return context 