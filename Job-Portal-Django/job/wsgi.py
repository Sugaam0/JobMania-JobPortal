import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job.settings')
application = get_wsgi_application()

# ✅ Create superuser using email only
if os.environ.get('RENDER_SUPERUSER') == 'true':
    from django.contrib.auth import get_user_model
    User = get_user_model()

    email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

    if email and password:
        if not User.objects.filter(email=email).exists():
            try:
                User.objects.create_superuser(email=email, password=password)
                print("✅ Superuser created.")
            except Exception as e:
                print(f"❌ Superuser creation failed: {e}")
        else:
            print("ℹ️ Superuser already exists.")
