import os
from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    """
    Creates a superuser non-interactively from environment variables, if one
    doesn't already exist. Safe to run on every deploy (idempotent) — this
    is how we create the first admin account on platforms like Render's
    free tier, which doesn't provide interactive shell access.
    """
    help = 'Creates a superuser from DJANGO_SUPERUSER_* env vars if none exists.'

    def handle(self, *args, **options):
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not all([email, username, password]):
            self.stdout.write('DJANGO_SUPERUSER_* env vars not set — skipping.')
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(f'Superuser {email} already exists — skipping.')
            return

        User.objects.create_superuser(
            username=username, email=email, password=password,
            role='hospital_admin',
        )
        self.stdout.write(self.style.SUCCESS(f'Superuser {email} created successfully.'))
