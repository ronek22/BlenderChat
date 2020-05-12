import bpy
from threading import Thread
from datetime import datetime
import os
from pprint import pprint
import functools

CHUNK_SIZE = 250000

def get_default_context():
    window = bpy.context.window_manager.windows[0]
    return {'window': window, 'screen': window.screen}

class WM_OT_EstablishConnection(bpy.types.Operator):
    bl_idname = "wm.establish_connection"
    bl_label = "Connect"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.socket_settings = context.window_manager.socket_settings

        print(f"MODE: {self.socket_settings.connection_type}")

        globals()["zmq"] = __import__("zmq")

        if self.socket_settings.connection_type == 'Client':
            return self.run_student(context)
        else:
            return self.run_lecturer(context)

    # region Lecturer
    def run_lecturer(self, context):

        if not self.socket_settings.is_connected:
            self.report({'INFO'}, "Connecting ZeroMQ socket...")
            # Creating a ZeroMQ context
            self.zmq_ctx = zmq.Context().instance()
            self.url = f"tcp://{'*'}:{self.socket_settings.port}"
            # store our connection in Blender's WindowManager for access in self.timed_msg_poller()
            bpy.types.WindowManager.socket = self.zmq_ctx.socket(zmq.SUB)
            bpy.types.WindowManager.socket.bind(self.url)  # publisher connects to this (subscriber)
            bpy.types.WindowManager.socket.setsockopt(zmq.SUBSCRIBE, ''.encode('ascii')) # subcribe by prefix, '' get everything
            self.report({'INFO'}, "Sub bound to: {}\nWaiting for data...".format(self.url))

            # REQ SOCKET FOR ASKING STUDENTS FOR .BLEND FILE
            bpy.types.WindowManager.req = self.zmq_ctx.socket(zmq.REQ)

            # poller socket for checking server replies periodically 
            self.poller = zmq.Poller()
            self.poller.register(bpy.types.WindowManager.socket, zmq.POLLIN)
            self.socket_settings.is_connected = True
            # have blender call our data listeting function in the background
            bpy.app.timers.register(functools.partial(self.timed_msg_poller_for_lecturer, context))
        return {'FINISHED'}

    def handle_student_list(self, scene, user, uid, rep_socket):
        student = next((student for student in scene.students if student.uid == uid), None)
        if not student:
            duplicate_user = sum(s.name == user for s in scene.students)
            if duplicate_user > 0:
                user += f'_{duplicate_user}' 
            student = scene.students.add()
            student.name = user
            student.rep_socket = rep_socket.decode()
            student.id = len(scene.students)
            student.uid = uid
            scene.student_index = len(scene.students)-1

        self.socket_settings.login = user
        # if student reconnects, probably get new rep_socket 
        student.rep_socket = rep_socket.decode()

        return student


    def timed_msg_poller_for_lecturer(self, context):

        socket = bpy.types.WindowManager.socket

        if socket:
            # get sockets with messages
            # don't wait for msgs
            sockets = dict(self.poller.poll(0))
            
            if socket in sockets:
                mode, rep_socket, user, uid, msg = socket.recv_multipart()
                user = self.socket_settings.login = user.decode('ascii')
                uid = uid.decode()
                mode = mode.decode()

                # TODO: check if recv_multipart has 4 parts if yes handle students otherwise not

                student = self.handle_student_list(context.scene, user, uid, rep_socket)

                if mode == 'file':
                    path = f"{self.socket_settings.path}/{student.name}.blend" 
                    with open(path, 'wb') as file:
                        file.write(msg)
                elif mode == 'img':
                    path = f"{self.socket_settings.path}/{student.name}.png"
                    with open(path,'wb') as file:
                        file.write(msg)
                    context.window_manager.reload_previews = True
                elif mode == 'msg':
                    msg = self.socket_settings.message = msg.decode('utf-8')
                    print(f"{student.name} > {msg}")
                elif mode == 'intro':
                    msg = self.socket_settings.message = msg.decode('utf-8')
                    print(f"REPLY SOCKET FOR {student.name}: {rep_socket.decode('utf-8')}")

                # How to report from timer?         
            return 0.001
    # endregion

    # region Student
    def run_student(self, context):
        if not self.socket_settings.is_connected:
            self.report({'INFO'}, 'Connecting to Lecturer...')
            self.zmq_ctx = zmq.Context().instance()
            # TODO: CONNECT TO GIVEN URL BY LECTURER
            self.url = f"tcp://{self.socket_settings.ip}:{self.socket_settings.port}"
            
            bpy.types.WindowManager.socket = self.zmq_ctx.socket(zmq.PUB)
            bpy.types.WindowManager.socket.connect(self.url)
            from time import sleep
            sleep(.1)
            self.report({'INFO'}, "Student connected to: {}".format(self.url))


            # REPLY STUDENT SERVER
            rep_address = f"tcp://{context.scene.networks}"
            print(f"REP-ADDRESS: {rep_address}")
            bpy.types.WindowManager.rep = self.zmq_ctx.socket(zmq.REP)
            rep_port = bpy.types.WindowManager.rep.bind_to_random_port('tcp://*')
            bpy.types.WindowManager.rep_address = f"{rep_address}:{rep_port}"

            # NON-BLOCKING BEHAVIOR OF REP SERVER GUARANTEED BY POLLER
            self.poller = zmq.Poller()
            self.poller.register(bpy.types.WindowManager.rep, zmq.POLLIN)
            self.socket_settings.is_connected = True

            # INTRODUCE TO STUDENT TO LECTURER
            data = context.window_manager.socket_settings
            rep_socket = bpy.types.WindowManager.rep_address.encode()
            login =  data.login.encode('ascii')
            uid = data.uid.encode('utf-8')
            msg = bytes("Dzień Dobry!", 'utf-8')
            print(f"{rep_socket.decode()} | {login.decode('ascii')} | {uid.decode()} | {msg.decode()}")
            bpy.types.WindowManager.socket.send_multipart([b'intro', rep_socket, login, uid, msg])
            data.message = ""

            self.socket_settings.is_connected = True

            # bpy.app.timers.register(functools.partial(self.timed_msg_poller_for_student, context))
            bpy.app.timers.register(self.timed_msg_poller_for_student)

            # test of periodically send screen
            bpy.app.timers.register(self.send_screens_periodically)

        return {'FINISHED'}

    def timed_msg_poller_for_student(self):
        socket = bpy.types.WindowManager.rep
        if socket:
            sockets = dict(self.poller.poll(0))
            if socket in sockets:
                msg = socket.recv_string()

                if msg == "SEND FILE":
                    path = '/tmp/current.blend'
                    bpy.ops.wm.save_as_mainfile(filepath=path, check_existing=False)
                    
                    with open(path, 'rb') as file:
                        data = file.read()
                    socket.send(data)

                
                # How to report from timer?         
            return 0.001

    def send_screens_periodically(self):
        socket = bpy.types.WindowManager.socket

        if socket:
            # send every minute
            login =  self.socket_settings.login.encode('ascii')
            uid = self.socket_settings.uid.encode('utf-8')
            rep_socket = bpy.types.WindowManager.rep_address.encode('utf-8')

            screenshot("screen.png")
            
            with open("/tmp/screen.png", 'rb') as file:
                data = file.read()

            socket.send_multipart([b'img', rep_socket, login, uid, data])
        # self.report({'INFO'}, 'Screen sent succesfully')

        return 60
    # endregion


