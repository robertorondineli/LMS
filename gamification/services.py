from django.utils import timezone
from django.db.models import F
from .models import (
    Achievement, UserAchievement, Streak,
    Level, UserLevel, Quest, UserQuest
)

class GamificationService:
    @staticmethod
    def check_achievements(user, action_type, context=None):
        achievements = Achievement.objects.filter(type=action_type, is_hidden=False)
        earned_achievements = []
        
        for achievement in achievements:
            if GamificationService._check_achievement_requirements(
                user, achievement, context
            ):
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                
                if created:
                    earned_achievements.append(user_achievement)
                    user_level = UserLevel.objects.get(user=user)
                    user_level.add_points(achievement.points)
        
        return earned_achievements
    
    @staticmethod
    def _check_achievement_requirements(user, achievement, context):
        req = achievement.requirement
        
        if achievement.type == 'COURSE':
            return GamificationService._check_course_achievement(user, req)
        elif achievement.type == 'STREAK':
            return GamificationService._check_streak_achievement(user, req)
        elif achievement.type == 'QUIZ':
            return GamificationService._check_quiz_achievement(user, req)
        elif achievement.type == 'SOCIAL':
            return GamificationService._check_social_achievement(user, req)
        elif achievement.type == 'CONTENT':
            return GamificationService._check_content_achievement(user, req)
        
        return False
    
    @staticmethod
    def update_streak(user):
        streak, created = Streak.objects.get_or_create(user=user)
        streak.update_streak()
        
        # Verifica conquistas relacionadas a sequência
        GamificationService.check_achievements(user, 'STREAK', {
            'current_streak': streak.current_streak,
            'longest_streak': streak.longest_streak
        })
        
        return streak
    
    @staticmethod
    def get_available_quests(user):
        now = timezone.now()
        return Quest.objects.filter(
            is_active=True,
            expires_at__gt=now
        ).exclude(
            userquest__user=user,
            userquest__completed=True
        )
    
    @staticmethod
    def update_quest_progress(user, quest_type, context):
        quests = UserQuest.objects.filter(
            user=user,
            quest__type=quest_type,
            completed=False
        ).select_related('quest')
        
        completed_quests = []
        
        for user_quest in quests:
            if GamificationService._check_quest_requirements(
                user_quest, context
            ):
                user_quest.completed = True
                user_quest.completed_at = timezone.now()
                user_quest.save()
                
                user_level = UserLevel.objects.get(user=user)
                user_level.add_points(user_quest.quest.points)
                
                completed_quests.append(user_quest)
        
        return completed_quests
    
    @staticmethod
    def get_leaderboard(course=None, timeframe='ALL'):
        queryset = UserLevel.objects.select_related('user', 'level')
        
        if course:
            queryset = queryset.filter(user__enrolled_courses=course)
        
        if timeframe == 'WEEKLY':
            start_date = timezone.now() - timezone.timedelta(days=7)
            queryset = queryset.filter(
                userachievement__earned_at__gte=start_date
            )
        elif timeframe == 'MONTHLY':
            start_date = timezone.now() - timezone.timedelta(days=30)
            queryset = queryset.filter(
                userachievement__earned_at__gte=start_date
            )
        
        return queryset.order_by('-total_points')[:10]