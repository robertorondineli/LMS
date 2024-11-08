from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from .models import Point, Achievement, UserLevel, Streak

class GamificationReports:
    @staticmethod
    def get_engagement_metrics(days=30):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        return {
            'total_points_awarded': Point.objects.filter(
                earned_at__gte=start_date
            ).aggregate(Sum('amount'))['amount__sum'] or 0,
            
            'active_users': Point.objects.filter(
                earned_at__gte=start_date
            ).values('user').distinct().count(),
            
            'achievements_earned': Achievement.objects.filter(
                earned_at__gte=start_date
            ).count(),
            
            'average_level': UserLevel.objects.aggregate(
                Avg('current_level__number')
            )['current_level__number__avg'] or 0,
            
            'streak_stats': {
                'average_streak': Streak.objects.aggregate(
                    Avg('current_streak')
                )['current_streak__avg'] or 0,
                'users_with_streak_7plus': Streak.objects.filter(
                    current_streak__gte=7
                ).count()
            }
        }
    
    @staticmethod
    def get_leaderboard(limit=10):
        return UserLevel.objects.select_related('user').order_by(
            '-current_level__number',
            '-user__points'
        )[:limit]
    
    @staticmethod
    def get_achievement_distribution():
        return Achievement.objects.values(
            'badge__name'
        ).annotate(
            total=Count('id')
        ).order_by('-total')
    
    @staticmethod
    def get_user_progress_report(user):
        return {
            'points_history': Point.objects.filter(user=user).values(
                'earned_at__date'
            ).annotate(
                total=Sum('amount')
            ).order_by('earned_at__date'),
            
            'achievements': Achievement.objects.filter(user=user).select_related(
                'badge'
            ).order_by('earned_at'),
            
            'current_streak': Streak.objects.get(user=user).current_streak,
            
            'level_progress': {
                'current_level': user.userlevel.current_level.number,
                'points_to_next': user.userlevel.points_to_next_level,
                'total_points': Point.objects.filter(user=user).aggregate(
                    Sum('amount')
                )['amount__sum'] or 0
            }
        } 