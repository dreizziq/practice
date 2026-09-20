from django.db import models
from django.conf import settings

class Note(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='notes')
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=~models.Q(title=''), name='note_title_not_empty'),
            models.CheckConstraint(condition=~models.Q(body=''), name='note_body_not_empty'),
        ]

    def __str__(self):
        return f'{self.title} {self.body}'
