# coding: utf-8
import pandas
import pandas as pd
df = pd.read_csv(r"C:/Users/Hp/Downloads/vendors.csv")
from ai_auth.models import AiUser
AiUser.objects.all()
AiUser._meta.fields
df_ = df [["email", "password", "created_at", "first_name", "last_name"]]
df_ = df [["email", "password", "created_at", "name", "lastname"]]
df_.rename(columns={"created_at" : "date_joined" }, inplace= True)
df_.head()
df["fullname"] = df.name + " " + df.lastname
df_["fullname"] = df_.name + " " + df_.lastname
df_["from_mysql"] = True
df_2 = df_.drop(["name", "lastname"], axis=1)
def get_utc( x ):
        from datetime import datetime   
            import pytz
local = pytz.timezone('Asia/Kolkata')
naive = datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
local_dt = local.localize(naive, is_dst=None)
utc_dt = local_dt.astimezone(pytz.utc)
def get_utc( x ):
        from datetime import datetime   
            import pytz
local = pytz.timezone('Asia/Kolkata')
naive = datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
local_dt = local.localize(naive, is_dst=None)
utc_dt = local_dt.astimezone(pytz.utc)
def get_utc( x ):
    from datetime import datetime   
    import pytz

    local = pytz.timezone('Asia/Kolkata')
    naive = datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
    local_dt = local.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt
    
df_2.date_joined = df_2.date_joined.apply( get_utc )
df_2.drop_duplicates(subset ="email",
                     keep = False, inplace = True)
for  i, j in df_2.iloc[:, :].iterrows():
    instance  = AiUser( **j)
    instance.save()
    
get_ipython().run_line_magic('save', 'current_session ~0/')
