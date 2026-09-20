from django import forms
from tastypie.authentication import SessionAuthentication
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpNotFound
from tastypie.resources import ModelResource
from tastypie.serializers import Serializer
from tastypie.validation import CleanedDataFormValidation

from .models import Note
from .permissions import NoteAuthorization, is_auditor


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ('title', 'body')


class NoteResource(ModelResource):
    def get_object_list(self, request):
        queryset = super().get_object_list(request)
        user = request.user
        if not user.is_authenticated:
            return queryset.none()
        if user.is_superuser or is_auditor(user):
            return queryset
        return queryset.filter(owner=user)

    def obj_create(self, bundle, **kwargs):
        return super().obj_create(bundle, owner=bundle.request.user)

    def obj_update(self, bundle, **kwargs):
        # Prevent Tastypie's PUT-to-create fallback for inaccessible IDs.
        if not self.get_object_list(bundle.request).filter(pk=kwargs.get('pk')).exists():
            raise ImmediateHttpResponse(response=HttpNotFound())
        return super().obj_update(bundle, **kwargs)

    class Meta:
        queryset = Note.objects.all().order_by('pk')
        resource_name = 'note'
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'put', 'delete']
        authentication = SessionAuthentication()
        authorization = NoteAuthorization()
        fields = ['title', 'body']
        serializer = Serializer(formats=['json'])
        validation = CleanedDataFormValidation(form_class=NoteForm)
