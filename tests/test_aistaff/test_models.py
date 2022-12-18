from ai_staff.models import Currencies,Languages
import pytest

# @pytest.mark.django_db
# class TestAiUserModel():
#     def test_create(self):
#         Currencies.objects.create(currency="RUPEE",currency_code="RRR")
#         assert Currencies.objects.filter(currency="RUPEE").exists()



@pytest.mark.django_db
class TestLanguagesModel():
    def test_list(self):
        Languages.objects.all()
        assert Languages.objects.filter(language="Tamil").exists()
