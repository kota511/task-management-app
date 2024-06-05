from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Task, Team
from django.utils import timezone
from datetime import timedelta

class EditTaskViewTestCase(TestCase):
    """Tests for the Edit Tasks View"""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json'
    ]

    def setUp(self):
        """Set up the test case"""

        """Create a user and log them in."""
        self.user = User.objects.get(username='@johndoe')
        self.user.set_password('password')
        self.user.save()

        self.team = Team.objects.create(name="Test Team", description="Example description.", owner=self.user)
        self.team.members.add(self.user)

        self.task = Task.objects.create(
            title='Original Title',
            description='Original Description',
            due_date=timezone.now() + timedelta(days=1),
            team=self.team,
            assigned_to=self.user,
            status=Task.TaskStatus.NOT_STARTED,
            priority=1
        )
        
        self.url = reverse('edit_task', args=[self.task.id])
        self.successurl = reverse('dashboard')

        self.form_input = {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'due_date': timezone.now() + timedelta(days=2),
            'team': self.team.id,
            'assigned_to': self.user.id,
            'status': Task.TaskStatus.IN_PROGRESS,
            'priority': 2
        }

    def test_get_edit_task(self):
        """Test rendering the edit task view."""
        self.client.login(username='@johndoe', password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_task.html')

    def test_update_task_title(self):
        """Test updating the task's title."""
        self.client.login(username='@johndoe', password='password')
        updated_data = self.form_input.copy()
        updated_data['title'] = 'Updated Title'
        response = self.client.post(self.url, updated_data)
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Title')

    def test_update_task_description(self):
        """Test updating the task's description."""
        self.client.login(username='@johndoe', password='password')
        updated_data = self.form_input.copy()
        updated_data['description'] = 'New Description'
        response = self.client.post(self.url, updated_data)
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.description, 'New Description')

    def test_update_task_due_date(self):
        """Test updating the task's due date."""
        self.client.login(username='@johndoe', password='password')
        new_due_date = (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M')
        updated_data = self.form_input.copy()
        updated_data['due_date'] = new_due_date
        response = self.client.post(self.url, updated_data)
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.due_date.strftime('%Y-%m-%dT%H:%M'), new_due_date)

    def test_update_task_assigned_to(self):
        """Test updating the task's assigned user."""
        self.client.login(username='@johndoe', password='password')
        another_user = User.objects.get(pk = 2)
        self.team.members.add(another_user)
        updated_data = self.form_input.copy()
        updated_data['assigned_to'] = another_user.id
        response = self.client.post(self.url, updated_data)
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.assigned_to.id, another_user.id)

    def test_update_task_status(self):
        """Test updating the task's status."""
        self.client.login(username='@johndoe', password='password')
        updated_data = self.form_input.copy()
        updated_data['status'] = Task.TaskStatus.COMPLETE
        response = self.client.post(self.url, updated_data)
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.TaskStatus.COMPLETE)

    def test_update_task_priority(self):
        """Test updating the task's priority."""
        self.client.login(username='@johndoe', password='password')
        updated_data = self.form_input.copy()
        updated_data['priority'] = 5 
        response = self.client.post(self.url, updated_data)
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.priority, 5)

    def test_delete_task(self):
        """Test deleting the task."""
        self.client.login(username='@johndoe', password='password')
        response = self.client.post(self.url, {'delete': 'True'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(pk=self.task.id).exists())

    def test_access_control(self):
        """Test access control for the edit_task view."""
        task_id = 1
        url = reverse('edit_task', args=[task_id])
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('log_in') + '?next=/dashboard/', status_code=302, target_status_code=200)

    def test_unauthenticated_access(self):
        """Test unauthenticated access to the edit_task view."""
        task_id = 1
        url = reverse('edit_task', args=[task_id])
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_edit_task_url(self):
        """Test that the url for the edit_task view is valid."""
        task_id = 1
        url = reverse('edit_task', args=[task_id])
        self.assertEqual(url, f'/task/{task_id}/edit_task/')

    def test_get_edit_task(self):
        """Test rendering the edit task view."""
        self.client.login(username='@johndoe', password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_task.html')

    def test_get_object_task_does_not_exist(self):
        """Test handling of Task.DoesNotExist exception."""
        task_id = 50
        url = reverse('edit_task', args=[task_id])
        self.client.login(username='@johndoe', password='password')
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('dashboard'), status_code=302, target_status_code=200)
        self.assertContains(response, "Task does not exist.")

    def test_dispatch_task_does_not_exist(self):
        """Test handling of Task.DoesNotExist exception in dispatch method."""
        task_id = 50
        url = reverse('edit_task', args=[task_id])
        self.client.login(username='@johndoe', password='password')
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('dashboard'), status_code=302, target_status_code=200)
        self.assertContains(response, "Task does not exist.")
    
    def test_valid_task_redirect(self):
        """Test that the edit task view redirects to the team_detail view on valid input."""
        self.client.login(username='@johndoe', password='password')
        response = self.client.post(self.url, self.form_input)
        self.assertRedirects(response, reverse('team_detail', args=[self.team.id]), status_code=302, target_status_code=200)