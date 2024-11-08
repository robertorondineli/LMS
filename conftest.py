import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from courses.models import Course, Module, Lesson
from communication.models import Discussion, Comment
from decimal import Decimal

User = get_user_model()

@pytest.fixture
def user_data():
    return {
        'username': 'testuser',
        'email': 'test@test.com',
        'password': 'testpass123',
        'first_name': 'Test',
        'last_name': 'User'
    }

@pytest.fixture
def user(db, user_data):
    return User.objects.create_user(**user_data)

@pytest.fixture
def instructor(db):
    return User.objects.create_user(
        username='instructor',
        email='instructor@test.com',
        password='testpass123'
    )

@pytest.fixture
def course(db, instructor):
    image = SimpleUploadedFile(
        "course.jpg",
        b"file_content",
        content_type="image/jpeg"
    )
    return Course.objects.create(
        title='Test Course',
        description='Test Description',
        instructor=instructor,
        price=Decimal('99.99'),
        image=image
    )

@pytest.fixture
def module(db, course):
    return Module.objects.create(
        course=course,
        title='Test Module',
        description='Test Module Description'
    )

@pytest.fixture
def lesson(db, module):
    return Lesson.objects.create(
        module=module,
        title='Test Lesson',
        content='Test Lesson Content'
    )

@pytest.fixture
def discussion(db, course, user):
    return Discussion.objects.create(
        course=course,
        author=user,
        title='Test Discussion',
        content='Test Discussion Content'
    )

@pytest.fixture
def comment(db, discussion, user):
    return Comment.objects.create(
        discussion=discussion,
        author=user,
        content='Test Comment Content'
    )

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client 