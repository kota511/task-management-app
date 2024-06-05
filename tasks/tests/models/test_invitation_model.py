"""Unit tests for the Invitation model."""
from django.db import IntegrityError
from django.core.exceptions import ValidationError, PermissionDenied
from django.test import TestCase
from tasks.models import User, Team, Invitation

from django.utils import timezone
from datetime import timedelta

class InvitationModelTestCase(TestCase):
    """Unit tests for the Invitation Model."""
    
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/other_teams.json',
        'tasks/tests/fixtures/default_invitation.json',
        'tasks/tests/fixtures/other_invitations.json',
    ]

    def setUp(self):
        """Set up the test"""
        self.sender = User.objects.get(username='@johndoe')
        self.recipient = User.objects.get(username="@janedoe")
        self.team = Team.objects.get(pk=1)
        self.invitation = Invitation.objects.get(pk=1)
    
    # Testing the sender field
    def test_sender_is_team_owner(self):
        """Test that the sender is the owner of the team"""
        self.invitation.team.owner = self.recipient
        self._assert_invitation_is_invalid()

    # Testing the recipient field
    def test_sender_must_not_be_recipient(self):
        """Test that the sender is not the recipient"""
        self.invitation.recipient = self.invitation.sender
        self._assert_invitation_is_invalid()

    def test_recipient_must_not_be_in_team(self):
        """Test that the recipient is not in the team"""
        second_team = Team.objects.get(pk=2)
        self.invitation.team = second_team
        self._assert_invitation_is_invalid()

    def test_invitation_is_deleted_when_recipient_is_deleted(self):
        """Test that the invitation is deleted when the recipient is deleted"""""
        invitation_id = self.invitation.id
        self.recipient.delete() 
        with self.assertRaises(Invitation.DoesNotExist):
            Invitation.objects.get(id=invitation_id)

    # Testing the team field
    def test_invitation_is_deleted_when_team_is_deleted(self):
        """Test that the invitation is deleted when the team is deleted"""""
        invitation_id = self.invitation.id
        self.team.delete() 
        with self.assertRaises(Invitation.DoesNotExist):
            Invitation.objects.get(id=invitation_id)

    def test_invitation_must_be_unique(self):
        """Test that the invitation is unique"""
        try:
            Invitation.objects.create(
                sender=self.sender,
                recipient=self.recipient,
                team=self.team
            )
        except IntegrityError as e:
            self.assertTrue("UNIQUE constraint failed" in str(e))
        else:
            self.fail("Creating duplicate invitation should raise IntegrityError")

    # Testing the message field
    def test_message_may_be_blank(self):
        """Test that the message may be blank"""
        self.invitation.message = ''
        self._assert_invitation_is_valid()

    def test_message_may_not_be_unique(self):
        """Test that the message may not be unique"""
        second_invitation = Invitation.objects.get(pk=2)
        self.invitation.message = second_invitation.message
        self._assert_invitation_is_valid()
    
    def test_message_may_contain_500_characters(self):
        """Test that the message may contain 500 characters"""
        self.invitation.message = 'x' * 500
        self._assert_invitation_is_valid()

    def test_message_may_not_contain_501_characters(self):
        """Test that the message may not contain 501 characters"""
        self.invitation.message = 'x' * 501
        self._assert_invitation_is_invalid()

    # Testing the accept invitation method
    def test_invitation_can_only_be_accepted_by_recipient(self):
        """Test that the invitation can only be accepted by the recipient"""
        other_user = User.objects.get(pk=3)
        with self.assertRaises(PermissionDenied):
            self.invitation.accept_invitation(other_user)

    def test_invitation_can_only_be_accepted_once(self):
        """Test that the invitation can only be accepted once"""
        invitation_id = self.invitation.id
        self.invitation.accept_invitation(self.recipient)
        with self.assertRaises(Invitation.DoesNotExist):
            Invitation.objects.get(id=invitation_id)  

    # Testing the decline invitation method
    def test_invitation_can_only_be_declined_by_recipient(self):
        """Test that the invitation can only be declined by the recipient"""
        other_user = User.objects.get(pk=3)
        with self.assertRaises(PermissionDenied):
            self.invitation.decline_invitation(other_user)

    def test_invitation_can_only_be_declined_once(self):
        """Test that the invitation can only be declined once"""
        invitation_id = self.invitation.id
        self.invitation.decline_invitation(self.recipient)
        with self.assertRaises(Invitation.DoesNotExist):
            Invitation.objects.get(id=invitation_id)

    def test_team_owner_send_multiple_invitations(self):
        """Test that the team owner can send multiple invitations to different recipients"""
        second_recipient = User.objects.get(pk=3)
        invitation_2 = Invitation.objects.get(pk=2)

        self.assertEqual(self.invitation.sender, self.sender)
        self.assertEqual(invitation_2.sender, self.sender)
        self.assertEqual(self.invitation.recipient, self.recipient)
        self.assertEqual(invitation_2.recipient, second_recipient)
        self.assertEqual(self.invitation.team, self.team)
        self.assertEqual(invitation_2.team, self.team)

    def test_recipient_receive_invitations_from_different_teams(self):
        """Test that the recipient can receive invitations from different teams"""
        invitation_2 = Invitation.objects.get(pk=3)

        self.assertEqual(self.invitation.recipient, self.recipient)
        self.assertEqual(invitation_2.recipient, self.recipient)
        self.assertNotEqual(self.invitation.team, invitation_2.team)
        self.assertNotEqual(self.invitation.sender, invitation_2.sender)

    def test_created_at_set_on_creation(self):
        """Test that the created_at field is set on creation"""
        self.assertIsNotNone(self.invitation.created_at)

    def _assert_invitation_is_valid(self):
        """Assert that the invitation is valid"""
        try:
            self.invitation.full_clean()
        except(ValidationError):
            self.fail("Test invitation should be valid")

    def _assert_invitation_is_invalid(self):
        """Assert that the invitation is invalid"""
        with self.assertRaises(ValidationError):
            self.invitation.full_clean()
