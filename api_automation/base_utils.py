import json

class BaseUtils:

    def json_dump_str_to_data(self, json_dump_str):
        return json.loads(json_dump_str)

    def get_key_from_data(self, json_dump_str, key):
        return self.json_dump_str_to_data(json_dump_str)[key]\

