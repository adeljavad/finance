from django.contrib import admin
from .models import Document, TrialBalance, ChatMessage

admin.site.register(Document)
admin.site.register(TrialBalance)
admin.site.register(ChatMessage)
