from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group
from django.dispatch import receiver

@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    # Define the user plans/groups
    plans = ['Free', 'Solo', 'Dev', 'Pro']
    for plan in plans:
        Group.objects.get_or_create(name=plan)
