from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized


def is_auditor(user):
    return user.is_authenticated and user.groups.filter(name='Auditors').exists()


class NoteAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        return object_list

    def read_detail(self, object_list, bundle):
        return True  # The resource queryset already enforces ownership.

    def create_detail(self, object_list, bundle):
        user = bundle.request.user
        if is_auditor(user) and not user.is_superuser:
            raise Unauthorized('Auditors have read-only access.')
        return bundle.obj.owner_id == user.pk or user.is_superuser

    def update_detail(self, object_list, bundle):
        return self.create_detail(object_list, bundle)

    def delete_detail(self, object_list, bundle):
        return self.create_detail(object_list, bundle)
