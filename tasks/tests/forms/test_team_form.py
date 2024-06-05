"""Unit tests of the team form."""
from django.test import TestCase
from tasks.models import User, Team, Invitation
from tasks.forms import TeamForm

class TeamFormTestWithoutExistingTeam(TestCase):
    """Unit tests of the team form."""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/other_teams.json',
    ]

    def setUp(self):
        """Set up the test case."""
        self.owner = User.objects.get(username='@johndoe')
        self.second_user = User.objects.get(username='@janedoe')
        self.third_user = User.objects.get(username='@petrapickles')

    # Test form accepts valid input data
    def test_team_form_valid_data(self):
        """Test that valid data is accepted by the form. - Name, Description, Invite Members"""
        form_data = {
            'name': 'New Team',
            'description': 'A new team',
            'members': self.second_user.username,
            'message': 'Please join my team.'
        }
        form = TeamForm(data=form_data, owner=self.owner)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['message'], 'Please join my team.')

    def test_team_form_invalid_message(self):
        """Test that an invalid message is not accepted by the form."""
        form_data = {
            'name': 'New Team',
            'description': 'A new team',
            'members': self.second_user.username,
            'message': 'A' * 501,
        }
        form = TeamForm(data=form_data, owner=self.owner)
        self.assertFalse(form.is_valid())

    def test_team_form_invalid_name(self):
        """Test that an invalid name is not accepted by the form."""
        form_data = {
            'name': '12345',
            'description': 'A team',
            'members': self.second_user.username,
        }
        form = TeamForm(data=form_data, owner=self.owner)
        self.assertFalse(form.is_valid())
        self.assertIn("Team name must contain at least one letter.", form.errors['name'])

    def test_team_form_invalid_name_length(self):
        """Test that an invalid name length is not accepted by the form."""
        form_data = {
            'name': 'A' * 51,
            'description': 'A team',
            'members': self.second_user.username,
        }
        form = TeamForm(data=form_data, owner=self.owner)
        self.assertFalse(form.is_valid())

    def test_team_form_invalid_description(self):
        """Test that an invalid description is not accepted by the form."""
        form_data = {
            'name': 'New Team',
            'description': 'A' * 501,
            'members': self.second_user.username,
        }
        form = TeamForm(data=form_data, owner=self.owner)
        self.assertFalse(form.is_valid())

    def test_team_form_multiple_valid_invites(self):
        """Test that multiple invitations can be sent to the same user."""
        form_data = {
            'name': 'New Team',
            'description': 'A team',
            'members': self.second_user.username + ', ' + self.third_user.username,
        }
        form = TeamForm(data=form_data, owner=self.owner)
        self.assertTrue(form.is_valid())

    def test_team_form_duplicate_invites(self):
        """Test that duplicate invitations cannot be sent to the same user."""
        form_data = {
            'name': 'New Team',
            'description': 'A team',
            'members': self.second_user.username + ', ' + self.second_user.username,
        }
        form = TeamForm(data=form_data, owner=self.owner)
        self.assertFalse(form.is_valid())
        self.assertIn("You have a duplicate entry for @janedoe in the team.", form.errors['members'])

    def test_team_form_add_self_as_member(self):
        """Test that the owner cannot add themselves as a member."""
        form_data = {
            'name': 'New Team',
            'description': 'A team',
            'members': self.owner.username,
        }
        form = TeamForm(data=form_data, owner=self.owner)
        self.assertFalse(form.is_valid())
        self.assertIn("You cannot add yourself to the team.", form.errors['members'])

    def test_team_form_nonexistent_member(self):
        """Test that a nonexistent member cannot be added to a team."""
        form_data = {
            'name': 'New Team',
            'description': 'A team',
            'members': '@nonexistentuser',
        }
        form = TeamForm(data=form_data, owner=self.owner)
        self.assertFalse(form.is_valid())