class WM_OT_SendMessage(bpy.types.Operator):
    bl_idname = "wm.send_message"
    bl_label = "Send Msg"

    def execute(self, context):
        data = context.window_manager.socket_settings
        rep_socket = context.window_manager.rep_address.encode('utf-8')
        login =  data.login.encode('ascii')
        uid = data.uid.encode('utf-8')
        msg = data.message.encode('utf-8')
        socket_pub = bpy.types.WindowManager.socket

        socket_pub.send_multipart([b'msg', rep_socket, login, uid, msg])
        data.message = ""
        self.report({'INFO'}, f"Message: {msg.decode('utf-8')} sent")

        return {'FINISHED'}

class WM_OT_SendFile(bpy.types.Operator):
    bl_idname = "wm.send_file"
    bl_label = "Send File"

    def execute(self, context):
        # save current blend file, only work for linux now
        socket = bpy.types.WindowManager.socket
        rep_socket = context.window_manager.rep_address.encode('utf-8')

        path = '/tmp/current.blend'
        bpy.ops.wm.save_as_mainfile(filepath=path, check_existing=False)
        self.report({'INFO'}, 'Current file save to tmp/current.blend')
        
        data = context.window_manager.socket_settings
        login =  data.login.encode('ascii')
        uid = data.uid.encode('utf-8')
        

        with open(path, 'rb') as file:
            data = file.read()
        socket.send_multipart([b'file',rep_socket, login, uid, data])
        self.report({'INFO'}, 'Blend file sent succesfully')

        return {'FINISHED'}

