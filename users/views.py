from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView
from django.urls import reverse_lazy
from .models import CustomUser
from .forms import CustomUserUpdateForm

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('users:dashboard')

class CustomLogoutView(LogoutView):
    next_page = 'users:login'

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'users/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['enrolled_courses'] = user.courses_enrolled.all()
        if user.role == 'INSTRUCTOR':
            context['teaching_courses'] = user.courses_teaching.all()
        context['progress'] = self.get_user_progress()
        return context
    
    def get_user_progress(self):
        user = self.request.user
        enrollments = user.enrollment_set.all()
        return {
            'total_courses': enrollments.count(),
            'completed_courses': enrollments.filter(completed=True).count(),
            'in_progress_courses': enrollments.filter(completed=False).count()
        }

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserUpdateForm
    template_name = 'users/profile_update.html'
    success_url = reverse_lazy('users:profile')
    
    def get_object(self):
        return self.request.user 