from django.test import TestCase
from django.urls import reverse
from tasks.models import Team, User
from django.contrib.messages import get_messages
from django.contrib import messages

class TeamDetailViewTest(TestCase):
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json'
    ]

    def setUp(self):
        """Create a user and log them in."""
        self.user = User.objects.get(username='@johndoe')
        self.user.set_password('password')
        self.user.save()
        self.second_user = User.objects.get(username='@janedoe')
        self.second_user.set_password('password')
        self.second_user.save()
        self.team = Team.objects.get(name='Test Team')

    def test_team_detail_view(self):
        """Test the team detail view."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('team_detail', kwargs={'pk': self.team.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'teams.html')

    def test_team_detail_non_member_access(self):
        """Test access to the team detail page by a non-member."""
        self.client.login(username=self.second_user.username, password='password')
        response = self.client.get(reverse('team_detail', kwargs={'pk': self.team.id}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
        response_messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(msg.level == messages.ERROR for msg in response_messages))

    def test_member_leaves_team(self):
        """Test a member leaving a team."""
        self.team.members.add(self.second_user)
        self.client.login(username=self.second_user.username, password='password')
        response = self.client.post(reverse('team_detail', kwargs={'pk': self.team.id}), {
            'action': 'leave_team'
        })
        self.assertRedirects(response, reverse('dashboard'))
        response_messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(msg.message == "You have left the team." for msg in response_messages))
    
    def test_owner_cannot_leave_team(self):
        """Test the team owner trying to leave the team."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(reverse('team_detail', kwargs={'pk': self.team.id}), {
            'action': 'leave_team'
        })
        self.assertRedirects(response, reverse('team_detail', kwargs={'pk': self.team.id}))
        response_messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(msg.level == messages.ERROR and "Owner cannot leave the team" in msg.message for msg in response_messages))

    def test_team_detail_owner_restriction(self):
        """Test the team detail view with a non-existent team ID."""
        self.client.login(username='@janedoe', password='password')  # Non-owner
        response = self.client.post(reverse('team_detail', kwargs={'pk': self.team.id}), {
            'edit_name': True,
            'name': 'Attempted Edit'
        })
        self.team.refresh_from_db()
        self.assertNotEqual(self.team.name, 'Attempted Edit')

    def test_team_detail_view_context_data(self):
        """Test the team detail view context data."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('team_detail', kwargs={'pk': self.team.id}))
        self.assertIn('team', response.context)
        self.assertEqual(response.context['team'], self.team)
