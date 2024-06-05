from .models import Team

def teams(request):
    """Inserts the teams into the context of every template."""
    if request.user.is_authenticated:
        teams = Team.objects.filter(members=request.user).order_by('name')
        return {'teams': teams}
    return {'teams': []}