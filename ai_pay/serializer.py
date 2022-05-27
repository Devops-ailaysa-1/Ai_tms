from rest_framework import serializers
from ai_pay.models import PurchaseOrder

class PurchaseOrderSerializer(serializers.serializer):

    class Meta:
        model = PurchaseOrder
        fields = ('PO_id','client')


class PurchaseOrder(serializers.Modelserializer):
    class Meta:
        model = PurchaseOrder
        fields = ('PO_id','client')
