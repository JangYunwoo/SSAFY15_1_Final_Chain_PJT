from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Mail, Notification


@login_required
def inbox(request):
    notifications = Notification.objects.filter(user=request.user)
    mails = Mail.objects.filter(receiver=request.user)
    return render(request, "notifications/inbox.html", {"notifications": notifications, "mails": mails})
