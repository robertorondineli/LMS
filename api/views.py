from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from .serializers import (
    UserSerializer, CourseSerializer, LessonSerializer,
    EventSerializer, AssessmentSerializer, ContentSerializer
)
from .permissions import IsOwnerOrStaff, IsEnrolledInCourse
from .throttling import UserBurstRateThrottle, UserSustainedRateThrottle
from courses.models import Course, Lesson
from events.models import Event
from assessments.models import Assessment
from content.models import Content
from django_filters.rest_framework import DjangoFilterBackend

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.annotate(
        enrolled_count=Count('enrolled_students')
    )
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [UserBurstRateThrottle]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['category', 'level', 'status']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'enrolled_count', 'price']
    
    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        course = self.get_object()
        user = request.user
        
        if user in course.enrolled_students.all():
            return Response({'detail': 'Já matriculado'}, status=400)
        
        course.enrolled_students.add(user)
        return Response({'detail': 'Matriculado com sucesso'})
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        course = self.get_object()
        user = request.user
        
        if user not in course.enrolled_students.all():
            return Response({'detail': 'Não matriculado'}, status=403)
        
        progress = course.get_user_progress(user)
        return Response(progress)

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type', 'status', 'is_online']
    search_fields = ['title', 'description']
    
    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        event = self.get_object()
        user = request.user
        
        try:
            registration = event.register_participant(user)
            return Response({'detail': 'Registrado com sucesso'})
        except ValueError as e:
            return Response({'detail': str(e)}, status=400)

class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsEnrolledInCourse]
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        assessment = self.get_object()
        answers = request.data.get('answers', [])
        
        try:
            result = assessment.submit_answers(request.user, answers)
            return Response(result)
        except ValueError as e:
            return Response({'detail': str(e)}, status=400)

class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['content_type', 'status']
    search_fields = ['title', 'description']