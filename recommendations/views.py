from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import PersonalizedRecommendation, UserPreference
from .services import RecommendationService
from django.db.models import Prefetch
from courses.models import Course

class RecommendationsView(LoginRequiredMixin, TemplateView):
    template_name = 'recommendations/recommendations.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Gera novas recomendações se necessário
        if not PersonalizedRecommendation.objects.filter(user=user).exists():
            RecommendationService.generate_recommendations(user)
        
        # Obtém recomendações ativas
        recommendations = PersonalizedRecommendation.objects.filter(
            user=user,
            is_dismissed=False
        ).select_related('content_type').prefetch_related(
            Prefetch(
                'content_object',
                queryset=Course.objects.select_related('instructor')
            )
        )
        
        # Agrupa por razão
        grouped_recommendations = {}
        for rec in recommendations:
            if rec.reason not in grouped_recommendations:
                grouped_recommendations[rec.reason] = []
            grouped_recommendations[rec.reason].append(rec)
        
        context['grouped_recommendations'] = grouped_recommendations
        
        # Obtém preferências do usuário
        try:
            context['preferences'] = UserPreference.objects.get(user=user)
        except UserPreference.DoesNotExist:
            context['preferences'] = None
        
        return context 