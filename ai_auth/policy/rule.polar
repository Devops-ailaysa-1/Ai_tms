# allow(_user:ai_auth::AiUser, "GET", http_request: Request) if
#     http_request.path = "/auth/oso-test/";


# allow(user:ai_auth::AiUser, _action, _resource) if
#     user.is_staff = ;

# allow(user:ai_auth::AiUser, _action, _resource) if
#     user = _resource.owner;

# allow(_user: AiUser, "POST", http_request: HttpRequest) if
#     http_request.path = "/auth/dj-rest-auth/login/" or
#     http_request.path = "/auth/dj-rest-auth/registration/";


# allow(user: ai_auth::AiUser, "GET", project: ai_workspace::Project) if
#     project.ai_user = user;

# allow(user: ai_auth::AiUser, "read", task: ai_workspace::Task) if
#     task.job.project.ai_user = user;

actor ai_auth::AiUser {
}

resource ai_workspace::Task{
    permissions = ["read", "create","update","delete"];
    roles = ["Editor", "Project owner","Reviewer","Agency Project owner",
            "Agency Editor","Agency Reviewer","Agency Admin"];

    "read" if "Editor";
    "create" if "Editor";
    "update" if "Project owner";
    "delete" if "Project owner";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";


    "Editor" if "Agency Editor";
    "Agency Editor" if "Agency Project owner";
    "Agency Editor" if "Agency Reviewer";
    "Agency Project owner" if "Agency Admin";

}

resource ai_workspace::Project{
    permissions = ["read", "create","update","delete"];
    roles = ["Editor", "Project owner","Reviewer"];

    "read" if "Editor";
    "create" if "Project owner";
    "update" if "Project owner";
    "delete" if "Project owner";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";

}


# has_role(actor: ai_auth::AiUser, role_name: String, resource: Resource) if
# ai_auth::TaskRoles.objects.filter(user:actor,task_pk:resource.task_obj.id,role__role__name:role_name).count() != 0;

# For models with task obj
has_role(actor: ai_auth::AiUser, role_name: String,resource:Resource) if
resource.__class__ in [ai_workspace::Task,ai_workspace::TaskAssign,ai_workspace::TaskAssignInfo,ai_workspace_okapi::Document,
    ai_workspace_okapi::Segment,,ai_workspace_okapi::SplitSegment,ai_workspace_okapi::MergeSegment,ai_workspace_okapi::Comment]
and ai_auth::TaskRoles.objects.filter(user:actor,task_pk:resource.task_obj.id ,role__role__name:role_name).count() != 0;

# has_role(actor: ai_auth::AiUser, role_name: String, resource : ai_workspace::Project,ai_workspace::ProjectContentType,ai_workspace::ProjectFilesCreateType,
# ai_workspace::ProjectSteps,ai_workspace::ProjectSubjectField) if
# ai_auth::TaskRoles.objects.filter(user:actor,task_pk__in:resource.proj_obj.get_tasks_pk ,proj_pk:resource.proj_obj.id,role__role__name:role_name).count() != 0;

# For models without task obj
has_role(actor: ai_auth::AiUser, role_name: String, resource:Resource) if
resource.__class__ in [ai_workspace::Project,ai_workspace::Job] 
and ai_auth::TaskRoles.objects.filter(user:actor,task_pk__in:resource.proj_obj.get_tasks_pk ,proj_pk:resource.proj_obj.id,role__role__name:role_name).count() != 0;


has_role(actor: ai_auth::AiUser, _role_name: "Project owner", resource:Resource) if
    ai_auth::Team.objects.filter(owner : resource.owner_pk).count() !=0 and 
    actor in ai_auth::Team.objects.get(owner :resource.owner_pk).get_project_manager;

## For agency
# For models without task obj 
has_role(actor: ai_auth::AiUser, _role_name: "Agency Project owner", resource:Resource) if
resource.__class__ in [ai_workspace::Project,ai_workspace::Job] 
and actor.internal_member.count() != 0
and team_resource(actor,ai_auth::TaskRoles.objects.filter(task_pk:resource.task_obj.id ,role__role__name__in:["Editor","Reviewer"]));

