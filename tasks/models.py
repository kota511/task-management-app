from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from libgravatar import Gravatar

class User(AbstractUser):
    """Model used for user authentication, and team member related information."""

    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[RegexValidator(
            regex=r'^@\w{3,}$',
            message='Username must consist of @ followed by at least three alphanumericals'
        )]
    )
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    email = models.EmailField(unique=True, blank=False)


    class Meta:
        """Model options."""

        ordering = ['last_name', 'first_name']

    def full_name(self):
        """Return a string containing the user's full name."""

        return f'{self.first_name} {self.last_name}'

    def gravatar(self, size=120):
        """Return a URL to the user's gravatar."""

        gravatar_object = Gravatar(self.email)
        gravatar_url = gravatar_object.get_image(size=size, default='mp')
        return gravatar_url

    def mini_gravatar(self):
        """Return a URL to a miniature version of the user's gravatar."""
        
        return self.gravatar(size=60)

class Team(models.Model):
    """Model used for a team"""
    name = models.CharField(
        max_length=50, 
        blank=False, 
        validators=[RegexValidator(
            regex=r'^.*[a-zA-Z].*$',
            message='Team name must contain at least one letter.'
        )]
    )
    description = models.CharField(blank=True, max_length=500)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    members = models.ManyToManyField(User, blank=True, related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)

    def remove_member(self, username):
        """Remove member from the team"""
        user = User.objects.get(username=username)
        if user in self.members.all():
            if self.owner == user:
                return False
            else:
                self.remove_task(username)
                self.members.remove(user)
                return True
        else:
            return False
    
    def delete_team(self, user):
        """Delete the team"""
        if self.owner == user:
            self.delete()
            return True
        else:
            return False
    
    def send_invitation(self, sender_username, recipient_username, message=None):
        """Send an invitation to join the team."""
        sender = User.objects.get(username=sender_username)
        recipient = User.objects.get(username=recipient_username)
        if self.members.filter(id=recipient.id).exists():
            return False
        if message is None:
            message = ""
        Invitation.objects.create(
            sender=sender,
            recipient=recipient,
            team=self,
            message=message
        )
        return True

    @classmethod
    def create_team(cls, name, description, owner, members=None, message=None):
        """Create a new team and add members."""
        team = cls(name=name, description=description, owner=owner)
        team.save()
        if members:
            for member in members:
                team.send_invitation(owner, member, message)
        team.members.add(owner)
        return team
    
    def __str__(self):
        """Return a string representation of the model."""
        return self.name
    
    @classmethod
    def edit_team(cls, pk, owner_username, new_name, new_description, members=None, message=None, remove_members=None):
        """Edit name and description of the team"""
        owner = User.objects.get(username=owner_username)
        team = cls.objects.get(id=pk)
        team.name = new_name
        team.description = new_description
        if members:
            for member in members:
                team.send_invitation(owner, member, message)
        if remove_members:
            for member in remove_members:
                team.remove_member(member)
        team.save()
        return team
    
    def remove_task(self, member):
        tasks = Task.objects.filter(assigned_to=member.id).filter(team=self.id)
        for task in tasks:
            task.delete()

class Invitation(models.Model):
    """Model used to keep track of invitations sent between users."""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations', null=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations', null=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False)
    message = models.CharField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Model Options."""
        unique_together = ['recipient', 'team']
        ordering = ['created_at']

    def accept_invitation(self, user):
        if user != self.recipient:
            raise PermissionDenied("Only the recipient can accept this invitation.")
        
        self.team.members.add(self.recipient)
        self.delete()

    def decline_invitation(self, user):
        if user != self.recipient:
            raise PermissionDenied("Only the recipient can decline this invitation.")
        
        self.delete()
    
    def clean(self):
        super().clean() 

        if self.sender != self.team.owner:
            raise ValidationError("The sender must be the team owner.")
        if self.sender.username == self.recipient.username:
            raise ValidationError("Sender and recipient cannot be the same user.")
        if self.recipient in self.team.members.all():
            raise ValidationError("The recipient is already a part of this team.")
        
class Task(models.Model):
    """Model used for a task"""
    class TaskStatus(models.TextChoices):
        NOT_STARTED = 'Not Started', 'Not Started'
        IN_PROGRESS = 'In Progress', 'In Progress'
        COMPLETE = 'Complete', 'Complete'

    title = models.CharField(
        max_length=50,
        blank=False,
        validators=[RegexValidator(
            regex=r'^.*[a-zA-Z].*$',
            message='Title must contain at least one letter.'
        )]
    )
    description = models.CharField(blank=True, max_length=500)
    
    def validate_due_date_not_in_past(value):
       """Validate that the due date is not in the past."""
       if value < timezone.now():
           raise ValidationError('Due date must be in the future.')
    
    due_date = models.DateTimeField(validators=[validate_due_date_not_in_past])
    assigned_to = models.ForeignKey(User, blank=False, on_delete=models.CASCADE, related_name='assigned_to')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=30,
        choices=TaskStatus.choices,
        default=TaskStatus.NOT_STARTED
    )
    priority = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate the model."""
        super().clean()
        if self.team and self.assigned_to_id not in self.team.members.values_list('id', flat=True):
            raise ValidationError("The assigned to user is not part of this team")


    def __str__(self):
        """Return a string representation of the model."""
        return self.title