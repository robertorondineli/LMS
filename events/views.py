from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Event, EventRegistration, EventFeedback
from .services import EventService
from .forms import EventForm, EventRegistrationForm, FeedbackForm
from datetime import datetime
import pytz

class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Event.objects.filter(status='SCHEDULED')
        
        # Filtros
        event_type = self.request.GET.get('type')
        if event_type:
            queryset = queryset.filter(type=event_type)
        
        date_filter = self.request.GET.get('date')
        if date_filter:
            if date_filter == 'today':
                queryset = queryset.filter(start_date__date=datetime.now().date())
            elif date_filter == 'week':
                queryset = queryset.filter(
                    start_date__date__range=[
                        datetime.now().date(),
                        datetime.now().date() + timedelta(days=7)
                    ]
                )
            elif date_filter == 'month':
                queryset = queryset.filter(
                    start_date__date__range=[
                        datetime.now().date(),
                        datetime.now().date() + timedelta(days=30)
                    ]
                )
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(description__icontains=search)
            )
        
        return queryset.select_related('organizer')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['upcoming_events'] = Event.objects.filter(
            status='SCHEDULED',
            start_date__gt=datetime.now()
        ).order_by('start_date')[:5]
        return context

class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['user_registration'] = EventRegistration.objects.filter(
                event=self.object,
                participant=self.request.user
            ).first()
        return context

class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    success_url = reverse_lazy('event_list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        form.instance.organizer = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Evento criado com sucesso!')
        return response

class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    
    def test_func(self):
        event = self.get_object()
        return self.request.user == event.organizer or self.request.user.is_staff
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Evento atualizado com sucesso!')
        return response

class EventRegistrationView(LoginRequiredMixin, CreateView):
    model = EventRegistration
    form_class = EventRegistrationForm
    template_name = 'events/registration_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = get_object_or_404(Event, pk=self.kwargs['event_id'])
        return context
    
    def form_valid(self, form):
        event = get_object_or_404(Event, pk=self.kwargs['event_id'])
        try:
            registration = EventService.register_participant(
                event,
                self.request.user
            )
            messages.success(self.request, 'Inscrição realizada com sucesso!')
            return redirect('event_detail', pk=event.pk)
        except ValueError as e:
            messages.error(self.request, str(e))
            return redirect('event_detail', pk=event.pk)

class EventFeedbackView(LoginRequiredMixin, CreateView):
    model = EventFeedback
    form_class = FeedbackForm
    template_name = 'events/feedback_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = get_object_or_404(Event, pk=self.kwargs['event_id'])
        return context
    
    def form_valid(self, form):
        event = get_object_or_404(Event, pk=self.kwargs['event_id'])
        form.instance.event = event
        form.instance.participant = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Feedback enviado com sucesso!')
        return response

class EventCalendarView(View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        calendar_data = EventService.generate_calendar_invite(event)
        
        response = HttpResponse(calendar_data, content_type='text/calendar')
        response['Content-Disposition'] = f'attachment; filename="{event.slug}.ics"'
        return response

class EventAttendanceView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        event = get_object_or_404(Event, pk=self.kwargs['event_id'])
        return self.request.user == event.organizer or self.request.user.is_staff
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        participant_id = request.POST.get('participant_id')
        
        registration = get_object_or_404(
            EventRegistration,
            event=event,
            participant_id=participant_id
        )
        
        try:
            EventService.mark_attendance(registration)
            messages.success(request, 'Presença registrada com sucesso!')
        except ValueError as e:
            messages.error(request, str(e))
        
        return redirect('event_detail', pk=event_id) 