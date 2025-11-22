from rest_framework import serializers
from .models import Document, TrialBalance, ChatMessage

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'

class TrialBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrialBalance
        fields = '__all__'

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'
