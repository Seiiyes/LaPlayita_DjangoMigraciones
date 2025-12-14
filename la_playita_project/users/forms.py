from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from .models import Usuario, Rol
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
import os
from email.mime.image import MIMEImage


class VendedorRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'telefono')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Documento"
        self.fields['first_name'].label = "Nombres"
        self.fields['last_name'].label = "Apellidos"
        self.fields['email'].label = "Correo Electrónico"
        self.fields['telefono'].label = "Teléfono"

    def save(self, commit=True):
        user = super().save(commit=False)
        # Asignar rol 'Vendedor' por defecto al registrarse
        user.rol = Rol.objects.get(nombre='Vendedor')
        if commit:
            user.save()
        return user


class CustomPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        """Given an email, return matching user(s) who should receive a reset."""
        return Usuario.objects.filter(
            email__iexact=email,
            estado__in=['activo', 'inactivo'],
        )

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.txt',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        """
        Generates a one-use only link for resetting password and sends to the user.
        """
        email = self.cleaned_data["email"]
        for user in self.get_users(email):
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            
            context = {
                'email': email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
            }
            if extra_email_context is not None:
                context.update(extra_email_context)

            # Render email body to a string
            body = render_to_string(email_template_name, context)
            
            # Create the email, and attach the HTML version
            subject = render_to_string(subject_template_name, context)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            
            from_email = settings.DEFAULT_FROM_EMAIL
            
            msg = EmailMultiAlternatives(subject, body, from_email, [email])
            
            if html_email_template_name:
                html_body = render_to_string(html_email_template_name, context)
                msg.attach_alternative(html_body, "text/html")

                # Attach image
                image_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'core', 'img', 'la-playita-logo.png')
                try:
                    with open(image_path, 'rb') as f:
                        logo_image = MIMEImage(f.read())
                        logo_image.add_header('Content-ID', '<logo>')
                        msg.attach(logo_image)
                except FileNotFoundError:
                    # Handle case where image is not found, maybe log it
                    pass

            msg.send()