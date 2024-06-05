"""Forms for the tasks app."""
from datetime import timezone
from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from .models import User, Task, Team, Invitation

class LogInForm(forms.Form):
    """Form enabling registered users to log in."""

    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput())

    def get_user(self):
        """Returns authenticated user if possible."""

        user = None
        if self.is_valid():
            username = self.cleaned_data.get('username')
            password = self.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
        return user


class UserForm(forms.ModelForm):
    """Form to update user profiles."""

    class Meta:
        """Form options."""

        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

class NewPasswordMixin(forms.Form):
    """Form mixing for new_password and password_confirmation fields."""

    new_password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(),
        validators=[RegexValidator(
            regex=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9]).*$',
            message='Password must contain an uppercase character, a lowercase '
                    'character and a number'
            )]
    )
    password_confirmation = forms.CharField(label='Password confirmation', widget=forms.PasswordInput())

    def clean(self):
        """Form mixing for new_password and password_confirmation fields."""

        super().clean()
        new_password = self.cleaned_data.get('new_password')
        password_confirmation = self.cleaned_data.get('password_confirmation')
        if new_password != password_confirmation:
            self.add_error('password_confirmation', 'Confirmation does not match password.')


class PasswordForm(NewPasswordMixin):
    """Form enabling users to change their password."""

    password = forms.CharField(label='Current password', widget=forms.PasswordInput())

    def __init__(self, user=None, **kwargs):
        """Construct new form instance with a user instance."""
        
        super().__init__(**kwargs)
        self.user = user

    def clean(self):
        """Clean the data and generate messages for any errors."""

        super().clean()
        password = self.cleaned_data.get('password')
        if self.user is not None:
            user = authenticate(username=self.user.username, password=password)
        else:
            user = None
        if user is None:
            self.add_error('password', "Password is invalid")

    def save(self):
        """Save the user's new password."""

        new_password = self.cleaned_data['new_password']
        if self.user is not None:
            self.user.set_password(new_password)
            self.user.save()
        return self.user


class SignUpForm(NewPasswordMixin, forms.ModelForm):
    """Form enabling unregistered users to sign up."""

    class Meta:
        """Form options."""

        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def save(self):
        """Create a new user."""

        super().save(commit=False)
        user = User.objects.create_user(
            self.cleaned_data.get('username'),
            first_name=self.cleaned_data.get('first_name'),
            last_name=self.cleaned_data.get('last_name'),
            email=self.cleaned_data.get('email'),
            password=self.cleaned_data.get('new_password'),
        )
        return user
    
class CreateTaskForm(forms.ModelForm):
    """Form used to create tasks"""

    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'assigned_to', 'status', 'priority', 'team']
        labels = {
            'title' : 'Task Title',
            'description' : 'Task Description',
            'due_date' : 'Due Date',
            'assigned_to': 'Assigned To',
            'status': 'Current Completion Status',
            'priority': 'Task Priority',
        }
        widgets = {
            'description': forms.Textarea(),
            'due_date': forms.widgets.DateTimeInput(attrs={'type': 'datetime-local'}),
            'priority': forms.widgets.NumberInput(attrs={'min': 1, 'max': 5}),
            'assigned_to': forms.Select(),
            'team': forms.HiddenInput()
        }

    def __init__(self, *args, pk=None, **kwargs):
        """Construct new form instance with a team instance."""
        super(CreateTaskForm, self).__init__(*args, **kwargs)
        
        if pk:
            self.fields['team'].initial = pk
            try:
                team = Team.objects.get(id=pk)
                self.fields['assigned_to'].queryset = team.members.all()
            except Team.DoesNotExist:
                self.fields['assigned_to'].queryset = User.objects.none()
        else:
            self.fields['assigned_to'].queryset = User.objects.all()

    def clean(self):
        """Validate the form."""
        cleaned_data = super().clean()
        team = cleaned_data.get('team')
        assigned_to = cleaned_data.get('assigned_to')

        if team and assigned_to and assigned_to not in team.members.all():
            raise forms.ValidationError("Assigned user must be a member of the selected team.")

        return cleaned_data

    def save(self, commit=True):
        """Save the task."""
        task = super().save(commit=False)
        task.title = self.cleaned_data.get('title')
        task.description = self.cleaned_data.get('description')
        task.due_date = self.cleaned_data.get('due_date')
        task.assigned_to = self.cleaned_data.get('assigned_to')
        task.team = self.cleaned_data.get('team')
        task.status = self.cleaned_data.get('status')
        task.priority = self.cleaned_data.get('priority')

        if commit:
            task.save()
            self.save_m2m()
            
        return task

