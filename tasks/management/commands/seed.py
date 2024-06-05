from typing import Any
from django.core.management.base import BaseCommand, CommandError

from tasks.models import User, Team, Task, Invitation
import datetime

import pytz
from faker import Faker
import random

from django.utils import timezone
from datetime import timedelta, datetime
from random import randint, random

user_fixtures = [
    {'username': '@janedoe', 'email': 'jane.doe@example.org', 'first_name': 'Jane', 'last_name': 'Doe'},
    {'username': '@charlie', 'email': 'charlie.johnson@example.org', 'first_name': 'Charlie', 'last_name': 'Johnson'},
    {'username': '@sarah', 'email': 'sarah.johnson@example.org', 'first_name': 'Sarah', 'last_name': 'Johnson'},
    {'username': '@bob', 'email': 'bob.bobson@example.org', 'first_name': 'Bob', 'last_name': 'Bobson'},
]

class Command(BaseCommand):
    """Build automation command to seed the database."""

    USER_COUNT = 400
    TEAM_COUNT = 200
    TASK_COUNT = 300
    INVITATION_COUNT = 150
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self):
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        self.create_users()
        self.users = User.objects.all()
        self.create_teams()
        self.teams = Team.objects.all()
        self.create_invitations()
        self.invitations = Invitation.objects.all()
        self.create_tasks()
        self.tasks = Task.objects.all()

#-----------------Seed Users------------------------------------------------------

    def create_users(self):
        self.try_create_superuser()
        self.generate_user_fixtures()
        self.generate_random_users()

    def try_create_superuser(self):
        try:
            self.create_superuser()
        except:
            pass

    def create_superuser(self):
        user = User.objects.create_superuser(
            username = '@johndoe',
            email = 'john.doe@example.org',
            password = self.DEFAULT_PASSWORD,
            first_name = 'John',
            last_name = 'Doe',
        )

    def generate_user_fixtures(self):
        for data in user_fixtures:
            self.try_create_user(data)

    def generate_random_users(self):
        user_count = User.objects.count()
        while  user_count < self.USER_COUNT:
            print(f"Seeding user {user_count}/{self.USER_COUNT}", end='\r')
            self.generate_user()
            user_count = User.objects.count()
        print("User seeding complete.      ")

    def generate_user(self):
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        email = create_email(first_name, last_name)
        username = create_username(first_name, last_name)
        self.try_create_user({'username': username, 'email': email, 'first_name': first_name, 'last_name': last_name})
       
    def try_create_user(self, data):
        try:
            self.create_user(data)
        except:
            pass

    def create_user(self, data):
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=Command.DEFAULT_PASSWORD,
            first_name=data['first_name'],
            last_name=data['last_name'],
        )

    def get_rand_user(self):
        index = randint(0, self.users.count()-1)
        return self.users[index]

#-----------------------------Seed Teams------------------------------------------

    def create_teams(self):
        self.generate_team_fixtures()
        self.generate_random_teams()

    def generate_team_fixtures(self):
        self.generate_testing_team()
        self.generate_jane_doe_team()

    def generate_testing_team(self):
        name = 'Testing Team'
        description = 'Team with John, Jane and Charlie'
        owner = User.objects.get(username = '@johndoe')
        members = []
        members.append(owner)
        members.append(User.objects.get(username = '@janedoe'))
        members.append(User.objects.get(username = '@charlie'))
        created_at = self.faker.past_datetime(start_date = '-365d', tzinfo=pytz.UTC)
        self.try_create_team({'name': name, 'description': description, 'owner': owner, 'members': members, 'created_at': created_at})

    def generate_jane_doe_team(self):
        name = '@janedoe Team'
        description = 'Team of @janedoe'
        owner = User.objects.get(username = '@janedoe')
        members = []
        members.append(owner)
        created_at = self.faker.past_datetime(start_date = '-365d', tzinfo=pytz.UTC)
        self.try_create_team({'name': name, 'description': description, 'owner': owner, 'members': members, 'created_at': created_at})

    def generate_random_teams(self):
        team_count = Team.objects.count()
        while team_count < self.TEAM_COUNT:
            print(f"Seeding team {team_count}/{self.TEAM_COUNT}", end='\r')
            self.generate_team()
            team_count = Team.objects.count()
        print("Team seeding complete.      ") 

    def generate_team(self):
        name = self.faker.text(max_nb_chars=50)
        description = self.faker.text(max_nb_chars=100)
        owner = self.get_rand_user()
        member_count = randint(0, 4)
        members = []
        members.append(owner)
        while member_count > 0:
            new_member = self.get_rand_user()
            if new_member != owner:
                members.append(new_member)
                member_count -= 1
        created_at = self.faker.past_datetime(start_date = '-365d', tzinfo=pytz.UTC)
        self.try_create_team({'name': name, 'description': description, 'owner': owner, 'members': members, 'created_at': created_at})

    def try_create_team(self, data):
        try:
            self.create_team(data)
        except:
            pass
            

    def create_team(self, data):
        team = Team()
        team.name = data['name']
        team.description = data['description']
        team.owner = data['owner']
        team.created_at = data['created_at']
        team.save()
        team.members.set(data['members'])

    def get_rand_team(self):
        index = randint(0, self.teams.count()-1)
        return self.teams[index]
    
    def get_rand_user_in_team(self, team):
        team_members = list(team.members.all())
        if len(team_members) > 0:
            index = randint(0, len(team_members) - 1)
            return team_members[index]
        
    def get_rand_user_not_in_team(self, team):
        rand_user = self.get_rand_user()
        team_members = list(team.members.all())
        member_in_team = False
        for member in team_members:
            if rand_user == member:
                member_in_team = True
        if member_in_team:
            self.get_rand_user_not_in_team(team)
        else:
            return rand_user
    
