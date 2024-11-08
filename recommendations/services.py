from django.db.models import Count, Avg, Q
from django.contrib.contenttypes.models import ContentType
from .models import (
    UserPreference, UserInteraction, ContentSimilarity,
    PersonalizedRecommendation
)
from courses.models import Course, Lesson
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

class RecommendationService:
    @staticmethod
    def generate_recommendations(user):
        # Limpa recomendações antigas
        PersonalizedRecommendation.objects.filter(user=user).delete()
        
        recommendations = []
        
        # Combina diferentes estratégias de recomendação
        content_based = RecommendationService._content_based_recommendations(user)
        collaborative = RecommendationService._collaborative_recommendations(user)
        popularity = RecommendationService._popularity_based_recommendations(user)
        
        # Pesos para cada estratégia
        recommendations.extend([
            (item, score * 0.4, 'Baseado em seus interesses')
            for item, score in content_based
        ])
        recommendations.extend([
            (item, score * 0.4, 'Alunos similares também gostaram')
            for item, score in collaborative
        ])
        recommendations.extend([
            (item, score * 0.2, 'Popular entre os alunos')
            for item, score in popularity
        ])
        
        # Ordena e remove duplicatas
        seen_items = set()
        unique_recommendations = []
        
        for item, score, reason in sorted(recommendations, key=lambda x: x[1], reverse=True):
            if item.id not in seen_items:
                seen_items.add(item.id)
                unique_recommendations.append((item, score, reason))
        
        # Salva as recomendações
        content_type = ContentType.objects.get_for_model(Course)
        
        PersonalizedRecommendation.objects.bulk_create([
            PersonalizedRecommendation(
                user=user,
                content_type=content_type,
                object_id=item.id,
                score=score,
                reason=reason
            )
            for item, score, reason in unique_recommendations[:20]  # Top 20
        ])
    
    @staticmethod
    def _content_based_recommendations(user):
        # Obtém preferências do usuário
        preferences = UserPreference.objects.get(user=user)
        
        # Obtém cursos que o usuário ainda não interagiu
        completed_courses = UserInteraction.objects.filter(
            user=user,
            interaction_type='COMPLETE',
            content_type=ContentType.objects.get_for_model(Course)
        ).values_list('object_id', flat=True)
        
        available_courses = Course.objects.exclude(id__in=completed_courses)
        
        recommendations = []
        
        for course in available_courses:
            score = 0
            
            # Pontuação baseada em categorias
            common_categories = set(course.categories) & set(preferences.preferred_categories)
            score += len(common_categories) * 0.3
            
            # Pontuação baseada em interesses
            common_interests = set(course.tags) & set(preferences.interests)
            score += len(common_interests) * 0.3
            
            # Pontuação baseada no nível de dificuldade
            if course.difficulty == preferences.difficulty_preference:
                score += 0.2
            
            # Pontuação baseada no tempo necessário
            if course.estimated_time <= preferences.time_availability:
                score += 0.2
            
            if score > 0:
                recommendations.append((course, score))
        
        return sorted(recommendations, key=lambda x: x[1], reverse=True)
    
    @staticmethod
    def _collaborative_recommendations(user):
        # Matriz de interações usuário-curso
        interactions = UserInteraction.objects.filter(
            content_type=ContentType.objects.get_for_model(Course)
        ).values('user', 'object_id', 'interaction_type')
        
        user_course_matrix = defaultdict(lambda: defaultdict(float))
        
        # Pesos para diferentes tipos de interação
        weights = {
            'VIEW': 0.2,
            'COMPLETE': 1.0,
            'LIKE': 0.8,
            'BOOKMARK': 0.6,
            'SHARE': 0.7,
            'COMMENT': 0.5
        }
        
        for interaction in interactions:
            user_course_matrix[interaction['user']][interaction['object_id']] += \
                weights[interaction['interaction_type']]
        
        # Converte para matriz numpy
        users = list(user_course_matrix.keys())
        courses = list(set(
            course_id 
            for user_interactions in user_course_matrix.values() 
            for course_id in user_interactions
        ))
        
        matrix = np.zeros((len(users), len(courses)))
        
        for i, u in enumerate(users):
            for j, c in enumerate(courses):
                matrix[i, j] = user_course_matrix[u][c]
        
        # Calcula similaridade entre usuários
        user_similarity = cosine_similarity(matrix)
        
        # Encontra usuários similares
        user_index = users.index(user.id)
        similar_users = [
            users[i] 
            for i in user_similarity[user_index].argsort()[-6:-1]  # Top 5 similares
        ]
        
        # Recomendações baseadas em usuários similares
        recommendations = defaultdict(float)
        
        for similar_user in similar_users:
            similarity_score = user_similarity[user_index][users.index(similar_user)]
            
            for course_id, score in user_course_matrix[similar_user].items():
                if course_id not in user_course_matrix[user.id]:
                    recommendations[course_id] += score * similarity_score
        
        # Converte IDs para objetos Course
        courses = Course.objects.in_bulk(recommendations.keys())
        return [
            (courses[course_id], score)
            for course_id, score in sorted(
                recommendations.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ]
    
    @staticmethod
    def _popularity_based_recommendations(user):
        # Cursos populares que o usuário ainda não completou
        completed_courses = UserInteraction.objects.filter(
            user=user,
            interaction_type='COMPLETE',
            content_type=ContentType.objects.get_for_model(Course)
        ).values_list('object_id', flat=True)
        
        popular_courses = Course.objects.exclude(
            id__in=completed_courses
        ).annotate(
            interaction_count=Count('userinteraction'),
            avg_rating=Avg('rating')
        ).filter(
            Q(interaction_count__gt=0) | Q(avg_rating__gt=0)
        )
        
        # Normaliza contagens e ratings
        max_interactions = popular_courses.aggregate(
            max=models.Max('interaction_count')
        )['max'] or 1
        
        recommendations = []
        
        for course in popular_courses:
            # Combina contagem de interações e rating médio
            popularity_score = (
                (course.interaction_count / max_interactions) * 0.7 +
                ((course.avg_rating or 0) / 5.0) * 0.3
            )
            
            recommendations.append((course, popularity_score))
        
        return sorted(recommendations, key=lambda x: x[1], reverse=True) 