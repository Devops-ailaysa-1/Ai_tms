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

allow(user: ai_auth::AiUser, action: String, resource) if
    action = "read" and
    user = resource.owner;



allow(user: ai_auth::AiUser, action: String, resource) if
    rbac_allow(user, action, resource); #and role_resource_check(user,role,resource);

# rbac_allow(actor: ai_auth::AiUser,action,resource) if
#    action = "read" and
#    actor = resource.owner;



rbac_allow(actor: ai_auth::AiUser,action,resource) if
   action = "read" and
   role_allow(actor,resource);

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

editor_resources(res) if
res in [ai_workspace::Task,ai_workspace::Document];


project_owner_resources(res) if
res in [ai_workspace::Task,ai_workspace::Document,ai_auth::Team];

#if user is editor
role_allow(user:ai_auth::AiUser,resource) if
ai_auth::TaskRoles.objects.filter(user:user,task_pk:resource.task_pk,role__role__name:"Editor").count() != 0
and editor_resources(resource);

#if user is project owner
role_allow(user:ai_auth::AiUser,resource) if
ai_auth::TaskRoles.objects.filter(user:user,task_pk:resource.task_pk,role__role__name:"Editor").count() != 0
and project_owner_resources(resource);


# and resource.task_pk = ai_auth::TaskRoles.objects.filter(user:user).task_pk;


# # resource_role_applies_to('','');

#  role_allow(role,action,resource) if
#     role


# user_in_role(actor, role, role_resource) if
# role_resource.
#     actor = ai_auth::TaskRoles.objects.filter()

