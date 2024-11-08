from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list'),
    path('curso/<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('curso/<slug:slug>/matricular/', views.CourseEnrollView.as_view(), name='course_enroll'),
    path('curso/<slug:slug>/modulo/<int:module_id>/', views.ModuleDetailView.as_view(), name='module_detail'),
    path('meus-cursos/', views.UserCoursesView.as_view(), name='user_courses'),
    # URLs para instrutores
    path('instrutor/cursos/', views.InstructorCoursesView.as_view(), name='instructor_courses'),
    path('instrutor/curso/novo/', views.CourseCreateView.as_view(), name='course_create'),
    path('instrutor/curso/<slug:slug>/editar/', views.CourseUpdateView.as_view(), name='course_update'),
    path('instrutor/curso/<slug:slug>/modulo/novo/', views.ModuleCreateView.as_view(), name='module_create'),
    path('modulo/<int:module_id>/conteudo/novo/', views.ContentCreateView.as_view(), name='content_create'),
    path('modulo/<int:module_id>/conteudo/ordem/', views.ContentOrderView.as_view(), name='content_order'),
    path('curso/<slug:slug>/matricular/', views.CourseEnrollmentView.as_view(), name='course_enroll'),
    path('conteudo/<int:content_id>/concluir/', views.ContentCompleteView.as_view(), name='content_complete'),
] 