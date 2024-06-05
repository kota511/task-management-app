"""Tests correct teams are displayed on Team Bar view."""
from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Team, Task

class DashboardTeamBarTestCase(TestCase):
   """Tests of the team bar for the current user"""

   fixtures = [
      'tasks/tests/fixtures/default_user.json',
      'tasks/tests/fixtures/other_users.json',
      'tasks/tests/fixtures/default_team.json',
      'tasks/tests/fixtures/other_teams.json'
   ]

   def setUp(self):
      """Creates users and teams."""
      self.user = User.objects.get(username='@johndoe')
      self.user.set_password('password')
      self.user.save()
      self.second_user = User.objects.get(username='@janedoe')
      self.second_user.set_password('password')
      self.second_user.save()
      self.team = Team.objects.get(name='Test Team')
      self.second_team = Team.objects.get(name='Test Team 2')
      self.third_team = Team.objects.get(name='Test Team 3')


   def test_correct_teams_displayed(self):
      """Test for the correct teams are displayed"""
      #Check for Default User
      self.client.login(username='@johndoe', password='password')
      response = self.client.get(reverse('dashboard'))
      self.assertEqual(response.status_code, 200)
      team_detail_urls1 = [
         reverse('team_detail', args=[self.team.id]), reverse('team_detail', args=[self.second_team.id])
      ]
      for url in team_detail_urls1:
         self.assertContains(response, url)
      self.client.logout()

      #Check for Other User
      self.client.login(username='@janedoe', password='password')
      response = self.client.get(reverse('dashboard'))
      self.assertEqual(response.status_code, 200)
      team_detail_urls1 = [
         reverse('team_detail', args=[self.second_team.id]), reverse('team_detail', args=[self.third_team.id])
      ]
      for url in team_detail_urls1:
         self.assertContains(response, url)
      self.client.logout()


   def test_no_incorrect_teams_displayed(self):
      """Test for the incorrect teams are not displayed"""
      #Check for Default User
      self.client.login(username='@johndoe', password='password')
      response = self.client.get(reverse('dashboard'))
      self.assertEqual(response.status_code, 200)
      self.assertNotContains(response, reverse('team_detail', args=[self.third_team.id]))
      self.client.logout()

      #Check for Other User
      self.client.login(username='@janedoe', password='password')
      response = self.client.get(reverse('dashboard'))
      self.assertEqual(response.status_code, 200)
      self.assertNotContains(response, reverse('team_detail', args=[self.team.id]))
      self.client.logout()