class WM_OT_SendScreen(bpy.types.Operator):
    bl_idname = "wm.send_screen"
    bl_label = "Send Screen"

    def execute(self, context):
        data = context.window_manager.socket_settings
        login =  data.login.encode('ascii')
        uid = data.uid.encode('utf-8')
        socket = bpy.types.WindowManager.socket
        rep_socket = context.window_manager.rep_address.encode('utf-8')

        screenshot("screen.png")
        
        with open("/tmp/screen.png", 'rb') as file:
            data = file.read()

        socket.send_multipart([b'img', rep_socket, login, uid, data])
        # self.report({'INFO'}, 'Screen sent succesfully')


        return {'FINISHED'}



class WM_OT_CloseConnection(bpy.types.Operator):
    bl_idname = "wm.close_server"
    bl_label = "Close connection"

    def clear_student_list(self, context):
        scn = context.scene
        lst = scn.students

        if len(lst) > 0:
            # remove last item first
            for i in range(len(lst)-1,-1,-1):
                scn.students.remove(i)
            self.report({'INFO'}, 'All students remove')
        else:
            self.report({'INFO'}, 'Nothing to remove')

        

    def execute(self, context):
        socket_settings = context.window_manager.socket_settings
        if bpy.app.timers.is_registered(WM_OT_EstablishConnection.timed_msg_poller_for_lecturer):
            bpy.app.timers.unregister(WM_OT_EstablishConnection.timed_msg_poller_for_lecturer())

        try:
            bpy.types.WindowManager.socket.close()
            self.report({'INFO'}, 'Lecturer sub socket closed')
        except AttributeError:
            self.report({'INFO'}, 'Lecturer sub socket was not active')

        try:
            bpy.types.WindowManager.req.close()
            self.report({'INFO'}, 'Lecturer req socket closed')
        except AttributeError:
            self.report({'INFO'}, 'Lecturer req socket was not active')


        bpy.types.WindowManager.req = None
        bpy.types.WindowManager.socket = None
        context.window_manager.reload_previews = True
        # bpy.types.WindowManager.reload_previews = True
        self.clear_student_list(context)
        socket_settings.is_connected = False
        socket_settings.login = ''
        socket_settings.message = ''

        return {'FINISHED'}

class WM_OT_CloseClient(bpy.types.Operator):
    bl_idname = "wm.close_client"
    bl_label = "Close connection"

    def execute(self, context):

        if bpy.app.timers.is_registered(WM_OT_EstablishConnection.send_screens_periodically):
            bpy.app.timers.unregister(WM_OT_EstablishConnection.send_screens_periodically())

        if bpy.app.timers.is_registered(WM_OT_EstablishConnection.timed_msg_poller_for_student):
            bpy.app.timers.unregister(WM_OT_EstablishConnection.timed_msg_poller_for_student())

        try:
            bpy.types.WindowManager.socket.close()
            self.report({'INFO'}, 'Student pub socket closed')
        except AttributeError:
            self.report({'INFO'}, 'Student pub socket was not active')

        try:
            bpy.types.WindowManager.rep.close()
            self.report({'INFO'}, 'Student rep socket closed')
        except AttributeError:
            self.report({'INFO'}, 'Student rep socket was not active')


        bpy.types.WindowManager.socket = None
        bpy.types.WindowManager.rep = None
        socket_settings = context.window_manager.socket_settings
        socket_settings.is_connected = False

        return {'FINISHED'}

# =====================================================================
# ===== OPERATORS IN LECTURER SOCKETS, OPERATION OF STUDENTS LIST =====
# =====================================================================

def remove_student(context):
    context.scene.students.remove(context.scene.student_index)
    context.scene.student_index -= 1
    context.window_manager.reload_previews = True

class STUDENT_OT_actions(bpy.types.Operator):
    bl_idname = "student.list_action"
    bl_label = "List Actions"
    bl_description = "Managing list of students"
    bl_options = {'REGISTER'}

    action: bpy.props.EnumProperty(items=(('REMOVE', "Remove", ""),))

    def invoke(self, context, event):

        wm = bpy.types.WindowManager
        scene = context.scene
        idx = scene.student_index

        try:
            student = scene.students[idx]
        except IndexError:
            print("Student not found. Error with list")
        else:
            if self.action == "REMOVE":
                remove_student(context)
                self.report({'INFO'}, f"Item {student.name} removed")
        return {"FINISHED"}

