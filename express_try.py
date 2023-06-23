from ai_workspace.models import *
text = '''Della H. Raney (January 10, 1912 – October 23, 1987) was an American nurse. Raney was the first African American nurse to report for duty in World War II, and the first to be appointed chief nurse. In 1944, she became the first black nurse affiliated with the Army Air Corps promoted to captain, and was later promoted to major in 1946. Raney retired from the Army in 1978. This photograph of Raney seated behind her desk was taken in 1945; at the time, she headed the nursing staff at the station hospital at Camp Beale in California.

Della H. Raney (January 10, 1912 – October 23, 1987) was an American nurse. Raney was the first African American nurse to report for duty in World War II, and the first to be appointed chief nurse. In 1944, she became the first black nurse affiliated with the Army Air Corps promoted to captain, and was later promoted to major in 1946. Raney retired from the Army in 1978. This photograph of Raney seated behind her desk was taken in 1945; at the time, she headed the nursing staff at the station hospital at Camp Beale in California.

Della H. Raney (January 10, 1912 – October 23, 1987) was an American nurse. Raney was the first African American nurse to report for duty in World War II, and the first to be appointed chief nurse. In 1944, she became the first black nurse affiliated with the Army Air Corps promoted to captain, and was later promoted to major in 1946. Raney retired from the Army in 1978. This photograph of Raney seated behind her desk was taken in 1945; at the time, she headed the nursing staff at the station hospital at Camp Beale in California.'''
NEWLINES_RE = re.compile(r"\n{2,}")
    no_newlines = text.strip("\n")  # remove leading and trailing "\n"
    split_text = NEWLINES_RE.split(no_newlines)
for i,j  in enumerate(split_text):
    sents = nltk.sent_tokenize(j)
    for l,k in enumerate(sents):
        print("para------->",i)
        print("sent--------->",k)
        print("sent_seq------>",l)
        ExpressProjectSrcSegment.objects.create(task_id=6095,src_text_unit=i,src_text=k,seq_id=l)
import nltk
for i,j  in enumerate(split_text):
    sents = nltk.sent_tokenize(j)
    for l,k in enumerate(sents):
        print("para------->",i)
        print("sent--------->",k)
        print("sent_seq------>",l)
        ExpressProjectSrcSegment.objects.create(task_id=6095,src_text_unit=i,src_text=k,seq_id=l)
ExpressProjectSrcSegment.objects.all()
ExpressProjectSrcSegment.objects.all().delete()
for i,j  in enumerate(split_text):
    sents = nltk.sent_tokenize(j)
    for l,k in enumerate(sents):
        print("para------->",i)
        print("sent--------->",k)
        print("sent_seq------>",l)
        tar = get_translation(mt_engine_id=1,source_string = k ,source_lang_code=task.job.source_lang_code , target_lang_code=task.job.target_lang_code,user_id=109)
        ExpressProjectSrcSegment.objects.create(task_id=6095,src_text_unit=i,src_text=k,seq_id=l)
from ai_workspace.api_views import get_translation
for i,j  in enumerate(split_text):
    sents = nltk.sent_tokenize(j)
    for l,k in enumerate(sents):
        print("para------->",i)
        print("sent--------->",k)
        print("sent_seq------>",l)
        tar = get_translation(mt_engine_id=1,source_string = k ,source_lang_code=task.job.source_lang_code , target_lang_code=task.job.target_lang_code,user_id=109)
        ExpressProjectSrcSegment.objects.create(task_id=6095,src_text_unit=i,src_text=k,seq_id=l)
for i,j  in enumerate(split_text):
    sents = nltk.sent_tokenize(j)
    for l,k in enumerate(sents):
        print("para------->",i)
        print("sent--------->",k)
        print("sent_seq------>",l)
        #tar = get_translation(mt_engine_id=1,source_string = k ,source_lang_code=task.job.source_lang_code , target_lang_code=task.job.target_lang_code,user_id=109)
        ExpressProjectSrcSegment.objects.create(task_id=6095,src_text_unit=i,src_text=k,seq_id=l)
for i in ExpressProjectSrcSegment:
    print(i.source)
for i in ExpressProjectSrcSegment.objects.all():
    print(i.src_text)
print(In[13])
for i in ExpressProjectSrcSegment.objects.all():
    print(i.src_text)
    tar = get_translation(mt_engine_id=1,source_string = k ,source_lang_code=i.task.job.source_lang_code , target_lang_code=i.task.job.target_lang_code,user_id=109)
    ExpressProjectTarSegment.objects.create(src_seg = i,mt_raw = tar,mt_engine=1)
