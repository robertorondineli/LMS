from django.db import models
from django.conf import settings
from courses.models import Course
from django.template.loader import render_to_string
from django.utils import timezone
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import uuid

class Certificate(models.Model):
    TYPES = [
        ('COMPLETION', 'Conclusão de Curso'),
        ('ACHIEVEMENT', 'Conquista Especial'),
        ('PARTICIPATION', 'Participação'),
        ('EXCELLENCE', 'Excelência')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPES)
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='certificates/')
    verification_code = models.CharField(max_length=50, unique=True)
    
    def generate_certificate(self):
        # Carrega o template do certificado
        template = Image.open('static/images/certificate_template.png')
        draw = ImageDraw.Draw(template)
        
        # Carrega fontes
        title_font = ImageFont.truetype('static/fonts/Montserrat-Bold.ttf', 60)
        text_font = ImageFont.truetype('static/fonts/Montserrat-Regular.ttf', 30)
        
        # Adiciona textos
        draw.text((template.width/2, 300), self.title, 
                 font=title_font, fill='black', anchor='mm')
        draw.text((template.width/2, 400), 
                 f"Concedido a {self.user.get_full_name()}", 
                 font=text_font, fill='black', anchor='mm')
        draw.text((template.width/2, 500), self.description, 
                 font=text_font, fill='black', anchor='mm')
        draw.text((template.width/2, 600), 
                 f"Emitido em {self.issued_at.strftime('%d/%m/%Y')}", 
                 font=text_font, fill='black', anchor='mm')
        
        # Gera QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f'https://seusite.com/certificates/verify/{self.verification_code}')
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Adiciona QR Code ao certificado
        template.paste(qr_img, (template.width - 200, template.height - 200))
        
        # Salva o certificado
        buffer = BytesIO()
        template.save(buffer, format='PNG')
        self.image.save(f'certificate_{self.id}.png', 
                       BytesIO(buffer.getvalue()), 
                       save=False)
        
        return self.image

class Badge(models.Model):
    LEVELS = [
        ('BRONZE', 'Bronze'),
        ('SILVER', 'Prata'),
        ('GOLD', 'Ouro'),
        ('DIAMOND', 'Diamante')
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    level = models.CharField(max_length=20, choices=LEVELS)
    icon = models.ImageField(upload_to='badges/')
    requirements = models.JSONField()
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def check_requirements(self, user):
        # Implementa lógica de verificação dos requisitos
        pass

class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    progress = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ['user', 'badge'] 