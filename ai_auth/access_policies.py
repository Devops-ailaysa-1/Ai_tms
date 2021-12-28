
from django.db.models import manager
from ai_auth import managers
from rest_access_policy import AccessPolicy
from ai_auth.models import Team



class InternalTeamAccess(AccessPolicy):
    statements = [
        {"action": ["list","create","update","delete"], 
        "principal": ["*"],  
        "effect": "allow",
        #"condition":["is_admin"]
        "condition_expression": ["is_admin"]
         },
        {
        "action": ["create",], 
        "principal": ["group:member","group:project_owner","group:account_owners"],  
        "effect": "allow",
        #"condition":[""]
        "condition_expression": ["(is_project_owner and is_internalmember) or is_team_owner)"]
         },
        {
        "action": ["list",], 
        "principal": ["*"],  
        "effect": "allow",
        #"condition":["is_project_owner"]
        "condition_expression": ["is_internalmember or is_team_owner"]
         },
         {
        "action": ["update","delete"], 
        "principal": ["group:member","group:project_owner","group:account_owner"],  
        "effect": "allow",
        #"condition":[""]
        "condition_expression": ["(is_project_owner and is_added) or is_team_owner)"]
         },
    ]

    def is_admin(self,request, view, action) -> bool:
        return request.user.is_superuser

    def is_project_owner(self, request, view, action: str) -> bool:
        team = request.POST.get('team')
        print(team)
        print(action)
        managers = Team.objects.get(id=team).internal_member_team_info.filter(role__role = "project owner")
        print("view",view)
        #print("action",action) 
        return request.user in managers

    # def is_internalmember(self,request, view, action) -> bool:
    #     return request.user.is_internal_member

class MemberCreationAccess(AccessPolicy):
    statements = [
        {"action": ["*"], 
        "principal": ["group:account_owner",],  
        "effect": "allow",
        "condition":["is_team_owner"]
        #"condition_expression": ["(is_project_owner or is_team_owner)"]
         },
    ]

class TeamAccess(AccessPolicy):
    statements = [
        # {"action": ["*"], 
        # "principal": ["group:account_owners"],  
        # "effect": "allow",
        # "condition":["is_team_owner"]
        # #"condition_expression": ["(is_project_owner or is_team_owner)"]
        #  },
        {"action": ["list"], 
        "principal": ["group:account_owners"],  
        "effect": "allow",
        #"condition":["is_team_owner"]
        "condition_expression": ["(is_project_owner or is_team_owner)"]
         },
        {"action": ["*"], 
        "principal": ["group:internalmember"],  
        "effect": "allow",
        "condition":["is_project_owner"]
        #"condition_expression": ["(is_project_owner or is_team_owner)"]
         },
    ]

    def is_project_owner(self, request, view, action: str) -> bool:
        team = request.POST.get('team')
        managers = Team.objects.get(id=team).internal_member_team_info.filter(role__role = "project owner")
        print("view",view)
        #print("action",action)
        return request.user in managers 


    def is_team_owner(request, view, action: str) -> bool:
        team = request.POST.get('team')
        print(request)
        print("inside team")
        print(team)
        if not team:
            team = request.user.team_owner.id
        print(request.user.team_owner.id)
        return request.user.team_owner.id == int(team)


class ProjectAccess(AccessPolicy):
    statements = [
        {"action": ["*"], 
        "principal": ["group:vendor"],  
        "effect": "allow",
        "condition":["is_assigned"]
        #"condition_expression": ["(is_project_owner or is_team_owner)"]
         },
        {"action": ["*"], 
        "principal": ["group:account_owner"],  
        "effect": "allow",
        "condition":["is_team_owner"]
        #"condition_expression": ["(is_project_owner or is_team_owner)"]
         },
        {"action": ["*"], 
        "principal": ["group:project_owners"],  
        "effect": "allow",
        #"condition":["is_project_owner"]
        "condition_expression": ["(is_project_owner and is_project_owner)"]
         },
    ]

