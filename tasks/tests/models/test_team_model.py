"""Unit tests for the Team Model."""
from django.test import TestCase
from django.core.exceptions import ValidationError
from tasks.models import Team, User, Invitation, Task

class TeamModelTestCase(TestCase):
    """Unit tests for the Team Model."""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/other_tasks.json',
        'tasks/tests/fixtures/other_teams.json'
    ]

    def setUp(self):
        """Set up the test case."""
        self.user = User.objects.get(username='@johndoe')
        self.team = Team.objects.get(pk=1)
        self.second_team = Team.objects.get(pk=2)
        self.task = Task.objects.get(title='Second Test Task')
        self.second_user = User.objects.get(username='@janedoe')
        self.third_user = User.objects.get(username='@petrapickles')
        self.fourth_user = User.objects.get(username='@peterpickles')

    # Testing the team str method
    def test_team_str(self):
        """Test the string representation of the Team model."""
        team_name = "Test Team"
        team = Team.objects.create(name=team_name, description="Example description.", owner=self.user)
        self.assertEqual(str(team), team_name)

    # Testing the name field
    def test_name_cannot_be_blank(self):
        """Test that the name field cannot be blank."""
        self.team.name = ''
        self._assert_team_is_invalid()

    def test_name_must_contain_at_least_one_letter(self):
        """Test that the name field must contain at least one letter."""
        self.team.name = '1234567890'
        self._assert_team_is_invalid()

    def test_name_can_be_50_characters_long(self):
        """Test that the name field can be 50 characters long."""
        self.team.name = 'A' * 50
        self._assert_team_is_valid()

    def test_name_cannot_be_51_characters_long(self):
        """Test that the name field cannot be 51 characters long."""
        self.team.name = 'A' * 51
        self._assert_team_is_invalid()

    # Testing the description field
    def test_description_can_be_blank(self):
        """Test that the description field can be blank."""
        self.team.description = ''
        self._assert_team_is_valid()

    def test_description_cannot_exceed_500_characters(self):
        """Test that the description field cannot exceed 500 characters."""
        self.team.description = 'A' * 501
        self._assert_team_is_invalid()

    def test_team_can_have_multiple_members(self):
        """Test that a team can have multiple members."""
        self.team.members.add(self.second_user)
        self.assertEqual(self.team.members.count(), 2)

    # Testing the remove member method
    def test_remove_member(self):
        """Test removing a member from a team."""
        self.team.members.add(self.second_user)
        self.team.remove_member(self.second_user)
        self.assertFalse(self.team.members.filter(username = self.second_user.username).exists())

        self.assertFalse(Task.objects.filter(title=self.task.id).exists())

    def test_remove_member_fails_if_user_is_owner(self):
        """Test that removing the owner of the team fails."""
        self.assertFalse(self.team.remove_member(self.user))

    def test_remove_member_fails_if_user_is_not_a_member(self):
        """Test that removing a user who is not a member fails."""
        self.assertFalse(self.team.remove_member(self.second_user))

    # Testing the invitation feature
    def test_send_invitation_to_non_member(self):
        """Test sending an invitation to a non-member."""
        self.team.members.add(self.third_user)
        self.assertFalse(self.team.send_invitation(self.user, self.third_user))
    
    def test_send_invitation_to_self(self):
        """Test sending an invitation to yourself."""
        self.assertFalse(self.team.send_invitation(self.user, self.user))

    # Testing the create_team method
    def test_create_team(self):
        """Test creating a new team."""
        new_team = Team.create_team('New Team', 'Description', self.user, [self.fourth_user])
        self.assertIsInstance(new_team, Team)

    def test_create_team_message(self):
        """Test creating a new team with a message."""
        new_team = Team.create_team('New Team', 'Description', self.user, [self.fourth_user], 'Join my team')
        self.assertEqual(new_team.invitations.first().message, 'Join my team')

    def test_create_team_message(self):
        """Test creating a new team with a message."""
        new_team = Team.create_team('New Team', 'Description', self.user, [self.fourth_user], 'Join my team')
        invitation = Invitation.objects.filter(team=new_team, recipient=self.fourth_user).first()
        self.assertIsNotNone(invitation)
        self.assertEqual(invitation.message, 'Join my team')

    # Testing the edit_team member
    def test_edit_team(self):
        """Test editing a team."""
        self.team.edit_team(self.team.id, self.user, 'New Team', 'New Description', [self.fourth_user], 'Join my team')
        self.team.refresh_from_db()
        self.assertEqual(self.team.name, 'New Team')
        self.assertEqual(self.team.description, 'New Description')
        invitation = Invitation.objects.filter(team=self.team, recipient=self.fourth_user).first()
        self.assertIsNotNone(invitation)
        self.assertEqual(invitation.message, 'Join my team')

    def test_edit_team_no_invite(self):
        """Test editing a team."""
        self.team.edit_team(self.team.id, self.user, 'New Team', 'New Description')
        self.team.refresh_from_db()
        self.assertEqual(self.team.name, 'New Team')
        self.assertEqual(self.team.description, 'New Description')

    # Testing the delete_team method
    def test_delete_team_as_owner(self):
        """Test deleting a team as the owner."""
        temp_team = Team.create_team('Temp Team', 'Description', self.user)
        temp_team.owner = self.user
        self.assertTrue(temp_team.delete_team(self.user))

    def test_delete_team_as_member(self):
        """Test deleting a team as a member."""
        temp_team = Team.create_team('Temp Team', 'Description', self.user, [self.fourth_user])
        self.assertFalse(temp_team.delete_team([self.fourth_user]))

    def test_delete_member_as_owner(self):
        """Test deleting a member as the owner."""
        temp_team = Team.create_team('Temp Team', 'Description', self.user)
        temp_team.members.add(self.fourth_user)
        temp_team.edit_team(temp_team.id, self.user, temp_team.name, temp_team.description, remove_members=[self.fourth_user])
        temp_team.refresh_from_db()
        self.assertEqual(temp_team.members.count(), 1)
        self.assertNotIn(self.fourth_user, temp_team.members.all())

    def test_delete_member_as_member(self):
        """Test deleting a member as a member."""
        temp_team = Team.create_team('Temp Team', 'Description', self.user)
        temp_team.members.add(self.fourth_user)
        temp_team.edit_team(temp_team.id, self.fourth_user, temp_team.name, temp_team.description, remove_members=[self.user])
        temp_team.refresh_from_db()
        self.assertEqual(temp_team.members.count(), 2)
        self.assertIn(self.user, temp_team.members.all())

    def test_delete_member_as_non_member(self):
        """Test deleting a member as a non-member."""
        temp_team = Team.create_team('Temp Team', 'Description', self.user)
        temp_team.members.add(self.fourth_user)
        temp_team.edit_team(temp_team.id, self.third_user, temp_team.name, temp_team.description, remove_members=[self.user])
        temp_team.refresh_from_db()
        self.assertEqual(temp_team.members.count(), 2)
        self.assertIn(self.user, temp_team.members.all())
    
    def _assert_team_is_valid(self):
        """Assert that the team is valid."""
        try:
            self.team.full_clean()
        except ValidationError:
            self.fail("Team should be valid")

    def _assert_team_is_invalid(self):
        """Assert that the team is invalid."""
        with self.assertRaises(ValidationError):
            self.team.full_clean()