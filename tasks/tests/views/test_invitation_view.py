"""Tests of the invitation view."""
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from tasks.models import User, Team, Invitation
from tasks.tests.helpers import reverse_with_next


class InvitationViewTestCase(TestCase):
    """Tests of the invitation view."""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/default_invitation.json'
    ]

    def setUp(self):
        """Set up the test"""
        self.url = reverse('view_invitation')
        self.user = User.objects.get(username='@janedoe')
        self.user.set_password('password')
        self.user.save()

        self.invitation = Invitation.objects.get(pk=1)
    
    def test_view_invitation_url(self):
        """Test that the view invitation url is '/view_invitation/'"""
        self.assertEqual(self.url,'/view_invitation/')

    def test_get_view_invitation(self):
        """Test that the view invitation page is rendered correctly"""
        self.client.login(username='@janedoe', password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_invitation.html')
    
    def test_accept_valid_invitation(self):
        """Test that a valid invitation is accepted"""
        self.client.login(username='@janedoe', password='password')
        before_count = Invitation.objects.count()
        response = self.client.post(reverse('view_invitation'), {'accept_invitation': self.invitation.id})
        after_count = Invitation.objects.count()
        self.assertEqual(after_count, before_count-1)
        self.assertEqual(response.status_code, 302)
        
    def test_accept_invalid_invitation(self):
        """Test that an invalid invitation is not accepted"""
        self.user = User.objects.get(username='@johndoe')
        self.user.set_password('password')
        self.user.save()
        self.client.login(username='@johndoe', password='password')
        before_count = Invitation.objects.count()
        response = self.client.post(reverse('view_invitation'), {'accept_invitation': self.invitation.id})
        after_count = Invitation.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 302)

    def test_decline_valid_invitation(self):
        """Test that a valid invitation is declined"""
        self.client.login(username='@janedoe', password='password')
        before_count = Invitation.objects.count()
        response = self.client.post(reverse('view_invitation'), {'decline_invitation': self.invitation.id})
        after_count = Invitation.objects.count()
        self.assertEqual(after_count, before_count-1)
        self.assertEqual(response.status_code, 302)
    
    def test_decline_invalid_invitation(self):
        """Test that an invalid invitation is not declined"""
        self.user = User.objects.get(username='@johndoe')
        self.user.set_password('password')
        self.user.save()
        self.client.login(username='@johndoe', password='password')
        before_count = Invitation.objects.count()
        response = self.client.post(reverse('view_invitation'), {'decline_invitation': self.invitation.id})
        after_count = Invitation.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 302)
    
    def test_invitation_does_not_exist(self):
        """Test that an invitation that does not exist is not accepted"""
        self.client.login(username='@janedoe', password='password')
        recipient = self.invitation.recipient
        response = self.client.post(self.url, {'decline_invitation': 999, 'user': recipient})
        self.assertEqual(response.status_code, 302)
    
    def test_invitation_list(self):
        """Test that the invitation list is rendered correctly"""
        self.client.login(username='@janedoe', password='password')
        self._create_test_invitations(settings.INVITATIONS_PER_PAGE)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_invitation.html')
        self.assertEqual(len(response.context['invitations']), settings.INVITATIONS_PER_PAGE)
        self.assertFalse(response.context['is_paginated'])
        for invitation_id in range(1, settings.INVITATIONS_PER_PAGE+1):
            invitation = Invitation.objects.get(pk=invitation_id)
            self.assertContains(response, invitation.sender.username)
            self.assertContains(response, invitation.team.name)
            self.assertContains(response, invitation.message)

    def test_invitation_list_with_pagination(self):
        """Test that the invitation list is paginated correctly"""
        self.client.login(username='@janedoe', password='password')
        self._create_test_invitations(2*settings.INVITATIONS_PER_PAGE)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_invitation.html')
        self.assertEqual(len(response.context['invitations']), settings.INVITATIONS_PER_PAGE)
        self.assertTrue(response.context['is_paginated'])

        # Test if the first page is accessible
        page_one_url = reverse('view_invitation') + '?page=1'
        response = self.client.get(page_one_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_invitation.html')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['invitations']), settings.INVITATIONS_PER_PAGE)
        page_obj = response.context['page_obj']
        self.assertFalse(page_obj.has_previous())
        self.assertTrue(page_obj.has_next())

        # Test if the second page is accessible
        page_two_url = reverse('view_invitation') + '?page=2'
        response = self.client.get(page_two_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_invitation.html')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['invitations']), settings.INVITATIONS_PER_PAGE)
        page_obj = response.context['page_obj']
        self.assertTrue(page_obj.has_previous())
        self.assertFalse(page_obj.has_next())

    def test_get_invitation_list_redirects_when_not_logged_in(self):
        """Test that the invitation list redirects to the login page when the user is not logged in"""
        redirect_url = reverse_with_next('log_in', self.url)
        response = self.client.get(self.url)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
    
    def test_invitation_list_filtering(self):
        """Test that the invitation list is filtered correctly"""
        self.client.login(username='@janedoe', password='password')
        response = self.client.get(reverse('view_invitation'))

        self.assertQuerysetEqual(
            response.context['invitations'],
            Invitation.objects.filter(recipient=self.user),
            transform=lambda x: x
        )

        sender = User.objects.get(username='@johndoe')
        self.assertNotIn(
            sender,
            [invitation.recipient for invitation in response.context['invitations']]
        )

    def test_redirect_after_actions(self):
        """Test that the user is redirected to the invitation list after accepting or declining an invitation"""
        self.client.login(username='@janedoe', password='password')
        response = self.client.post(reverse('view_invitation'), {'accept_invitation': self.invitation.id})
        self.assertRedirects(response, reverse('view_invitation'))

    def test_error_messages_display(self):
        """Test that error messages are displayed correctly"""
        self.client.login(username='@janedoe', password='password')
        response = self.client.post(reverse('view_invitation'), {'invalid_action': self.invitation.id})
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(messages)
        self.assertEqual(messages[0].tags, 'danger')
        self.assertEqual(messages[0].message, 'Invalid Action')


    def _create_test_invitations(self, number_of_invitations):
        """Create test invitations"""
        sender = User.objects.get(username='@johndoe')
        for i in range(2, number_of_invitations+1):
            Team.create_team(f"Team {i}", "Hello", self.user)
            team = Team.objects.get(pk=i)
            Invitation.objects.create(sender=sender, team=team, recipient=self.user, message=f"Invitation {i+1}")