class STUDENT_OT_send(bpy.types.Operator):
    bl_idname = "student.send"
    bl_label = "Send request"
    bl_description = "Use it for load student .blend file"
    bl_options = {'REGISTER', 'UNDO'}
    request_timeout = 1000
    request_retries = 3

    @classmethod
    def poll(cls, context):
        return bool(context.scene.students)

    def remove_student(self, context):
        context.scene.students.remove(context.scene.student_index)
        context.scene.student_index -= 1
        context.window_manager.reload_previews = True

    def open_file(self, context, student, data):
        import subprocess

        settings = context.window_manager.socket_settings

        if not data:
            return {'CANCELLED'}

        path = f"{settings.path}/{student.name}.blend" 
        with open(path, 'wb') as file:
            file.write(data)

        self.report({'INFO'}, f"File for {student.name} save into: {settings.path}/{student.name}.blend")
        subprocess.Popen([bpy.app.binary_path, path])
        self.report({'INFO'}, f"Opened {student.name} project into exisiting instance of blender")
        

        return {'FINISHED'}


    def send_request_for_file(self, context, student):
        '''Lazy Pirate Pattern'''

        req = zmq.Context().instance().socket(zmq.REQ)
        req.connect(student.rep_socket)

        poll = zmq.Poller()
        poll.register(req, zmq.POLLIN)

        retries_left = self.request_retries
        while retries_left:
            self.report({'INFO'}, f"Request for file sending to {student.name} binded to {student.rep_socket} and waiting for reply..")
            req.send_string("SEND FILE")
            expect_reply = True
            while expect_reply:
                socks = dict(poll.poll(self.request_timeout))
                if socks.get(req) == zmq.POLLIN:
                    data = req.recv()
                    if self.open_file(context, student, data) == {'CANCELLED'}:
                        break
                    # Succesful reply disconnect socket
                    req.disconnect(student.rep_socket)
                    expect_reply = False
                    retries_left = 0
                else:
                    self.report({'WARNING'}, 'No response from student, retrying...')
                    req.setsockopt(zmq.LINGER, 0)
                    req.close()
                    poll.unregister(req)
                    retries_left-=1
                    if retries_left == 0:
                        self.report({'ERROR'}, 'Student seems to be offline, abandonig')
                        remove_student(context)
                        # context.scene.student_index -= 1
                        # context.scene.students.remove(idx)
                        # context.window_manager.reload_previews = True
                        break
                    self.report({'INFO'}, 'Reconnecting and resending')
                    req = zmq.Context().instance().socket(zmq.REQ)
                    req.connect(student.rep_socket)
                    poll.register(req, zmq.POLLIN)
                    req.send_string('SEND FILE')



    def execute(self, context):
        scene = context.scene
        idx = scene.student_index

        try:
            student = scene.students[idx]
        except IndexError:
            self.report({'INFO'}, "Nothing selected in the list")
            return {'CANCELLED'}

        self.send_request_for_file(context, student)
        
        return {'FINISHED'}


# save screenshot
def screenshot(P_filename, P_path = None):
  L_saveAs = P_filename
  L_saveAs = os.path.join(P_path, L_saveAs) if P_path else os.path.join("/tmp", L_saveAs)
  print("Scene saved in " + L_saveAs)

  #XXX: switching to 3D full view = maximize scene in main window
  #bpy.context.window.screen = bpy.data.screens['3D View Full']
  for window in bpy.context.window_manager.windows:
    screen = window.screen
    for area in screen.areas:
      print("Area   : " + str(area.type))
      if area.type == 'VIEW_3D':
        for space in area.spaces:
          print("Space  : " + str(space.type))
          if space.type == 'VIEW_3D':
            #space.viewport_shade = 'RENDERED'
            for region in area.regions:
              print("Region  : " + str(region.type))
              if region.type == 'WINDOW':
                L_altBpyCtx = {                        # defining alternative context (allowing modifications without altering real one)
                  'area'      : area                   # our 3D View (first found)
                , 'blend_data': bpy.context.blend_data # just to suppress PyContext warning, doesn't seem to have any effect
                #, 'edit_text' : bpy.context.edit_text  # just to suppress PyContext warning, doesn't seem to have any effect
                , 'region'    : None                   # just to suppress PyContext warning, doesn't seem to have any effect
                #, 'scene'     : bpy.context.scene
                , 'scene'     : bpy.context.scene
                , 'space'     : space
                , 'screen'    : window.screen
                #, 'window'    : bpy.context.window     # current window, could also copy context
                , 'window'    : window                 # current window, could also copy context
                }
                bpy.ops.screen.screenshot(L_altBpyCtx, filepath = L_saveAs, full = False, check_existing=False)
                break #XXX: limit to the window of the 3D View
            break #XXX: limit to the corresponding space (3D View)
        break #XXX: limit to the first 3D View (area)
    return "SAVED_SCREENSHOT"

