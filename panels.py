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

# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------

class ChatProperties(PropertyGroup):

    port : IntProperty(
        name = "Port number",
        description="Port number of client or server",
        default = 12345,
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
        scene = context.scene
        mytool = scene.my_tool

        if not mytool.is_connected:
            layout.prop(mytool, "connection_type", text="") 
            layout.prop(mytool, "port")

            if mytool.connection_type == 'Client':
                layout.prop(mytool, "login")

            layout.operator("wm.establish_connection")
        else:
            if mytool.connection_type == 'Client':
                layout.prop(mytool, "message")
                layout.operator("wm.send_message")
            else:
                layout.prop(mytool, "is_connected")
                layout.operator("wm.run_loop")
                layout.operator("wm.close_server")

        
