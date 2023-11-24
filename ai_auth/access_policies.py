
from django.db.models import manager
from ai_auth import managers
from ai_auth.utils import get_plan_name
# from rest_access_policy import AccessPolicy
from ai_auth.models import Team,AiUser
from ai_workspace.models import TaskAssignInfo
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import BasePermission


class IsBusinessUser(BasePermission):
    """
    Allows access only to Business Plan users.
    """

    def has_permission(self, request, view):
        if request.user.is_internal_member == True:
            user = request.user.team.owner
        else:
            user = request.user
        plan_name = get_plan_name(user=user)
        if plan_name!=None and plan_name == "Business":
            return True
        else:
            return False


class IsEnterpriseUser(BasePermission):
    """
    Allows access only to Enterprise Plan users.
    """

    def has_permission(self, request, view):
        user = request.user.team.owner if request.user.team else request.user
        return user.is_enterprise


# class InternalTeamAccess(AccessPolicy):
#     statements = [
#         {"action": ["*"], 
#         "principal": ["*"],  
#         "effect": "allow",
#         #"condition":["is_admin"]
#         "condition_expression": ["is_admin"]
#          },
#         {
#         "action": ["create",], 
#         "principal": ["*"],  
#         "effect": "allow",
#         #"condition":[""]
#         "condition_expression": ["(is_project_owner and is_internalmember) or is_team_owner)"]
#          },
#         {
#         "action": ["list",], 
#         "principal": ["*"],  
#         "effect": "allow",
#         #"condition":["is_project_owner"]
#         "condition_expression": ["(is_project_owner or is_team_owner)"]
#          },
#          {
#         "action": ["update","delete"], 
#         "principal": ["*"],  
#         "effect": "allow",
#         #"condition":[""]
#         "condition_expression": ["(is_project_owner and is_added) or is_team_owner)"]
#          },
#     ]

#     def is_admin(self,request, view, action) -> bool:
#         return request.user.is_superuser

#     def is_project_owner(self, request, view, action: str) -> bool:
#         team = request.POST.get('team' ,None)
#         if not team:
#             team = request.query_params.get('team', None)
#         print(team)
#         print(action)
#         managers = Team.objects.get(name = team).internal_member_team_info.filter(role__name = "project owner")
#         print("project_manager",managers)
#         print("view",view)
#         #print("action",action) 
#         return request.user.internal_member.last() in managers

#     # def is_internalmember(self,request, view, action) -> bool:
#     #     return request.user.is_internal_member

#     def is_team_owner(self, request, view, action: str) -> bool:
#         team = request.POST.get('team' ,None)
#         if not team:
#             team = request.query_params.get('team', None)

#         if team:
#             team = Team.objects.get(name = team).id
#         print(repr(request))
#         print(request.user)
#         print("inside team")
#         print(team)
#         if team:
#             try:
#                 team_owner = request.user.team_owner.id
#                 print("id",request.user.team_owner.id)
#             except ObjectDoesNotExist:
#                 print("team Doesn't exists")
#                 return False
#         else:
#             team_owner = None
                
#         # print(request.user.team_owner.id)

#         print("team",team)
#         if (team_owner == team) and (team_owner != None):
#             return True
#         else:
#             return False

         

# class MemberCreationAccess(AccessPolicy):
#     statements = [
#         {"action": ["*"], 
#         "principal": ["group:account_owner",],  
#         "effect": "allow",
#         "condition":["is_team_owner"]
#         #"condition_expression": ["(is_project_owner or is_team_owner)"]
#          },
#     ]

# class TeamAccess(AccessPolicy):
#     statements = [
#         # {"action": ["*"], 
#         # "principal": ["group:account_owners"],  
#         # "effect": "allow",
#         # "condition":["is_team_owner"]
#         # #"condition_expression": ["(is_project_owner or is_team_owner)"]
#         #  },
#         {"action": ["list"], 
#         "principal": ["group:account_owners"],  
#         "effect": "allow",
#         #"condition":["is_team_owner"]
#         "condition_expression": ["(is_project_owner or is_team_owner)"]
#          },
#         {"action": ["*"], 
#         "principal": ["group:internalmember"],  
#         "effect": "allow",
#         "condition":["is_project_owner"]
#         #"condition_expression": ["(is_project_owner or is_team_owner)"]
#          },
#     ]

#     def is_project_owner(self, request, view, action: str) -> bool:
#         team = request.POST.get('team')
#         managers = Team.objects.get(id=team).internal_member_team_info.filter(role__role = "project owner")
#         print("view",view)
#         #print("action",action)
#         return request.user in managers 


#     def is_team_owner(request, view, action: str) -> bool:
#         team = request.POST.get('team')
#         print(request)
#         print("inside team")
#         print(team)
#         if not team:
#             team = request.user.team_owner.id
#         print(request.user.team_owner.id)
#         return request.user.team_owner.id == int(team)


# class ProjectAccess(AccessPolicy):
#     statements = [
#         {"action": ["create"], 
#         "principal": ["*",],  
#         "effect": "allow",
#         "condition":["(is_internalmember and is_project_owner_internal) or (is_team_owner) "]
#         #"condition_expression": ["(is_project_owner or is_team_owner)"]
#          },
#         {"action": ["list"], 
#         "principal": ["*"],  
#         "effect": "allow",
#      #   "condition":["*"]
#         #"condition_expression": ["(is_project_owner or is_team_owner)"]
#          },
#         {"action": ["update"], 
#         "principal": ["group:project_owners"],  
#         "effect": "allow",
#         #"condition":["is_project_owner"]
#         "condition_expression": ["(is_project_created or is_project_owner_internal) or team_owner_project"]
#          },
#     ]


# class ProjectAssignment(AccessPolicy):
#     statements = [
#         {"action": ["create"], 
#         "principal": ["group:account_owners","group:project_owners"],  
#         "effect": "allow",
#         "condition":["(is_internalmember and is_project_owner_internal) or (not is_internalmember) "]
#         #"condition_expression": ["(is_project_owner or is_team_owner)"]
#          },
#         {"action": ["update"], 
#         "principal": ["group:project_owners","group:account_owners"],  
#         "effect": "allow",
#         #"condition":["is_project_owner"]
#         "condition_expression": ["is_assigned or is_team_owner_task"]
#          },
#     ]

#     def is_assigned(request, view, action) -> bool:
#         tasks = request.POST.getlist('task')
#         result = False
#         for iter in tasks:
#             task_assign_info = TaskAssignInfo.objects.get(task_id = iter)
#             if task_assign_info.assigned_by == request.user:
#                 result = True
#             else:
#                 result = False     
#         return result 
    
#     def is_team_owner_task(request, view, action) -> bool:
#         tasks = request.POST.getlist('task')
#         for iter in tasks:
#             task_assign_info = TaskAssignInfo.objects.get(task_id = iter)
#             if task_assign_info.job.project.team == request.user.team:
#                 result = True
#             else:
#                 result = False     
#         return result 
