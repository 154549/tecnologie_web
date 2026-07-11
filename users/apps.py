from django.apps import AppConfig
from django.db.models.signals import post_migrate


#post_migrate si attiva da solo subito dopo ogni "manage.py migrate"
#a differenza dell'import di urls.py, a questo punto le tabelle esistono di sicuro
def seed_initial_data(sender, **kwargs):
    from DjangBook.initcmds import init_db
    init_db()


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        post_migrate.connect(seed_initial_data, sender=self)
