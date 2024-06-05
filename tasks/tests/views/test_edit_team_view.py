from django.test import TestCase
from django.urls import reverse
from tasks.models import Team, User, Invitation
from django.contrib.messages import get_messages
from django.contrib import messages

class EditTeamViewTest(TestCase):
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
        self.team = Team.objects.get(pk=1)

    def test_get_object_exists(self):
        """Test retrieving an existing team in EditTeamView."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('edit_team', kwargs={'pk': self.team.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'].id, self.team.id)

    def test_get_object_nonexistent(self):
        """Test retrieving a non-existent team in EditTeamView."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('edit_team', kwargs={'pk': 999}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    def test_edit_nonexistent_team(self):
        """Test editing a non-existent team."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('edit_team', kwargs={'pk': 999}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
        response_messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(msg.level == messages.ERROR for msg in response_messages))

    def test_non_member_edit_attempt(self):
        """Test a non-member trying to edit a team."""
        self.client.login(username=self.second_user.username, password='password')
        response = self.client.post(reverse('edit_team', kwargs={'pk': self.team.id}), {
            'name': 'New Name'
        })
        self.assertRedirects(response, reverse('dashboard'))
        response_messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(msg.level == messages.ERROR for msg in response_messages))

    def test_edit_team_with_pk(self):
        """Test editing a team with a specific primary key (pk)."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(reverse('edit_team', kwargs={'pk': self.team.id}), {
            'name': 'Updated Team Name'
        })
        self.assertEqual(response.status_code, 302)
        self.team.refresh_from_db()
        self.assertEqual(self.team.name, 'Updated Team Name')

    def test_delete_team_by_owner(self):
        """Test deleting a team by the owner."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(reverse('edit_team', kwargs={'pk': self.team.id}), {
            'action': 'delete_team'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
        with self.assertRaises(Team.DoesNotExist):
            Team.objects.get(id=self.team.id)

    def test_edit_team_view(self):
        """Test the edit team view."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('edit_team', kwargs={'pk': self.team.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_team.html')

    def test_edit_team(self):
        """Test editing a team."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(reverse('edit_team', kwargs={'pk': self.team.id}), {
            'name': 'Updated Team Name',
            'description': 'Updated Description'
        })
        self.assertEqual(response.status_code, 302)
        self.team.refresh_from_db()
        self.assertEqual(self.team.name, 'Updated Team Name')
        self.assertEqual(self.team.description, 'Updated Description')

    def test_edit_team_without_name(self):
        """Test editing a team without a name."""
        self.client.login(username=self.user.username, password='password')
        original_name = self.team.name

        response = self.client.post(reverse('edit_team', kwargs={'pk': self.team.id}), {
            'name': '',
            'description': 'Updated description'
        })
        self.assertEqual(response.status_code, 200)
        self.team.refresh_from_db()
        self.assertEqual(self.team.name, original_name)

    def test_delete_team(self):
        """Test deleting a team."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(reverse('edit_team', kwargs={'pk': self.team.id}), {
            'action': 'delete_team'
        })
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(Team.DoesNotExist):
            Team.objects.get(id=self.team.id)

    def test_edit_team_with_invalid_data(self):
        """Test editing a team with invalid data using the primary key."""
        self.client.login(username=self.user.username, password='password')
        old_name = self.team.name
        response = self.client.post(reverse('edit_team', kwargs={'pk': self.team.id}), {
            'name': '',
        })
        self.assertEqual(response.status_code, 200)
        self.team.refresh_from_db()
        self.assertEqual(self.team.name, old_name)

    def test_edit_nonexistent_team(self):
        """Test editing a non-existent team."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('edit_team', kwargs={'pk': 999}))
        self.assertEqual(response.status_code, 302)

    def test_remove_member_from_team(self):
        """Test removing a member from a team."""
        self.client.login(username=self.user.username, password='password')
        self.team.members.add(self.second_user)
        self.assertIn(self.second_user, self.team.members.all())
        response = self.client.post(reverse('edit_team', kwargs={'pk': self.team.id}), {
            'name': 'name',
            'remove_members': [self.second_user.id],
        })
        self.team.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(self.second_user, self.team.members.all())

    def test_invite_valid_member(self):
        """Test adding a valid member to the team."""
        self.client.login(username=self.user.username, password='password')
        valid_member_username = '@janedoe'
        response = self.client.post(reverse('edit_team', kwargs={'pk': self.team.id}), {
            'name': self.team.name,
            'members': valid_member_username
        })
        self.assertEqual(response.status_code, 302)
        self.team.refresh_from_db()
        valid_member = User.objects.get(username=valid_member_username)
        self.assertTrue(Invitation.objects.filter(recipient=valid_member, team=self.team))

    def test_invite_invalid_member(self):
        """Test adding an invalid member to the team."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(reverse('edit_team', kwargs={'pk': self.team.id}), {
            'name': self.team.name,
            'members': 'nonexistentuser'
        })
        self.assertEqual(response.status_code, 200)
        form_errors = response.context['form'].errors
        self.assertIn("Member nonexistentuser does not exist.", form_errors['members'])

    def test_delete_team_by_non_owner(self):
        """Test deleting a team by a non-owner."""
        self.client.login(username='@janedoe', password='password')
        response = self.client.post(reverse('edit_team', kwargs={'pk': self.team.id}), {
            'action': 'delete_team'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Team.objects.filter(id=self.team.id).exists())

    def test_edit_team_view_messages(self):
        """Test the messages displayed on the edit team view."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('team_detail', kwargs={'pk': 999}))
        self.assertEqual(response.status_code, 302)

    def test_regular_form_submission(self):
        """Test regular form submission without 'delete_team' action."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(reverse('edit_team', kwargs={'pk': self.team.id}), {
            'name': 'Updated Team Name',
        })
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('team_detail', kwargs={'pk': self.team.id})
        self.assertRedirects(response, expected_url)
        self.team.refresh_from_db()
        self.assertEqual(self.team.name, 'Updated Team Name')

    def test_delete_team_without_permission(self):
        """Test attempting to delete a team without having permissions."""
        self.team.members.add(self.second_user)
        self.client.login(username=self.second_user.username, password='password')
        response = self.client.post(reverse('edit_team', kwargs={'pk': self.team.id}), {
            'action': 'delete_team'
        })
        expected_redirect_url = reverse('edit_team', kwargs={'pk': self.team.id})
        self.assertRedirects(response, expected_redirect_url)
        response_messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(msg.level == messages.ERROR and "You do not have permissions to delete team" in str(msg) for msg in response_messages))