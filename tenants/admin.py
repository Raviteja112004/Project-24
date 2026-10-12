from django.contrib import admin
from .models import Tenant, TenantMembership
# Register your models here.
admin.site.register( [Tenant,TenantMembership])