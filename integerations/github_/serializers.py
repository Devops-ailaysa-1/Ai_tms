from rest_framework import serializers
import json
from .models import GithubOAuthToken, FetchInfo,\
    Repository

from github import Github

class GithubOAuthTokenSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("oauth_token", "ai_user", \
                  "is_token_expired", "username")
        model = GithubOAuthToken

        extra_kwargs = {
            "username": {"read_only": True}
        }

    def validate_oauth_token(self, value):
        g = Github(value)

        try:
            g.get_user().login
        except:
            raise serializers.ValidationError("Token is invalid!!!")

        return value

    def create(self, validated_data):
        data = validated_data
        g = Github(data["oauth_token"])
        username = g.get_user().login
        data["username"] = username
        return super().create(data)


