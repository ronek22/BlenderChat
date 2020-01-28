import bpy
from threading import Thread
import zmq 


user = None

class WM_OT_EstablishConnection(bpy.types.Operator):
    bl_idname = "wm.establish_connection"
    bl_label = "Connect"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.socket_settings = context.window_manager.socket_settings

        print(f"MODE: {self.socket_settings.connection_type}")

        if self.socket_settings.connection_type == 'Client':
            return self.run_student(context)
        else:
            return self.run_lecturer(context)

    def run_lecturer(self, context):
        if not self.socket_settings.is_connected:
            self.report({'INFO'}, "Connecting ZeroMQ socket...")
            # Creating a ZeroMQ context
            self.zmq_ctx = zmq.Context().instance()
            self.url = f"tcp://{'127.0.0.1'}:{self.socket_settings.port}"
            # store our connection in Blender's WindowManager for access in self.timed_msg_poller()
            bpy.types.WindowManager.socket = self.zmq_ctx.socket(zmq.SUB)
            bpy.types.WindowManager.socket.bind(self.url)  # publisher connects to this (subscriber)
            bpy.types.WindowManager.socket.setsockopt(zmq.SUBSCRIBE, ''.encode('ascii'))
            self.report({'INFO'}, "Sub bound to: {}\nWaiting for data...".format(self.url))

            # poller socket for checking server replies periodically 
            self.poller = zmq.Poller()
            # (socket, mode)
            self.poller.register(bpy.types.WindowManager.socket, zmq.POLLIN)

            self.socket_settings.is_connected = True

            # have blender call our data listeting function in the background
            bpy.app.timers.register(self.timed_msg_poller)
        return {'FINISHED'}

    def run_student(self, context):
        if not self.socket_settings.is_connected:
            self.report({'INFO'}, 'Connecting to Lecturer...')
            self.zmq_ctx = zmq.Context().instance()
            self.url = f"tcp://{'127.0.0.1'}:{self.socket_settings.port}"
            
            bpy.types.WindowManager.socket = self.zmq_ctx.socket(zmq.PUB)
            bpy.types.WindowManager.socket.connect(self.url)
            self.report({'INFO'}, "Student connected to: {}".format(self.url))
            self.socket_settings.is_connected = True

        return {'FINISHED'}

    def timed_msg_poller(self):
        socket = bpy.types.WindowManager.socket

        if socket:
            # get sockets with messages
            # don't wait for msgs
            sockets = dict(self.poller.poll(0))

            if socket in sockets:
                user, msg = socket.recv_multipart()

                user = self.socket_settings.login = user.decode('ascii')
                msg = self.socket_settings.message = msg.decode('utf-8')
                print(f"{user} > {msg}")

                # How to report from timer?         
            return 0.001


class WM_OT_SendMessage(bpy.types.Operator):
    bl_idname = "wm.send_message"
    bl_label = "Send"

    def execute(self, context):
        data = context.window_manager.socket_settings
        login =  data.login.encode('ascii')
        msg = data.message.encode('utf-8')
        socket_pub = bpy.types.WindowManager.socket

        socket_pub.send_multipart([login, msg])
        data.message = ""
        self.report({'INFO'}, f"Message: {msg.decode('utf-8')} sent")

        return {'FINISHED'}

class WM_OT_CloseConnection(bpy.types.Operator):
    bl_idname = "wm.close_server"
    bl_label = "Close connection"

    def execute(self, context):
        socket_settings = context.window_manager.socket_settings
        if bpy.app.timers.is_registered(WM_OT_EstablishConnection.timed_msg_poller):
            bpy.app.timers.unregister(WM_OT_EstablishConnection.timed_msg_poller())

        try:
            bpy.types.WindowManager.socket.close()
            self.report({'INFO'}, 'Lecturer socket closed')
        except AttributeError:
            self.report({'INFO'}, 'Lecturer socket was not active')

        bpy.types.WindowManager.socket = None
        socket_settings.is_connected = False

        return {'FINISHED'}


class WM_OT_CloseClient(bpy.types.Operator):
    bl_idname = "wm.close_client"
    bl_label = "Close connection"

    def execute(self, context):

        try:
            bpy.types.WindowManager.socket.close()
            self.report({'INFO'}, 'Student socket closed')
        except AttributeError:
            self.report({'INFO'}, 'Student socket was not active')


        socket_settings = context.window_manager.socket_settings
        socket_settings.is_connected = False

        return {'FINISHED'}


