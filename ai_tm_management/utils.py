from translate.storage.tmx import  tmxfile

class TmUtils:
    '''
    tmxfile library supports only one source and one target tmx files...
    '''
    def __init__(self, file_name,
        target_language_codes,
        source_language_code="en"):
        self.file_name = file_name
        self.target_language_code = target_language_code
        self.source_language_code = source_language_code


    @staticmethod
    def get_tmxfile_obj(file_name, src_lng_code, tar_lng_code):
        with open(file_name, "rb") as fin:
            tmx_file = tmxfile(fin, src_lng_code, tar_lng_code)
        return tmx_file

    @staticmethod
    def get_extracted_data(tmx_file_iter):
        ret_data = []
        for node in tmx_file.unit_iter():
            ret_data.append({"source":node.source,
                "target":node.target})
        return ret_data

    def extracted_data_from_file(self):
        tmx_file_iter = self.get_tmxfile_obj(self.file_name,
            self.source_language_code, self.target_language_code)
        return self.get_extracted_data(tmx_file_iter=tmx_file_iter)








