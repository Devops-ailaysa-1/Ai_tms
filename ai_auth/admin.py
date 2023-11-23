from django.contrib import admin
from .models import (AiUser, UserAttribute,
                    TempPricingPreference,CreditPack,UserCredits,
                    BillingAddress,UserTaxInfo,Team,InternalMember, 
                    VendorOnboarding,ExistingVendorOnboardingCheck,CampaignUsers,
                    AilaysaCampaigns,TaskRoles,ProjectRoles,ApiUsage,SubscriptionOrder,
                    TroubleshootIssues,AiTroubleshootData,PurchasedUnits,PurchasedUnitsCount,
                    EnterpriseUsers)
from ai_vendor.models import VendorOnboardingInfo,VendorLanguagePair
from django.contrib.auth.models import Permission
from django.contrib.admin import AdminSite
#from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _
from django.db.models import Count
# from ai_staff.forms import AiUserCreationForm, AiUserChangeForm
#from django.contrib.auth import get_user_model



# Custom Admin page #

# User = get_user_model()


# class MyUserChangeForm(UserChangeForm):
#     class Meta(UserChangeForm.Meta):
#         model = User



# class UserAdmin(BaseUserAdmin):
#     add_form =  UserCreationForm

#     list_display = ('username', 'email', 'is_admin')
#     list_filter = ('is_admin',)

#     fieldsets = (
#         (None, {'fields': ('username', 'email','password')}),

#         ('Permissions', {'fields': ('is_admin',)}),
#     )

#     search_fields =  ('username', 'email')
#     ordering = ('username','email')

#     filter_horizontal = ()

# admin.site.register(MyUser,UserAdmin)




# def has_superuser_permission(request):
#     return request.user.is_active and request.user.is_superuser

# # Only superuser can access root admin site (default)
# admin.site.has_permission = has_superuser_permission

class StaffAdminSite(AdminSite):
    """Staff admin page definition"""
    site_header = "Ailaysa Staff"
    index_title = 'Staff administration'

staff_admin_site = StaffAdminSite(name='ai_staff')

# available only to super_users
# @admin.register(AiUser)
# class RootUserAdmin(UserAdmin):
#     # model = AiUser
#     # list_display = ('email','fullname','is_staff')
#     # fieldsets = UserAdmin.fieldsets + (
#     #         (None, {'fields': ('country','fullname')}),
#     #          ('Permissions', {'fields': ('is_admin',)}),
#     # )
#     # search_fields =  ('fullname', 'email')
#     # ordering = ('email',)

#     # def get_form(self, request, obj=None, **kwargs):
#     #     kwargs['exclude'] = ['first_name','last_name','username','password2', 'password1']
#     #     #kwargs['fields'] = ['']
#     #     return super(RootUserAdmin, self).get_form(request, obj, **kwargs)

#     fieldsets = (
#         (None, {'fields': ( 'email', 'password')}),
#         (_('Personal info'), {'fields': ('fullname',)}),
#         (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
#                                        'groups', 'user_permissions')}),
#         (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
#     )
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'password')}
#         ),
#     )
#     form = AiUserCreationForm
#     add_form = AiUserChangeForm
#     list_display = ('email', 'is_staff')
#     search_fields = ('email',)
#     ordering = ('email',)

# available to both types of admins hr (is_staff) and root (is_superuser)
@admin.register(VendorOnboarding)
@admin.register(VendorOnboarding, site=staff_admin_site)
class VAAdmin(admin.ModelAdmin):
#     fieldsets = (
#     (None, {'fields': ( 'name', 'email','cv_file','status')}),
#     #(_('Personal info'), {'fields': ('fullname',)}),
#     #(_('Permissions'), {'fields': (,)}),
#    # (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
#     )
    list_display = ("name", "email", "cv_file","status","country")
    def country(self,obj):
        try:
            user = AiUser.objects.get(email=obj.email)
        except AiUser.DoesNotExist:
            return None
        return user.country.name
@admin.register(VendorOnboardingInfo)
@admin.register(VendorOnboardingInfo, site=staff_admin_site)
class VOIAdmin(admin.ModelAdmin):
    list_display = ("user","fullname","country","vendor_status","cv_uploaded","service_rates_status","email_sent","email_sent_time","last_login")
    list_filter = ('user__existing_vendor_info__mail_sent','user__existing_vendor_info__mail_sent_time',)
    def cv_uploaded(self, obj):
        ven = VendorOnboarding.objects.filter(email=obj.user.email)
        if ven.exists():
            return True
        else:
            return False
    def fullname(self,obj):
        return obj.user.fullname
    def country(self,obj):
        return obj.user.country.name
    cv_uploaded.boolean = True

    def service_rates_status(self,obj):
        res = VendorLanguagePair.objects.filter(user=obj.user).values('user').annotate(service=Count('service')).annotate(service_type=Count('servicetype'))
        if len(res) != 0:
            if res[0].get('service',0) > 0 or  res[0].get('servicetype',0) > 0:
                return True
            else:
                return False

    service_rates_status.boolean= True

    def vendor_status(self,obj):
        try:
            ven = VendorOnboarding.objects.get(email=obj.user.email)
            if ven.get_status_display() == "Accepted":
                return True
            else:
                return False
        except:
            return False

    vendor_status.boolean= True

    def email_sent(self,obj):
        try:
            exe_ven = ExistingVendorOnboardingCheck.objects.get(user=obj.user)
            return exe_ven.mail_sent
        except BaseException as e:
            return False

    email_sent.boolean= True

    def email_sent_time(self,obj):
        try:
            exe_ven = ExistingVendorOnboardingCheck.objects.get(user=obj.user)
            return exe_ven.mail_sent_time
        except:
            return None

    def last_login(self,obj):
        last_login = obj.user.last_login
        return last_login




@admin.register(ExistingVendorOnboardingCheck)
class ExistingVendorEmailAdmin(admin.ModelAdmin):
    list_display = ("user","gen_password","mail_sent","mail_sent_time")

@admin.register(UserCredits)
class UserCreditsAdmin(admin.ModelAdmin):
    list_display = ("id","user","stripe_cust_id","buyed_credits","credits_left","expiry","ended_at")
    list_filter = ('user__email',)

@admin.register(ApiUsage)
class ApiUsageAdmin(admin.ModelAdmin):
    list_display = ("uid","email","service","usage")
    list_filter = ("email",)


@admin.register(CampaignUsers)
class ApiUsageAdmin(admin.ModelAdmin):
    list_display = ("user","campaign_code")
    list_filter = ("user__email",)

    def campaign_code(self,obj):
        return obj.campaign_name.campaign_name
    
@admin.register(EnterpriseUsers)
class EnterpriseUsersAdmin(admin.ModelAdmin):
    list_display = ("user","subscription_name")

# Custom Admin Page  #

# Register your models here.
admin.site.register(AiUser)
admin.site.register(UserAttribute)
admin.site.register(Permission)
admin.site.register(TempPricingPreference)
admin.site.register(CreditPack)
# admin.site.register(CampaignUsers)
admin.site.register(BillingAddress)
admin.site.register(UserTaxInfo)
admin.site.register(Team)
admin.site.register(InternalMember)
admin.site.register(AilaysaCampaigns)
admin.site.register(TaskRoles)
admin.site.register(ProjectRoles)
admin.site.register(SubscriptionOrder)
#admin.site.register(PersonalInformation)
admin.site.register(AiTroubleshootData)
admin.site.register(TroubleshootIssues)
admin.site.register(PurchasedUnits)
admin.site.register(PurchasedUnitsCount)
