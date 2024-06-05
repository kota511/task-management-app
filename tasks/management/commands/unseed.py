from django.core.management.base import BaseCommand, CommandError
from tasks.models import User, Team, Task, Invitation

class Command(BaseCommand):
    """Build automation command to unseed the database."""
    
    help = 'Seeds the database with sample data'

    def handle(self, *args, **options):
        """Unseed the database."""

        Task.objects.filter().delete()
        Invitation.objects.filter().delete()
        Team.objects.filter().delete()
        User.objects.filter(is_staff=False).delete()