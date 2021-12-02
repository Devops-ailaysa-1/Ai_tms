
from django.db.models import manager
from ai_auth import managers
from rest_access_policy import AccessPolicy
from ai_auth.models import Team

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
        {"action": ["*"], 
        "principal": ["group:account_owner"],  
        "effect": "allow",
        "condition":["is_team_owner"]
        #"condition_expression": ["(is_project_owner or is_team_owner)"]
         },
        {"action": ["*"], 
        "principal": ["group:internalmember"],  
        "effect": "allow",
        "condition":["is_project_owner"]
        #"condition_expression": ["(is_project_owner or is_team_owner)"]
         },
    ]

class ProjectAccess(AccessPolicy):
    statements = [
        {"action": ["*"], 
        "principal": ["group:vendor"],  
        "effect": "allow",
        "condition":["is_vendor"]
        #"condition_expression": ["(is_project_owner or is_team_owner)"]
         },
    ]



