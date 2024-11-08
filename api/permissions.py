from rest_framework import permissions

class IsOwnerOrStaff(permissions.BasePermission):
    """
    Permite acesso apenas ao proprietário ou staff
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff

class IsEnrolledInCourse(permissions.BasePermission):
    """
    Permite acesso apenas a alunos matriculados
    """
    def has_object_permission(self, request, view, obj):
        return request.user in obj.course.enrolled_students.all() 