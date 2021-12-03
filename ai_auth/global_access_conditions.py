from ai_auth.models import Team


def is_project_owner(self, request, view, action) -> bool:
    team = request.POST.get('team')
    managers = Team.objects.get(id=team).internal_member_team_info.filter(role__role = "project owner")
    print("view",view)
    print("action",action)
    return request.user in managers 


def is_team_owner(self,request, view, action) -> bool:
    team = request.POST.get('team')
    print("inside team")
    print(team)
    print(request.user.team_owner.id)

    return request.user.team_owner.id == int(team)

def is_internalmember(self,request, view, action) -> bool:
    return request.user.is_internal_member

def is_vendor(self,request, view, action) -> bool:
    return request.user.is_vendor

def is_assigned_vendor(self,request, view, action) -> bool:
    
    return request.user.is_vendor