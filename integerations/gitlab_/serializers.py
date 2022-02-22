from rest_framework import serializers
from gitlab import Gitlab

from .enums import DJ_APP_NAME
from ai_workspace.models import  Project, File, Job
from .models import GitlabApp, Repository, Branch, ContentFile
from ai_staff.models import AssetUsageTypes, Languages

class GitlabOAuthTokenSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("oauth_token", "ai_user", \
                  "is_token_expired", "username", "id")
        model = GitlabApp

        extra_kwargs = {
            "username": {"read_only": True}}

    def validate_oauth_token(self, value):
        gl = Gitlab("http://gitlab.com", value)

        try:
            gl.auth()
        except:
            raise serializers.ValidationError("Token is invalid!!!")

        return value


    def create(self, validated_data):
        data = validated_data
        gl = Gitlab("http://gitlab.com", data["oauth_token"])
        gl.auth()
        username = gl.user.username
        data["username"] = username

        if GitlabApp.objects.filter(
            ai_user=data["ai_user"],
            username=username
        ).first():
            raise serializers.ValidationError\
                ("Already github account registered!!!")
        return super().create(data)

class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'gitlab_token', 'repository_name', \
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
        print("list update called")
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
                  "file_path",
                  # 'created_on', 'accessed_on', 'updated_on'
                  ]

        extra_kwargs = {
            "id":{
                "read_only": False, "required": False
            }
        }

        model = ContentFile
        list_serializer_class = ContentFileListSerializer

    def create(self, validated_data):
        data = validated_data
        return super().create(data)


class LocalizeIdsSerializer(serializers.Serializer):
    localizable_ids = serializers.ListField()

class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ["id", 'project_name',
                  #'project_dir_path', 'created_at',
                  'ai_user',
                  #'ai_project_id', 'mt_engine', 'max_hits',
                  'threshold', f"project_{DJ_APP_NAME}downloadproject"
                  ]
        model = Project

        extra_kwargs = {
            "ai_user": {
                "required": False,},
            f"project_{DJ_APP_NAME}downloadproject":{
                "required": False}}

        validators = []

    def create(self, validated_data):
        data = validated_data
        project = Project.objects.create(**data)
        rel_obj = data[f'project_{DJ_APP_NAME}downloadproject']
        rel_obj.update_project(project=project)
        return project

    # def create(self, validated_data):
    #     data = validated_data
    #     return super().create(data)

class FileListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        ret = []
        for s_data in validated_data:
            ret.append(self.child.create(s_data))
        return ret

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'usage_type', 'file',
                  'project', f"{DJ_APP_NAME}contentfile"]
        model = File
        list_serializer_class = FileListSerializer

        extra_kwargs = {
            "project": {"required": False}}

        validators = []

    def create(self, validated_data):
        data = validated_data
        ret = super().create(data)
        cf = data[f'{DJ_APP_NAME}contentfile']
        cf.update_file(ret)
        return ret

class FileDataPrepareSerializer(serializers.Serializer):
    DEFAULT_ASSET = 1  # Need to add test

    usage_type = serializers.PrimaryKeyRelatedField(
        queryset=AssetUsageTypes.objects.all(),
        # default=AssetUsageTypes.objects.get(id=DEFAULT_ASSET)
    )
    files = serializers.ListField()
    content_files = serializers.ListField()

    @classmethod
    def get_dynamic_obj(cls, *args, **kwargs):
        cls.usage_type = serializers.CharField()
        obj = cls(*args, **kwargs)
        return obj

    def to_representation(self, instance):
        ret = super(FileDataPrepareSerializer, self)\
            .to_representation(instance=instance)
        ret = [{"usage_type":ret["usage_type"], "file":file, f"{DJ_APP_NAME}contentfile": contentfile} for
               file, contentfile in zip(ret.get("files"), ret.get("content_files"))]
        return ret

class JobListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        ret = []
        for s_data in validated_data:
            ret.append(self.child.create(s_data))
        return ret

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'source_language', 'target_language',
                  'project', ]
        model = Job
        list_serializer_class = JobListSerializer

        extra_kwargs = {
            "project": {
                "required": False}}

        validators = []

    def create(self, validated_data):
        data = validated_data
        return super().create(data)

class JobDataPrepareSerializer(serializers.Serializer):
    source_language = serializers.IntegerField()
    target_languages = serializers.ListField()

    def to_representation(self, instance):
        ret = super(JobDataPrepareSerializer, self)\
            .to_representation(instance=instance)
        ret = [{"source_language":ret["source_language"], "target_language":target_language} for
               target_language in ret.get("target_languages")]
        return ret




