"""Tests of the Create Tasks View"""
from django.shortcuts import redirect
from django.test import TestCase
from django.urls import reverse
from tasks.forms import CreateTaskForm
from tasks.models import User, Team, Task
from django.contrib.messages import get_messages

from django.utils import timezone
from datetime import timedelta

class CreateTaskViewTestCase(TestCase):
    """Tests of the create tasks view"""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/default_team.json'
    ]

    def setUp(self):
        """Set up the test case"""
        """Create a user and log them in."""
        self.user = User.objects.get(username='@johndoe')
        self.user.set_password('password')
        self.user.save()

        self.team = Team.objects.get(pk=1)
        self.url = reverse('create_task', kwargs={'pk': self.team.id})
        self.successurl = redirect(reverse('team_detail', kwargs={'pk': self.team.id}))

        self.form_input = {
        'title': 'Valid Title',
        'description': 'Valid Description',
        'due_date': timezone.now() + timedelta(days=1),
        'assigned_to': self.user.id,
        'status': Task.TaskStatus.NOT_STARTED,
        'priority': 1,
        'team': self.team.id, 
    }

    def test_access_control(self):
        """Test access control for the create_task view."""
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
        self.assertRedirects(response, '/log_in/?next=/teams/1/create_task/')

    def test_unauthenticated_access(self):
        """Test unauthenticated access to the create_task view."""
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_create_tasks_url(self):
        """Test that the url for the create_tasks view is valid."""
        self.assertEqual(self.url, '/teams/1/create_task/')

    def test_get_create_task(self):
        """Test that the create_task view renders the create_task.html template."""
        self.client.login(username='@johndoe', password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_task.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, CreateTaskForm))
        self.assertFalse(form.is_bound)

    def test_team_does_not_exist(self):
        """Test accessing create_task view with a non-existent team."""
        self.client.login(username='@johndoe', password='password')
        non_existent_team_url = reverse('create_task', kwargs={'pk': 999})
        response = self.client.get(non_existent_team_url, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, "The team does not exist.")
        self.assertEqual(messages[0].tags, 'danger')

    def test_user_not_member_of_team(self):
        """Test accessing create_task view as a user who is not a member of the team."""
        other_user = User.objects.create(username='@janedoe')
        other_user.set_password('password')
        other_user.save()

        self.client.login(username='@janedoe', password='password')
        response = self.client.get(self.url, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, "You are not a member of this team.")
        self.assertEqual(messages[0].tags, 'danger')

    def test_post_task_nonexistent_team(self):
        """Test task submission for a non-existent team."""
        self.client.login(username='@johndoe', password='password')
        non_existent_team_url = reverse('create_task', kwargs={'pk': 999})
        response = self.client.post(non_existent_team_url, self.form_input, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, "The team does not exist.")
        self.assertEqual(messages[0].tags, 'danger')

    def test_invalid_task_entered(self):
        """Test that the create_task view renders the create_task.html template with an invalid task."""
        self.client.login(username='@johndoe', password='password')
        self.form_input['title'] = ''
        response = self.client.post(self.url, self.form_input, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_task.html')
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())

    def test_valid_task_redirect(self):
        """Test that the create_task view redirects to the team_detail view on valid input."""
        self.client.login(username='@johndoe', password='password')
        response = self.client.post(self.url, self.form_input)
        self.assertRedirects(response, reverse('team_detail', args=[self.team.id]), status_code=302, target_status_code=200)

    def test_valid_task_save(self):
        """Test that the create_task view saves a valid task."""
        self.client.login(username='@johndoe', password='password')
        before_count = Task.objects.count()
        self.client.post(self.url, self.form_input, follow=True)
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count + 1)
        task = Task.objects.latest('id')
        self.assertEqual(task.title, self.form_input['title'])
        self.assertEqual(task.description, self.form_input['description'])
        self.assertEqual(task.due_date, self.form_input['due_date'])
        self.assertEqual(task.team.id, self.team.id)
        self.assertEqual(task.assigned_to.id, self.form_input['assigned_to'])
        self.assertEqual(task.status, self.form_input['status'])
        self.assertEqual(task.priority, self.form_input['priority'])
    