from ai_staff.models import Languages
from rest_framework.test import APITestCase

languages_locale_dict = {lang.id:lang.locale.count() for lang in Languages.objects.all()}

class TestRelations(APITestCase):

    def test_language_and_locale_relation(self):
        for id, count in languages_locale_dict.items():
            if not (count>0):
                raise ValueError(f"this language id --->{id} should have atleast one locale!!!")



