from rest_framework import serializers
from .models import GitlabApp, Repository
from gitlab import Gitlab

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