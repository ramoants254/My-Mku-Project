import json
from channels.generic.websocket import WebsocketConsumer
from .models import Seat, Booking

class SeatConsumer(WebsocketConsumer):
    async def connect(self):
        self.bus_id=self.scope['url_route']['kwargs']['bus_id']
        self.room_group_name=f'seats_{self.bus_id}'

        #Join room group

        await.self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    #Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        text_data_json=json.loads(text_data)
        seat_id=text_data_json['seat_id']
        action=text_data_json['action']

        if action=='book':
            seat=seat.objects.get(id=seat_id)
            seat.is_available=False
            set.save()


        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type':'seat_update',
                'seat_id':seat_id,
                'is_available':seat.is_available
            }
        )

    #Receive message from room group
    async def seat_update(self,event):
        await self.send(text_data=json.dumps(
            {
                'seat_id':event['seat_id'],
                'is_available':event['is_available']
            }
        ))

