from ai_auth.models import AiUser,UserCredits
from django.db.models import Q
from pathlib import Path
import json
import pandas as pd
import numpy as np
from collections import Counter,OrderedDict
from ai_workspace.models import Project
from djstripe.models import Subscription,Charge
import logging
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import Workbook
logger = logging.getLogger('django')
# FIXTURE_DIR_PATH = Path(__file__).parent.joinpath("fixtures")


# with FIXTURE_DIR_PATH.joinpath("test_users.json").open("r") as f:
#         test_users =json.load(f)



class AilaysaReport:
    def get_users(self,is_vendor=False,period=None,test=False):
        users= AiUser.objects.filter(~Q(email__icontains='deleted')&~Q(email='AnonymousUser')&~Q(is_staff=True) \
                    &~Q(is_internal_member=True)&Q(is_vendor=is_vendor)&~Q(email__icontains="+"))
        if test:
            users= AiUser.objects.filter(~Q(email__icontains='deleted')&~Q(email='AnonymousUser')&~Q(is_staff=True) \
                    &~Q(is_internal_member=True)&Q(is_vendor=is_vendor)&~Q(email__icontains="+"))
        else:
            users= AiUser.objects.filter(~Q(email__icontains='deleted')&~Q(email='AnonymousUser')&~Q(is_staff=True) \
                    &~Q(is_internal_member=True)&Q(is_vendor=is_vendor))
        if period != None:
            start_date = timezone.now()
            end_date =start_date + timedelta(period)
            users = users.filter(date_joined__range=[start_date,end_date])
        return users

    def get_projects_and_langs(self,users):
        tot_langpairs,langpair=[],[]
        pairs=dict()
        for user in users:
            projs = Project.objects.filter(ai_user=user)
            for proj in projs:
                jobs = proj.project_jobs_set.all()
                for job in jobs:
                    #print(job.__str__())
                    langpair.append(job.__str__())
            pairs[user]=langpair
            tot_langpairs.extend(pairs)
        tot_counts = Counter(tot_langpairs)
       # return pairs,tot_langpairs,

    def project_count(self,users):
        projs_count=dict()
        for user in users:
            projs = Project.objects.filter(ai_user=user)
            projs_count[user]=projs.count()
        return projs_count

    def user_credits(self,users):
        user_credits=dict()
        for user in users:
            uss = UserCredits.objects.filter(user=user)
            buy,left=0,0
            for us in uss:
                buy=buy+us.buyed_credits
                left=left+us.credits_left
            user_credits[user]={'buy':buy,'left':left}
        return user_credits
    
    def user_and_countries(self,users):
        return Counter(users.values_list('country__name',flat=True))
    
    def no_of_active_user(self,users):
        return Subscription.objects.filter(status__in=['trialing','active','past_due']). \
            filter(Q(customer__subscriber__in=users)&~Q(plan__product__name="Pro - V")).values \
                ('customer__email').annotate(dcount =Count("customer__email")).count()
    
    def paid_users(self,users):
        return Charge.objects.filter(customer__subscriber__in=users,status="succeeded").values('customer__email').annotate \
            (dcount =Count("customer__email"))
    
    def users_trial_ending(self,users):
        start_date = timezone.now()
        end_date =start_date + timedelta(8)

        return Subscription.objects.filter(status__in=['trialing']).filter(Q(customer__subscriber__in=users)&~Q(plan__product__name="Pro - V")).filter \
            (trial_end__range=[start_date,end_date]).values("trial_end")
    
    def vendors_added_week(self,users):
        vendors = AiUser.objects.filter(~Q(email__icontains='deleted')&~Q(email='AnonymousUser')&~Q(is_staff=True)&~Q(is_internal_member=True)&Q(is_vendor=True))
        one_week_ago = timezone.now() - timedelta(days=7)
        return vendors.filter(date_joined__gte=one_week_ago).values('date_joined')

    def users_by_plan(self,users):
        return Subscription.objects.filter(status__in=['trialing','active','past_due']).filter(Q(customer__subscriber__in=users)&~Q(plan__product__name="Pro - V")).values \
            ('plan__product__name').annotate(dcount =Count("plan__product__name"))
    
    def langpairs_and_users(self,users):
        from collections import Counter

        tot_langpairs,langpair=[],[]
        pairs=dict()
        for user in users:
            projs = Project.objects.filter(ai_user=user)
            for proj in projs:
                jobs = proj.project_jobs_set.all()
                for job in jobs:
                    #print(job.__str__())
                    langpair.append(job.__str__())
            pairs[user.email]=langpair
        for key, value in pairs.items():
            tot_langpairs.extend(value)
        return Counter(tot_langpairs).most_common()
            
    def user_subscription_info(self,users,status=['trialing','active','past_due']):

        ## subscriptions data returns (sub_id,plan_name,plan_status,user_email)
        res = Subscription.objects.filter(status__in=status).filter \
        (Q(customer__subscriber__in=users)&~Q(plan__product__name="Pro - V")).values \
            ('customer__email').annotate(dcount =Count("customer__email")).filter(dcount=1)
        res_err = Subscription.objects.filter(status__in=status).filter \
        (Q(customer__subscriber__in=users)&~Q(plan__product__name="Pro - V")).values \
            ('customer__email').annotate(dcount =Count("customer__email")).filter(dcount__gte=2)
        if res_err.count()>0:
            logger.error("users have more than one active subscriptions")
        return res

    def users_details(self,users,proj_details,user_credits_ls,subs_details):
        
        data =[]
        df = pd.DataFrame(data, columns=['UID',
            'Email',
            'Country',
            'Projects Created',
            #'Langpair Used',
            'Intial Credits',
            'Credits Left',
            'Plan',
            'Subscription status'])
        for user in users:

            if proj_details:
                proj_count = proj_details.get(user)
            
            if user_credits_ls:
                user_credi_details = user_credits_ls.get(user)
                print(user_credi_details)


            if subs_details:
                try:
                    subs_details.get(customer__email=user.email).get('customer__email')
                    sub = Subscription.objects.get(customer__email=user.email,status__in=['trialing','active','past_due'])
                    plan_name = sub.plan.product.name
                    status = sub.status
                except:
                    sub = None
                    plan_name = None
                    status = None

            df2 = {'UID':user.uid,'Email':user.email, 'Country': user.country.name, 'Projects Created': proj_count,'Intial Credits':user_credi_details.get('buy'),'Credits Left':user_credi_details.get('left'),
                    'Plan':plan_name,'Subscription status':status,'Created at':pd.to_datetime(user.date_joined.replace(tzinfo=None))}
            df = df.append(df2, ignore_index = True)
            # df.insert(loc=0, column='UID', value=player_vals)
            # df.insert(loc=0, column='Email', value=player_vals)
            # df.insert(loc=0, column='Country', value=player_vals)
        return df
        
        # df = pd.DataFrame.from_dict({
        #     'UID': ['Nik', 'Kate', 'Evan', 'Kyra'],
        #     'Email': [31, 30, 40, 33],
        #     'Country': ['Toronto', 'London', 'Kingston', 'Hamilton'],
        #     'Projects Created':[0,1,2,4],
        #     'Langpair Used':['English-Tamil','Tamil-French','English-Tamil','English-Hindhi'],
        #     'Intial Credits':[2000,2000,2000,2000],
        #     'Credits Left':[100,200,202,20],
        #     'Plan':['pro','pro','Business','pro'],
        #     'Subscription status':['active','inactive','trialing','past_due']
        # })

    #df = df.append({'Name':'Jane', 'Age':25, 'Location':'Madrid'}, ignore_index=True)

       # df.to_excel('ailaysa-report.xlsx',index=False)
        # writer = pd.ExcelWriter("SalesReport.xlsx")
        # repr_sales.to_excel(writer, sheet_name="Sale per rep")

    # def chart_gen(self,df):
    #    df3 = df.groupby(pd.Grouper(key='Created at', axis=0, freq='M')).count()
    #    df3[df3['Created at'].dt.date.astype(str) == '2022-12-12']

    def users_stats(self,users):
        subs_details_trial = self.user_subscription_info(users,status=['trialing',])
        subs_details_past_due = self.user_subscription_info(users,status=['past_due',])
        users_week = self.get_users(period=8)
        vendors_week = self.get_users(is_vendor=True,period=8)
        paid_users =self.paid_users(users)
        df = pd.DataFrame(data =([subs.get('customer__email') for subs in subs_details_trial]),columns =['user in trial'])
        df1 = pd.DataFrame(data =([subs.get('customer__email') for subs in subs_details_past_due]),columns =['user in past_due'])
        df2 = pd.DataFrame(data =([user.email for user in users_week]),columns =['users added in week'])
        df3 = pd.DataFrame(data =([vendor.email for vendor in vendors_week]),columns =['Vendor added in week'])
        df4 = pd.DataFrame(data =([user.get('customer__email') for user in paid_users]),columns =['paid users'])
        result = pd.concat([df,df1,df2,df3,df4],axis=1)
        return result



    def create_excel(self,users):
        wb = Workbook()
        ws1 = wb.create_sheet("user_lang")
        ws2 = wb.create_sheet("countries")
        ws3 = wb.create_sheet("projects")
        ws4 =wb.create_sheet("users_counts")
        ws5 =wb.create_sheet("users_details")
        tot_pairs = self.langpairs_and_users(users)
        user_countries = self.user_and_countries(users)
        proj_count =self.project_count(users)
        projs_det = self.project_count(users)
        user_credits_ls = self.user_credits(users)
        subs_details = self.user_subscription_info(users)
        

        df4 = pd.DataFrame({'Language pairs':[pair[0] for pair in tot_pairs],'No of Task':[pair[1] for pair in tot_pairs]})
        for r in dataframe_to_rows(df4, index=False, header=True):
            ws1.append(r)
        df5 = pd.DataFrame({'Countries':[key for key in user_countries.keys()],'No of users':[value for value in user_countries.values()]})
        for r in dataframe_to_rows(df5, index=False, header=True):
            ws2.append(r)
        df6 = pd.DataFrame({'Users':[key.email for key in proj_count.keys()],'No of projects':[value for value in proj_count.values()]})
        for r in dataframe_to_rows(df6, index=False, header=True):
            ws3.append(r)
        df7 = self.users_stats(users)
        for r in dataframe_to_rows(df7, index=False, header=True):
            ws4.append(r)
        df8 = self.users_details(users,projs_det,user_credits_ls,subs_details)
        for r in dataframe_to_rows(df8, index=False, header=True):
            ws5.append(r)

        wb.save("ai_reports.xlsx")


 


    def create_chart(self):
        pass


    def report_generate(self):
        users = self.get_users()
        self.create_excel(users)