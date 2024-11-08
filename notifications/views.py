from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Notification, NotificationPreference
from .services import NotificationService

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).select_related('content_type')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Notification.objects.filter(
            user=self.request.user,
            read=False
        ).count()
        return context

class NotificationCenterView(LoginRequiredMixin, ListView):
    template_name = 'notifications/notification_center.html'
    context_object_name = 'notifications'
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user,
            read=False
        ).select_related('content_type')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['preferences'] = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )[0]
        return context

class NotificationPreferencesView(LoginRequiredMixin, DetailView):
    model = NotificationPreference
    template_name = 'notifications/preferences.html'
    
    def get_object(self):
        return NotificationPreference.objects.get_or_create(
            user=self.request.user
        )[0]
    
    def post(self, request, *args, **kwargs):
        preferences = self.get_object()
        
        preferences.email_notifications = request.POST.get(
            'email_notifications', False
        ) == 'on'
        preferences.push_notifications = request.POST.get(
            'push_notifications', False
        ) == 'on'
        
        notification_types = {}
        for type, _ in Notification.TYPES:
            notification_types[type] = request.POST.get(f'type_{type}', False) == 'on'
        
        preferences.notification_types = notification_types
        preferences.save()
        
        return JsonResponse({'status': 'success'})

class MarkNotificationReadView(LoginRequiredMixin, View):
    def post(self, request, notification_id):
        success = NotificationService.mark_as_read(notification_id, request.user)
        return JsonResponse({'success': success})

class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    def post(self, request):
        count = NotificationService.mark_all_as_read(request.user)
        return JsonResponse({'count': count}) 