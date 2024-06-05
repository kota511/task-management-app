import django_filters
from django import forms
from .models import Task, User, Team

class DashboardTaskFilter(django_filters.FilterSet):
    """Filter for the dashboard view."""
    # Possibly use this later, this filter is not used currently

    SORT_CHOICES = (
        ('dateUp', 'Due Date Increasing'),
        ('dateDown', 'Due Date Decreasing'),
        ('creationUp', 'Creation Date Increasing'),
        ('creationDown', 'Creation Date Decreasing'),
        ('priorityUp', 'Priority Increasing'),
        ('priorityDown', 'Priority Decreasing'),
        ('alphabetical', 'Task Title'),
        ('status', 'Status')
    )

    def sorting_function(self, queryset, name, value):
        """Sort the queryset based on the value."""
        if value == 'dateUp':
            return queryset.order_by('due_date')
        elif value == 'dateDown':
            return queryset.order_by('-due_date')
        elif value == 'creationUp':
            return queryset.order_by('created_at')
        elif value == 'creationDown':
            return queryset.order_by('-created_at')
        elif value == 'priorityUp':
            return queryset.order_by('priority')
        elif value == 'priorityDown':
            return queryset.order_by('-priority')
        elif value == 'alphabetical':
            return queryset.order_by('title')
        elif value == 'status':
            return queryset.order_by('status')

    priority = django_filters.NumberFilter(field_name='priority', label='Priority', min_value=1, max_value=50, widget=forms.NumberInput(attrs={'style': 'width: 8%;'}))
    startDate = django_filters.DateTimeFilter(field_name='due_date', label='Start Date', lookup_expr='gte', widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    endDate = django_filters.DateTimeFilter(field_name='due_date', label='End Date', lookup_expr='lte', widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    sort = django_filters.ChoiceFilter(label='Sort By',choices=SORT_CHOICES, method='sorting_function')
    team__name = django_filters.CharFilter(field_name='team__name', label='Team name contains', lookup_expr='icontains', widget=forms.TextInput(attrs={'style': 'width: 30%;'}))

    class Meta:
        model = Task
        fields = {
            'title':['icontains'],
            #'team__name': ['icontains'],
            'status': ['exact']
        }

class TeamTaskFilter(django_filters.FilterSet):

    SORT_CHOICES = (
        ('dateUp', 'Due Date Increasing'),
        ('dateDown', 'Due Date Decreasing'),
        ('creationUp', 'Creation Date Increasing'),
        ('creationDown', 'Creation Date Decreasing'),
        ('priorityUp', 'Priority Increasing'),
        ('priorityDown', 'Priority Decreasing'),
        ('alphabetical', 'Task Title'),
        ('status', 'Status')
    )

    def sorting_function(self, queryset, name, value):
        """Sort the queryset based on the value."""
        if value == 'dateUp':
            return queryset.order_by('due_date')
        elif value == 'dateDown':
            return queryset.order_by('-due_date')
        elif value == 'creationUp':
            return queryset.order_by('created_at')
        elif value == 'creationDown':
            return queryset.order_by('-created_at')
        elif value == 'priorityUp':
            return queryset.order_by('priority')
        elif value == 'priorityDown':
            return queryset.order_by('-priority')
        elif value == 'alphabetical':
            return queryset.order_by('title')
        elif value == 'status':
            return queryset.order_by('status')

    assigned_to__username = django_filters.CharFilter(field_name='assigned_to__username', label='Username contains', lookup_expr='icontains', widget=forms.TextInput(attrs={'style': 'width: 30%;'}))
    priority = django_filters.NumberFilter(field_name='priority', label='Priority', min_value=1, widget=forms.NumberInput(attrs={'style': 'width: 8%;'}))
    startDate = django_filters.DateTimeFilter(field_name='due_date', label='Start Date', lookup_expr='gte', widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    endDate = django_filters.DateTimeFilter(field_name='due_date', label='End Date', lookup_expr='lte', widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    sort = django_filters.ChoiceFilter(label='Sort By',choices=SORT_CHOICES, method='sorting_function')
    
    class Meta:
        model = Task
        fields = {
            'title':['icontains'],
            'status':['exact']
        }