from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.views.generic import FormView, UpdateView, CreateView, ListView, DetailView
from django.urls import reverse
from tasks.forms import LogInForm, PasswordForm, UserForm, SignUpForm, TeamForm, CreateTaskForm, EditTaskForm
from tasks.helpers import login_prohibited
from tasks.models import User, Task, Team, Invitation
from tasks.filters import DashboardTaskFilter, TeamTaskFilter

@login_required
def dashboard(request):
    """Display the current user's dashboard."""

    current_user = request.user

    """Render Tasks Area & Filter Bar"""
    tasks = Task.objects.all()
    tasks = tasks.filter(assigned_to=current_user)
    
    teams = Team.objects.filter(members=current_user)
    dashboard_filter = DashboardTaskFilter(request.GET, queryset=tasks)
    filtered_teams = dashboard_filter.filter_user_teams(teams, current_user)
    context = {
        'tasks' : dashboard_filter.qs
    }

    context['user'] = current_user
    context['myFilter'] = dashboard_filter.form

    return render(request, 'dashboard.html', context)


@login_prohibited
def home(request):
    """Display the application's start/home screen."""

    return render(request, 'home.html')

class LoginProhibitedMixin:
    """Mixin that redirects when a user is logged in."""

    redirect_when_logged_in_url = None

    def dispatch(self, *args, **kwargs):
        """Redirect when logged in, or dispatch as normal otherwise."""
        if self.request.user.is_authenticated:
            return self.handle_already_logged_in(*args, **kwargs)
        return super().dispatch(*args, **kwargs)

    def handle_already_logged_in(self, *args, **kwargs):
        url = self.get_redirect_when_logged_in_url()
        return redirect(url)

    def get_redirect_when_logged_in_url(self):
        """Returns the url to redirect to when not logged in."""
        if self.redirect_when_logged_in_url is None:
            raise ImproperlyConfigured(
                "LoginProhibitedMixin requires either a value for "
                "'redirect_when_logged_in_url', or an implementation for "
                "'get_redirect_when_logged_in_url()'."
            )
        else:
            return self.redirect_when_logged_in_url

class DashboardView(LoginRequiredMixin, ListView):
    """Display the current user's dashboard."""
    queryset = Task.objects.all()
    template_name = 'dashboard.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(assigned_to=self.request.user)
        self.filterset = DashboardTaskFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['myFilter'] = self.filterset.form
        context['user'] = self.request.user
        return context

class LogInView(LoginProhibitedMixin, View):
    """Display login screen and handle user login."""

    http_method_names = ['get', 'post']
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def get(self, request):
        """Display log in template."""

        self.next = request.GET.get('next') or ''
        return self.render()

    def post(self, request):
        """Handle log in attempt."""

        form = LogInForm(request.POST)
        self.next = request.POST.get('next') or settings.REDIRECT_URL_WHEN_LOGGED_IN
        user = form.get_user()
        if user is not None:
            login(request, user)
            return redirect(self.next)
        messages.add_message(request, messages.ERROR, "The credentials provided were invalid!")
        return self.render()

    def render(self):
        """Render log in template with blank log in form."""

        form = LogInForm()
        return render(self.request, 'log_in.html', {'form': form, 'next': self.next})


def log_out(request):
    """Log out the current user"""

    logout(request)
    return redirect('home')


class PasswordView(LoginRequiredMixin, FormView):
    """Display password change screen and handle password change requests."""

    template_name = 'password.html'
    form_class = PasswordForm

    def get_form_kwargs(self, **kwargs):
        """Pass the current user to the password change form."""

        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        """Handle valid form by saving the new password."""

        form.save()
        login(self.request, self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect the user after successful password change."""

        messages.add_message(self.request, messages.SUCCESS, "Password updated!")
        return reverse('dashboard')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Display user profile editing screen, and handle profile modifications."""

    model = UserForm
    template_name = "profile.html"
    form_class = UserForm

    def get_object(self):
        """Return the object (user) to be updated."""
        user = self.request.user
        return user

    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)


class SignUpView(LoginProhibitedMixin, FormView):
    """Display the sign up screen and handle sign ups."""

    form_class = SignUpForm
    template_name = "sign_up.html"
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def form_valid(self, form):
        team = form.save()
        login(self.request, team)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)