t = Task.objects.last()
t.job
t.job.source_lanuage_code
t.job.source_language_code
t.job.target_language_code
for i in ExpressProjectSrcSegment.objects.all():
    print(i.src_text)
    tar = get_translation(mt_engine_id=1,source_string = k ,source_lang_code=i.task.job.source_language_code , target_lang_code=i.task.job.target_language_code,user_id=109)
    ExpressProjectTarSegment.objects.create(src_seg = i,mt_raw = tar,mt_engine=1)
for i in ExpressProjectSrcSegment.objects.all():
    print(i.src_text)
    tar = get_translation(mt_engine_id=1,source_string = k ,source_lang_code=i.task.job.source_language_code , target_lang_code=i.task.job.target_language_code,user_id=109)
    ExpressProjectSrcMTRaw.objects.create(src_seg = i,mt_raw = tar,mt_engine=1)
for i in ExpressProjectSrcSegment.objects.all():
    print(i.src_text)
    tar = get_translation(mt_engine_id=1,source_string = k ,source_lang_code=i.task.job.source_language_code , target_lang_code=i.task.job.target_language_code,user_id=109)
    ExpressProjectSrcMTRaw.objects.create(src_seg = i,mt_raw = tar,mt_engine_id=1)
ExpressProjectSrcSegment.objects.filter(task_id=6025)
query = ExpressProjectSrcSegment.objects.filter(task_id=6025).query
query.group_by = ['designation']
results = QuerySet(query=query, model=ExpressProjectSrcSegment)
rr=ExpressProjectSrcSegment.objects.filter(task_id=6025).raw('SELECT * FROM ai_workspace GROUP BY src_text_unit')
rr
for i in rr:
    print(i)
rr=ExpressProjectSrcSegment.objects.filter(task_id=6025).raw('SELECT * FROM ai_workspace_expressprojectsrcsegment GROUP BY src_text_unit')
rr
for i in rr:
    print(i)
rr=ExpressProjectSrcSegment.objects.raw('SELECT * FROM ai_workspace_expressprojectsrcsegment GROUP BY src_text_unit')
rr
for i in rr:
    print(i)
query = ExpressProjectSrcSegment.objects.filter(task_id=6025).query
query.group_by = ['designation']
results = QuerySet(query=query, model=ExpressProjectSrcSegment)
from django.db.models.query import QuerySet
query = ExpressProjectSrcSegment.objects.filter(task_id=6025).query
query.group_by = ['designation']
results = QuerySet(query=query, model=ExpressProjectSrcSegment)
results
query = ExpressProjectSrcSegment.objects.filter(task_id=6025).query
query.group_by = ['src_text_unit']
results = QuerySet(query=query, model=ExpressProjectSrcSegment)
results
query = ExpressProjectSrcSegment.objects.filter(task_id=6095).query
query.group_by = ['src_text_unit']
results = QuerySet(query=query, model=ExpressProjectSrcSegment)
results
results = ExpressProjectSrcSegment.objects.filter(task_id = 6095).distinct('src_text_unit')
for i in results:
    rr = ExpressProjectSrcSegment.objects.filter(task_id = 6095).filter(src_text_unit=i.src_text_unit)
results = ExpressProjectSrcSegment.objects.filter(task_id = 6095).distinct('src_text_unit')
for i in results:
    rr = ExpressProjectSrcSegment.objects.filter(task_id = 6095).filter(src_text_unit=i.src_text_unit)
    print(rr)
results = ExpressProjectSrcSegment.objects.filter(task_id = 6095).distinct('src_text_unit')
for i in results:
    rr = ExpressProjectSrcSegment.objects.filter(task_id = 6095).filter(src_text_unit=i.src_text_unit)
    print(rr)
    for i in rr:
        print(i.src_text)
results = ExpressProjectSrcSegment.objects.filter(task_id = 6095).distinct('src_text_unit')
src=''
for i in results:
    rr = ExpressProjectSrcSegment.objects.filter(task_id = 6095).filter(src_text_unit=i.src_text_unit)
    print(rr)
    for i in rr:
        print(i.src_text)
        src = src + i.src_text
        print(src)
results = ExpressProjectSrcSegment.objects.filter(task_id = 6095).distinct('src_text_unit')
src=''
for i in results:
    rr = ExpressProjectSrcSegment.objects.filter(task_id = 6095).filter(src_text_unit=i.src_text_unit)
    print(rr)
    for i in rr:
        print(i.src_text)
        src = src + i.src_text
    print(src)
results = ExpressProjectSrcSegment.objects.filter(task_id = 6095).distinct('src_text_unit')
src=''
for i in results:
    rr = ExpressProjectSrcSegment.objects.filter(task_id = 6095).filter(src_text_unit=i.src_text_unit)
    print(rr)
    for i in rr:
        print(i.src_text)
        src = src + i.src_text
    src
%save express_try.py
%hist -f  express_try.py
