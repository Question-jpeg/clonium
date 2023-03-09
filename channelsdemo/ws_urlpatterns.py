from django.urls import path

from channelsdemo.consumers import ApiConsumer

ws_urlpatterns = [
    path('ws/', ApiConsumer.as_asgi(), name='api-consumer')
]