# For models with task obj
has_role(actor: ai_auth::AiUser, _role_name: "Agency Project owner",resource:Resource) if
resource.__class__ in [ai_workspace::Task,ai_workspace::TaskAssign,ai_workspace::TaskAssignInfo,ai_workspace_okapi::Document,
    ai_workspace_okapi::Segment,ai_workspace_okapi::SplitSegment,ai_workspace_okapi::MergeSegment,ai_workspace_okapi::Comment]
and actor.internal_member.count() != 0
and team_resource(actor,ai_auth::TaskRoles.objects.filter(task_pk:resource.task_obj.id ,role__role__name__in:["Editor","Reviewer"]));

# and ai_auth::TaskRoles.objects.filter(user:actor.team.owner,task_pk:resource.task_obj.id ,role__role__name__in:["Editor","Reviewer"]).count() != 0


## For Agency Admin
# For models without task obj 
has_role(actor: ai_auth::AiUser, role_name: "Agency Admin", resource:Resource) if
resource.__class__ in [ai_workspace::Project,ai_workspace::Job] 
and actor.is_agency
and ai_auth::TaskRoles.objects.filter(user:actor,task_pk__in:resource.proj_obj.get_tasks_pk ,proj_pk:resource.proj_obj.id,role__role__name:role_name).count() != 0;

# For models with task obj
has_role(actor: ai_auth::AiUser, role_name: "Agency Admin",resource:Resource) if
resource.__class__ in [ai_workspace::Task,ai_workspace::TaskAssign,ai_workspace::TaskAssignInfo,ai_workspace_okapi::Document,
    ai_workspace_okapi::Segment,ai_workspace_okapi::SplitSegment,ai_workspace_okapi::MergeSegment,ai_workspace_okapi::Comment]
and actor.is_agency
and ai_auth::TaskRoles.objects.filter(user:actor,task_pk:resource.task_obj.id ,role__role__name:role_name).count() != 0;


team_resource(actor,assignes) if
task_role in assignes
and task_role.user.team != nil
and actor in task_role.user.team.get_project_manager;


# has_role(actor: ai_auth::AiUser, role_name: String, resource:ai_workspace::Task) if
# ai_auth::TaskRoles.objects.filter(user:actor,task_pk:resource.task_pk,role__role__name:role_name).count() != 0;

allow(user: ai_auth::AiUser, action: String, resource) if
    action in ["read","create","update","delete","download"] and
    user.id = resource.owner_pk;



allow(user: ai_auth::AiUser, action: String, resource) if
    rbac_allow(user, action, resource); #and role_resource_check(user,role,resource);


# ## without action string
# rbac_allow(actor: ai_auth::AiUser,action,resource) if
#    action = "read" and
#    role_allow(actor,resource);

# rbac_allow(actor: ai_auth::AiUser,action,resource) if
#    role_allow(actor,action,resource);

rbac_allow(actor: ai_auth::AiUser,action,resource) if
   role_allow(actor,action,resource);



role_allow(actor: ai_auth::AiUser,action,resource) if
   has_permission(actor, action, resource);


# has_permission(actor, action, resource)if 
# [ai_workspace::Job,ai_workspace_okapi::Segment,ai_workspace_okapi::MT_RawTranslation]
#role_resource_check(actor,role,resource):

# user_role(actor:ai_auth::AiUser,role,resource) if
# resource_roles(actor,role,role_resource);


# resource_roles(user,role,role_resource) if
# ai_auth::TaskRoles.objects.filter(user=user).role_name = "Project owner" 
# and role_resource in ["ai_auth::Team"];

# resource_roles(user,role,role_resource) if
# ai_auth::TaskRoles.objects.filter(user=user).role_name = "Editor" 
# and role_resource in ["ai_workspace::Task","ai_workspace::Document"];

# rbac_allow(actor: ai_auth::AiUser, action, resource) if
#     resource_role_applies_to(resource, role_resource) and
#     user_in_role(actor, role, role_resource) and
#     role_allow(role, action, resource);

# editor_resources(res) if
# res in [ai_workspace::Task,ai_workspace::Document];


# project_owner_resources(res) if
# res in [ai_workspace::Task,ai_workspace::Document,ai_auth::Team];

#if user is editor
# role_allow(user:ai_auth::AiUser,action,resource) if
# ai_auth::TaskRoles.objects.filter(user:user,task_pk:resource.task_pk,role__role__name:"Editor").count() != 0
# and has_permission(user,action,resource);


