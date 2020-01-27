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
            bpy.types.WindowManager.socket_sub = self.zmq_ctx.socket(zmq.SUB)
            bpy.types.WindowManager.socket_sub.bind(self.url)  # publisher connects to this (subscriber)
            bpy.types.WindowManager.socket_sub.setsockopt(zmq.SUBSCRIBE, ''.encode('ascii'))
            self.report({'INFO'}, "Sub bound to: {}\nWaiting for data...".format(self.url))

            # poller socket for checking server replies periodically 
            self.poller = zmq.Poller()
            # (socket, mode)
            self.poller.register(bpy.types.WindowManager.socket_sub, zmq.POLLIN)

            self.socket_settings.is_connected = True

            # have blender call our data listeting function in the background
            bpy.app.timers.register(self.timed_msg_poller)
        return {'FINISHED'}

    def run_student(self, context):
        self.socket_settings.is_connected = True
        return {'FINISHED'}

    def timed_msg_poller(self):
        socket_sub = bpy.types.WindowManager.socket_sub

        if socket_sub:
            # get sockets with messages
            # don't wait for msgs
            sockets = dict(self.poller.poll(0))

            if socket_sub in sockets:
                topic, msg = socket_sub.recv_multipart()
                print(f"On topic {topic}, data: {msg}")

                self.socket_settings.message = msg.decode('utf-8')
                # Why this is not reporting
                self.report({'INFO'}, f"Received: {self.socket_settings.message}")
                # Here gonna be all logic             
            return 0.001


class WM_OT_SendMessage(bpy.types.Operator):
    bl_idname = "wm.send_message"
    bl_label = "Send"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        user.send_message(mytool.message)
        return {'FINISHED'}

class WM_OT_CloseConnection(bpy.types.Operator):
    bl_idname = "wm.close_server"
    bl_label = "Close connection"

    def execute(self, context):
        socket_settings = context.window_manager.socket_settings
        if bpy.app.timers.is_registered(WM_OT_EstablishConnection.timed_msg_poller):
            bpy.app.timers.unregister(WM_OT_EstablishConnection.timed_msg_poller())

        try:
            bpy.types.WindowManager.socket_sub.close()
            self.report({'INFO'}, 'Lecturer socket closed')
        except AttributeError:
            self.report({'INFO'}, 'Lecturer socket was not active')

        bpy.types.WindowManager.socket_sub = None
        socket_settings.is_connected = False

        return {'FINISHED'}


class WM_OT_CloseClient(bpy.types.Operator):
    bl_idname = "wm.close_client"
    bl_label = "Close connection"

    def execute(self, context):
        socket_settings = context.window_manager.socket_settings
        socket_settings.is_connected = False

        return {'FINISHED'}


