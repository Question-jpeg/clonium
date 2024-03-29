import json
from asgiref.sync import async_to_sync
from uuid import uuid4
from channels.generic.websocket import WebsocketConsumer

class ApiConsumer(WebsocketConsumer):

    def remove_room_code(self):
        if self.room_code:
                async_to_sync(self.channel_layer.group_discard)(self.room_code, self.channel_name)
        self.room_code = None
        self.field_data = None

    def notify_self(self, event):
        typee = event['type']
        data = event.get('data', None)
        self.send(text_data=json.dumps({
            'type': typee,
            'data': data
        }))


    def connect(self):
        self.accept()

        self.room_code = None
        self.username = None
        self.uid = str(uuid4())
        self.field_data = None

        self.send(text_data=json.dumps({
            'type': 'connection_established',
            'data': {'uid': self.uid}
        }))        


    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        typee = text_data_json['type']
        try:
            data = text_data_json['data']
        except:
            pass

        if typee == 'local_message':
            print('message received')

        if typee == 'create_room':
            self.remove_room_code()

            self.room_code = str(uuid4())
            self.username = data['username']

            async_to_sync(self.channel_layer.group_add)(self.room_code, self.channel_name)
            self.send(text_data=json.dumps({'type': 'room_created', 'data': {'code': self.room_code}}))

        if typee == 'connect_to_room':
            self.remove_room_code()

            self.room_code = data['code']
            self.username = data['username']
            
            async_to_sync(self.channel_layer.group_add)(self.room_code, self.channel_name)
            async_to_sync(self.channel_layer.group_send)(self.room_code, { "type": "get_room_info" })

        if self.room_code:
            if typee == 'send_message':
                async_to_sync(self.channel_layer.group_send)(self.room_code, { "type": "message", 'data': {'username': self.username, 'text': data['text']} })

            if typee == 'update_field':
                self.field_data = data
                async_to_sync(self.channel_layer.group_send)(self.room_code, { "type": "field_info", 'data': data })

            if typee == 'get_room_info':
                async_to_sync(self.channel_layer.group_send)(self.room_code, { "type": "get_room_info" })

            if typee == 'player_ready':
                async_to_sync(self.channel_layer.group_send)(self.room_code, { "type": "player_ready", 'data': {'value': data['value'], 'uid': self.uid} })

            if typee == 'leave_room':
                async_to_sync(self.channel_layer.group_send)(self.room_code, { "type": "player_left", 'data': {'uid': self.uid} })

                self.remove_room_code()
                    
            if typee == 'leave_field':
                async_to_sync(self.channel_layer.group_send)(self.room_code, { "type": "player_left_the_field", 'data': {'uid': self.uid} })


            if typee == 'start_game':
                order = data['order']
                names_mapping = data['names_mapping']                
                async_to_sync(self.channel_layer.group_send)(self.room_code, { "type": "game_started", 'data': {'order': order, 'names_mapping': names_mapping, 'field_data': self.field_data} })

            if typee == 'move':
                coordinates = data['coordinates']
                async_to_sync(self.channel_layer.group_send)(self.room_code, { "type": "player_moved", 'data': {'coordinates': coordinates, 'uid': self.uid} })

            if typee == 'ready_for_move':
                async_to_sync(self.channel_layer.group_send)(self.room_code, { "type": "player_ready_for_move", 'data': {'uid': self.uid} })
        else:
            if typee != "leave_room":
                self.send(text_data=json.dumps({'type': 'disconnected'}))
        

    def get_room_info(self, event):
        if self.room_code:
            async_to_sync(self.channel_layer.group_send)(self.room_code, {'type': 'player_info', 'data': {'name': self.username, 'uid': self.uid, 'is_host': bool(self.field_data)}})
            if self.field_data:
                async_to_sync(self.channel_layer.group_send)(self.room_code, {'type': 'get_ready'})
                async_to_sync(self.channel_layer.group_send)(self.room_code, { "type": "field_info", 'data': self.field_data })

    def message(self, event):
        self.notify_self(event)

    def get_ready(self, event):
        self.notify_self(event)

    def player_ready(self, event):
        self.notify_self(event)

    def player_ready_for_move(self, event):
        self.notify_self(event)

    def player_info(self, event):
        self.notify_self(event)

    def player_left(self, event):
        self.notify_self(event)

    def player_left_the_field(self, event):
        self.notify_self(event)


    def field_info(self, event):
        self.notify_self(event)

    def game_started(self, event):
        self.notify_self(event)

    def player_moved(self, event):
        self.notify_self(event)

    def disconnect(self, code):        
        if self.room_code:        
            async_to_sync(self.channel_layer.group_send)(self.room_code, { "type": "player_left", 'data': {'uid': self.uid} })
            async_to_sync(self.channel_layer.group_send)(self.room_code, { "type": "player_left_the_field", 'data': {'uid': self.uid} })
            self.remove_room_code()
