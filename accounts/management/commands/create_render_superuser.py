import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create or update a production superuser from environment variables.'

    def handle(self, *args, **options):
        username = (
            os.getenv('DJANGO_SUPERUSER_USERNAME')
            or os.getenv('ADMIN_USERNAME')
        )
        email = (
            os.getenv('DJANGO_SUPERUSER_EMAIL')
            or os.getenv('ADMIN_EMAIL')
            or ''
        )
        password = (
            os.getenv('DJANGO_SUPERUSER_PASSWORD')
            or os.getenv('ADMIN_PASSWORD')
        )

        if not username:
            raise CommandError(
                'Set DJANGO_SUPERUSER_USERNAME or ADMIN_USERNAME before '
                'running create_render_superuser.'
            )

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True,
            },
        )

        changed_fields = []

        if email and user.email != email:
            user.email = email
            changed_fields.append('email')

        if not user.is_staff:
            user.is_staff = True
            changed_fields.append('is_staff')

        if not user.is_superuser:
            user.is_superuser = True
            changed_fields.append('is_superuser')

        if created:
            if not password:
                user.delete()
                raise CommandError(
                    'Set DJANGO_SUPERUSER_PASSWORD or ADMIN_PASSWORD to '
                    'create the production superuser.'
                )
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created production superuser '{username}'."
                )
            )
            return

        if password:
            user.set_password(password)
            changed_fields.append('password')

        if changed_fields:
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Updated production superuser '{username}'."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Production superuser '{username}' already exists."
                )
            )
