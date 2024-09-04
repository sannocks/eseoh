from django.apps import AppConfig

class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        # Import signals inside the ready() method to avoid AppRegistryNotReady error
        import users.signals
