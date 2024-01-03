from rest_framework import serializers
from .models import Providers, InvoiceDetail

class ProvidersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Providers
        fields = '__all__'

class InvoiceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceDetail
        fields = ['ivo_det_id', 'prod_id', 'quantity_invo_det', 'invo_det_invo_id']