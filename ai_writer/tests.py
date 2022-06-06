# from urllib import response
# from django.test import TestCase
# from rest_framework.test import APITestCase
# # Create your tests here.
 
# from ai_writer.models import FileDetails
 
 

# from ailaysadoc_api.settings import BASE_URL


# class DocTestCase(APITestCase):
#     def setUp(self) -> None:
#         FileDetails.objects.create(file_name = "Ailaysa_Test_file",
#                                         user_name = "Ailaysa" , 
#                                         store_quill_data = "some_quilljs_test in dict format", 
#                                         store_quill_text = "some_quilljs in plain text format")

#         FileDetails.objects.create(file_name = "Ailaysa_Test_file2",
#                                         user_name = "Ailaysa" , 
#                                         store_quill_data = "some_quilljs_test in dict format2", 
#                                         store_quill_text = "some_quilljs in plain text format2")


        
#         FileDetails.objects.create(file_name = "Ailaysa_Test_file3",
#                                         user_name = "Ailaysa" , 
#                                         store_quill_data = "some_quilljs_test in dict format3", 
#                                         store_quill_text = "some_quilljs in plain text format3")


#     def test_get_method(self):
#         url = BASE_URL+"/ailaysa-creator/"
#         response = self.client.get(url)
#         self.assertEqual(response.status_code , 200)
#         q =FileDetails.objects.all()
#         self.assertEqual(q.count(),3)
#         q = FileDetails.objects.filter(user_name = "Ailaysa")
#         self.assertEqual(q.count() , 3)


#     def test_delete_method_success(self):
#         url = BASE_URL+"/ailaysa-creator/1/"
#         response = self.client.delete(url)
#         self.assertEqual(response.status_code , 200)
