from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import UserLevel, UserAchievement, Streak, UserQuest
from .services import GamificationService

class GamificationProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'gamification/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Informações do nível
        user_level = UserLevel.objects.get(user=user)
        next_level = user_level.level.number + 1
        
        try:
            next_level_obj = Level.objects.get(number=next_level)
            points_to_next = next_level_obj.points_required - user_level.total_points
        except Level.DoesNotExist:
            points_to_next = 0
        
        context['user_level'] = user_level
        context['points_to_next'] = points_to_next
        
        # Conquistas
        context['achievements'] = UserAchievement.objects.filter(
            user=user
        ).select_related('achievement')
        
        # Sequência
        context['streak'] = Streak.objects.get_or_create(user=user)[0]
        
        # Missões ativas
        context['active_quests'] = UserQuest.objects.filter(
            user=user,
            completed=False,
            quest__is_active=True
        ).select_related('quest')
        
        # Ranking
        context['leaderboard'] = GamificationService.get_leaderboard()
        
        return context
