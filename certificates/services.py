from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Certificate, Badge, UserBadge
import hashlib

class CertificateService:
    @staticmethod
    def generate_verification_code(certificate):
        # Gera um código único de verificação
        data = f"{certificate.id}{certificate.user.id}{certificate.issued_at}"
        return hashlib.sha256(data.encode()).hexdigest()[:50]
    
    @staticmethod
    def issue_certificate(user, course, type='COMPLETION'):
        # Verifica se o usuário completou o curso
        if type == 'COMPLETION' and not course.is_completed(user):
            raise ValueError("Usuário não completou o curso")
        
        # Cria o certificado
        certificate = Certificate.objects.create(
            user=user,
            course=course,
            type=type,
            title=f"Certificado de {dict(Certificate.TYPES)[type].lower()}",
            description=f"Certificado de {dict(Certificate.TYPES)[type].lower()} " \
                       f"do curso {course.title}",
            verification_code=CertificateService.generate_verification_code(certificate)
        )
        
        # Gera a imagem do certificado
        certificate.generate_certificate()
        certificate.save()
        
        # Envia email com o certificado
        CertificateService.send_certificate_email(certificate)
        
        return certificate
    
    @staticmethod
    def verify_certificate(verification_code):
        try:
            return Certificate.objects.get(verification_code=verification_code)
        except Certificate.DoesNotExist:
            return None
    
    @staticmethod
    def send_certificate_email(certificate):
        context = {
            'user': certificate.user,
            'certificate': certificate,
            'verification_url': f'https://seusite.com/certificates/verify/{certificate.verification_code}'
        }
        
        html_message = render_to_string('certificates/email/certificate.html', context)
        
        send_mail(
            subject='Seu Certificado está pronto!',
            message='',
            from_email='noreply@seusite.com',
            recipient_list=[certificate.user.email],
            html_message=html_message
        )

class BadgeService:
    @staticmethod
    def check_user_badges(user):
        # Verifica todas as badges disponíveis
        badges = Badge.objects.all()
        earned_badges = []
        
        for badge in badges:
            user_badge, created = UserBadge.objects.get_or_create(
                user=user,
                badge=badge
            )
            
            if not created and user_badge.earned_at:
                continue
            
            if badge.check_requirements(user):
                user_badge.earned_at = timezone.now()
                user_badge.save()
                earned_badges.append(user_badge)
                
                # Adiciona pontos ao usuário
                user.profile.add_points(badge.points)
        
        return earned_badges
    
    @staticmethod
    def get_user_progress(user, badge):
        user_badge = UserBadge.objects.filter(user=user, badge=badge).first()
        if not user_badge:
            return 0
        
        total_requirements = len(badge.requirements)
        completed_requirements = sum(
            1 for req in badge.requirements 
            if user_badge.progress.get(req['id'], 0) >= req['value']
        )
        
        return (completed_requirements / total_requirements) * 100 