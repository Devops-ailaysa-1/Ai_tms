from integerations.github_.serializers import\
    ContentFileSerializer as GithubContentFileSerializer
from integerations.gitlab_.serializers import\
    ContentFileSerializer as GitLabContentFileSerializer


serializer_map = {
    "gitlab__contentfile_serializer": GitLabContentFileSerializer,
    "github__contentfile_serializer": GithubContentFileSerializer
}

