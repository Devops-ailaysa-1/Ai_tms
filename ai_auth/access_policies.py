
from django.db.models import manager
from ai_auth import managers
from rest_access_policy import AccessPolicy
from ai_auth.models import Team

class MemberCreationAccess(AccessPolicy):
    statements = [
        {"action": ["create","list"], 
        "principal": ["group:project_managers"],  
         "effect": "allow"
         },
    ]

    # @classmethod
    # def scope_queryset(cls, request, queryset):
    #     if request.user.(name='editor').exists():
    #         return queryset

    #     return queryset.filter(status='published')

    # def is_project_owner(self, request, view, action) -> bool:
    #     team = request.POST.get('team')
    #     managers = Team.objects.get(id=team).internal_member_team_info.filter(role__role = "project owner")
    #     return request.user in managers 

