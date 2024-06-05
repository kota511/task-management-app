"""Unit tests of the create task form."""
from django.test import TestCase
from tasks.forms import CreateTaskForm
from tasks.models import Task, User, Team
from django import forms
from django.utils import timezone
from datetime import timedelta

class CreateTaskFormTestCase(TestCase):
    """Unit tests of the create task form."""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/default_team.json'
    ]

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.team = Team.objects.get(pk = 1)
        self.form_input = {
            'title': 'Valid Title',
            'description': 'Valid Description',
            'due_date': timezone.now() + timedelta(days=1),
            'assigned_to': self.user.pk,
            'status': Task.TaskStatus.NOT_STARTED,
            'priority': 1,
            'team': self.team.pk,
        }
        self.emptyForm = CreateTaskForm()

    # Testing form accepts valid input data
    def test_valid_create_task_form(self):
        """Test that the form accepts valid input data"""
        form = CreateTaskForm(data=self.form_input)
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

    # Testing form uses model validation
    def test_form_uses_model_validation_for_title(self):
        """Test that the form uses model validation for the title field"""
        self.form_input['title'] = ''
        form = CreateTaskForm(data=self.form_input)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    # Testing the priority field
    def test_priority_range_valid(self):
        """Test that the priority field is valid"""
        self.form_input['priority'] = 0
        form = CreateTaskForm(data=self.form_input)
        self.assertFalse(form.is_valid())
        self.assertIn('priority', form.errors)     

    # Testing form saves
    def test_form_saves_correctly(self):
        """Test that the form saves correctly"""
        form = CreateTaskForm(data=self.form_input)
        if form.is_valid():
            form.save()
            task = Task.objects.get(title='Valid Title') 
            self.assertEqual(task.description, 'Valid Description')
            self.assertEqual(task.assigned_to, self.user)
            self.assertEqual(task.team, self.team)
            self.assertEqual(task.status, Task.TaskStatus.NOT_STARTED)
            self.assertEqual(task.priority, 1)
        else:
            self.fail("Form is not valid.")
    
    # Testing the team attribute
    def test_assigned_user_must_be_team_member(self):
        """Test that an error is raised if the assigned user is not a team member"""
        non_member_user = User.objects.create(username='nonmember', password='password')
        self.form_input['assigned_to'] = non_member_user.pk
        form = CreateTaskForm(data=self.form_input, pk=self.team.pk)
        self.assertFalse(form.is_valid())
        self.assertIn("The assigned to user is not part of this team", form.errors['__all__'])

    def test_assigned_to_queryset_empty_if_team_does_not_exist(self):
        """Test that assigned_to queryset is empty if the team does not exist"""
        non_existent_team_id = 9999
        form = CreateTaskForm(pk=non_existent_team_id)
        self.assertEqual(form.fields['assigned_to'].queryset.count(), 0)
        