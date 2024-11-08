from django.utils import timezone
from django.db.models import Avg, Count, Q
from .models import (
    Assessment, UserAssessment, UserAnswer, Question,
    QuestionOption, AutomatedFeedback
)
import numpy as np
from datetime import timedelta

class AssessmentService:
    @staticmethod
    def start_assessment(user, assessment):
        """Inicia uma nova tentativa de avaliação"""
        # Verifica tentativas anteriores
        attempt_count = UserAssessment.objects.filter(
            user=user,
            assessment=assessment
        ).count()
        
        if attempt_count >= assessment.attempts_allowed:
            raise ValueError("Número máximo de tentativas atingido")
        
        # Cria nova tentativa
        user_assessment = UserAssessment.objects.create(
            user=user,
            assessment=assessment,
            attempt_number=attempt_count + 1
        )
        
        return user_assessment
    
    @staticmethod
    def submit_answer(user_assessment, question, answer_data):
        """Processa e avalia uma resposta"""
        if user_assessment.status != 'IN_PROGRESS':
            raise ValueError("Avaliação não está em andamento")
        
        # Verifica tempo limite
        if user_assessment.assessment.time_limit:
            time_limit = timedelta(minutes=user_assessment.assessment.time_limit)
            if timezone.now() - user_assessment.started_at > time_limit:
                user_assessment.status = 'TIMED_OUT'
                user_assessment.save()
                raise ValueError("Tempo limite excedido")
        
        # Processa resposta baseado no tipo de questão
        if question.type == 'MULTIPLE_CHOICE':
            return AssessmentService._process_multiple_choice(
                user_assessment, question, answer_data
            )
        elif question.type == 'TRUE_FALSE':
            return AssessmentService._process_true_false(
                user_assessment, question, answer_data
            )
        elif question.type == 'ESSAY':
            return AssessmentService._process_essay(
                user_assessment, question, answer_data
            )
        elif question.type == 'CODING':
            return AssessmentService._process_coding(
                user_assessment, question, answer_data
            )
        elif question.type == 'MATCHING':
            return AssessmentService._process_matching(
                user_assessment, question, answer_data
            )
    
    @staticmethod
    def complete_assessment(user_assessment):
        """Finaliza e avalia uma avaliação"""
        if user_assessment.status != 'IN_PROGRESS':
            raise ValueError("Avaliação já foi finalizada")
        
        total_points = user_assessment.assessment.get_total_points()
        earned_points = UserAnswer.objects.filter(
            user_assessment=user_assessment
        ).aggregate(total=models.Sum('points_earned'))['total'] or 0
        
        # Calcula pontuação final
        score = (earned_points / total_points) * 100 if total_points > 0 else 0
        
        # Atualiza status
        user_assessment.status = 'COMPLETED'
        user_assessment.completed_at = timezone.now()
        user_assessment.score = score
        user_assessment.time_spent = timezone.now() - user_assessment.started_at
        user_assessment.save()
        
        return user_assessment
    
    @staticmethod
    def get_feedback(user_assessment):
        """Gera feedback detalhado da avaliação"""
        feedback = {
            'score': user_assessment.score,
            'passing_score': user_assessment.assessment.passing_score,
            'time_spent': user_assessment.time_spent,
            'questions': []
        }
        
        for answer in UserAnswer.objects.filter(
            user_assessment=user_assessment
        ).select_related('question'):
            question_feedback = {
                'question': answer.question.content,
                'correct': answer.is_correct,
                'points_earned': answer.points_earned,
                'feedback': answer.feedback,
                'explanation': answer.question.explanation
            }
            
            if user_assessment.assessment.show_answers:
                if answer.question.type in ['MULTIPLE_CHOICE', 'TRUE_FALSE']:
                    question_feedback['correct_options'] = list(
                        answer.question.options.filter(
                            is_correct=True
                        ).values_list('content', flat=True)
                    )
                
            feedback['questions'].append(question_feedback)
        
        return feedback
    
    @staticmethod
    def _process_multiple_choice(user_assessment, question, answer_data):
        selected_options = QuestionOption.objects.filter(
            id__in=answer_data.get('selected_options', [])
        )
        
        correct_options = question.options.filter(is_correct=True)
        is_correct = set(selected_options) == set(correct_options)
        
        points_earned = question.points if is_correct else 0
        
        user_answer = UserAnswer.objects.create(
            user_assessment=user_assessment,
            question=question,
            is_correct=is_correct,
            points_earned=points_earned
        )
        user_answer.selected_options.set(selected_options)
        
        # Aplica feedback automatizado
        feedback = AutomatedFeedback.objects.filter(
            question=question
        ).first()
        
        if feedback:
            feedback.apply_feedback(user_answer)
        
        return user_answer
    
    @staticmethod
    def _process_essay(user_assessment, question, answer_data):
        text_answer = answer_data.get('text', '')
        
        user_answer = UserAnswer.objects.create(
            user_assessment=user_assessment,
            question=question,
            text_answer=text_answer
        )
        
        # Análise inicial do texto
        AssessmentService._analyze_essay(user_answer)
        
        return user_answer
    
    @staticmethod
    def _analyze_essay(user_answer):
        """Análise automatizada de resposta dissertativa"""
        text = user_answer.text_answer.lower()
        question = user_answer.question
        
        # Análise básica
        word_count = len(text.split())
        if word_count < 50:
            user_answer.feedback = "Resposta muito curta. Desenvolva mais seus argumentos."
            user_answer.points_earned = question.points * 0.3
        elif word_count < 100:
            user_answer.feedback = "Resposta adequada, mas poderia ser mais desenvolvida."
            user_answer.points_earned = question.points * 0.7
        else:
            user_answer.feedback = "Resposta bem desenvolvida."
            user_answer.points_earned = question.points
        
        # Aqui poderia integrar com API de NLP para análise mais avançada
        
        user_answer.save() 