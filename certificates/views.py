from django.views.generic import DetailView, ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from .models import Certificate, Badge, UserBadge
from .services import CertificateService, BadgeService

class CertificateListView(LoginRequiredMixin, ListView):
    model = Certificate
    template_name = 'certificates/certificate_list.html'
    context_object_name = 'certificates'
    
    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user)

class CertificateDetailView(LoginRequiredMixin, DetailView):
    model = Certificate
    template_name = 'certificates/certificate_detail.html'
    
    def get_object(self):
        return get_object_or_404(
            Certificate,
            id=self.kwargs['certificate_id'],
            user=self.request.user
        )

class CertificateVerificationView(TemplateView):
    template_name = 'certificates/verify.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        verification_code = self.kwargs.get('verification_code')
        
        if verification_code:
            certificate = CertificateService.verify_certificate(verification_code)
            context['certificate'] = certificate
            context['is_valid'] = certificate is not None
        
        return context

class BadgeListView(LoginRequiredMixin, ListView):
    model = Badge
    template_name = 'certificates/badge_list.html'
    context_object_name = 'badges'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Adiciona progresso para cada badge
        context['badge_progress'] = {
            badge.id: BadgeService.get_user_progress(user, badge)
            for badge in context['badges']
        }
        
        # Badges conquistadas
        context['earned_badges'] = UserBadge.objects.filter(
            user=user,
            earned_at__isnull=False
        ).select_related('badge')
        
        return context 