# coding: utf-8
from ai_workspace.models import *
from ai_vendor.models import *
pr = Project.objects.last()
pr.get_jobs
pr.id
pr = Project.objects.get(id=970)
pr.get_jobs
jobs = pr.get_jobs
for i in jobs:
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.src_lang_id) & Q(target_lang_id=i.tar_lang_id)).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(Q(source_lang_id=i.src_lang_id) & Q(target_lang_id=i.tar_lang_id)).order_by("user").distinct("user").values('id')))
         
for i in jobs:
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_languauge_id)).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id)).order_by("user").distinct("user").values('id')))
         
         
for i in jobs:
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id)).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id)).order_by("user").distinct("user").values('id')))
         
         
from django.db.models import OuterRef, Subquery
for i in jobs:
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id)).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id)).order_by("user").distinct("user").values('id')))
         
         
tt
for i in tt:
    print(i.user)
    
for i in tt:
    print(i.user,i.source_lang_id,i.target_lang_id)
    
    
for i in tt:
    print(i.user,i.user_id,i.source_lang_id,i.target_lang_id)
    
    
    
for i in jobs:
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id)).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id)).order_by("user").distinct("user").values('id')))
         
         
for i in tt:
    print(i.user,i.user_id,i.source_lang_id,i.target_lang_id)
    
    
    
for i in jobs:
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id)).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id)).order_by("user").distinct("user").values('id')))
    for i in tt:
        print(i.user,i.user_id,i.source_lang_id,i.target_lang_id)
             
         
lang_pair = VendorLanguagePair.objects.none()
for i in jobs:
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id))
    lang_pair = lang_pair.union(tr)
    
             
         
lang_pair = VendorLanguagePair.objects.none()
for i in jobs:
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id))
    lang_pair = lang_pair.union(tt)
    
    
             
         
tt
for i in tt:
    res = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id)).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id)).order_by("user").distinct("user").values('id')))
    print(i.user,i.user_id,i.source_lang_id,i.target_lang_id)
    
             
         
for i in tt:
    res = VendorLanguagePair.objects.filter(id = i.id).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id = i.id).order_by("user").distinct("user").values('id')))
    print(i.user,i.user_id,i.source_lang_id,i.target_lang_id)
    
             
         
for i in tt:
    print(i)
    res = VendorLanguagePair.objects.filter(id = i.id).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id = i.id).order_by("user").distinct("user").values('id')))
    print(i.user,i.user_id,i.source_lang_id,i.target_lang_id)
    
             
         
for i in tt:
    print(i.source_lang_id)
    res = VendorLanguagePair.objects.filter(id = i.id).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id = i.id).order_by("user").distinct("user").values('id')))
    print(i.user,i.user_id,i.source_lang_id,i.target_lang_id)
    
             
         
for i in tt:
    print(i.source_lang_id,i.target_lang_id)
    res = VendorLanguagePair.objects.filter(id = i.id).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id = i.id).order_by("user").distinct("user").values('id')))
    print(i.user,i.user_id,i.source_lang_id,i.target_lang_id)
    
             
         
lang_pair = VendorLanguagePair.objects.none()
for i in jobs:
    print(i.source_language_id,i.target_language_id)
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id))
    lang_pair = lang_pair.union(tt)
    
    
             
         
lang_pair = VendorLanguagePair.objects.none()
for i in jobs:
    print(i.source_language_id,i.target_language_id)
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id))
    lang_pair = lang_pair.union(tt)
    print(lang_pair)
    
             
         
lang_pair = VendorLanguagePair.objects.none()
for i in jobs:
    print(lang_pair)
    print(i.source_language_id,i.target_language_id)
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id))
    lang_pair = lang_pair.union(tt)
    
             
         
lang_pair = VendorLanguagePair.objects.none()
for i in jobs:
    print(lang_pair)
    print(i.source_language_id,i.target_language_id)
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id))
    lang_pair = lang_pair.union(tt)
print(lang_pair)

             
         
lang_pair = VendorLanguagePair.objects.none()
for i in jobs:
    print(lang_pair)
    print(i.source_language_id,i.target_language_id)
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id))
    lang_pair_1 = lang_pair.union(tt)
print(lang_pair_1)

             
         
lang_pair = VendorLanguagePair.objects.none()
for i in jobs:
    print(lang_pair)
    print(i.source_language_id,i.target_language_id)
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id))
    lang_pair = lang_pair.union(tt)
print(lang_pair)


             
         
lang_pair = VendorLanguagePair.objects.none()
for i in jobs:
    print(lang_pair)
    print(i.source_language_id,i.target_language_id)
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id))
    print(tt.count())
    lang_pair = lang_pair.union(tt)
print(lang_pair)


             
         
lang_pair = VendorLanguagePair.objects.none()
for i in jobs:
    print(lang_pair)
    print(i.source_language_id,i.target_language_id)
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id))
    print(tt.count())
    lang_pair = lang_pair.union(tt)
print(lang_pair.count())


             
         
