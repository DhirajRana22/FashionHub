from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from .models import UserMessage

class UserMessageMiddleware(MiddlewareMixin):
    """Middleware to display stored messages for a user when they log in"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            user_messages = UserMessage.objects.filter(user=request.user, read=False)
            
            if user_messages.exists():
                for msg in user_messages:
                    messages.add_message(request, msg.level, msg.message)
                    msg.read = True
                
                # Update all messages as read in a single query
                user_messages.update(read=True)
                
        return None 