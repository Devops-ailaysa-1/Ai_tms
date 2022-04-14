from rest_framework import serializers
import json
from .models import GithubApp, FetchInfo,\
    Repository, Branch, ContentFile, HookDeck, FileConnector, \
    DownloadProject
from ai_workspace.models import  Project, File, Job, ProjectFilesCreateType, ProjectSteps
from ai_staff.models import AssetUsageTypes, Languages, ProjectType
from django.shortcuts import get_object_or_404, reverse

from github import Github
from collections import OrderedDict
from ai_auth.models import AiUser
from .enums import DJ_APP_NAME, HOOK_LISTEN_ADDRESS
from controller.models import DownloadController, FileController

import hmac, hashlib
import os
import uuid
import cryptocode


class GithubOAuthTokenSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("oauth_token", "ai_user", \
                  "is_token_expired", "username", "id")
        model = GithubApp

        extra_kwargs = {
            "username": {"read_only": True}}

    def validate_oauth_token(self, value):
        g = Github(value)

        try:
            g.get_user().login
        except:
            raise serializers.ValidationError({"detail":"Token is invalid!!!3333"})

        return value

    def create(self, validated_data):
        data = validated_data
        g = Github(data["oauth_token"])
        username = g.get_user().login
        data["username"] = username

        if GithubApp.objects.filter(
            ai_user=data["ai_user"],
            username=username
        ).first():
            raise serializers.ValidationError\
                ({"detail": "Already github account registered!!!"})
        return super().create(data)

class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'github_token', 'repository_name', \
                  'is_localize_registered', 'is_alive_in_github',\
                  'repository_fullname']
        model = Repository
        extra_kwargs = {
        }

    def create(self, validated_data):
        data = validated_data
        return super().create(data)

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'branch_name', 'is_localize_registered', 'repo',
                  # 'created_on', 'accessed_on', 'updated_on'
                  ]
        model = Branch

    def create(self, validated_data):
        data = validated_data
        return super().create(data)

class ContentFileListSerializer(serializers.ListSerializer):
    def update(self, instance, validated_data):
        instance_mapping = {this.id: this for this in instance}
        data_mapping = {item['id']: item for item in validated_data}

        # Perform creations and updates.
        ret = []
        for data_id, data in data_mapping.items():
            ins = instance_mapping.get(data_id, None)
            if ins is not None:
                ret.append(self.child.update(ins, data))
        return ret

class ContentFileSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'branch', 'is_localize_registered', 'file',
                  "file_path", "size_of_file_with_units",
                  "is_file_size_exceeded", "is_translatable"
                  # 'created_on', 'accessed_on', 'updated_on'
                  ]

        extra_kwargs = {
            "id":{
                "read_only": False, "required": False } }

        model = ContentFile
        list_serializer_class = ContentFileListSerializer

    def create(self, validated_data):
        data = validated_data
        return super().create(data)

class LocalizeIdsSerializer(serializers.Serializer):
    localizable_ids = serializers.ListField()


class FileListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        ret = []
        for s_data in validated_data:
            ret.append(self.child.create(s_data))
        return ret

class FileSerializer(serializers.ModelSerializer):
    contentfile_id = serializers.IntegerField()
    class Meta:
        fields = ['id', 'usage_type', 'file', 'project',
                  "contentfile_id"]
                  # f"{DJ_APP_NAME}contentfile"

        model = File
        list_serializer_class = FileListSerializer

        extra_kwargs = {
            "project": {"required": False},
            "usage_type": {"default":
                AssetUsageTypes.objects.first()},
            "file_filecontroller": {"required": False},
        }

        validators = []

    def create(self, validated_data):
        contentfile_id = validated_data.pop("contentfile_id")
        file = super().create(validated_data)
        rel_obj = FileController()
        rel_obj.update_file(file=file, related_model_string=\
            f"{DJ_APP_NAME}.FileConnector",contentfile_id =\
            contentfile_id)
        return file

class JobListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        ret = []
        for s_data in validated_data:
            ret.append(self.child.create(s_data))
        return ret

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'source_language', 'target_language', 'project', ]
        model = Job
        list_serializer_class = JobListSerializer

        extra_kwargs = {
            "project": {
                "required": False}}

        validators = []

    def create(self, validated_data):
        data = validated_data
        return super().create(data)

class DownloadControllerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DownloadController
        fields = "__all__"
        extra_kwargs = {
            "related_model_string": {"default":"github_.DownloadProject"}
        }

class FileConnectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileConnector
        fields = "__all__"

class ProjectStepsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSteps
        fields = ("project", "steps")
        extra_kwargs = {
            "project": {"required": False}
        }

class ProjectSerializerV2(serializers.ModelSerializer):
    # jobs = JobSerializer(many=True)
    # files = FileSerializer(many=True)
    branch_id = serializers.IntegerField(write_only=True)
    file_create_type = serializers.CharField(read_only=True,
            source="project_file_create_type.file_create_type")
    proj_steps = ProjectStepsSerializer(many=True)

    class Meta:
        model = Project
        fields = ( "project_name", "branch_id", "file_create_type",
                   "mt_engine", "project_type", "proj_steps")

        extra_kwargs = {
            "project_type": {"default": ProjectType.objects.get(id=2)} # "Advanced project type..."
        }
        # "download_controller",

    def create(self, validated_data):
        branch_id = validated_data.pop("branch_id")
        proj_steps = validated_data.pop("proj_steps")
        print("data----->", validated_data)
        project = super().create(validated_data)
        rel_obj = DownloadController()
        rel_obj.update_project(project=project, related_model_string=
            f"{DJ_APP_NAME}.DownloadProject", branch_id=branch_id)
        ProjectFilesCreateType.objects.create(project=project,
            file_create_type=ProjectFilesCreateType.FileType.integeration)
        for proj_step in proj_steps:
            ProjectSteps.objects.create(**proj_step, project=project)
        return project

