from django import forms
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
from tastypie.serializers import Serializer
from tastypie.validation import CleanedDataFormValidation

from .models import Note


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ('title', 'body')


class NoteResource(ModelResource):
    class Meta:
        queryset = Note.objects.all().order_by('pk')
        resource_name = 'note'
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'put', 'delete']
        # Open CRUD access for the local tutorial, as in the original article.
        authorization = Authorization()
        fields = ['title', 'body']
        serializer = Serializer(formats=['json'])
        validation = CleanedDataFormValidation(form_class=NoteForm)
