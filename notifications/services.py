from django.template import Template, Context
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Notification, NotificationPreference, NotificationTemplate
import json
import firebase_admin
from firebase_admin import messaging

class NotificationService:
    @staticmethod
    def create_notification(user, type, title, message, **kwargs):
        """Cria e envia uma notificação"""
        # Verifica preferências do usuário
        preferences = NotificationPreference.objects.get_or_create(user=user)[0]
        
        if not preferences.can_send_notification(type):
            return None
            
        # Cria a notificação
        notification = Notification.objects.create(
            user=user,
            type=type,
            title=title,
            message=message,
            priority=kwargs.get('priority', 'MEDIUM'),
            content_type=kwargs.get('content_type'),
            object_id=kwargs.get('object_id'),
            scheduled_for=kwargs.get('scheduled_for')
        )
        
        # Envia notificações em tempo real se não for agendada
        if not notification.scheduled_for:
            NotificationService._send_notification(notification)
        
        return notification
    
    @staticmethod
    def send_bulk_notifications(users, type, title, message, **kwargs):
        """Envia notificações em massa"""
        notifications = []
        
        for user in users:
            preferences = NotificationPreference.objects.get_or_create(user=user)[0]
            
            if preferences.can_send_notification(type):
                notification = Notification(
                    user=user,
                    type=type,
                    title=title,
                    message=message,
                    priority=kwargs.get('priority', 'MEDIUM'),
                    content_type=kwargs.get('content_type'),
                    object_id=kwargs.get('object_id'),
                    scheduled_for=kwargs.get('scheduled_for')
                )
                notifications.append(notification)
        
        # Cria notificações em bulk
        created_notifications = Notification.objects.bulk_create(notifications)
        
        # Envia notificações em tempo real se não for agendada
        if not kwargs.get('scheduled_for'):
            for notification in created_notifications:
                NotificationService._send_notification(notification)
        
        return created_notifications
    
    @staticmethod
    def mark_as_read(notification_id, user):
        """Marca uma notificação como lida"""
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            notification.read = True
            notification.read_at = timezone.now()
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False
    
    @staticmethod
    def mark_all_as_read(user):
        """Marca todas as notificações do usuário como lidas"""
        return Notification.objects.filter(
            user=user,
            read=False
        ).update(
            read=True,
            read_at=timezone.now()
        )
    
    @staticmethod
    def _send_notification(notification):
        """Envia notificação pelos canais configurados"""
        preferences = NotificationPreference.objects.get(user=notification.user)
        
        # Envia email se configurado
        if preferences.email_notifications:
            NotificationService._send_email_notification(notification)
        
        # Envia push se configurado
        if preferences.push_notifications:
            NotificationService._send_push_notification(notification)
    
    @staticmethod
    def _send_email_notification(notification):
        """Envia notificação por email"""
        template = NotificationTemplate.objects.get(
            type=notification.type,
            active=True
        )
        
        context = {
            'user': notification.user,
            'notification': notification,
            'site_url': settings.SITE_URL
        }
        
        email_content = Template(template.email_template).render(Context(context))
        
        send_mail(
            subject=template.subject,
            message=email_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.user.email],
            html_message=email_content
        )
    
    @staticmethod
    def _send_push_notification(notification):
        """Envia push notification"""
        if not notification.user.device_token:
            return
            
        template = NotificationTemplate.objects.get(
            type=notification.type,
            active=True
        )
        
        message = messaging.Message(
            notification=messaging.Notification(
                title=notification.title,
                body=Template(template.push_template).render(
                    Context({'notification': notification})
                )
            ),
            token=notification.user.device_token,
            data={
                'notification_id': str(notification.id),
                'type': notification.type,
                'url': f'/notifications/{notification.id}'
            }
        )
        
        messaging.send(message) 