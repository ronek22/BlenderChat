from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )
import bpy
# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------

class ChatProperties(PropertyGroup):

    port : IntProperty(
        name = "Port number",
        description="Port number of client or server",
        default = 5550,
        min = 1024,
        max = 65535
        )

    login : StringProperty(
        name="User Name",
        description="Provide your username",
        default="",
        maxlen=50
        )

    connection_type : EnumProperty(
        name="Type of user:",
        description="Apply Data to attribute.",
        items=[ ('Server', "Lecturer", ""),
                ('Client', "Student", ""),
               ]
        )

    message: StringProperty(
        name="Message",
        default="",
        maxlen=100
    )

    is_connected : BoolProperty(
        name="Is Connected",
        default=False,
    )

    path : StringProperty(
        name="Server path:",
        description="Select where images and .blend files from student will be saved",
        default='/tmp/blend_support',
        subtype='DIR_PATH'
    )


class PIPZMQProperties(PropertyGroup):
    """pip install and pyzmq install Properties"""
    install_status: StringProperty(name="Install status",
                                   description="Install status messages",
                                   default="pyzmq not found in Python distribution",
                                   )




class OBJECT_PT_CustomPanel(Panel):
    bl_label = "Chat Panel"
    bl_idname = "OBJECT_PT_custom_panel"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_category = "Chat"
    bl_context = "objectmode" 


    @classmethod
    def poll(cls,context):
        return context.object is not None

    def draw(self, context):

        layout = self.layout
        mytool = context.window_manager.socket_settings
        
        try:
            import zmq


            if not mytool.is_connected:
                layout.prop(mytool, "connection_type", text="") 
                layout.prop(mytool, "port")

                if mytool.connection_type == 'Client':
                    layout.prop(mytool, "login")
                else:
                    layout.prop(mytool, 'path')

                layout.operator("wm.establish_connection")
            else:
                if mytool.connection_type == 'Client':
                    layout.prop(mytool, "message")
                    row = layout.row()
                    row.operator("wm.send_message")
                    row.operator("wm.send_file")
                    row.operator("wm.send_screen")
                    layout.operator("wm.close_client")

                

                    tex = bpy.data.textures[0]
                    col = layout.box().column()
                    col.template_preview(tex)
                else:

                    # layout.prop(mytool, "is_connected")
                    layout.prop(mytool, "login")
                    layout.prop(mytool, "message")
                    layout.operator("wm.close_server")
        except ImportError:
            # keep track of how our installation is going
            install_props = context.window_manager.install_props

            # button: enable pip and install pyzmq if not available
            layout.operator("pipzmq.pip_pyzmq")
            # show status messages (kinda cramped)
            layout.prop(install_props, "install_status")  

        
