from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from .models import Discussion, Comment, Message, ChatRoom, Announcement
from .forms import DiscussionForm, CommentForm, MessageForm, AnnouncementForm

class DiscussionListView(LoginRequiredMixin, ListView):
    model = Discussion
    template_name = 'communication/discussion_list.html'
    context_object_name = 'discussions'
    paginate_by = 20
    
    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        queryset = Discussion.objects.filter(course_id=course_id)
        
        # Filtros
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )
            
        filter_by = self.request.GET.get('filter')
        if filter_by == 'my_discussions':
            queryset = queryset.filter(author=self.request.user)
        elif filter_by == 'no_answers':
            queryset = queryset.filter(comment__isnull=True)
        elif filter_by == 'solved':
            queryset = queryset.filter(comment__is_solution=True)
            
        return queryset.distinct()

class DiscussionDetailView(LoginRequiredMixin, DetailView):
    model = Discussion
    template_name = 'communication/discussion_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comment_set.filter(parent=None)
        context['comment_form'] = CommentForm()
        return context
    
    def post(self, request, *args, **kwargs):
        discussion = self.get_object()
        form = CommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.discussion = discussion
            comment.author = request.user
            comment.save()
            
            # Notifica o autor da discussão
            if discussion.author != request.user:
                Notification.objects.create(
                    recipient=discussion.author,
                    title=f"Novo comentário em sua discussão",
                    message=f"{request.user.get_full_name()} comentou em '{discussion.title}'",
                    notification_type='COMMENT'
                )
        
        return redirect('communication:discussion_detail', pk=discussion.pk)

class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'communication/message_list.html'
    context_object_name = 'messages'
    
    def get_queryset(self):
        return Message.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user)
        ).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Message.objects.filter(
            recipient=self.request.user,
            read_at__isnull=True
        ).count()
        return context

class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'communication/message_form.html'
    success_url = reverse_lazy('communication:message_list')
    
    def form_valid(self, form):
        form.instance.sender = self.request.user
        response = super().form_valid(form)
        
        # Notifica o destinatário
        Notification.objects.create(
            recipient=form.instance.recipient,
            title="Nova mensagem",
            message=f"Você recebeu uma mensagem de {self.request.user.get_full_name()}",
            notification_type='MESSAGE'
        )
        
        return response

class ChatRoomView(LoginRequiredMixin, DetailView):
    model = ChatRoom
    template_name = 'communication/chat_room.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = self.object.chatmessage_set.all()
        return context
    
    def post(self, request, *args, **kwargs):
        room = self.get_object()
        message = request.POST.get('message')
        
        if message:
            ChatMessage.objects.create(
                room=room,
                author=request.user,
                content=message
            )
        
        return redirect('communication:chat_room', pk=room.pk)

class AnnouncementCreateView(LoginRequiredMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'communication/announcement_form.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.course_id = self.kwargs['course_id']
        response = super().form_valid(form)
        
        # Notifica todos os alunos do curso
        course = form.instance.course
        for student in course.students.all():
            Notification.objects.create(
                recipient=student,
                title=f"Novo anúncio em {course.title}",
                message=form.instance.title,
                notification_type='ANNOUNCEMENT'
            )
        
        return response 