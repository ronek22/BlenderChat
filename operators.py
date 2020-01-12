import bpy
from threading import Thread

user = None

class WM_OT_EstablishConnection(bpy.types.Operator):
    bl_idname = "wm.establish_connection"
    bl_label = "Connect"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        global user

        if mytool.connection_type == 'Client':
            from . client import Client
            user = Client(mytool.login, mytool.port)
            mytool.is_connected = True
        else:
            from . aio_server2 import run_server, aiohttp_server
            try:
                user = Thread(target=run_server, args=(aiohttp_server(),))
                user.start()
                mytool.is_connected = True
            except OSError:
                self.report({'ERROR'}, 'Address already in use, try with different port')
                return {'CANCELLED'}
        return {'FINISHED'}

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
        global user
        
        scene = context.scene
        mytool = scene.my_tool
        user.close()
        user = None
        mytool.is_connected = False
        return {'FINISHED'}


