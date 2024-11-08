from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from .models import Assessment, UserAssessment, Question, UserAnswer
from .services import AssessmentService
from django.urls import reverse_lazy

class AssessmentListView(LoginRequiredMixin, ListView):
    model = Assessment
    template_name = 'assessments/assessment_list.html'
    context_object_name = 'assessments'
    
    def get_queryset(self):
        return Assessment.objects.filter(
            course__in=self.request.user.enrolled_courses.all(),
            active=True
        ).select_related('course')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Adiciona progresso do usuário
        user_assessments = UserAssessment.objects.filter(
            user=self.request.user,
            assessment__in=context['assessments']
        ).select_related('assessment')
        
        context['user_progress'] = {
            ua.assessment_id: {
                'attempts': ua.attempt_number,
                'best_score': ua.score,
                'status': ua.status
            }
            for ua in user_assessments
        }
        
        return context

class AssessmentDetailView(LoginRequiredMixin, DetailView):
    model = Assessment
    template_name = 'assessments/assessment_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        assessment = self.object
        
        # Verifica tentativas anteriores
        previous_attempts = UserAssessment.objects.filter(
            user=user,
            assessment=assessment
        ).order_by('-started_at')
        
        context['previous_attempts'] = previous_attempts
        context['attempts_remaining'] = (
            assessment.attempts_allowed - previous_attempts.count()
        )
        
        # Verifica se há uma tentativa em andamento
        active_attempt = previous_attempts.filter(
            status='IN_PROGRESS'
        ).first()
        
        if active_attempt:
            context['active_attempt'] = active_attempt
            if assessment.time_limit:
                time_passed = timezone.now() - active_attempt.started_at
                minutes_remaining = assessment.time_limit - (time_passed.seconds // 60)
                context['minutes_remaining'] = max(0, minutes_remaining)
        
        return context

class StartAssessmentView(LoginRequiredMixin, DetailView):
    model = Assessment
    template_name = 'assessments/take_assessment.html'
    
    def get(self, request, *args, **kwargs):
        assessment = self.get_object()
        
        try:
            user_assessment = AssessmentService.start_assessment(
                request.user, assessment
            )
            return super().get(request, *args, **kwargs)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('assessment_detail', pk=assessment.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assessment = self.object
        
        user_assessment = UserAssessment.objects.get(
            user=self.request.user,
            assessment=assessment,
            status='IN_PROGRESS'
        )
        
        context['user_assessment'] = user_assessment
        context['questions'] = assessment.generate_question_set()
        
        if assessment.time_limit:
            context['minutes_remaining'] = assessment.time_limit
        
        return context

class SubmitAnswerView(LoginRequiredMixin, View):
    def post(self, request, assessment_id):
        user_assessment = get_object_or_404(
            UserAssessment,
            id=assessment_id,
            user=request.user,
            status='IN_PROGRESS'
        )
        
        data = json.loads(request.body)
        question = get_object_or_404(Question, id=data['question_id'])
        
        try:
            answer = AssessmentService.submit_answer(
                user_assessment, question, data
            )
            
            return JsonResponse({
                'success': True,
                'points_earned': answer.points_earned,
                'feedback': answer.feedback
            })
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class CompleteAssessmentView(LoginRequiredMixin, View):
    def post(self, request, assessment_id):
        user_assessment = get_object_or_404(
            UserAssessment,
            id=assessment_id,
            user=request.user
        )
        
        try:
            completed = AssessmentService.complete_assessment(user_assessment)
            feedback = AssessmentService.get_feedback(completed)
            
            return JsonResponse({
                'success': True,
                'redirect_url': reverse_lazy(
                    'assessment_results',
                    kwargs={'pk': completed.id}
                ),
                'feedback': feedback
            })
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class AssessmentResultsView(LoginRequiredMixin, DetailView):
    model = UserAssessment
    template_name = 'assessments/assessment_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_assessment = self.object
        
        context['feedback'] = AssessmentService.get_feedback(user_assessment)
        context['passed'] = (
            user_assessment.score >= user_assessment.assessment.passing_score
        )
        
        return context