# role_allow(user:ai_auth::AiUser,resource) if
# ai_auth::TaskRoles.objects.filter(user:user,task_pk:resource.task_pk,role__role__name:"Editor").count() != 0
# and editor_resources(resource);


#if user is project owner
# role_allow(user:ai_auth::AiUser,resource) if
# ai_auth::TaskRoles.objects.filter(user:user,task_pk:resource.task_pk,role__role__name:"Project owner").count() != 0
# and project_owner_resources(resource);




# has_permission(actor, "write", resource: ai_workspace::Task) if
#   has_role(actor, "Editor", resource); 


# has_role(actor, "Editor", resource) if 
# ai_auth::TaskRoles.objects.filter(user:actor,task_pk:resource.task_pk,role__role__name:"Editor").count() != 0;


# has_role(user: User, name: String, resource: Resource) if
#   role in user.roles and
#   role.name = name and
#   role.resource = resource;






# and resource.task_pk = ai_auth::TaskRoles.objects.filter(user:user).task_pk;


# # resource_role_applies_to('','');

#  role_allow(role,action,resource) if
#     role


# user_in_role(actor, role, role_resource) if
# role_resource.
#     actor = ai_auth::TaskRoles.objects.filter()

# resource ai_workspace::Team{
#     permissions = ["read", "create","update","delete"];
#     roles = ["Editor", "Project owner"];

#     "read" if "Editor";
#     "create" if "Project owner";
#     "update" if "Project owner";
#     "delete" if "Project owner";
#     "Editor" if "Project owner";

# }


resource ai_workspace::File{
    permissions = ["read", "create","update","delete"];
    roles = ["Editor", "Project owner","Reviewer","Agency Project owner",
            "Agency Editor","Agency Reviewer","Agency Admin"];

    "read" if "Editor";
    "create" if "Project owner";
    "update" if "Project owner";
    "delete" if "Project owner";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";

}


resource ai_workspace::Job{
    permissions = ["read", "create","update","delete"];
    roles = ["Editor", "Project owner","Reviewer","Agency Project owner",
            "Agency Editor","Agency Reviewer","Agency Admin"];

    "read" if "Editor";
    "create" if "Project owner";
    "update" if "Project owner";
    "delete" if "Project owner";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";

}

resource ai_workspace::ProjectContentType{
    permissions = ["read", "create","update","delete"];
    roles = ["Editor", "Project owner","Reviewer","Agency Project owner",
            "Agency Editor","Agency Reviewer","Agency Admin"];

    "read" if "Editor";
    "create" if "Project owner";
    "update" if "Project owner";
    "delete" if "Project owner";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";

}

resource ai_workspace::ProjectSubjectField{
    permissions = ["read", "create","update","delete"];
    roles = ["Editor", "Project owner","Reviewer","Agency Project owner",
            "Agency Editor","Agency Reviewer","Agency Admin"];

    "read" if "Editor";
    "create" if "Project owner";
    "update" if "Project owner";
    "delete" if "Project owner";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";

}

resource ai_workspace::ProjectSteps{
    permissions = ["read", "create","update","delete"];
    roles = ["Editor", "Project owner","Reviewer","Agency Project owner",
            "Agency Editor","Agency Reviewer","Agency Admin"];

    "read" if "Editor";
    "create" if "Project owner";
    "update" if "Project owner";
    "delete" if "Project owner";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";

}

resource ai_workspace_okapi::Segment{
    permissions = ["read", "create","update","delete"];
    roles = ["Editor", "Project owner","Reviewer","Agency Project owner",
            "Agency Editor","Agency Reviewer","Agency Admin"];

    "read" if "Editor";
    "create" if "Editor";
    "update" if "Editor";
    "delete" if "Project owner";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";

    "read" if "Agency Editor";
    "create" if "Agency Project owner";
    "update" if "Agency Project owner";
    "delete" if "Agency Project owner";
    "Editor" if "Agency Project owner";
    "Editor" if "Agency Reviewer";
    "Agency Project owner" if "Agency Admin";

}

resource ai_workspace_okapi::SplitSegment{
    permissions = ["read", "create","update","delete"];
    roles = ["Editor", "Project owner","Reviewer","Agency Project owner",
            "Agency Editor","Agency Reviewer","Agency Admin"];

    "read" if "Editor";
    "create" if "Editor";
    "update" if "Editor";
    "delete" if "Project owner";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";

    "read" if "Agency Editor";
    "create" if "Agency Project owner";
    "update" if "Agency Project owner";
    "delete" if "Agency Project owner";
    "Editor" if "Agency Project owner";
    "Editor" if "Agency Reviewer";
    "Agency Project owner" if "Agency Admin";

}

