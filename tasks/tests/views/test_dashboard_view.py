"""Tests correct filters applied to dashboard view."""
from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Team, Task

class DashboardViewTestCase(TestCase):
    """Tests of the dashboard view."""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/default_task.json'
    ]

    def setUp(self):
        """Create user, team, and task."""
        self.user = User.objects.get(username='@johndoe')
        self.user.set_password('password')
        self.user.save()
        self.team = Team.objects.get(name='Test Team')
        self.task = Task.objects.get(title='Test Task')
    
    def test_unauthenticated_access(self):
        """Test unauthenticated access to the dashboard view."""
        response = self.client.get(reverse('dashboard'))
        self.assertNotEqual(response.status_code, 200) 

    def test_supposed_elements_dashboard_view(self):
        """Test the dashboard view contains all urls needed"""
        self.client.login(username='@johndoe', password='password')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        menu_urls = [
            reverse('profile'), reverse('log_out'), reverse('dashboard'), reverse('password'),
            reverse('view_invitation'), reverse('team_detail', kwargs={'pk': self.team.id}), reverse('edit_task', args=[self.task.id])
        ]
        for url in menu_urls:
            self.assertContains(response, url)

    def test_not_supposed_elements_dashboard_view(self):
        """Test the dashboard view does not contain other urls"""
        self.client.login(username='@johndoe', password='password')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        menu_urls = [
            reverse('log_in'), reverse('sign_up'), 
            reverse('create_task', kwargs={'pk': self.team.id}),
        ]
        for url in menu_urls:
            self.assertNotContains(response, url)


