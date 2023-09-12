from ai_auth.models import UserCredits,TroubleshootIssues


class AilaysaTroubleShoot:

    # issues = (
    #     (0,"country_empty"),
    #     (1,"initial_credit_zero"),
    #     (2,"multiple_stripe_customer"),
    #     (3,"no_stripe_customer_found"),
    #     (4,"multiple_active_subscription"),
    #     (5,"no_subscription_created"),
    #     (6,"no_credits_found"),
    #     (7,"intial_credit_zero")
    # )
    issues_found =[] 

    def __init__(self,user,request=None):
        self.user = user
        self.request = request
        self.issues_found = []
        self.issues = TroubleshootIssues.objects.all()
    
    def account_basic_check(self):
        user = self.user
        if not user.is_internal_member:
            if user.country == None:
                self.issues_found.append(self.issues.get(issue="country_empty"))

    def subscription_check(self):
        user = self.user
        cust = None
        ## considered 
        if user.djstripe_customers.all().count() > 1:
            self.issues_found.append(self.issues.get(issue="multiple_stripe_customer"))
        elif user.djstripe_customers.all().count() == 0:
            self.issues_found.append(self.issues.get(issue="no_stripe_customer_found"))
        else:
            cust = user.djstripe_customers.last()

        if cust != None:
           if cust.subscriptions.filter(status__in=["active","trialing","past_due"]).count() > 1:
                self.issues_found.append(self.issues.get(issue="multiple_active_subscription"))

           if cust.subscriptions.all().count() == 0:
                self.issues_found.append(self.issues.get(issue="no_subscription_created")) 

        ## deprecate if Ailaysa subscription flow is added
    
    def credits_check(self):
        if not self.user.is_internal_member:
            us = UserCredits.objects.filter(user=self.user)
            if us.count() == 0:
                self.issues_found.append(self.issues.get(issue="no_credits_found"))
            elif us.count() == 1:
                if us.last().buyed_credits == 0 :
                    self.issues_found.append(self.issues.get(issue="intial_credit_zero"))   

    def account_signup_check(self):
        self.account_basic_check()
        self.subscription_check()
        print("issues",self.issues)
        print(self.issues.filter(issue="no_stripe_customer_found").last())
        if not self.issues.filter(issue="no_stripe_customer_found").last() in self.issues_found:
            self.credits_check()
        return self.issues_found

        

         
   