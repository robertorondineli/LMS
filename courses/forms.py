from django import forms
from .models import Course, Module, Content

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'departments', 'is_mandatory', 'thumbnail']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'departments': forms.SelectMultiple(attrs={'class': 'select2'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        
        # Adiciona classes específicas para campos especiais
        self.fields['is_mandatory'].widget.attrs['class'] = 'form-check-input'
        self.fields['thumbnail'].widget.attrs['class'] = 'form-control-file'

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class ContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['title', 'content_type', 'content', 'file', 'order']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        
        self.fields['file'].widget.attrs['class'] = 'form-control-file'
        
    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        content = cleaned_data.get('content')
        file = cleaned_data.get('file')
        
        if content_type in ['VIDEO', 'PDF'] and not file:
            raise forms.ValidationError(
                f"Um arquivo é obrigatório para conteúdo do tipo {content_type}"
            )
        
        if content_type == 'TEXT' and not content:
            raise forms.ValidationError(
                "O conteúdo é obrigatório para tipo TEXT"
            )
        
        return cleaned_data 