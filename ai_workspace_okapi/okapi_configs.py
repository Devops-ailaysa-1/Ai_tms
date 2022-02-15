

ALLOWED_FILE_EXTENSIONSFILTER_MAPPER ={
     ('.txt',): 'plain-text-processor',
     ('.odt', '.odp', '.ods'): 'openoffice-file-processor',
     ('.html', '.htm', '.xhtml'): 'html-processor',
     ('.tmx',): 'tmx-processor',
     ('.json',): 'json-processor',
     ('.properties',): 'properties-filter',
     ('.po',): 'po-processor',
     ('.ts',): 'ts-processor',
     ('.doc',
      '.docx',
      '.xlsx',
      '.pptx',
      '.docm',
      '.dotx',
      '.dotm'): 'open-xml-processor',
     ('.xliff', '.xlf'): 'xliff-processor',
     ('.md',): 'mark-down-processor',
     ('.rtf',): 'rtf-processor',
     ('.idml',): 'idml-processor',
     ('.sdlxliff',): 'sdl-package-processor',
     ('.resx',): 'resx-processor',
     ('.srt',): 'srt-processor',
     ('.csv', '.tsv'): 'table-processor',
     ('.strings',): 'strings-processor'
}

def flatten_mapper(data):
    ret = {}
    for k, v in data.items():
        for _ in k:
            ret[_] = v

    return ret

ALLOWED_FILE_EXTENSIONSFILTER_MAPPER_FLATTEN = flatten_mapper(ALLOWED_FILE_EXTENSIONSFILTER_MAPPER)

CURRENT_SUPPORT_FILE_EXTENSIONS_LIST = [
    ".txt", ".html", ".tsv", ".csv", ".odp", ".ods", ".odt", ".json",
    ".properties", ".po", ".docx", ".xlsx", ".pptx", ".xliff", ".xlf",
    ".idml", ".srt", ".strings"
]#".dotx" -> file processing pending