class CreateTaskView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = CreateTaskForm
    template_name = "create_task.html"

    def get(self, request, pk):
        """Display create_task form template only if user is a member of the team."""
        try:
            team = Team.objects.get(pk=pk)
        except Team.DoesNotExist:
            messages.add_message(request, messages.ERROR, "The team does not exist.")
            return redirect(reverse('dashboard'))

        if request.user not in team.members.all():
            messages.add_message(request, messages.ERROR, "You are not a member of this team.")
            return redirect(reverse('dashboard'))

        form = self.form_class(pk=pk, initial={'team': pk})
        return render(request, self.template_name, {'form': form, 'pk': pk})

    def post(self, request, pk):
        """Handle task submission"""
        try:
            team = Team.objects.get(pk=pk)
        except Team.DoesNotExist:
            messages.add_message(request, messages.ERROR, "The team does not exist.")
            return redirect(reverse('dashboard'))
        form = self.form_class(request.POST, pk=pk)
        if form.is_valid():
            task = form.save(commit=False)
            task.team = team 
            task.save()
            return redirect(reverse('team_detail', args=[pk]))
        return render(request, self.template_name, {'form': form, 'pk': pk})

class EditTaskView(LoginRequiredMixin, UpdateView):
    """Display task editing screen, and handle task modifications."""

    model = Task
    template_name = "edit_task.html"
    form_class = EditTaskForm

    def get_object(self, queryset=None):
        """Return the object (task) to be updated or redirect if not found."""
        try:
            return Task.objects.get(id=self.kwargs['pk'])
        except Task.DoesNotExist:
            return None
        
    def dispatch(self, request, *args, **kwargs):
        """Handle requests and redirect if the task does not exist."""
        self.object = self.get_object()
        if self.object is None:
            messages.add_message(self.request, messages.ERROR, "Task does not exist.")
            return redirect(reverse('dashboard'))
        team = self.object.team
        if request.user not in team.members.all():
            messages.add_message(request, messages.ERROR, "You are not a member of this team.")
            return redirect(reverse('dashboard'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Handle valid form by updating the task."""
        form.save()
        messages.add_message(self.request, messages.SUCCESS, "Task updated successfully.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Return redirect URL after successful update."""
        task = self.get_object()
        return reverse('team_detail', kwargs={'pk': task.team.pk})
    
    def get_form_kwargs(self):
        """Get the current user and pass it to the form."""
        kwargs = super(EditTaskView, self).get_form_kwargs()
        task = self.get_object()
        if task and task.team:
            kwargs['pk'] = task.team.pk
        return kwargs
    
    def post(self, request, *args, **kwargs):
        """Handle the delete task button."""
        self.object = self.get_object()
        if "delete" in request.POST:
            self.object.delete()
            messages.add_message(request, messages.SUCCESS, "Task deleted successfully.")
            return redirect(reverse('dashboard'))
        else:
            return super().post(request, *args, **kwargs)

class CreateTeamView(LoginRequiredMixin, CreateView):
    """Display the create team screen and handle team creation."""
    model = Team
    template_name= "create_team.html"
    form_class = TeamForm
    http_method_names = ['get', 'post']
    
    def get_form_kwargs(self):
        """Get the current user and pass it to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['owner'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Handle valid form by creating the team."""
        owner = self.request.user
        Team.create_team(form.cleaned_data['name'], form.cleaned_data['description'], owner, form.cleaned_data['members'], form.cleaned_data['message'])
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Return redirect URL after successful creation."""
        messages.add_message(self.request, messages.SUCCESS, "Team successfully created.") 
        return reverse('dashboard')
        
class TeamDetailView(DetailView):
    model = Team
    template_name = 'teams.html'
    context_object_name = 'team'

    def get_team(self):
        """Return the team to be displayed."""
        try:
            return Team.objects.get(id=self.kwargs['pk'])
        except Team.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        """Handle requests and redirect if the team does not exist."""
        team = self.get_team()

        if team is None:
            messages.error(request, "Team does not exist.")
            return redirect(reverse('dashboard'))

        team_members = team.members.all()
        if request.user not in team_members:
            messages.error(request, "You are not a member of this team.")
            return redirect(reverse('dashboard'))

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Return the context data (team and tasks) to be displayed."""
        context = super().get_context_data(**kwargs)
        team = self.get_team()

        queryset = Task.objects.filter(team=team)
        team_members = team.members.all()
        team_dashboard_filter = TeamTaskFilter(self.request.GET, queryset=queryset)

        context.update({
            'tasks': team_dashboard_filter.qs,
            'myFilter': team_dashboard_filter.form,
            'members': team_members
        })

        return context

    def post(self, request, *args, **kwargs):
        """Handle the delete team button."""
        team = self.get_object()
        if 'action' in request.POST and request.POST['action'] == 'leave_team':
            if team.remove_member(request.user): 
                messages.add_message(request, messages.SUCCESS, "You have left the team.")
                return redirect('dashboard')
            else:
                messages.add_message(request, messages.ERROR, "Owner cannot leave the team.")
        return redirect(self.request.path_info)

class EditTeamView(LoginRequiredMixin, UpdateView):
    """Display team editing screen, and handle team modifications."""

    model = Team
    template_name = "edit_team.html"
    form_class = TeamForm
    
    def get_object(self):
        """Return the object (team) to be updated."""
        try:
            return Team.objects.get(id=self.kwargs['pk'])
        except Team.DoesNotExist:
            return None
        
    def dispatch(self, request, *args, **kwargs):
        """Handle requests and redirect if the team does not exist."""
        team = self.get_object()
        if team is None:
            messages.add_message(request, messages.ERROR, "Team does not exist.")
            return redirect(reverse('dashboard'))
        
        if self.request.user not in team.members.all():
            messages.add_message(request, messages.ERROR, "You are not a member of this team.")
            return redirect(reverse('dashboard'))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Get the current user and pass it to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['pk'] = self.kwargs['pk']
        kwargs['owner'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Handle valid form by updating the team."""
        self.owner_username = self.request.user.username
        self.pk = self.kwargs['pk']
        
        # Collects the data from the form and passes it to the edit_team function
        edit_team_data = {
            'pk': self.pk,
            'owner_username': self.owner_username,
            'new_name': form.cleaned_data['name'],
            'new_description': form.cleaned_data['description'],
            'members': form.cleaned_data['members'],
            'message': form.cleaned_data['message'],
            'remove_members': form.cleaned_data.get('remove_members')
        }
        Team.edit_team(**edit_team_data)
        return redirect(self.get_success_url())
    
    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Team updated!")
        return reverse('team_detail', kwargs={'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        """Handle the delete team button."""
        team = self.get_object()
        if 'action' in request.POST and request.POST['action'] == 'delete_team':
            if team.delete_team(self.request.user):
                messages.add_message(request, messages.SUCCESS, "Team deleted!")
                return redirect(reverse('dashboard'))
            else:
                messages.add_message(request, messages.ERROR, "You do not have permissions to delete team.")
                return redirect(self.request.path_info)
        # Handle the regular form submission
        return super().post(request, *args, **kwargs)

class InvitationListView(LoginRequiredMixin, ListView):

    model = Invitation
    template_name = "view_invitation.html"
    context_object_name = "invitations"
    paginate_by = settings.INVITATIONS_PER_PAGE

    def get_queryset(self):
        """Return the invitations for the current user."""
        return Invitation.objects.filter(recipient=self.request.user)
    
    def post(self, request):
        action = None
        if 'accept_invitation' in request.POST:
            action = 'accept_invitation'
        elif 'decline_invitation' in request.POST:
            action = 'decline_invitation'

        if action:
            invitation_id = request.POST[action]
            user = request.user
            self._handle_invitation_action(action, invitation_id=invitation_id, user=user)
        else:
            messages.error(self.request, "Invalid Action")
        return redirect('view_invitation')
        
    def _handle_invitation_action(self, action, **kwargs):
        """Handle the invitation action."""
        invitation_id = kwargs.pop('invitation_id', None)
        user = kwargs.pop('user', None)

        try:
            invitation = Invitation.objects.get(pk=invitation_id)
        except Invitation.DoesNotExist:
            messages.error(self.request, "Invitation does not exist")
            return  

        try:
            if action == 'accept_invitation':
                invitation.accept_invitation(user)
                messages.success(self.request, 'Invitation accepted successfully.')
            elif action == 'decline_invitation':
                invitation.decline_invitation(user)
                messages.success(self.request, 'Invitation declined successfully.')
            
        except PermissionDenied as e:
            messages.error(self.request, str(e))

def SortTasksByStatus(queryset):
    """Takes all tasks passed and produces the quantity, and 3 lists of tasks sorted by Task Status"""
    task_count = queryset.count()
    
    #Organise all filtered tasks into 4 lists according to Task Status
    notStarted_tasks = queryset.filter(status=Task.TaskStatus.NOT_STARTED)
    inProgress_tasks = queryset.filter(status=Task.TaskStatus.IN_PROGRESS)
    completed_tasks = queryset.filter(status=Task.TaskStatus.COMPLETE)

    max_rows = max(notStarted_tasks.count(), inProgress_tasks.count())

    task_data = {
        'max_rows' : max_rows,
        'taskQuantity' : task_count,
        'notStared_tasks' : notStarted_tasks,
        'inProgress_tasks' : inProgress_tasks,
        'completed_tasks' : completed_tasks
    }

    return task_data