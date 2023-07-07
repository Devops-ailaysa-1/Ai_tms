from ai_workspace.models import Task
from rest_framework import serializers
from ai_pay.models import POAssignment, POTaskDetails, PurchaseOrder,AilaysaGeneratedInvoice
from django.http import HttpRequest
from django.db.models import Q
from djstripe.models import Invoice,Customer

class POTaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = POTaskDetails
        fields = "__all__"


class POAssignmentSerializer(serializers.ModelSerializer):
    # tasks = POTaskSerializer(many=True,source='assignment_po')
    class Meta:
        model = POAssignment    
        fields =('assignment_id','step')


class PurchaseOrderSerializer(serializers.ModelSerializer):
    # currency_code = serializers.CharField(source='currency.currency_code')
    currency_code = serializers.SerializerMethodField()
    client_name = serializers.CharField(source='client.fullname')
    seller_name = serializers.CharField(source='seller.fullname')
    client_country = serializers.CharField(source='client.country.name')
    seller_country = serializers.CharField(source='seller.country.name')
    assignment = POAssignmentSerializer()
    # tasks = POTaskSerializer(many=True,source='po_task')
    class Meta:
        model = PurchaseOrder
        fields = ('poid','client','seller','client_name','seller_name','client_country','seller_country','po_status','po_file',
                'currency','currency_code','created_at','po_total_amount','assignment')
        extra_kwargs = {
		 	"currency_name": {"read_only": True},
             "currency":{"write_only":True},
             "client_name":{"read_only": True},
            "seller_name":{"read_only": True},
            "client_country":{"read_only": True},
            "seller_country":{"read_only": True},
            "po_file":{"read_only": True}
             #"created_at":{"write_only":True}
            }

    def get_currency_code(self,obj):
        if  obj.currency ==None:
            return None 
        else:
            return obj.currency.currency_code


class PurchaseOrderListSerializer(serializers.Serializer):
    payable=serializers.SerializerMethodField()
    receivable=serializers.SerializerMethodField()


    def _get_request(self):
        request = self.context
        if not isinstance(request, HttpRequest):
            request = request._request
        return request

    def get_payable(self,obj):
        query = obj.filter(client = self._get_request().user).order_by('-created_at')
        return PurchaseOrderSerializer(query,many=True).data


    def get_receivable(self,obj):
        query = obj.filter(seller = self._get_request().user).order_by('-created_at')
        return PurchaseOrderSerializer(query,many=True).data


class PurchaseOrderTaskListSerializer(serializers.Serializer):
    payable=serializers.SerializerMethodField()
    receivable=serializers.SerializerMethodField()

    def _get_request(self):
        request = self.context
        if not isinstance(request, HttpRequest):
            request = request._request
        return request

    def _get_user(self):
        user = self._get_request().user
        if user.is_internal_member:
            user = user.team.owner
        return user
   

    def get_payable(self,obj):
        query = obj.filter(client = self._get_user()).order_by('-created_at')
        return PurchaseOrderSerializer(query,many=True).data


    def get_receivable(self,obj):
        query = obj.filter(seller = self._get_user()).order_by('-created_at')
        return PurchaseOrderSerializer(query,many=True).data

    
class AilaysaGeneratedInvoiceSerializer(serializers.ModelSerializer):
    currency_code = serializers.CharField(source='currency.currency_code')
    client_name = serializers.CharField(source='client.fullname')
    seller_name = serializers.CharField(source='seller.fullname')
    class Meta:
        model = AilaysaGeneratedInvoice
        fields = ('id','invoid','invo_status','client','seller','client_name','seller_name',
                'currency','currency_code','created_at','tax_amount','total_amount','grand_total')
        extra_kwargs = {
		 	"currency_name": {"read_only": True},
             "currency":{"write_only":True},
             "client_name":{"read_only": True},
            "seller_name":{"read_only": True},
            "currency_code":{"read_only":True},
             #"created_at":{"write_only":True}
            }

    def validate(self, data):
        instance = getattr(self, 'instance', None)
        if data['invo_status'] == 'void' and instance:
            if instance.invo_status != 'open':
                raise serializers.ValidationError({"invo_status": "invoice status not suitable for voiding"})
        if data['invo_status'] == 'paid' and instance:
            if instance.invo_status != 'open':
                raise serializers.ValidationError({"invo_status": "invoice status not suitable for voiding"})         
        return data

    def update(self, instance, validated_data):
        if validated_data.get('invo_status'):
            instance.invo_status = validated_data.get("invo_status",\
                instance.invo_status)
            instance.save()      
        return instance



