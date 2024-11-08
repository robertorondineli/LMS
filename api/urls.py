from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.documentation import include_docs_urls
from .views import (
    CourseViewSet, EventViewSet,
    AssessmentViewSet, ContentViewSet
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'events', EventViewSet)
router.register(r'assessments', AssessmentViewSet)
router.register(r'content', ContentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    path('docs/', include_docs_urls(
        title='API Documentation',
        description='RESTful API para o sistema de aprendizado'
    )),
] 