class ProjectCreateReqReslvSerlzr(serializers.Serializer):
    project_name = serializers.CharField()
    source_language = serializers.IntegerField()
    target_languages = serializers.ListField()
    localizable_ids = serializers.ListField()
    steps = serializers.ListField()
    mt_engine = serializers.IntegerField()

    def to_representation(self, instance):
        ret = super().to_representation(instance=instance)
        ret["file_connectors"] = [{"contentfile": _id} for _id in
            ret.pop("localizable_ids")]
        sl = ret.pop("source_language")
        ret["jobs"] = [{"source_language": sl , "target_language": tl}
            for tl in ret.pop("target_languages")]
        ret["proj_steps"] = [{"steps": step} for step in ret.pop("steps")]
        if not ret["proj_steps"]:
            ret["proj_steps"] = [{"steps": 1}] # Post editing default add
        return ret

class GithubHookSerializerD1(serializers.Serializer):
    payload = serializers.JSONField()

class GithubHookSerializerD3(serializers.ModelSerializer):
    name = serializers.CharField()
    full_name = serializers.CharField()

    def validate(self, attrs):
        print("validate call+++++")
        if not Repository.objects.filter(repository_name=attrs["name"],
            repository_fullname=attrs["full_name"]):
            raise serializers.ValidationError("repository not exist!!!")
        return super().validate(attrs=attrs)

    class Meta:
        model = Repository
        fields = ("name", "full_name", "id", "repository_fullname")
        read_only_fields = ("id", "repository_fullname")

    def to_representation(self, instance):
        self.instance = Repository.objects.filter(
            repository_name=self.data["name"], repository_fullname=
        self.data["full_name"]).first()
        return super().to_representation(instance=instance)

class GithubHookSerializerD4(serializers.Serializer):
    modified = serializers.ListField()
    added = serializers.ListField()
    removed = serializers.ListField()

class GithubHookSerializerD5(serializers.Serializer):
    id = serializers.CharField()

class GithubHookSerializerD2(serializers.Serializer):
    ref = serializers.CharField()
    created = serializers.BooleanField()
    repository = GithubHookSerializerD3()
    commits = GithubHookSerializerD4(many=True)
    head_commit = GithubHookSerializerD5()

    def validate_ref(self, value):
        if 'refs/heads' in value:
            return value
        raise ValueError("refs/heads is missing in value. So you should modify "
            "the validation prefix content or someother fix..." )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["ref"] = ret["ref"].replace("refs/heads/", "")
        ret["commit_hash"] = ret["head_commit"]["id"]
        return ret


class HookDeckSerializer(serializers.ModelSerializer):

    class Meta:
        fields = [ 'project', 'hook_url',
            'password', "hook_ref_token"]
        model = HookDeck
        extra_kwargs = {
            "hook_url": {"required": False},
            "password": {"required": False},
            "hook_ref_token": {"required": False}
        }

    def create(self, validated_data):
        data = validated_data
        return super().create(data)

    # def to_representation(self, instance):
    #     ret = super().to_representation(instance=instance)
    #     if self.context.get("for_hook_api_call", False):
    #         ret["name"] = instance.hook_name
    #         ret["source"] = {}
    #         ret["source"]["name"] = instance.source_name
    #         ret["destination"] = {}
    #         ret["destination"]["name"] = instance.destination_name
    #         ret["destination"]["cli_path"] = instance.hook_cli_path
    #
    #     return ret

class HookDeckCallSerializerSub2(serializers.Serializer):
    name = serializers.CharField()
    cli_path = serializers.CharField()

class HookDeckCallSerializerSub1(serializers.Serializer):
    name = serializers.CharField()

class HookDeckCallSerializer(serializers.Serializer):
    name = serializers.CharField()
    source = HookDeckCallSerializerSub1()
    destination = HookDeckCallSerializerSub2()

class HookDeckResponseSerializer(serializers.Serializer):
    url = serializers.CharField()

    def to_internal_value(self, data):
        url_data = data["source"]
        return super().to_internal_value(data=url_data)

class TokenValidateSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value):
        if not HookDeck.objects.filter(hook_ref_token=value):
            raise serializers.ValidationError("token is invalid")

        return value

    def validate(self, attrs):
        req = self.context["request"]
        instance = HookDeck.objects.filter(hook_ref_token=attrs["token"]).first()
        secret = instance.password
        is_valid = self.validate_signature(req, secret)
        if not is_valid:
            raise serializers.ValidationError("secret key not matching")
        self.instance = instance
        return super().validate(attrs=attrs)

    class Meta:
        # model = HookDeck
        fields = ("token", )

    def validate_signature(self, payload, secret):

        signature_header = payload.headers['X-Hub-Signature']
        sha_name, github_signature = signature_header.split('=')
        if sha_name != 'sha1':
            print('ERROR: X-Hub-Signature in payload headers was not sha1=****')
            return False

        body = payload.body
        local_signature = hmac.new(secret.encode('utf-8'), msg=body,
                                   digestmod=hashlib.sha1)

        return hmac.compare_digest(local_signature.hexdigest(), github_signature)

