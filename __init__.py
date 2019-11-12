# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "ChatAddon",
    "author" : "Jakub Ronkiewicz",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "3D View > Tools",
    "warning" : "", # used for warning icon and text in addons panel
    "category" : "Development"
}

import bpy
from bpy.props import PointerProperty
from . operators import WM_OT_EstablishConnection, WM_OT_SendMessage, WM_OT_CloseConnection
from . panels import ChatProperties, OBJECT_PT_CustomPanel

classes = (
        WM_OT_EstablishConnection,
        WM_OT_SendMessage,
        WM_OT_CloseConnection,
        ChatProperties,
        OBJECT_PT_CustomPanel
    )

# register, unregister = bpy.utils.register_classes_factory(classes)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_tool = PointerProperty(type=ChatProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool


if __name__ == "__main__":
    register()