class EditTaskForm(forms.ModelForm):
    """Form to edit a task."""
    class Meta:
        model = Task
        fields = ["title", "description", "due_date", "team", "assigned_to", "status", "priority"]
        labels = {
            'title': 'Task Title',
            'description': 'Task Description',
            'due_date': 'Due Date',
            'team': 'In Team',
            'status': 'Current Completion Status',
            'priority': 'Task Priority',
        }
        widgets = {
            'description': forms.Textarea(),
            'due_date': forms.widgets.DateTimeInput(attrs={'type': 'datetime-local'}),
            'priority': forms.widgets.NumberInput(attrs={'min': 1, 'max': 5}),
            'assigned_to': forms.Select(),
            'team': forms.Select(),
        }

    def __init__(self, *args, pk=None, **kwargs):
        """Construct new form instance with a team instance."""
        super(EditTaskForm, self).__init__(*args, **kwargs)

        self.fields['team'].widget = forms.HiddenInput()
        
        try:
            team = Team.objects.get(id=pk)
            self.fields['assigned_to'].queryset = team.members.all()
        except Team.DoesNotExist:
            self.fields['assigned_to'].queryset = User.objects.none()

    def save(self, commit=True):
        """Save the task."""
        task = super().save(commit=False)
        if commit:
            task.save()
        return task

class TeamForm(forms.ModelForm):
    """Form to create or edit a team."""
    members = forms.CharField(required=False, label='Invite Members', widget=forms.TextInput(attrs={'placeholder': 'Enter usernames separated by commas'}))
    message = forms.CharField(required=False, label='Invite Message', widget=forms.Textarea(attrs={'placeholder': 'Enter your invitation message here', 'rows': 3,}), max_length=500)
    remove_members = forms.ModelMultipleChoiceField(queryset=User.objects.none(), required=False, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Team
        fields = ['name', 'description', 'members', 'remove_members']
        labels = {
            'name': 'Team Name*',
            'description': 'Team Description',
            'remove_members': 'Remove Members',
        }

        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter team name here'}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter team description here', 'rows': 3})
        }

    def __init__(self, *args, pk=None, owner=None, **kwargs):
        """Construct new form instance with a team instance."""
        self.pk = pk
        self.owner = owner
        self.team = None
        if self.pk:
            try:
                self.team = Team.objects.get(id=self.pk)
                kwargs['instance'] = self.team
            except Team.DoesNotExist:
                self.team = None
                
        super().__init__(*args, **kwargs)
        # Set the initial value for the members field as it gets filled with queryset of members in team without this.
        self.initial['members'] = ''
        if self.team:
            self.fields['remove_members'].queryset = self.team.members.exclude(username=self.owner.username)
            if self.team.members.count() <= 1:
                self.fields.pop('remove_members', None)
        else:
            # Remove the remove_members field if creating a new team.
            del self.fields['remove_members']

    def clean_name(self):
        """Validate the name field."""
        name = self.cleaned_data.get('name', '').strip()
        if not any(char.isalpha() for char in name):
            raise forms.ValidationError("Team name must contain at least one letter.")
        return name
    
    def clean_members(self):
        """Validate the members field."""
        members_input = self.cleaned_data.get('members', '')
        member_names = [name.strip() for name in members_input.split(',') if name.strip()]
        # Create arrays for members and errors to be used later.
        members = []
        errors = []
        # Collect usernames to check for duplicates.
        seen_usernames = set()
        # Iterate through the members and check if they are valid.
        for member in member_names:
            self._validate_member(member, members, seen_usernames, errors)
            seen_usernames.add(member)

        self._raise_errors(errors)
        return members

    def _validate_member(self, member, members, seen_usernames, errors):
        """Validate a member."""
        if self._is_duplicate(member, seen_usernames):
            errors.append(forms.ValidationError(f"You have a duplicate entry for {member} in the team."))
            return
        try:
            user = User.objects.get(username=member)
            self._check_user_validity(user, member, members, errors)
        except User.DoesNotExist:
            errors.append(forms.ValidationError(f"Member {member} does not exist."))

    def _is_duplicate(self, member, seen_usernames):
        """Check if the member is a duplicate."""
        return member in seen_usernames

    def _check_user_validity(self, user, member, members, errors):
        """Check if the user is valid."""
        if user.username == self.owner.username:
            errors.append(forms.ValidationError("You cannot add yourself to the team."))
            return

        members.append(user)

        if self.team:
            if user in self.team.members.all() and user.username != self.team.owner.username:
                errors.append(forms.ValidationError(f"{member} is already a member of the team."))
            if Invitation.objects.filter(recipient=user, team=self.team).exists():
                errors.append(forms.ValidationError(f"Invitation already pending for {member}."))

    def _raise_errors(self, errors):
        """Raise errors if there are any."""
        if errors:
            raise forms.ValidationError(errors)

    def clean_remove_members(self):
        """Validate the remove_members field."""
        remove_members = self.cleaned_data.get('remove_members', [])
        return remove_members