class TeamFormTestWithExistingTeam(TestCase):
    """Unit tests for the TeamForm when editing team."""
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/other_teams.json',
    ]

    def setUp(self):
        """Set up the test case."""
        self.owner = User.objects.get(username='@johndoe')
        self.second_user = User.objects.get(username='@janedoe')
        self.third_user = User.objects.get(username='@petrapickles')
        self.team = Team.objects.get(pk=1)
        self.team_other = Team.objects.get(pk=2)
        self.existing_team_pk = 1 

    def test_form_with_existing_team_pk(self):
        """Test that the form has a team when an existing primary key (pk) is provided."""
        form = TeamForm(owner=self.owner, pk=self.existing_team_pk)
        self.assertIsNotNone(form.team)
        self.assertEqual(form.team.id, self.existing_team_pk)

    def test_form_with_nonexistent_team_pk(self):
        """Test that the form does not have a team when a nonexistent team PK is provided."""
        form = TeamForm(owner=self.owner, pk=4)
        self.assertIsNone(form.team)

    def test_form_initialization_without_owner(self):
        """Test that the owner is set to None when owner_username is not provided."""
        form = TeamForm()
        self.assertIsNone(form.owner)

    def test_edit_team_remove_member(self):
        """Test that a member can be removed from the team."""
        self.team_other.members.add(self.second_user)
        form_data = {
            'name': 'Test Team',
            'description': 'Example description',
            'members': '',
            'remove_members': [self.second_user.id]
        }
        form = TeamForm(data=form_data, owner=self.owner, pk=self.team_other.id)
        self.assertTrue(form.is_valid())
    def test_edit_team_remove_multiple_members(self):
        """Test that multiple members can be removed from the team."""
        self.team_other.members.add(self.second_user)
        self.team_other.members.add(self.third_user)
        form_data = {
            'name': 'Test Team',
            'description': 'Example description',
            'members': '',
            'remove_members': [self.second_user.id, self.third_user.id]
        }
        form = TeamForm(data=form_data, owner=self.owner, pk=self.team_other.id)
        self.assertTrue(form.is_valid())

    def test_inviting_user_to_team(self):
        """Test that a user can be invited to a team."""
        form_data = {
            'name': 'New Team',
            'description': 'A team',
            'members': self.second_user.username,
        }
        form = TeamForm(data=form_data, owner=self.owner, pk=self.team.id)
        self.assertTrue(form.is_valid())

    def test_inviting_multiple_users_to_team(self):
        """Test that multiple users can be invited to a team."""
        form_data = {
            'name': 'New Team',
            'description': 'A team',
            'members': self.second_user.username + ', ' + self.third_user.username,
        }
        form = TeamForm(data=form_data, owner=self.owner, pk=self.team.id)
        self.assertTrue(form.is_valid())

    def test_inviting_existing_member(self):
        """Test that an existing member cannot be added to a team."""
        form_data = {
            'name': self.team_other.name,
            'description': self.team_other.description,
            'members': self.second_user.username,
        }
        form = TeamForm(data=form_data, owner=self.owner, pk=self.team_other.id)
        self.assertFalse(form.is_valid())
        self.assertIn("@janedoe is already a member of the team.", form.errors['members'])

    def test_adding_member_with_pending_invitation(self):
        """Test that a member with a pending invitation cannot be reinvited to a team."""
        Invitation.objects.create(sender=self.owner, recipient=self.second_user, team=self.team)
        form_data = {
            'name': self.team.name,
            'description': self.team.description,
            'members': self.second_user.username,
        }
        form = TeamForm(data=form_data, owner=self.owner, pk=self.team.id)
        self.assertFalse(form.is_valid())
        self.assertIn("Invitation already pending for @janedoe.", form.errors['members'])

    def test_team_form_invite_after_already_invited(self):
        """Test that a user cannot be invited after already being invited."""
        Invitation.objects.create(sender=self.owner, recipient=self.second_user, team=self.team)
        form_data = {
            'name': 'New Team',
            'description': 'A team',
            'members': self.second_user.username,
        }
        form = TeamForm(data=form_data, owner=self.owner, pk=self.team.id)
        self.assertFalse(form.is_valid())
        self.assertIn("Invitation already pending for @janedoe.", form.errors['members'])