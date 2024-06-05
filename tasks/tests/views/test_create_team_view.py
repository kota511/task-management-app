from django.test import TestCase
from django.urls import reverse
from tasks.models import Team, User

class CreateTeamViewTest(TestCase):
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

    def test_access_control(self):
        """Test access control for the create team view."""
        response = self.client.get(reverse('create_team'))
        self.assertNotEqual(response.status_code, 200)
        self.assertRedirects(response, '/log_in/?next=/create_team/')

    def test_create_team_view(self):
        """Test the create team view."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('create_team'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_team.html')

    def test_create_team(self):
        """Test creating a team."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(reverse('create_team'), {
            'name': "New Team",
            'description': 'New Team Description'
        })
        self.assertEqual(response.status_code, 302)
        new_team = Team.objects.get(name='New Team')
        self.assertEqual(new_team.owner, self.user)
        self.assertEqual(new_team.description, 'New Team Description')
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(Team.objects.filter(name='New Team').exists())

    def test_create_team_with_invalid_data(self):
        """Test creating a team with invalid data."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(reverse('create_team'), {
            'name': '',
            'description': 'Invalid team'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Team.objects.filter(name='').exists())
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_create_team_view_unauthenticated_access(self):
        """Test unauthenticated access to the create team view."""
        response = self.client.get(reverse('create_team'))
        self.assertNotEqual(response.status_code, 200)