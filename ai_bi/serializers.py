from rest_framework import serializers
from ai_auth.models import AiUser
from ai_bi.models import BiUser
from djstripe.models import Subscription,Customer,Plan,Charge


class AiUserSerializer(serializers.ModelSerializer):

    class Meta:
        model  = AiUser
        # fields ="__all__"
        exclude = ('password', )

class BiUserSerializer(serializers.ModelSerializer):
    name=serializers.SerializerMethodField()
    email=serializers.SerializerMethodField()
    # role=serializers.SerializerMethodField()
    class Meta:
        model  = BiUser
        fields =("id","bi_user","bi_role","name","email")
        read_only_fields = ("name","email")

    def get_name(self,obj):
        return obj.bi_user.fullname

    # def get_role(self,obj):
    #     return obj.get_bi_role_display()

    def get_email(self,obj):
        return obj.bi_user.email
    
class PlanSerializer(serializers.Serializer):
    name=serializers.SerializerMethodField()
    class Meta:
        model=Plan
        fields=("id","name")

    def get_name(self,obj):
        return obj.product.name

class StipeCustomerSerialiizer(serializers.ModelSerializer):
    class Meta:
        model=Customer
        fields=("id","subscriber","email","currency","djstripe_created","djstripe_updated")

class DjStripeUserSerializer(serializers.ModelSerializer):
    # email=serializers.SerializerMethodField()
    customer=StipeCustomerSerialiizer(read_only=True)
    plan=PlanSerializer(read_only=True)
    class Meta:
        model = Subscription
        fields=("id","djstripe_id","livemode","created","metadata","billing_cycle_anchor","status",
                "plan","canceled_at","start_date","cancel_at_period_end","current_period_start","current_period_end","djstripe_owner_account","customer")

    # def get_email(self,obj):
    #     return obj.customer.email

class ChargeSerialiizer(serializers.ModelSerializer):
    class Meta:
        model=Charge
        fields ="__all__"
        # fields=("id","subscriber","email","currency","djstripe_created","djstripe_updated")