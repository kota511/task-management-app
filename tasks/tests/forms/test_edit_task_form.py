"""Unit tests of the edit task form."""
from django.test import TestCase
from tasks.forms import EditTaskForm
from tasks.models import Task, User, Team
from django import forms
from django.utils import timezone
from datetime import timedelta

class EditTasksFormTestCase(TestCase):
    """Unit tests of the edit task form."""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_task.json',
        'tasks/tests/fixtures/default_team.json'
    ]

    def setUp(self):
        """Set up the test"""
        self.user = User.objects.get(username='@johndoe')

        self.team = Team.objects.get(pk = 1)

        self.task = Task.objects.get(pk=1)

        self.form_input = {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'due_date': self.task.due_date + timedelta(days=1),
            'assigned_to': self.user.id,
            'status': Task.TaskStatus.IN_PROGRESS,
            'priority': 2,
            'team': self.team.id
        }

        self.emptyForm = EditTaskForm(pk=self.team.pk)

    # Test form accepts valid input data
    def test_valid_edit_task_form(self):
        """Test that the form accepts valid input data"""
        task_instance = Task(
            title='Original Title',
            team=self.team,
            assigned_to=self.user
        )
        form = EditTaskForm(data=self.form_input, pk=self.team.pk, instance=task_instance)
        self.assertTrue(form.is_valid())

    # Testing form has necessary fields
    def test_form_has_necessary_fields(self):
        """Test that the form has all the necessary fields"""
        self.assertIn('title', self.emptyForm.fields)
        self.assertIn('description', self.emptyForm.fields)
        self.assertIn('due_date', self.emptyForm.fields)
        self.assertIn('assigned_to', self.emptyForm.fields)
        self.assertIn('status', self.emptyForm.fields)
        self.assertIn('priority', self.emptyForm.fields)

    # Test the field types of each form are correct
    def test_title_is_charfield(self):
        """Test that the title field is a CharField"""
        title_field = self.emptyForm.fields['title']
        self.assertTrue(isinstance(title_field, forms.CharField))

    def test_description_is_charfield(self):
        """Test that the description field is a CharField"""
        description_field = self.emptyForm.fields['description']
        self.assertTrue(isinstance(description_field, forms.CharField))

    def test_due_date_is_datetimefield(self):
        """Test that the due_date field is a DateTimeField"""
        due_date_field = self.emptyForm.fields['due_date']
        self.assertTrue(isinstance(due_date_field, forms.DateTimeField))

    def test_assigned_to_is_foreignkeyfield(self):
        """Test that the assigned_to field is a ForeignKeyField"""
        assigned_to_field = self.emptyForm.fields['assigned_to']
        self.assertTrue(isinstance(assigned_to_field, forms.ModelChoiceField))

    def test_status_is_choicefield(self):
        """Test that the status field is a ChoiceField"""
        status_field = self.emptyForm.fields['status']
        self.assertTrue(isinstance(status_field, forms.ChoiceField))

    def test_priority_is_integerfield(self):
        """Test that the priority field is an IntegerField"""
        priority_field = self.emptyForm.fields['priority']
        self.assertTrue(isinstance(priority_field, forms.IntegerField))

    # Test the field types of each form are correct
    def test_form_uses_model_validation_for_title(self):
        """Test that the form uses model validation for the title field"""
        self.form_input['title'] = ''
        task_instance = Task(
            title='Original Title',
            team=self.team, 
            assigned_to=self.user
        )
        form = EditTaskForm(data=self.form_input, pk=self.team.pk, instance=task_instance)
        self.assertFalse(form.is_valid())

    # Testing the assigned to field
    def test_assigned_to_queryset(self):
        """Test that the assigned_to field only contains users in the team"""
        self.user_not_in_team = User.objects.create(username='user1', email='user1@example.org')
        self.user_not_in_second_team = User.objects.create(username='user2', email='user2@example.org')
        form = EditTaskForm(pk=self.team.pk)

        assigned_to_queryset = form.fields['assigned_to'].queryset

        self.assertIn(self.user, assigned_to_queryset)
        self.assertNotIn(self.user_not_in_team, assigned_to_queryset)
        self.assertNotIn(self.user_not_in_second_team, assigned_to_queryset)

    def test_assigned_to_queryset_when_team_does_not_exist(self):
        """Test that the assigned_to field's queryset is empty when the team does not exist"""
        non_existent_team_pk = 9999

        form = EditTaskForm(pk=non_existent_team_pk)

        assigned_to_queryset = form.fields['assigned_to'].queryset
        self.assertFalse(assigned_to_queryset.exists())
