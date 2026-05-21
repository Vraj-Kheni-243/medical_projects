## VRAJ Care

Django-based doctor appointment booking system with patient registration,
doctor approval workflow, appointment cancellation, and password reset support.

Project screenshots:
https://drive.google.com/drive/folders/1U0dkGqYCfpAh__XIeurLs8ohiXD9cgyw?usp=sharing

## Password Reset Email Setup

Password reset emails are sent through SMTP when these environment variables are set.
For local development, copy `.env.example` to `.env` and fill in your real values:

```text
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-google-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
PUBLIC_SITE_URL=https://medical-projects.onrender.com
```

For Gmail, use a Google App Password, not your normal Gmail password. If the
email variables are missing, Django falls back to the console email backend and
prints reset links in the terminal.

Set `PUBLIC_SITE_URL` to the website address that users can open from their
phone. Do not use `localhost` or `127.0.0.1` for mobile password reset emails.

## Render Deployment

Set these environment variables on Render to create an admin account in the
production PostgreSQL database:

```text
DJANGO_SUPERUSER_USERNAME=your-admin-username
DJANGO_SUPERUSER_EMAIL=your-email@example.com
DJANGO_SUPERUSER_PASSWORD=your-secure-password
```

Use this build command on Render so Django installs dependencies, applies
migrations, creates/updates the production admin account, and collects admin,
Jazzmin, and project static files before the app starts:

```bash
pip install -r requirements.txt && python manage.py migrate && python manage.py create_render_superuser && python manage.py collectstatic --noinput
```

Use this start command:

```bash
gunicorn medical_system.wsgi:application
```

If Render says `Unknown command: 'create_render_superuser'`, the deployment is
missing the `accounts/management/commands/create_render_superuser.py` file.
Commit and push the `accounts/management/` directory to the same branch Render
deploys, then redeploy.
