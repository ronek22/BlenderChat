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
                       UIList
                       )
import bpy
import os
# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------

class StudentObject(PropertyGroup):
    name: StringProperty()
    rep_socket: StringProperty()


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
        default='/tmp',
        subtype='DIR_PATH'
    )

class PIPZMQProperties(PropertyGroup):
    """pip install and pyzmq install Properties"""
    install_status: StringProperty(name="Install status",
                                   description="Install status messages",
                                   default="pyzmq not found in Python distribution",
                                   )

class STUDENT_UL_items(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.3)
        split.label(text="Student: %d" % (index))
        #split.prop(item, "name", text="", emboss=False, translate=False, icon=custom_icon)
        split.label(text=item.name) # avoids renaming the item by accident

    def invoke(self, context, event):
        pass  


def enum_previews_from_directory_items(self, context):
    """EnumProperty callback"""
    enum_items = []

    if context is None:
        return enum_items

    wm = context.window_manager
    directory = wm.socket_settings.path
    reload = wm.reload_previews

    # Get the preview collection (defined in register func).
    pcoll = wm.preview_collections["main"]

    if not reload:
        return pcoll.my_previews

    pcoll.clear()

    print("Scanning directory: %s" % directory)
    print([(k,v.icon_id) for k, v in pcoll.items()])
    def_dir = os.path.dirname(bpy.data.filepath) + directory[:]
    if directory and os.path.exists(def_dir):
        # Scan the directory for png files
        image_paths = []
        for fn in os.listdir(def_dir):
            if fn.lower().endswith(".png"):
                image_paths.append(fn)

        print(image_paths)
        for i, name in enumerate(image_paths):
            # generates a thumbnail preview for a file.
            filepath = os.path.join(def_dir, name)
            if filepath not in [k for k, v in pcoll.items()]:
                thumb = pcoll.load(filepath, filepath, 'IMAGE', force_reload=True)
                enum_items.append((name, name, "", thumb.icon_id, i))
                print(f'Added thumbnail: {filepath}')


    pcoll.my_previews = enum_items
    pcoll.my_previews_dir = directory
    wm.reload_previews = False
    return pcoll.my_previews


class OBJECT_PT_CustomPanel(Panel):
    bl_label = "Chat Panel"
    bl_idname = "OBJECT_PT_custom_panel"
    bl_category = "Chat"

    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_context = "objectmode" 

    # bl_space_type = "PROPERTIES"   
    # bl_region_type = "WINDOW"
    # bl_context = "scene" 


    @classmethod
    def poll(cls,context):
        return context.object is not None

    def draw(self, context):


        layout = self.layout
        mytool = context.window_manager.socket_settings
        scene = bpy.context.scene
        wm = context.window_manager

        try:
            import zmq

            if not mytool.is_connected:
                layout.prop(mytool, "connection_type", text="") 
                layout.prop(mytool, "port")

                if mytool.connection_type == 'Client':
                    layout.prop(scene, "networks")
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

                
                else:
                    for _, network, _ in scene.network_list:
                        layout.label(text=network)
                    layout.prop(mytool, "login")
                    layout.prop(mytool, "message")

                    layout.label(text="Students list")


                    rows = 2
                    row = layout.row()
                    row.template_list("STUDENT_UL_items", "", scene, "students", scene, "student_index", rows=rows)

                    col = row.column(align=True)
                    col.operator("student.list_action", icon="ZOOM_IN", text="").action = "ADD"
                    col.operator("student.list_action", icon="ZOOM_OUT", text="").action = "REMOVE"


                    row = layout.row()
                    col = row.column(align=True)
                    row = col.row(align=True)
                    row.operator('student.send', icon="LINENUMBERS_ON")

                    layout.label(text="Students previews")


                    row = layout.row()
                    row.template_icon_view(wm, "my_previews", show_labels=True,scale=10.0, scale_popup=8.0)

                    row = layout.row()
                    row.prop(wm, "my_previews")

                    layout.operator("wm.close_server")
        except ImportError:
            # keep track of how our installation is going
            install_props = context.window_manager.install_props

            # button: enable pip and install pyzmq if not available
            layout.operator("pipzmq.pip_pyzmq")
            # show status messages (kinda cramped)
            layout.prop(install_props, "install_status")  

        
