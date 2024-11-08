from rest_framework import serializers
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson, Module
from events.models import Event, EventRegistration
from assessments.models import Assessment, Question
from content.models import Content

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['date_joined']

class CourseSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    enrolled_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'instructor', 
            'price', 'level', 'category', 'enrolled_count',
            'created_at', 'updated_at', 'status'
        ]

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'content',
            'order', 'duration', 'is_free'
        ]

class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    
    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'lessons']

class EventSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    available_spots = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'type',
            'start_date', 'end_date', 'registration_deadline',
            'max_participants', 'current_participants',
            'is_online', 'location', 'organizer',
            'available_spots', 'status'
        ]

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'description', 'course',
            'time_limit', 'passing_score', 'attempts_allowed',
            'status', 'created_at'
        ]

class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = [
            'id', 'title', 'description', 'content_type',
            'status', 'rich_text', 'media_url', 'tags',
            'created_at', 'updated_at'
        ] 