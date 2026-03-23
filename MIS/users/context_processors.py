from .models import Message
from django.contrib.auth import get_user_model

User = get_user_model()

def chat_context(request):
    """Add chat data to all authenticated user pages"""
    if request.user.is_authenticated:
        users = User.objects.all().order_by('id_number')
        unread_user_ids = []
        
        for u in users:
            if u != request.user:
                count = Message.objects.filter(
                    sender=u,
                    receiver=request.user,
                    is_read=False
                ).count()
                if count > 0:
                    unread_user_ids.append(u.id)
        
        return {
            'users': users,
            'unread_user_ids': unread_user_ids,
        }
    return {}