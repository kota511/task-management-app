"""Tests correct filters applied to Dashboard view."""
from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Team, Task
from tasks.filters import *

class DashboardTaskFilterTestCase(TestCase):
   """Tests of the dashboard unique task filters."""

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
      
      self.user = User.objects.get(username='@johndoe')
      self.user.set_password('password')
      self.user.save()
      self.second_user = User.objects.get(username='@janedoe')
      self.second_user.set_password('password')
      self.second_user.save()
      self.third_user = User.objects.get(username='@petrapickles')
      self.third_user.set_password('password')
      self.third_user.save()

      self.second_team = Team.objects.get(name='Test Team 2')
      self.task = Task.objects.get(title='Third Test Task') 

   def test_correct_queryset_passed(self):
      """Test for only tasks assigned to client is displayed."""
      #Test for Default User
      self.client.login(username='@johndoe', password='password')
      reponse = self.client.get(reverse('dashboard'))
      self.assertEqual(reponse.status_code, 200)

      filter_params = {}
      filtered_products = DashboardTaskFilter(filter_params, queryset=Task.objects.filter(assigned_to=self.user.id)).qs
      filtered_items = list(filtered_products)
        
      self.assertEqual(len(filtered_items), 1)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(assigned_to=self.user.id))
      self.client.logout()

      #Test for Other User - @janedoe
      self.client.login(username='@janedoe', password='password')
      response = self.client.get(reverse('dashboard'))
      self.assertEqual(response.status_code, 200)

      filter_params = {}
      filtered_products = DashboardTaskFilter(filter_params, queryset=Task.objects.filter(assigned_to=self.second_user.id)).qs
      filtered_items = list(filtered_products)
        
      self.assertEqual(len(filtered_items), 2)
      self.assertEqual(filtered_items[0].title, 'Second Test Task')
      self.assertEqual(filtered_items[1].title, 'Third Test Task')
      self.client.logout()

      #Test for Other User - @petrapickles
      self.client.login(username='@petrapickles', password='password')
      response = self.client.get(reverse('dashboard'))
      self.assertEqual(response.status_code, 200)

      filter_params = {}
      filtered_products = DashboardTaskFilter(filter_params, queryset=Task.objects.filter(assigned_to=self.third_user.id)).qs
      filtered_items = list(filtered_products)
        
      self.assertEqual(len(filtered_items), 1)
      self.assertEqual(filtered_items[0].title, 'Fourth Test Task')
      self.client.logout()
   
   def test_correct_status_options(self):
      """Test for choices listed for Status filter is correct to user."""
      self.client.login(username='@johndoe', password='password')
      response = self.client.get(reverse('dashboard'))
      self.assertEqual(response.status_code, 200)

      filter_form = DashboardTaskFilter(queryset=Task.objects.filter(assigned_to=self.user))
      task_statuses = [('Not Started', 'Not Started'), ('In Progress', 'In Progress'), ('Complete', 'Complete')]
      self.assertQuerysetEqual(filter_form.filters['status'].extra['choices'], task_statuses)

   #--------------- Tests for Dashboard Filter General Functionality ------------------------------------#
   def test_correct_result_for_title_common(self):
      """Test for tasks with title containing similar substring is displayed."""
      #Test for identical keyword in all task titles & case insensitivity
      filter_params = {'title__icontains': 'test task'}
      filtered_products = (DashboardTaskFilter(filter_params, queryset=Task.objects.all())).qs
      filtered_items = list(filtered_products)
        
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(title__icontains='test task'))

   def test_correct_result_for_title_unique(self):
      """Test for tasks with title containing a unique substring is displayed."""
      #Test for identical keyword in all task titles & case insensitivity
      filter_params = {'title__icontains': 'second'}
      filtered_products = (DashboardTaskFilter(filter_params, queryset=Task.objects.all())).qs
      filtered_items = list(filtered_products)
        
      self.assertEqual(len(filtered_items), 1)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(title__icontains='second'))

   def test_correct_result_for_status(self):
      """Test for tasks with correct status displayed."""
      filter_params = {'status': 'In Progress'}
      filtered_products = (DashboardTaskFilter(filter_params, queryset=Task.objects.all())).qs
      filtered_items = list(filtered_products)
        
      self.assertEqual(len(filtered_items), 1)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(status='In Progress'))
   
   def test_correct_result_for_priority(self):
      """Test for tasks with correct priority displayed."""
      filter_params = {'priority': '2'}
      filtered_products = (DashboardTaskFilter(filter_params, queryset=Task.objects.all())).qs
      filtered_items = list(filtered_products)
        
      self.assertEqual(len(filtered_items), 1)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(priority='2'))

   def test_correct_result_for_start_due_date(self):
      """Test for tasks due on and after start date displayed."""
      filter_params = {'startDate': '2024-10-12T00:00:00+00:00'}
      filtered_products = (DashboardTaskFilter(filter_params, queryset=Task.objects.all())).qs
      filtered_items = list(filtered_products)

      self.assertEqual(len(filtered_items), 2)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(due_date__gte='2024-10-12T00:00:00+00:00'))

   def test_correct_result_for_end_due_date(self):
      """Test for tasks due on and before end date displayed."""
      filter_params = {'endDate': '2024-10-11T00:00:00+00:00'}
      filtered_products = (DashboardTaskFilter(filter_params, queryset=Task.objects.all())).qs
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 2)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(due_date__lte='2024-10-11T00:00:00+00:00'))
      
   def test_correct_result_for_due_date_range(self):
      """Test for tasks due within due date range displayed."""
      filter_params = {
         'startDate': '2024-10-11T00:00:00+00:00',
         'endDate': '2024-10-23T00:00:00+00:00'
         }
      filtered_products = (DashboardTaskFilter(filter_params, queryset=Task.objects.all())).qs
      filtered_items = list(filtered_products)
        
      self.assertEqual(len(filtered_items), 3)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(due_date__gte='2024-10-11T00:00:00+00:00', due_date__lte='2024-10-23T00:00:00+00:00'))

   def test_correct_result_for_team(self):
      """Test for tasks assigned to correct team displayed."""
      filter_params = {'team__name': '2'}
      
      filtered_products = DashboardTaskFilter(filter_params, queryset=Task.objects.all()).qs
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 1)
      self.assertQuerysetEqual(filtered_items, Task.objects.filter(team=self.second_team.id))

   def test_correct_sort_due_date_increasing(self):
      """Test for tasks ordered by due date increasing."""
      filter = DashboardTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'dateUp')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('due_date'))

   def test_correct_sort_due_date_decreasing(self):
      """Test for tasks ordered by due date decreasing."""
      filter = DashboardTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'dateDown')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('-due_date'))

   def test_correct_sort_creation_date_increasing(self):
      """Test for tasks ordered by creation date increasing."""
      filter = DashboardTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'creationUp')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('created_at'))

   def test_correct_sort_creation_date_increasing(self):
      """Test for tasks ordered by creation date decreasing."""
      filter = DashboardTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'creationDown')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('-created_at'))

   def test_correct_sort_priority_increasing(self):
      """Test for tasks ordered by priority increasing."""
      filter = DashboardTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'priorityUp')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('priority'))

   def test_correct_sort_priority_decreasing(self):
      """Test for tasks ordered by priority decreasing."""
      filter = DashboardTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'priorityDown')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('-priority'))

   def test_correct_sort_title(self):
      """Test for tasks ordered by title alphabetically."""
      filter = DashboardTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'alphabetical')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('title'))

   def test_correct_sort_status(self):
      """Test for tasks ordered by status alphabetically."""
      filter = DashboardTaskFilter(queryset=Task.objects.all())
      filtered_products = filter.filters['sort'].filter(Task.objects.all(), 'status')
      filtered_items = list(filtered_products)
      
      self.assertEqual(len(filtered_items), 4)
      self.assertQuerysetEqual(filtered_items, Task.objects.order_by('status'))