#-------------------------------Seed Invitations-----------------------------------------

    def create_invitations(self):
        self.generate_random_invitations()

    def generate_random_invitations(self):
        invitation_count = Invitation.objects.count()
        while invitation_count < self.INVITATION_COUNT:
            print(f"Seeding invitation {invitation_count}/{self.INVITATION_COUNT}", end='\r')
            self.generate_invitation()
            invitation_count = Invitation.objects.count()
        print("Invitation seeding complete.      ") 

    def generate_invitation(self):
       rand_team = self.get_rand_team()
       sender = rand_team.owner
       recipient = self.get_rand_user_not_in_team(rand_team)
       team = rand_team
       message = self.faker.text(max_nb_chars=100)
       created_at = datetime.now()
       self.try_create_invitation({'sender': sender, 'recipient': recipient, 'team': team, 'message': message, 'created_at': created_at})

    def try_create_invitation(self, data):
        try:
            self.create_invitation(data)
        except:
            pass

    def create_invitation(self, data):
        invitation = Invitation()
        invitation.sender = data['sender']
        invitation.recipient = data['recipient']
        invitation.team = data['team']
        invitation.message = data['message']
        invitation.created_at = data['created_at']
        invitation.save()
    
    
#--------------------------------Seed Tasks----------------------------------------------

    def create_tasks(self):
        self.generate_random_tasks()
    
    def generate_random_tasks(self):
        task_count = Task.objects.count()
        while task_count < self.TASK_COUNT:
            print(f"Seeding task {task_count}/{self.TASK_COUNT}", end='\r')
            self.generate_task()
            task_count = Task.objects.count()
        print("Task seeding complete.      ")

    def generate_task(self):
        time_addition = randint(1,365)
        rand_team = self.get_rand_team()
        rand_status = randint(0, 2)
        title = self.faker.text(max_nb_chars=50)
        description = self.faker.text(max_nb_chars=100)
        due_date = timezone.now() + timedelta(days=time_addition)
        assigned_to = self.get_rand_user_in_team(rand_team)
        team = rand_team
        if rand_status == 0:
            status = Task.TaskStatus.NOT_STARTED
        elif rand_status == 1:
            status = Task.TaskStatus.IN_PROGRESS
        else:
            status = Task.TaskStatus.COMPLETE
        priority = randint(1, 5)
        created_at = datetime.now()
        updated_at = datetime.now()

        self.try_create_task({'title': title, 'description': description, 'due_date': due_date, 'assigned_to': assigned_to, 'team': team, 'status': status, 'priority': priority, 'created_at': created_at, 'updated_at': updated_at})

    def try_create_task(self, data):
        try:
            self.create_task(data)
        except:
            pass

    def create_task(self, data):
        task = Task()
        task.title = data['title']
        task.description = data['description']
        task.due_date = data['due_date']
        task.team = data['team']
        task.assigned_to = data['assigned_to']
        task.status = data['status']
        task.priority = data['priority']
        task.created_at = data['created_at']
        task.updated_at = data['updated_at']
        task.save()
        

def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return first_name + '.' + last_name + '@example.org'
