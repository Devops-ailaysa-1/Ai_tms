from ai_auth.models import Team,InternalMember
import logging
logger = logging.getLogger('django')

def is_project_owner(self, request, view, action: str) -> bool:
    team = request.POST.get('team')
    managers = Team.objects.get(id=team).internal_member_team_info.filter(role__role = "project owner")
 
    return request.user in managers 


def is_team_owner(request, view, action: str) -> bool:
    team = request.POST.get('team')

    if not team:
        team = request.user.team_owner.id
    return request.user.team_owner.id == int(team)

def is_internalmember(request, view, action: str) -> bool:
    return request.user.is_internal_member

def is_vendor(request, view, action) -> bool:
    return request.user.is_vendor

def is_assigned_vendor(request, view, action) -> bool:
    
    return request.user.is_vendor

def is_added(request, view, action) -> bool:
    try:
        pk = request.kwargs['pk']
        in_mem=InternalMember.objects.get(id=int(pk))
    except:
        logger.debug("In except")
    return request.user == in_mem.added_by

def is_admin(self,request, view, action) -> bool:
    return request.user.is_superuser

def is_project_owner_internal(request, view, action: str) -> bool:
    user = request.user
    managers = user.internal_member.filter(role__name="project owner")
    return managers.count()>0
 
def is_project_created(request, view, action: str) -> bool:
    obj = view.get_object()
    return obj.ai_user == request.user