resource ai_workspace_okapi::MergeSegment{
    permissions = ["read", "create","update","delete"];
    roles = ["Editor", "Project owner","Reviewer","Agency Project owner",
            "Agency Editor","Agency Reviewer","Agency Admin"];

    "read" if "Editor";
    "create" if "Editor";
    "update" if "Editor";
    "delete" if "Project owner";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";

    "read" if "Agency Editor";
    "create" if "Agency Project owner";
    "update" if "Agency Project owner";
    "delete" if "Agency Project owner";
    "Editor" if "Agency Project owner";
    "Editor" if "Agency Reviewer";
    "Agency Project owner" if "Agency Admin";

}


resource ai_workspace_okapi::Document{
    permissions = ["read", "create","update","delete","download"];
    roles = ["Editor", "Project owner","Reviewer","Agency Project owner",
            "Agency Editor","Agency Reviewer","Agency Admin"];

    "read" if "Editor";
    "create" if "Project owner";
    "update" if "Project owner";
    "delete" if "Project owner";
    "download" if "Project owner";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";

    "read" if "Agency Editor";
    "create" if "Agency Project owner";
    "update" if "Agency Project owner";
    "delete" if "Agency Project owner";
    "Editor" if "Agency Project owner";
    "Editor" if "Agency Reviewer";
    "Agency Project owner" if "Agency Admin";



}



resource ai_workspace_okapi::MT_RawTranslation{
    permissions = ["read", "create","update","delete"];
    roles = ["Editor", "Project owner","Reviewer","Agency Project owner",
            "Agency Editor","Agency Reviewer","Agency Admin"];

    "read" if "Editor";
    "create" if "Editor";
    "update" if "Editor";
    "delete" if "Project owner";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";

    "read" if "Agency Editor";
    "create" if "Agency Project owner";
    "update" if "Agency Project owner";
    "delete" if "Agency Project owner";
    "Editor" if "Agency Project owner";
    "Editor" if "Agency Reviewer";
    "Agency Project owner" if "Agency Admin";

}


resource ai_workspace::ProjectFilesCreateType{
    permissions = ["read", "create","update","delete"];
    roles = ["Editor", "Project owner","Reviewer","Agency Project owner",
            "Agency Editor","Agency Reviewer","Agency Admin"];

    "read" if "Editor";
    "create" if "Project owner";
    "update" if "Project owner";
    "delete" if "Project owner";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";

}


resource ai_workspace::TaskAssign{
    permissions = ["read", "create","update","delete"];
    roles = ["Editor", "Project owner","Reviewer","Agency Project owner",
            "Agency Editor","Agency Reviewer","Agency Admin"];

    "read" if "Editor";
    "create" if "Project owner";
    "update" if "Editor";
    "delete" if "Project owner";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";

}

resource ai_workspace::TaskAssignInfo{
    permissions = ["read", "create","update","delete"];
    roles = ["Editor", "Project owner","Reviewer","Agency Project owner",
            "Agency Editor","Agency Reviewer","Agency Admin"];

    "read" if "Editor";
    "create" if "Project owner";
    "update" if "Editor";
    "delete" if "Project owner";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";

    "read" if "Agency Editor";
    "create" if "Agency Project owner";
    "update" if "Agency Project owner";
    "delete" if "Agency Project owner";
    "Editor" if "Agency Project owner";
    "Editor" if "Agency Reviewer";
    "Agency Project owner" if "Agency Admin";

}


resource ai_workspace_okapi::Comment{
    permissions = ["read", "create","update","delete"];
    roles = ["Editor", "Project owner","Reviewer","Agency Project owner",
            "Agency Editor","Agency Reviewer","Agency Admin"];

    "read" if "Editor";
    "create" if "Editor";
    "update" if "Editor";
    "delete" if "Editor";
    "Editor" if "Project owner";
    "Editor" if "Reviewer";

    "Editor" if "Agency Editor";
    "Editor" if "Agency Project owner";
    "Editor" if "Agency Reviewer";
    "Agency Project owner" if "Agency Admin";


}