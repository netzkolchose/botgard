from django.contrib import admin

from django.core.exceptions import PermissionDenied


def isReadOnly(request):
    '''checks wether user is in the readOnly group'''
    return request.user.groups.filter(name='readOnly').count() > 0


class ReadPermissionModelAdmin(admin.ModelAdmin):

    def get_readonly_fields(self, request, obj=None):
        if (isReadOnly(request)):
            return list(self.readonly_fields) + \
            [field.name for field in obj._meta.fields]
        return list(self.readonly_fields)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if isReadOnly(request):
            if request.method != 'GET':
                raise PermissionDenied
        return super(ReadPermissionModelAdmin, self).change_view(request, object_id, form_url, extra_context)

    def changelist_view(self, request, extra_context=None):
        if isReadOnly(request):
            if request.method != 'GET':
                raise PermissionDenied
        return super(ReadPermissionModelAdmin, self).changelist_view(request, extra_context)


class ReadOnlyTabularInline(admin.TabularInline):
    #  extra = 0
    #  can_delete = False #if this is enabled nobody is able to delete any records
    editable_fields = []
    readonly_fields = []
    exclude = []

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if isReadOnly(request):
            if request.method != 'GET':
                raise PermissionDenied
        return super(ReadOnlyTabularInline, self).change_view(request, object_id, form_url)

    def get_readonly_fields(self, request, obj=None):
        if isReadOnly(request):
            return list(self.readonly_fields) + \
                [field.name for field in self.model._meta.fields
                if field.name not in self.editable_fields and
                    field.name not in self.exclude]
        else:
            return list(self.readonly_fields)

    def has_add_permission(self, request, obj):
        return not isReadOnly(request)

    def has_delete_permission(self, request, obj=None):
        return not isReadOnly(request) #  not working before Django V 1.5


class ReadOnlyStackedInline(admin.StackedInline):
    #  extra = 0
    #  can_delete = False #if this is enabled nobody is able to delete any records
    editable_fields = []
    readonly_fields = []
    exclude = []

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if isReadOnly(request):
            if request.method != 'GET':
                raise PermissionDenied
        return super(ReadOnlyTabularInline, self).change_view(request, object_id, form_url)

    def get_readonly_fields(self, request, obj=None):
        if isReadOnly(request):
            return list(self.readonly_fields) + \
                [field.name for field in self.model._meta.fields
                if field.name not in self.editable_fields and
                    field.name not in self.exclude]
        else:
            return list(self.readonly_fields)

    def has_add_permission(self, request, obj):
        return not isReadOnly(request)

    def has_delete_permission(self, request, obj=None):
        return not isReadOnly(request) #  not working before Django V 1.5
