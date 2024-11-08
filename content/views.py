from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from .models import Content, ContentVersion, ContentReview
from .services import ContentService
from .forms import ContentForm, ImportForm
import json

class ContentListView(LoginRequiredMixin, ListView):
    model = Content
    template_name = 'content/content_list.html'
    context_object_name = 'contents'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Content.objects.all()
        
        # Filtros
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        content_type = self.request.GET.get('type')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        return queryset.select_related('author')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_counts'] = {
            status: Content.objects.filter(status=status).count()
            for status, _ in Content.STATUS
        }
        return context

class ContentDetailView(LoginRequiredMixin, DetailView):
    model = Content
    template_name = 'content/content_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['versions'] = self.object.versions.all()[:5]
        context['reviews'] = self.object.reviews.all()
        context['comments'] = self.object.comments.filter(parent=None)
        return context

class ContentCreateView(LoginRequiredMixin, CreateView):
    model = Content
    form_class = ContentForm
    template_name = 'content/content_form.html'
    success_url = reverse_lazy('content_list')
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class ContentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Content
    form_class = ContentForm
    template_name = 'content/content_form.html'
    
    def test_func(self):
        content = self.get_object()
        return self.request.user == content.author or self.request.user.is_staff
    
    def form_valid(self, form):
        content = form.save(commit=False)
        ContentService.update_content(
            content,
            form.cleaned_data,
            self.request.user
        )
        return super().form_valid(form)

class ContentVersionView(LoginRequiredMixin, DetailView):
    model = ContentVersion
    template_name = 'content/content_version.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_version = self.object
        previous_version = ContentVersion.objects.filter(
            content=current_version.content,
            version_number=current_version.version_number - 1
        ).first()
        
        if previous_version:
            context['diff'] = ContentService.compare_versions(
                previous_version,
                current_version
            )
        
        return context

class ContentReviewView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ContentReview
    template_name = 'content/content_review.html'
    fields = ['status', 'comments']
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        review = form.save(commit=False)
        ContentService.review_content(
            review.content,
            self.request.user,
            review.status,
            review.comments
        )
        return super().form_valid(form)

class ContentImportView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = 'content/content_import.html'
    form_class = ImportForm
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        try:
            imported_content = ContentService.import_content(
                form.cleaned_data['file'],
                form.cleaned_data['format'],
                self.request.user
            )
            messages.success(
                self.request,
                f'Importados {len(imported_content)} itens com sucesso!'
            )
            return redirect('content_list')
        except Exception as e:
            messages.error(self.request, f'Erro na importação: {str(e)}')
            return self.form_invalid(form)

class ContentExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff
    
    def get(self, request):
        content_ids = request.GET.getlist('ids')
        format = request.GET.get('format', 'json')
        
        try:
            data = ContentService.export_content(content_ids, format)
            
            if format == 'json':
                response = HttpResponse(
                    data,
                    content_type='application/json'
                )
                filename = 'content_export.json'
            elif format == 'csv':
                response = HttpResponse(
                    data,
                    content_type='text/csv'
                )
                filename = 'content_export.csv'
            
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            messages.error(request, f'Erro na exportação: {str(e)}')
            return redirect('content_list') 