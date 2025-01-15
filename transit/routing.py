from django.urls import path,include
from . import consumers

websocket_urlpatterns=[
    # path('ws/transit/<str:room_name>/',consumers.ChatConsumer.as_asgi()),
    # path('ws/transit/<str:room_name>/<str:username>/',consumers.ChatConsumer.as_asgi()),
    # path('ws/transit/<str:room_name>/<str:username>/<str:bus_id>/',consumers.ChatConsumer.as_asgi()),
    path('ws/seats/<str:bus_id>/',consumers.SeatConsumer.as_asgi()),
]