from rest_framework import serializers
from ai_pay.models import POAssignment, POTaskDetails, PurchaseOrder,AilaysaGeneratedInvoice
from django.http import HttpRequest
from django.db.models import Q

class POTaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = POTaskDetails
        fields = "__all__"


class POAssignmentSerializer(serializers.ModelSerializer):
    tasks = POTaskSerializer(many=True,source='assignment_po')
    class Meta:
        model = POAssignment    
        fields =('assignment_id','tasks')


class PurchaseOrderSerializer(serializers.ModelSerializer):
    currency_code = serializers.CharField(source='currency.currency_code')
    client_name = serializers.CharField(source='client.fullname')
    seller_name = serializers.CharField(source='seller.fullname')
    client_country = serializers.CharField(source='client.country.name')
    seller_country = serializers.CharField(source='seller.country.name')
    assignment = POAssignmentSerializer()
    class Meta:
        model = PurchaseOrder
        fields = ('poid','client','seller','client_name','seller_name','client_country','seller_country','po_status',
                'currency','currency_code','created_at','po_total_amount','assignment')
        extra_kwargs = {
		 	"currency_name": {"read_only": True},
             "currency":{"write_only":True},
             "client_name":{"read_only": True},
            "seller_name":{"read_only": True},
            "client_country":{"read_only": True},
            "seller_country":{"read_only": True},
             #"created_at":{"write_only":True}
            }


class PurchaseOrderListSerializer(serializers.Serializer):
    payable=serializers.SerializerMethodField()
    receivable=serializers.SerializerMethodField()


    def _get_request(self):
        request = self.context
        if not isinstance(request, HttpRequest):
            request = request._request
        return request

    def get_payable(self,obj):
        query = obj.filter(client = self._get_request().user)
        return PurchaseOrderSerializer(query,many=True).data


    def get_receivable(self,obj):
        query = obj.filter(seller = self._get_request().user)
        return PurchaseOrderSerializer(query,many=True).data




    
class AilaysaGeneratedInvoiceSerializer(serializers.ModelSerializer):
    currency_code = serializers.CharField(source='currency.currency_code')
    client_name = serializers.CharField(source='client.fullname')
    seller_name = serializers.CharField(source='seller.fullname')
    class Meta:
        model = AilaysaGeneratedInvoice
        fields = ('invoid','invo_status','client','seller','client_name','seller_name',
                'currency','currency_code','created_at','tax_amount','total_amount','grand_total')
        extra_kwargs = {
		 	"currency_name": {"read_only": True},
             "currency":{"write_only":True},
             "client_name":{"read_only": True},
            "seller_name":{"read_only": True},
            "currency_code":{"read_only":True},
             #"created_at":{"write_only":True}
            }


class InvoiceListSerializer(serializers.Serializer):
    payable=serializers.SerializerMethodField()
    receivable=serializers.SerializerMethodField()


    def _get_request(self):
        request = self.context
        if not isinstance(request, HttpRequest):
            request = request._request
        return request

    def get_payable(self,obj):
        query = obj.filter(client = self._get_request().user)
        return AilaysaGeneratedInvoiceSerializer(query,many=True).data


    def get_receivable(self,obj):
        query = obj.filter(seller = self._get_request().user)
        return AilaysaGeneratedInvoiceSerializer(query,many=True).data