"""Tests correct filters applied to Team Detail view."""
from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Team, Task
from tasks.filters import *

class TeamDetailTaskFilterTestCase(TestCase):
   """Tests of the team detail unique task filters."""

   fixtures = [
      'tasks/tests/fixtures/default_user.json',
      'tasks/tests/fixtures/other_users.json',
      'tasks/tests/fixtures/default_team.json',
      'tasks/tests/fixtures/other_teams.json',
      'tasks/tests/fixtures/default_task.json',
      'tasks/tests/fixtures/other_tasks.json'
   ]

   def setUp(self):
      """Creates users, teams, and tasks."""
      #Users
      self.user = User.objects.get(username='@johndoe')
      self.user.set_password('password')
      self.user.save()

      #Teams
      self.team = Team.objects.get(name='Test Team')
      self.second_team = Team.objects.get(name='Test Team 2')

      #Tasks
      self.task = Task.objects.get(title='Third Test Task')

   def test_correct_queryset_passed(self):
      """Test for only tasks belonging to the team is displayed."""
      #Test for Default User
      self.client.login(username='@johndoe', password='password')
      response = self.client.get(reverse('team_detail', args=[self.team.id]))
      self.assertEqual(response.status_code, 200)

      filter_form = TeamTaskFilter(queryset=Task.objects.filter(team=self.team))
      filtered_tasks = list(filter_form.qs)
      self.assertEqual(len(filtered_tasks), 2)
      self.assertQuerysetEqual(filtered_tasks, Task.objects.filter(team=self.team.id))
   
   def test_team_tasks_not_assigned_to_client(self):
      """Test for tasks that are not assigned to client can be viewed."""
      self.client.login(username='@johndoe', password='password')
      response = self.client.get(reverse('team_detail', args=[self.second_team.id]))
      self.assertEqual(response.status_code, 200)

      filter_form = TeamTaskFilter(queryset=Task.objects.filter(team=self.second_team)).qs
      filtered_tasks = list(filter_form)
      self.assertEqual(len(filtered_tasks), 1)
      self.assertNotEqual(filtered_tasks, Task.objects.filter(team=self.second_team.id).filter(assigned_to=self.user.id))
      self.assertEqual(filtered_tasks, [self.task])

   def test_correct_status_options(self):
      """Test for choices listed for Status filter is correct to user."""
      self.client.login(username='@johndoe', password='password')
      response = self.client.get(reverse('team_detail', args=[self.team.id]))
      self.assertEqual(response.status_code, 200)

      filter_form = TeamTaskFilter(queryset=Task.objects.filter(team=self.team))
      task_statuses = [('Not Started', 'Not Started'), ('In Progress', 'In Progress'), ('Complete', 'Complete')]
      self.assertQuerysetEqual(filter_form.filters['status'].extra['choices'], task_statuses)

   #--------------- Tests for Team Detail Filter General Functionality ------------------------------------#
   def test_correct_result_for_title_common(self):
      """Test for tasks with title containing similar substring is displayed."""
      #Test for identical keyword in all task titles & case insensitivity
      filter_params = {'title__icontains': 'test task'}
      filtered_products = (TeamTaskFilter(filter_params, queryset=Task.objects.all())).qs
      filtered_items = list(filtered_products)
        
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(title__icontains='test task'))

   def test_correct_result_for_title_unique(self):
      """Test for tasks with title containing a unique substring is displayed."""
      #Test for identical keyword in all task titles & case insensitivity
      filter_params = {'title__icontains': 'second'}
      filtered_products = (TeamTaskFilter(filter_params, queryset=Task.objects.all())).qs
      filtered_items = list(filtered_products)
        
      self.assertEqual(len(filtered_items), 1)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(title__icontains='second'))

   def test_correct_result_for_status(self):
      """Test for tasks with correct status."""
      filter_params = {'status': 'In Progress'}
      filtered_products = (TeamTaskFilter(filter_params, queryset=Task.objects.all())).qs
      filtered_items = list(filtered_products)
        
      self.assertEqual(len(filtered_items), 1)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(status='In Progress'))
   
   def test_correct_result_for_priority(self):
      """Test for tasks with correct priority."""
      filter_params = {'priority': '2'}
      filtered_products = (TeamTaskFilter(filter_params, queryset=Task.objects.all())).qs
      filtered_items = list(filtered_products)
        
      self.assertEqual(len(filtered_items), 1)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(priority='2'))

   def test_correct_result_for_start_due_date(self):
      """Test for tasks due on and after start due date."""
      filter_params = {'startDate': '2024-10-12T00:00:00+00:00'}
      filtered_products = (TeamTaskFilter(filter_params, queryset=Task.objects.all())).qs
      filtered_items = list(filtered_products)

      self.assertEqual(len(filtered_items), 2)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(due_date__gte='2024-10-12T00:00:00+00:00'))

   def test_correct_result_for_end_due_date(self):
      """Test for tasks due on and before end due date."""
      filter_params = {'endDate': '2024-10-11T00:00:00+00:00'}
      filtered_products = (TeamTaskFilter(filter_params, queryset=Task.objects.all())).qs
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 2)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(due_date__lte='2024-10-11T00:00:00+00:00'))
      
   def test_correct_result_for_due_date_range(self):
      """Test for tasks in correct due date range."""
      #Test for tasks due on and before end date displayed.
      filter_params = {
         'startDate': '2024-10-11T00:00:00+00:00',
         'endDate': '2024-10-23T00:00:00+00:00'
         }
      filtered_products = (TeamTaskFilter(filter_params, queryset=Task.objects.all())).qs
      filtered_items = list(filtered_products)
        
      self.assertEqual(len(filtered_items), 3)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(due_date__gte='2024-10-11T00:00:00+00:00', due_date__lte='2024-10-23T00:00:00+00:00'))

   def test_correct_result_for_username_search(self):
      """Test for tasks assigned to user with username containing substring displayed."""
      filter_params = {'assigned_to__username': 'john'}
      
      filtered_products = TeamTaskFilter(filter_params, queryset=Task.objects.all()).qs
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 1)
      check_against = Task.objects.filter(assigned_to=self.user.id)
      self.assertQuerysetEqual(filtered_items, check_against)

   def test_correct_sort_due_date_increasing(self):
      """Test for tasks ordered by due date increasing."""
      filter = TeamTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'dateUp')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('due_date'))

   def test_correct_sort_due_date_decreasing(self):
      """Test for tasks ordered by due date decreasing."""
      filter = TeamTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'dateDown')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('-due_date'))

   def test_correct_sort_creation_date_increasing(self):
      """Test for tasks ordered by creation date increasing."""
      filter = TeamTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'creationUp')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('created_at'))

   def test_correct_sort_creation_date_increasing(self):
      """Test for tasks ordered by creation date decreasing."""
      filter = TeamTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'creationDown')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('-created_at'))

   def test_correct_sort_priority_increasing(self):
      """Test for tasks ordered by priority increasing."""
      filter = TeamTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'priorityUp')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('priority'))

   def test_correct_sort_priority_decreasing(self):
      """Test for tasks ordered by priority decreasing."""
      filter = TeamTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'priorityDown')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('-priority'))

   def test_correct_sort_title(self):
      """Test for tasks ordered by title alphabetically."""
      filter = TeamTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'alphabetical')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('title'))

   def test_correct_sort_status(self):
      """Test for tasks ordered by status alphabetically."""
      filter = TeamTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'status')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('status'))