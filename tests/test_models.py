from django.test import TestCase
from django.contrib.auth import get_user_model
from courses.models import Course, Module, Lesson
from communication.models import Discussion, Comment
from analytics.models import UserActivity
from django.utils import timezone
from decimal import Decimal
import pytest

User = get_user_model()

class CourseModelTests(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            username='instructor',
            email='instructor@test.com',
            password='testpass123'
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            instructor=self.instructor,
            price=Decimal('99.99')
        )
        
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123'
        )
    
    def test_course_creation(self):
        self.assertEqual(self.course.title, 'Test Course')
        self.assertEqual(self.course.instructor, self.instructor)
        self.assertEqual(self.course.students.count(), 0)
    
    def test_enroll_student(self):
        self.course.enroll_student(self.student)
        self.assertEqual(self.course.students.count(), 1)
        self.assertTrue(self.course.is_enrolled(self.student))
    
    def test_course_progress(self):
        self.course.enroll_student(self.student)
        module = Module.objects.create(
            course=self.course,
            title='Test Module'
        )
        lesson = Lesson.objects.create(
            module=module,
            title='Test Lesson'
        )
        
        # Inicialmente 0%
        self.assertEqual(self.course.get_progress(self.student), 0)
        
        # Marca lição como completa
        lesson.mark_completed(self.student)
        self.assertEqual(self.course.get_progress(self.student), 100)

    @pytest.mark.slow
    def test_heavy_operation(self):
        ...

    @pytest.mark.integration
    def test_api_integration(self):
        ...

class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@test.com')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
    
    def test_get_full_name(self):
        self.assertEqual(self.user.get_full_name(), 'Test User')
    
    def test_enrolled_courses(self):
        instructor = User.objects.create_user(
            username='instructor',
            email='instructor@test.com',
            password='testpass123'
        )
        
        course = Course.objects.create(
            title='Test Course',
            instructor=instructor
        )
        
        course.enroll_student(self.user)
        self.assertEqual(self.user.enrolled_courses.count(), 1)

class DiscussionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.instructor = User.objects.create_user(
            username='instructor',
            email='instructor@test.com',
            password='testpass123'
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            instructor=self.instructor
        )
        
        self.discussion = Discussion.objects.create(
            course=self.course,
            author=self.user,
            title='Test Discussion',
            content='Test Content'
        )
    
    def test_discussion_creation(self):
        self.assertEqual(self.discussion.title, 'Test Discussion')
        self.assertEqual(self.discussion.author, self.user)
    
    def test_add_comment(self):
        comment = Comment.objects.create(
            discussion=self.discussion,
            author=self.user,
            content='Test Comment'
        )
        
        self.assertEqual(self.discussion.comment_set.count(), 1)
        self.assertEqual(comment.content, 'Test Comment') 