from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.views import View
from .models import Course, Module, Content, Enrollment
from .forms import CourseForm, ModuleForm, ContentForm

class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 12

    def get_queryset(self):
        queryset = Course.objects.all()
        if self.request.user.is_authenticated:
            if self.request.user.role == 'STUDENT':
                return queryset.filter(departments__contains=self.request.user.department)
        return queryset

class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['is_enrolled'] = Enrollment.objects.filter(
                student=self.request.user,
                course=self.object
            ).exists()
        return context

class CourseEnrollView(LoginRequiredMixin, CreateView):
    model = Enrollment
    fields = []
    
    def form_valid(self, form):
        course = get_object_or_404(Course, slug=self.kwargs['slug'])
        if Enrollment.objects.filter(student=self.request.user, course=course).exists():
            messages.warning(self.request, 'Você já está matriculado neste curso.')
            return redirect('courses:course_detail', slug=course.slug)
            
        enrollment = form.save(commit=False)
        enrollment.student = self.request.user
        enrollment.course = course
        enrollment.save()
        messages.success(self.request, 'Matrícula realizada com sucesso!')
        return redirect('courses:module_detail', slug=course.slug, module_id=course.modules.first().id)

class ModuleDetailView(LoginRequiredMixin, DetailView):
    model = Module
    template_name = 'courses/module_detail.html'
    context_object_name = 'module'

    def get_object(self):
        return get_object_or_404(
            Module,
            id=self.kwargs['module_id'],
            course__slug=self.kwargs['slug']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object.course
        context['course'] = course
        context['modules'] = course.modules.all()
        return context

class InstructorCoursesView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Course
    template_name = 'courses/instructor/course_list.html'
    context_object_name = 'courses'

    def test_func(self):
        return self.request.user.role == 'INSTRUCTOR'

    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)

class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/instructor/course_form.html'
    
    def test_func(self):
        return self.request.user.role == 'INSTRUCTOR'
    
    def form_valid(self, form):
        form.instance.instructor = self.request.user
        messages.success(self.request, 'Curso criado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('courses:course_detail', kwargs={'slug': self.object.slug})

class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/instructor/course_form.html'
    
    def test_func(self):
        course = self.get_object()
        return self.request.user == course.instructor
    
    def form_valid(self, form):
        messages.success(self.request, 'Curso atualizado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('courses:course_detail', kwargs={'slug': self.object.slug})

class ModuleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Module
    form_class = ModuleForm
    template_name = 'courses/instructor/module_form.html'
    
    def test_func(self):
        course = get_object_or_404(Course, slug=self.kwargs['course_slug'])
        return self.request.user == course.instructor
    
    def form_valid(self, form):
        course = get_object_or_404(Course, slug=self.kwargs['course_slug'])
        form.instance.course = course
        messages.success(self.request, 'Módulo criado com sucesso!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, slug=self.kwargs['course_slug'])
        return context

class ContentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Content
    form_class = ContentForm
    template_name = 'courses/instructor/content_form.html'
    
    def test_func(self):
        module = get_object_or_404(Module, id=self.kwargs['module_id'])
        return self.request.user == module.course.instructor
    
    def form_valid(self, form):
        module = get_object_or_404(Module, id=self.kwargs['module_id'])
        form.instance.module = module
        messages.success(self.request, 'Conteúdo adicionado com sucesso!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module'] = get_object_or_404(Module, id=self.kwargs['module_id'])
        return context

class ContentOrderView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        module = get_object_or_404(Module, id=self.kwargs['module_id'])
        return self.request.user == module.course.instructor
    
    def post(self, request, *args, **kwargs):
        content_ids = request.POST.getlist('content[]')
        for order, content_id in enumerate(content_ids, 1):
            Content.objects.filter(id=content_id).update(order=order)
        return JsonResponse({'status': 'ok'})

class CourseEnrollmentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        course = get_object_or_404(Course, slug=kwargs['slug'])
        
        # Verifica se já está matriculado
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            messages.warning(request, 'Você já está matriculado neste curso.')
            return redirect('courses:course_detail', slug=course.slug)
        
        # Cria a matrícula
        Enrollment.objects.create(
            student=request.user,
            course=course
        )
        
        messages.success(request, 'Matrícula realizada com sucesso!')
        return redirect('courses:course_detail', slug=course.slug)

class ContentCompleteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        content = get_object_or_404(Content, id=kwargs['content_id'])
        enrollment = get_object_or_404(
            Enrollment,
            course=content.module.course,
            student=request.user
        )
        
        # Marca o conteúdo como concluído
        enrollment.completed_contents.add(content)
        
        # Atualiza o progresso
        total_contents = Content.objects.filter(
            module__course=content.module.course
        ).count()
        completed_contents = enrollment.completed_contents.count()
        
        progress = (completed_contents / total_contents) * 100
        enrollment.progress = progress
        
        if progress == 100:
            enrollment.completed = True
        
        enrollment.save()
        
        return JsonResponse({
            'status': 'ok',
            'progress': progress
        })