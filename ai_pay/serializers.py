from rest_framework import serializers
from ai_pay.models import POAssignment, POTaskDetails, PurchaseOrder
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
    assignment = POAssignmentSerializer()
    class Meta:
        model = PurchaseOrder
        fields = ('poid','client','seller','po_status','currency','assignment')


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




    