lang_pair = VendorLanguagePair.objects.none()
for i in jobs:
    print(lang_pair)
    print(i.source_language_id,i.target_language_id)
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id))
    print(tt.count())
    lang_pair = lang_pair.union(tt)
print(lang_pair.count())


             
         
lang_pair = VendorLanguagePair.objects.none()
for i in jobs:
    #print(lang_pair)
    print(i.source_language_id,i.target_language_id)
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id))
    print(tt.count())
    lang_pair = lang_pair.union(tt)
print(lang_pair.count())


             
         
for i in tt:
    print(i.source_lang_id,i.target_lang_id)
    res = VendorLanguagePair.objects.filter(id = i.id).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id = i.id).order_by("user").distinct("user").values('id')))
    print(i.user,i.user_id,i.source_lang_id,i.target_lang_id)
    
             
         
for i in lang_pair:
    print(i.source_lang_id,i.target_lang_id)
    res = VendorLanguagePair.objects.filter(id = i.id).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id = i.id).order_by("user").distinct("user").values('id')))
    print(i.user,i.user_id,i.source_lang_id,i.target_lang_id)
    
             
         
lang_pair = VendorLanguagePair.objects.none()
for i in jobs:
    #print(lang_pair)
    print(i.source_language_id,i.target_language_id)
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id)Q(deleted_at=None))
    print(tt.count())
    lang_pair = lang_pair.union(tt)
print(lang_pair.count())


             
         
lang_pair = VendorLanguagePair.objects.none()
for i in jobs:
    #print(lang_pair)
    print(i.source_language_id,i.target_language_id)
    tt = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id) & Q(deleted_at=None))
    print(tt.count())
    lang_pair = lang_pair.union(tt)
print(lang_pair.count())


             
         
for i in lang_pair:
    print(i.source_lang_id,i.target_lang_id)
    res = VendorLanguagePair.objects.filter(id = i.id).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id = i.id).order_by("user").distinct("user").values('id')))
    print(i.user,i.user_id,i.source_lang_id,i.target_lang_id)
    
             
         
out =[]
for i in lang_pair:
    print(i.source_lang_id,i.target_lang_id)
    res = VendorLanguagePair.objects.filter(id = i.id).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id = i.id).order_by("user").distinct("user").values('id')))
    dt = {"user":i.user.fullname,"user_id":i.user_id,"source":i.source_lang.language,"target":i.target_lang.language)
    out.append(dt)
    
             
         
out =[]
for i in lang_pair:
    print(i.source_lang_id,i.target_lang_id)
    res = VendorLanguagePair.objects.filter(id = i.id).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id = i.id).order_by("user").distinct("user").values('id')))
    dt = {"user":i.user.fullname,"user_id":i.user_id,"source":i.source_lang.language,"target":i.target_lang.language}
    out.append(dt)
    
             
         
out
out =[]
for i in lang_pair:
    print(i.source_lang_id,i.target_lang_id)
    res = VendorLanguagePair.objects.filter(id = i.id).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id = i.id).order_by("user").distinct("user").values('id')))
    print(res)
    
    
             
         
out =[]
for i in lang_pair:
    print(i.source_lang_id,i.target_lang_id)
    res = VendorLanguagePair.objects.filter(id = i.id).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id = i.id).order_by("user").distinct("user").values('id')))
    for j in res:
        print(j.user,j.source_lang_id,j.target_lang_id)
        
    
    
             
         
out =[]
for i in lang_pair:
    print(i.source_lang_id,i.target_lang_id)
    res = VendorLanguagePair.objects.filter(id = i.id).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id = i.id).order_by("user").distinct("user").values('id')))
    print(res.count())
    for j in res:
        print(j.user,j.source_lang_id,j.target_lang_id)
    
    
             
         
out =[]
for i in lang_pair:
    print(i.source_lang_id,i.target_lang_id)
    res = VendorLanguagePair.objects.filter(id = i.id).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id = i.id).order_by("user").distinct("user").values('id')))
    for j in res:
        dt = {"user":j.user.fullname,"user_id":j.user_id,"source":j.source_lang.language,"target":j.target_lang.language}
    out.append(dt)
    
             
         
out
out =[]
for i in lang_pair:
    print(i.source_lang_id,i.target_lang_id)
    res = VendorLanguagePair.objects.filter(id = i.id).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id = i.id).order_by("user").distinct("user").values('id')))
    for j in res:
        print(j)
        dt = {"user":j.user.fullname,"user_id":j.user_id,"source":j.source_lang.language,"target":j.target_lang.language}
    out.append(dt)
    
             
         
out =[]
for i in lang_pair:
    print(i.source_lang_id,i.target_lang_id)
    res = VendorLanguagePair.objects.filter(id = i.id).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id = i.id).order_by("user").distinct("user").values('id')))
    print(res.count())
    for j in res:
        print(j)
        dt = {"user":j.user.fullname,"user_id":j.user_id,"source":j.source_lang.language,"target":j.target_lang.language}
    out.append(dt)
    
             
         
out =[]
ids = []
for i in lang_pair:
    ids.append(i.id)     
