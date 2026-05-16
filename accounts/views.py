from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetView
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.http import urlsafe_base64_decode
from django.views import View
import logging
from urllib.parse import urlparse

from .forms import SimpleSetPasswordForm, VisibleFailurePasswordResetForm


logger = logging.getLogger(__name__)


# ================= REGISTER =================
def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if not username or not email or not password1 or not password2:
            messages.error(request, "All fields are required")
            return redirect('register')

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        user.save()

        messages.success(request, "Account created successfully. Please login.")
        return redirect('login')

    return render(request, "accounts/register.html")


# ================= LOGIN =================
def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('book_appointment')

        else:
            messages.error(request, "Invalid username or password")
            return redirect('login')

    return render(request, "accounts/login.html")


# ================= LOGOUT =================
def user_logout(request):
    logout(request)
    request.session.flush() 
    return redirect('/')


class VrajCarePasswordResetView(PasswordResetView):
    form_class = VisibleFailurePasswordResetForm
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.txt'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    from_email = settings.DEFAULT_FROM_EMAIL

    def form_valid(self, form):
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            messages.warning(
                self.request,
                'Email is not configured yet. The reset link was printed in the server terminal instead of being sent to an inbox.'
            )

        # Determine protocol and domain for the reset link.
        # PUBLIC_SITE_URL takes priority (needed for Render where the proxy
        # terminates TLS and request.is_secure() may return False).
        if settings.PUBLIC_SITE_URL:
            public_site = urlparse(settings.PUBLIC_SITE_URL)
            use_https = public_site.scheme == 'https'
            domain_override = public_site.netloc
        else:
            # Fall back to the forwarded proto header set by SECURE_PROXY_SSL_HEADER.
            use_https = self.request.is_secure()
            domain_override = None

        opts = {
            'use_https': use_https,
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': self.extra_email_context,
        }
        if domain_override:
            opts['domain_override'] = domain_override

        logger.info(
            'Password reset requested for email=%s use_https=%s domain=%s',
            form.cleaned_data.get('email'),
            use_https,
            domain_override,
        )

        try:
            form.save(**opts)
            logger.info('Password reset email dispatched successfully.')
            return redirect(self.get_success_url())
        except Exception:
            logger.exception(
                'Password reset email FAILED — BREVO_API_KEY or anymail error. '
                'Check Render env vars and anymail logs above.'
            )
            messages.error(
                self.request,
                'Password reset email could not be sent. Please try again later.'
            )
            return self.form_invalid(form)


class VrajCarePasswordResetConfirmView(View):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    token_generator = default_token_generator

    def get_user(self, uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            return User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None

    def dispatch(self, request, *args, **kwargs):
        self.user = self.get_user(kwargs.get('uidb64'))
        self.token = kwargs.get('token')
        self.validlink = (
            self.user is not None
            and self.token_generator.check_token(self.user, self.token)
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = SimpleSetPasswordForm(self.user) if self.validlink else None
        return render(request, self.template_name, {
            'form': form,
            'validlink': self.validlink,
        })

    def post(self, request, *args, **kwargs):
        if not self.validlink:
            messages.error(request, 'This password reset link is invalid or has expired.')
            return render(request, self.template_name, {
                'form': None,
                'validlink': False,
                'reset_error': 'This password reset link is invalid or has expired.',
            })

        form = SimpleSetPasswordForm(self.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your password has been changed. You can login now.')
            return render(request, 'accounts/password_reset_complete.html')

        messages.error(
            request,
            'Password was not changed. Please fix the password errors shown below.'
        )
        return render(request, self.template_name, {
            'form': form,
            'validlink': True,
            'reset_error': 'Password was not changed. Check both password boxes below.',
        })
