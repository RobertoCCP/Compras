from rest_framework import serializers
from .models import Providers

class ProvidersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Providers
        fields = '__all__'