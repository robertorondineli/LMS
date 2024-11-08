from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from courses.models import Course
from communication.models import Discussion
from decimal import Decimal

User = get_user_model()

class CourseAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            instructor=self.user,
            price=Decimal('99.99')
        )
    
    def test_get_course_list(self):
        response = self.client.get(reverse('api:course-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Course')
    
    def test_create_course(self):
        data = {
            'title': 'New Course',
            'description': 'New Description',
            'price': '149.99'
        }
        response = self.client.post(reverse('api:course-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 2)
    
    def test_enroll_course(self):
        url = reverse('api:course-enroll', kwargs={'pk': self.course.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.course.students.filter(id=self.user.id).exists())

class UserAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_user_profile(self):
        response = self.client.get(
            reverse('api:user-detail', kwargs={'pk': self.user.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
    
    def test_update_user_profile(self):
        data = {
            'first_name': 'Updated',
            'last_name': 'User'
        }
        response = self.client.patch(
            reverse('api:user-detail', kwargs={'pk': self.user.id}),
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

class DiscussionAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
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
    
    def test_get_discussions(self):
        response = self.client.get(reverse('api:discussion-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_create_discussion(self):
        data = {
            'course': self.course.id,
            'title': 'New Discussion',
            'content': 'New Content'
        }
        response = self.client.post(reverse('api:discussion-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Discussion.objects.count(), 2) 