class StripeInvoiceSerializer(serializers.ModelSerializer):
    invoid = serializers.CharField(source='number') 
    invo_status = serializers.CharField(source='status')
    currency_code = serializers.CharField(source='currency')
    client_name = serializers.CharField(source='customer_name')
    seller_name = serializers.CharField(source='account_name')
    created_at = serializers.DateTimeField(source='created')
    grand_total=serializers.DecimalField(max_digits=19,decimal_places=2,source='total')
    stripe= serializers.SerializerMethodField()
    class Meta:
        model = Invoice
        #fields ="__all__"
        # fields =('id','status','account_name','customer_name','total','tax','currency','created')
        fields = ('id','invoid','invo_status','client_name','seller_name',
        'currency','currency_code','created_at','grand_total','stripe')

    def get_stripe(self,obj):
        return {"stripe":True,"invoice_pdf":obj.invoice_pdf,"hosted_invoice_url":obj.hosted_invoice_url}


    # def to_representation(self, instance):
    #     response = super().to_representation(instance)
    #     response["payable"] = sorted(response["payable"], key=lambda x: x["created_at"])
    #     return response



class InvoiceListSerializer(serializers.Serializer):
      
    payable=serializers.SerializerMethodField()
    receivable=serializers.SerializerMethodField()
    # stripe_invoices_payable=serializers.SerializerMethodField()
    # stripe_invoices_receivable=serializers.SerializerMethodField()


    def _get_request(self):
        request = self.context
        if not isinstance(request, HttpRequest):
            request = request._request
        return request
    
    def _get_ordering(self):
        request = self._get_request()
        return request.GET.get('ordering','created_at')


    def _get_ordering(self):
        request = self._get_request()
        return request.GET.get('ordering','created_at')

    def get_payable(self,obj):
        query_off = obj.filter(client = self._get_request().user)
        off_payable = AilaysaGeneratedInvoiceSerializer(query_off,many=True).data
        cust=Customer.objects.filter(subscriber=self._get_request().user)
        query_stripe = Invoice.objects.filter(Q(customer__in=cust)& ~Q(djstripe_owner_account__id="acct_1JWwU2SHaXADggwo"))
        stripe_payable=  StripeInvoiceSerializer(query_stripe,many=True).data
        #jsonArray1 = off_payable.concat(stripe_payable)
        return off_payable+stripe_payable


    def get_receivable(self,obj):
        from ai_pay.api_views import get_connect_account
        acc = get_connect_account(self._get_request().user)
        query_off = obj.filter(seller = self._get_request().user)
        off_receivable = AilaysaGeneratedInvoiceSerializer(query_off,many=True).data
        if acc:
            query_stripe = Invoice.objects.filter(djstripe_owner_account=acc)
        else:
            query_stripe=None
        stripe_receivable=StripeInvoiceSerializer(query_stripe,many=True).data
        return off_receivable+stripe_receivable

    # def get_stripe_invoices_payable(self,obj):
    #     cust=Customer.objects.filter(subscriber=self._get_request().user)
    #     query = Invoice.objects.filter(customer__in=cust)
    #     return StripeInvoiceSerializer(query,many=True).data

    # def get_stripe_invoices_receivable(self,obj):
    #     from ai_pay.api_views import get_connect_account
    #     acc = get_connect_account(self._get_request().user)
    #     if acc:
    #         query = Invoice.objects.filter(djstripe_owner_account=acc)
    #     else:
    #         query=None
    #     return StripeInvoiceSerializer(query,many=True).data

    def to_representation(self, instance):
        print("ordering",self._get_ordering())
        response = super().to_representation(instance)
        response["payable"] = sorted(response["payable"], key=lambda x: x[self._get_ordering()], reverse=True)
        response["receivable"] = sorted(response["receivable"], key=lambda x: x[self._get_ordering()],reverse=True)
        return response


class ProjectPoSerializer(serializers.Serializer):  
    pass


class PoAssignDetailsSerializer(serializers.ModelSerializer):
    step = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    job = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    class Meta:
        model = POTaskDetails
        fields = ("task_id","file_name","job","po","assignment","step","source_language","target_language","project_name",
                  "projectid","word_count","char_count","estimated_hours","unit_price","unit_type",
                  "total_amount","currency","tsk_accepted","assign_status","reassigned")
        
    def get_step(self,obj):
        return obj.assignment.step.id
    
    def get_file_name(self,obj):
        tsk = Task.objects.get(id=obj.task_id)
        if tsk.file:
            return tsk.file.filename
        return None
    
    def get_job(self,obj):
        tsk = Task.objects.get(id=obj.task_id) 
        return tsk.job.id
    
    def get_currency(self,obj):
        tsk = Task.objects.get(id=obj.task_id) 
        return obj.po.currency.id
    
    # def get