# install pyzmq
class PIPZMQ_OT_pip_pyzmq(bpy.types.Operator):
    """Enables and updates pip, and installs pyzmq"""  # Use this as a tooltip for menu items and buttons.

    bl_idname = "pipzmq.pip_pyzmq"  # Unique identifier for buttons and menu items to reference.
    bl_label = "Enable pip & install pyzmq"  # Display name in the interface.
    bl_options = {'REGISTER'}

    def execute(self, context):  # execute() is called when running the operator.
        install_props = context.window_manager.install_props
        install_props.install_status = "Preparing to enable pip..."

        import subprocess  # use Python executable (for pip usage)
        import os
        
        # from platform import system
        # if system() != 'Windows':
        #     import ensurepip
        #     ensurepip.bootstrap()

        try:
            import pip
        except ModuleNotFoundError as e:
            install_props.install_status += f"\nPip import failed. {e}"
            import ensurepip
            ensurepip.bootstrap()
            os.environ.pop("PIP_REQ_TRACKER", None) # https://developer.blender.org/T71856

        # WORKS ONLY FROM 2.81
        # Pip is now enabled by default from 2.81, so no need for this solution anymore: https://developer.blender.org/T71856
        # ensurepip.bootstrap()
        pybin = bpy.app.binary_path_python
        if subprocess.call([pybin, '-m', 'pip', 'install', 'pyzmq']) != 0:
            install_props.install_status += "\nCouldn't install pyzmq."
            self.report({'ERROR'}, "Couldn't install pyzmq.")
            return {'CANCELLED'}

        self.report({'INFO'}, "pyzmq installed! READY!")

        #region BLENDER < 2.81
        # FOR BLENDER VERSIONS < 2.81
        # OS independent (Windows: bin\python.exe; Linux: bin/python3.7m)
        """
        py_path = Path(sys.prefix) / "bin"
        py_execs = list(py_path.glob("python3*"))
        py_execs = [x for x in py_execs if 'config' not in str(x.resolve())]

        py_exec = str(py_execs.pop(0))  # first file that starts with "python" in "bin" dir
        # TODO check permission rights
        if subprocess.call([py_exec, "-m", "ensurepip"]) != 0:
            install_props.install_status += "\nCouldn't activate pip."
            self.report({'ERROR'}, "Couldn't activate pip.")
            return {'CANCELLED'}
        install_props.install_status += "\nPip activated! Updating pip..."
        self.report({'INFO'}, "Pip activated! Updating pip...")
        if subprocess.call([py_exec, "-m", "pip", "install", "--upgrade", "pip"]) != 0:
            install_props.install_status += "\nCouldn't update pip."
            self.report({'ERROR'}, "Couldn't update pip.")
            return {'CANCELLED'}
        install_props.install_status += "\nPip updated! Installing pyzmq..."
        self.report({'INFO'}, "Pip updated! Installing pyzmq...")
        
        if subprocess.call([py_exec, "-m", "pip", "install", "wheel"]) != 0:
            install_props.install_status += "\nCouldn't install wheel."
            self.report({'ERROR'}, "Couldn't install wheel.")
            return {'CANCELLED'}

        install_props.install_status += "\npyzmq installed! READY!"
        self.report({'INFO'}, "pyzmq installed! READY!")

        if subprocess.call([py_exec, "-m", "pip", "install", "pyzmq"]) != 0:
            install_props.install_status += "\nCouldn't install pyzmq."
            self.report({'ERROR'}, "Couldn't install pyzmq.")
            return {'CANCELLED'}

        install_props.install_status += "\npyzmq installed! READY!"
        self.report({'INFO'}, "pyzmq installed! READY!")
        """
        #endregion

        return {'FINISHED'}  # Lets Blender know the operator finished successfully