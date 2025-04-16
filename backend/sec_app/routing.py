# sec_app/routing.py
from django.urls import re_path
from sec_app.consumers import RevenueConsumer  

websocket_urlpatterns = [
    re_path(r"ws/revenue/$", RevenueConsumer.as_asgi()),
]
