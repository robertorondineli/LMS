from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Event, EventRegistration, EventNotification
from datetime import timedelta
import icalendar
import pytz

class EventService:
    @staticmethod
    def create_event(data, organizer):
        """Cria um novo evento"""
        event = Event.objects.create(
            title=data['title'],
            description=data['description'],
            type=data['type'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            registration_deadline=data['registration_deadline'],
            max_participants=data.get('max_participants'),
            min_participants=data.get('min_participants', 1),
            is_online=data.get('is_online', True),
            location=data.get('location', ''),
            meeting_url=data.get('meeting_url', ''),
            meeting_password=data.get('meeting_password', ''),
            organizer=organizer,
            tags=data.get('tags', [])
        )
        
        # Adiciona apresentadores
        if 'presenters' in data:
            event.presenters.set(data['presenters'])
        
        # Cria sessões
        if 'sessions' in data:
            for session_data in data['sessions']:
                event.sessions.create(**session_data)
        
        return event
    
    @staticmethod
    def register_participant(event, participant):
        """Registra um participante no evento"""
        if event.is_full:
            raise ValueError("Evento está lotado")
            
        if timezone.now() > event.registration_deadline:
            raise ValueError("Prazo de inscrição encerrado")
        
        registration = EventRegistration.objects.create(
            event=event,
            participant=participant
        )
        
        # Atualiza contador de participantes
        event.current_participants += 1
        event.save()
        
        # Envia confirmação
        EventService.send_registration_confirmation(registration)
        
        return registration
    
    @staticmethod
    def cancel_registration(registration):
        """Cancela inscrição de participante"""
        if registration.status == 'CANCELLED':
            return
        
        registration.status = 'CANCELLED'
        registration.save()
        
        # Atualiza contador de participantes
        registration.event.current_participants -= 1
        registration.event.save()
        
        # Notifica participante
        EventService.send_cancellation_notification(registration)
    
    @staticmethod
    def mark_attendance(registration):
        """Marca presença do participante"""
        if not registration.event.start_date <= timezone.now() <= registration.event.end_date:
            raise ValueError("Fora do período do evento")
        
        registration.attended = True
        registration.attendance_date = timezone.now()
        registration.status = 'ATTENDED'
        registration.save()
    
    @staticmethod
    def generate_calendar_invite(event):
        """Gera arquivo ICS para o evento"""
        cal = icalendar.Calendar()
        cal.add('prodid', '-//Sistema de Eventos//BR')
        cal.add('version', '2.0')
        
        event_entry = icalendar.Event()
        event_entry.add('summary', event.title)
        event_entry.add('description', event.description)
        event_entry.add('dtstart', event.start_date)
        event_entry.add('dtend', event.end_date)
        
        if event.is_online:
            event_entry.add('location', event.meeting_url)
        else:
            event_entry.add('location', event.location)
        
        cal.add_component(event_entry)
        return cal.to_ical()
    
    @staticmethod
    def send_reminders():
        """Envia lembretes para eventos próximos"""
        tomorrow = timezone.now() + timedelta(days=1)
        upcoming_events = Event.objects.filter(
            start_date__date=tomorrow.date(),
            status='SCHEDULED'
        )
        
        for event in upcoming_events:
            registrations = event.eventregistration_set.filter(
                status='CONFIRMED'
            )
            
            for registration in registrations:
                EventService.send_reminder(registration)
    
    @staticmethod
    def send_registration_confirmation(registration):
        """Envia email de confirmação de inscrição"""
        context = {
            'registration': registration,
            'event': registration.event
        }
        
        message = render_to_string(
            'events/emails/registration_confirmation.html',
            context
        )
        
        # Cria notificação
        notification = EventNotification.objects.create(
            event=registration.event,
            type='CONFIRMATION',
            title='Inscrição Confirmada',
            message=message
        )
        notification.recipients.add(registration.participant)
        
        # Envia email
        send_mail(
            subject=f'Confirmação de Inscrição - {registration.event.title}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registration.participant.email],
            html_message=message
        )
    
    @staticmethod
    def send_reminder(registration):
        """Envia lembrete do evento"""
        context = {
            'registration': registration,
            'event': registration.event
        }
        
        message = render_to_string(
            'events/emails/event_reminder.html',
            context
        )
        
        # Cria notificação
        notification = EventNotification.objects.create(
            event=registration.event,
            type='REMINDER',
            title='Lembrete de Evento',
            message=message
        )
        notification.recipients.add(registration.participant)
        
        # Envia email
        send_mail(
            subject=f'Lembrete - {registration.event.title} amanhã',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registration.participant.email],
            html_message=message
        ) 