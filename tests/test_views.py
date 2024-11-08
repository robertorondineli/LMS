from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from courses.models import Course, Module, Lesson
from communication.models import Discussion
from decimal import Decimal

User = get_user_model()

class CourseViewTests(TestCase):
    def setUp(self):
        self.client = Client()
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
            description='Test Description',
            instructor=self.instructor,
            price=Decimal('99.99')
        )
    
    def test_course_list_view(self):
        response = self.client.get(reverse('courses:course_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/course_list.html')
        self.assertContains(response, 'Test Course')
    
    def test_course_detail_view(self):
        response = self.client.get(
            reverse('courses:course_detail', kwargs={'slug': self.course.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/course_detail.html')
        self.assertContains(response, 'Test Course')
    
    def test_enroll_course(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('courses:enroll_course', kwargs={'course_id': self.course.id})
        )
        self.assertEqual(response.status_code, 302)  # Redirect after enrollment
        self.assertTrue(self.course.students.filter(id=self.user.id).exists())

class DiscussionViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            instructor=self.user
        )
        
        self.discussion = Discussion.objects.create(
            course=self.course,
            author=self.user,
            title='Test Discussion',
            content='Test Content'
        )
    
    def test_discussion_list_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('communication:discussion_list', kwargs={'course_id': self.course.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'communication/discussion_list.html')
        self.assertContains(response, 'Test Discussion')
    
    def test_create_discussion(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('communication:create_discussion', kwargs={'course_id': self.course.id}),
            {
                'title': 'New Discussion',
                'content': 'New Content'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(
            Discussion.objects.filter(title='New Discussion').exists()
        ) 