res = VendorLanguagePair.objects.filter(id__in = ids).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id__in = ids).order_by("user").distinct("user").values('id')))
    for j in res:
        print(j)
        dt = {"user":j.user.fullname,"user_id":j.user_id,"source":j.source_lang.language,"target":j.target_lang.language}
    out.append(dt)
    
             
         
out =[]
ids = []
for i in lang_pair:
    ids.append(i.id)     
res = VendorLanguagePair.objects.filter(id__in = ids).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id__in = ids).order_by("user").distinct("user").values('id')))
for j in res:
    print(j)
    dt = {"user":j.user.fullname,"user_id":j.user_id,"source":j.source_lang.language,"target":j.target_lang.language}
    out.append(dt)
    
             
         
out
out =[]
ids = []
for i in lang_pair:
    ids.append(i.id)     
res = VendorLanguagePair.objects.filter(id__in = ids).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id__in = ids).order_by("user").distinct("user").values('id')))
print(res.count())
for j in res:
    print(j)
    dt = {"user":j.user.fullname,"user_id":j.user_id,"source":j.source_lang.language,"target":j.target_lang.language}
    out.append(dt)
    
             
         
out =[]
ids = []
for i in lang_pair:
    ids.append(i.id)   
yt = VendorLanguagePair.objects.filter(id__in = ids).count()
print("Yt",yt)
res = VendorLanguagePair.objects.filter(id__in = ids).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id__in = ids).order_by("user").distinct("user").values('id')))
print(res.count())
for j in res:
    print(j)
    dt = {"user":j.user.fullname,"user_id":j.user_id,"source":j.source_lang.language,"target":j.target_lang.language}
    out.append(dt)
    
             
         
out =[]
ids = []
for i in lang_pair:
    ids.append(i.id)   
yt = VendorLanguagePair.objects.filter(id__in = ids).count()
print("Yt",yt)
res = VendorLanguagePair.objects.filter(id__in = ids).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id__in = ids).order_by("user").distinct("user").values('id'))).values('user_id','source_lang_id','target_lang_id')
print(res.count())
for j in res:
    print(j)
#    dt = {"user":j.user.fullname,"user_id":j.user_id,"source":j.source_lang.language,"target":j.target_lang.language}
 #   out.append(dt)
    
             
         
out =[]
ids = []
for i in lang_pair:
    ids.append(i.id)   
yt = VendorLanguagePair.objects.filter(id__in = ids).count()
print("Yt",yt)
res = VendorLanguagePair.objects.filter(id__in = ids).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id__in = ids).order_by("user").values('id'))).values('user_id','source_lang_id','target_lang_id')
print(res.count())
for j in res:
    print(j)
#    dt = {"user":j.user.fullname,"user_id":j.user_id,"source":j.source_lang.language,"target":j.target_lang.language}
 #   out.append(dt)
    
             
         
out =[]
ids = []
for i in lang_pair:
    ids.append(i.id)   
yt = VendorLanguagePair.objects.filter(id__in = ids).count()
print("Yt",yt)
res = VendorLanguagePair.objects.filter(id__in = ids).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id__in = ids).order_by("user").values('id'))).distinct('target_lang_id')
print(res.count())
for j in res:
    print(j)
#    dt = {"user":j.user.fullname,"user_id":j.user_id,"source":j.source_lang.language,"target":j.target_lang.language}
 #   out.append(dt)
    
             
         
out =[]
ids = []
for i in lang_pair:
    ids.append(i.id)   
yt = VendorLanguagePair.objects.filter(id__in = ids).count()
print("Yt",yt)
res = VendorLanguagePair.objects.filter(id__in = ids).filter(pk__in=Subquery(
         VendorLanguagePair.objects.filter(id__in = ids).order_by("user").values('id'))).distinct('target_lang_id').values('user_id','source_lang_id','target_lang_id')
print(res.count())
for j in res:
    print(j)
#    dt = {"user":j.user.fullname,"user_id":j.user_id,"source":j.source_lang.language,"target":j.target_lang.language}
 #   out.append(dt)
    
             
         
res = VendorLanguagePair.objects.filter(id__in = ids)
from itertools import groupby
lang_pair_grouped_by_user = groupby(res.iterator(), lambda m: m.user)
messages_dict = {}
for user, group_of_lang_pairs in lang_pair_grouped_by_user:
    dict_key = user.fullname
    messages_dict[dict_key] = VendorLanguagePairSerializer(group_of_lang_pairs,many=True).data
print(messages_dict)

    
    
from ai_vendor.serializers import *
for user, group_of_lang_pairs in lang_pair_grouped_by_user:
    dict_key = user.fullname
    messages_dict[dict_key] = VendorLanguagePairSerializer(group_of_lang_pairs,many=True).data
print(messages_dict)

    
    
for user, group_of_lang_pairs in lang_pair_grouped_by_user:
    dict_key = user.fullname
    messages_dict[dict_key] = VendorLanguagePairSerializer(group_of_lang_pairs,many=True).data
print(messages_dict)

    
    
