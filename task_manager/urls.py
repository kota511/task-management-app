"""
URL configuration for task_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from tasks import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('log_in/', views.LogInView.as_view(), name='log_in'),
    path('log_out/', views.log_out, name='log_out'),
    path('password/', views.PasswordView.as_view(), name='password'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    path('sign_up/', views.SignUpView.as_view(), name='sign_up'),
    path('teams/<int:pk>/create_task/', views.CreateTaskView.as_view(), name='create_task'),
    path('task/<int:pk>/edit_task/', views.EditTaskView.as_view(), name='edit_task'),
    path('create_team/', views.CreateTeamView.as_view(), name='create_team'),
    path('teams/<int:pk>/', views.TeamDetailView.as_view(), name='team_detail'),
    path('teams/<int:pk>/edit_team/', views.EditTeamView.as_view(), name='edit_team'),
    path('view_invitation/', views.InvitationListView.as_view(), name='view_invitation'),
]
