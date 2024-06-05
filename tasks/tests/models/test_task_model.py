"""Unit tests for the Task model."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import User, Team, Task

from django.utils import timezone
from datetime import timedelta

class TaskModelTestCase(TestCase):
    """Unit tests for the Task Model."""
    
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/default_task.json',
        'tasks/tests/fixtures/other_tasks.json',
        'tasks/tests/fixtures/other_teams.json',
    ]

    def setUp(self):
        """Set up the test"""
        self.user = User.objects.get(username='@johndoe')
        self.team = Team.objects.get(pk=1)
        self.task = Task.objects.get(pk=1)

    def test_valid_task(self):
        """Test that the task is valid."""
        self._assert_task_is_valid()

    # Testing the title field
    def test_str_method(self):
        """Test the string representation of the Task model."""
        task_title = "Sample Task"
        task = Task.objects.create(
            title=task_title,
            description='Sample Description',
            due_date=timezone.now() + timedelta(days=1),
            team=self.team,
            assigned_to=self.user,
            status=Task.TaskStatus.NOT_STARTED,
            priority=1
        )
        self.assertEqual(str(task), task_title, "The __str__ method should return the task title.")

    def test_title_cannot_be_blank(self):
        """Test that the title field cannot be blank."""
        self.task.title = ''
        self._assert_task_is_invalid()
    
    def test_title_can_be_50_characters_long(self):
        """Test that the title field can be 50 characters long."""
        self.task.title = 'x' * 50
        self._assert_task_is_valid()

    def test_title_cannot_be_51_characters_long(self):
        """Test that the title field cannot be 51 characters long."""
        self.task.title = 'x' * 51
        self._assert_task_is_invalid()

    def test_title_may_not_be_unique(self):
        """Test that the title field may not be unique."""
        second_task = Task.objects.get(pk=2)
        self.task.title = second_task.title
        self._assert_task_is_valid()
    
    def test_title_must_contain_alphabets(self):
        """Test that the title field must contain alphabets."""
        self.task.title = '123'
        self._assert_task_is_invalid()

    # Testing the description field
    def test_description_may_be_blank(self):
        """Test that the description field may be blank."""
        self.task.description = ''
        self._assert_task_is_valid()

    def test_description_may_not_be_unique(self):
        """Test that the description field may not be unique."""
        second_task = Task.objects.get(pk=2)
        self.task.description = second_task.description
        self._assert_task_is_valid()
    
    def test_description_may_contain_500_characters(self):
        """Test that the description field may contain 500 characters."""
        self.task.description = 'x' * 500
        self._assert_task_is_valid()

    def test_description_may_not_contain_501_characters(self):
        """Test that the description field may not contain 501 characters."""
        self.task.description = 'x' * 501
        self._assert_task_is_invalid()

    # Testing the due date field
    def test_due_date_must_be_in_future(self):
        """Test that the due date field must be in the future."""
        self.task.due_date = timezone.now() + timedelta(days=5)
        self._assert_task_is_valid()

    def test_due_date_can_not_be_in_past(self):
        """Test that the due date field can not be in the past."""
        self.task.due_date = timezone.now() - timedelta(days=2)
        self._assert_task_is_invalid()
    
    def test_due_date_validator_must_be_in_future(self):
        """Test that the due date validator must be in the future."""
        future_date = timezone.now() + timedelta(days=5)
        try:
            Task.validate_due_date_not_in_past(future_date)
        except ValidationError:
            self.fail("validate_due_date_not_in_past raised ValidationError unexpectedly.")

    def test_due_date_validator_can_not_be_in_past(self):
        """Test that the due date validator can not be in the past."""
        past_date = timezone.now() - timedelta(days=2)
        with self.assertRaises(ValidationError):
            Task.validate_due_date_not_in_past(past_date)

    # Testing the assigned to field
    def test_task_assigned_to_one_user(self):
        """Test that the task can be assigned to one user."""
        self.assertEqual(self.task.assigned_to, self.user)
        self._assert_task_is_valid()

    def test_assigned_to_user_must_be_in_the_same_team_as_owner(self):
        """Test that the assigned to user must be in the same team as the owner."""
        second_user = User.objects.get(username='@petrapickles')
        self.team.members.add(second_user)
        self.task.assigned_to = second_user
        self.assertIn(self.task.assigned_to, self.task.team.members.all())
        
        self._assert_task_is_valid()

    def test_assigned_to_user_can_not_be_in_a_different_team(self):
        """Test that the assigned to user can not be in a different team."""
        second_user = User.objects.get(username='@janedoe')
        self.assertNotIn(second_user, self.task.team.members.all())

        self.task.assigned_to = second_user 
        self._assert_task_is_invalid()

    # Testing the team field
    def test_task_is_deleted_upon_team_deletion(self):
        """Test that the task is deleted upon team deletion."""
        self.team.delete()
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_multiple_tasks_can_be_associated_with_1_team(self):
        """Test that multiple tasks can be associated with 1 team."""
        second_task = Task.objects.get(pk=2)
        second_task.team = self.team
        self.assertEqual(self.task.team, self.team)
        self.assertEqual(second_task.team, self.team)
    
    # Testing the priority field
    def test_valid_priority_value_accepted(self):
        """Test that valid priority values are accepted."""
        self.task.priority = 3
        self.task.save()
        self._assert_task_is_valid()

    def test_valid_priority_edge_value_accepted(self):
        """Test that valid priority edge values are accepted."""
        self.task.priority = 1
        self.task.save()
        self._assert_task_is_valid()
        self.task.priority = 5
        self.task.save()
        self._assert_task_is_valid()

    def test_invalid_priority_values_rejected(self):
        """Test that invalid priority values are rejected."""
        self.task.priority = 0
        self.task.save()
        self._assert_task_is_invalid()
        self.task.priority = 6
        self.task.save()
        self._assert_task_is_invalid()
    
    def test_priority_default_value(self):
        """Test that the default priority of a new task is 1."""
        new_task = Task.objects.create(
            title = "my title",
            description = 'desc',
            assigned_to = self.user,
            team = self.team,
            due_date = timezone.now() + timedelta(days = 1),
            status = Task.TaskStatus.NOT_STARTED
        )
        self.assertEqual(new_task.priority, 1)
    
    def test_priority_valid_range(self):
        """Test that priority accepts values within the valid range."""
        for valid_priority in range(1, 6):  # Assuming priority range is 1-5
            self.task.priority = valid_priority
            self._assert_task_is_valid()
    
    def test_priority_invalid_range(self):
        """Test that priority does not accept values outside the valid range."""
        for invalid_priority in [0, 6]:  # Values outside the 1-5 range
            self.task.priority = invalid_priority
            self._assert_task_is_invalid()
    
    # Testing the created at field
    def test_created_at_set_on_creation(self):
        """Test that the task created_at field is set on creation."""
        self.assertIsNotNone(self.task.created_at)
    
    def test_task_created_at_does_not_change(self):
        """Test that the task created_at field does not change on update."""
        initial_created_at = self.task.created_at
        self.task.description = "This is the new description for the test task"
        self.task.save()
        self.assertEqual(initial_created_at, self.task.created_at)

    def test_task_updated_at_changes_on_update(self):
        """Test that the task updated_at field changes on update."""
        initial_updated_at = self.task.updated_at
        self.task.description = "This is the new description for the test task"
        self.task.save()
        self.assertLess(initial_updated_at, self.task.updated_at)

    # Testing the status field
    def test_default_task_status(self):
        """Test that the default status of a new task is 'Not Started'."""
        new_task = Task.objects.create(
            title='New Task',
            description='A new task description',
            due_date=timezone.now() + timedelta(days=1),
            team=self.team,
            assigned_to = self.user
        )
        self.assertEqual(new_task.status, Task.TaskStatus.NOT_STARTED)

    def test_status_assignment(self):
        """Test that status can be assigned and saved correctly."""
        self.task.status = Task.TaskStatus.IN_PROGRESS
        self.task.save()
        self.task.refresh_from_db()  # Reload the task from the database
        self.assertEqual(self.task.status, Task.TaskStatus.IN_PROGRESS)

    def test_invalid_status_assignment(self):
        """Test that assigning an invalid status raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.task.status = 'invalid status'
            self.task.full_clean()

    def _assert_task_is_valid(self):
        """Assert that the task is valid."""
        try:
            self.task.full_clean()
        except ValidationError:
            self.fail("Task should be valid")

    def _assert_task_is_invalid(self):
        """Assert that the task is invalid."""
        with self.assertRaises(ValidationError):
            self.task.full_clean()
