from django.contrib import admin

from .models import Mail, Notification

admin.site.register(Notification)
admin.site.register(Mail)
