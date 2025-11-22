from django.db import models
# from django.db.models.JSONField  import JSONField

class Document(models.Model):
    title = models.CharField(max_length=255)
    source = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)
    content = models.TextField()

    def __str__(self):
        return self.title

class TrialBalance(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField()  # expected to be JSON with accounts and balances

    def __str__(self):
        return f"TB:{self.name} ({self.id})"

class ChatMessage(models.Model):
    user = models.CharField(max_length=128, blank=True, null=True)
    role = models.CharField(max_length=16)  # 'user' or 'assistant' or 'system'
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
