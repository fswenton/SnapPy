from .hyperboloid_utilities import *
import math
import time

try:
    from sage.all import RealField
    RF = RealField()
except:
    from snappy.number import Number as RF

__all__ = ['HyperboloidNavigation']

_key_movement_bindings = {
    'a': (lambda rot_amount, trans_amount: unit_3_vector_and_distance_to_O13_hyperbolic_translation(
            [ -1.0,  0.0,  0.0 ], trans_amount)),
    'd': (lambda rot_amount, trans_amount: unit_3_vector_and_distance_to_O13_hyperbolic_translation(
            [ +1.0,  0.0,  0.0 ], trans_amount)),
    'c': (lambda rot_amount, trans_amount: unit_3_vector_and_distance_to_O13_hyperbolic_translation(
            [  0.0, -1.0,  0.0 ], trans_amount)),
    'e': (lambda rot_amount, trans_amount: unit_3_vector_and_distance_to_O13_hyperbolic_translation(
            [  0.0, +1.0,  0.0 ], trans_amount)),
    'w': (lambda rot_amount, trans_amount: unit_3_vector_and_distance_to_O13_hyperbolic_translation(
            [  0.0,  0.0, -1.0 ], trans_amount)),
    's': (lambda rot_amount, trans_amount: unit_3_vector_and_distance_to_O13_hyperbolic_translation(
            [  0.0,  0.0, +1.0 ], trans_amount)),
    'Left': (lambda rot_amount, trans_amount: O13_y_rotation(-rot_amount)),
    'Right': (lambda rot_amount, trans_amount: O13_y_rotation(rot_amount)),
    'Up': (lambda rot_amount, trans_amount: O13_x_rotation(-rot_amount)),
    'Down': (lambda rot_amount, trans_amount: O13_x_rotation(rot_amount)),
    'x': (lambda rot_amount, trans_amount: O13_z_rotation(-rot_amount)),
    'z': (lambda rot_amount, trans_amount: O13_z_rotation(rot_amount))
}

class HyperboloidNavigation:
    """
    A mixin class for a Tk widget that binds some key and mouse events
    to navigate through the hyperboloid model of hyperbolic 3-space.

    It manipulates self.view_state using self.raytracing_data which
    is expected to be, e.g., an instance of IdealTrigRaytracingData.
    """

    def __init__(self):
        self.refresh_delay = 10

        self.mouse_pos_when_pressed = None
        self.view_state_when_pressed = None
        self.last_mouse_pos = None

        self.current_keys_pressed = set()
        self.time_key_release_received = dict()
        self.last_time = dict()

        self.view_state = self.raytracing_data.initial_view_state()

        self.navigation_dict = {
            'translationVelocity' : ['float', 0.4],
            'rotationVelocity' : ['float', 0.4]
            }

        self.bind('<Enter>', self.tkEnter)
        self.bind('<KeyPress>', self.tkKeyPress)
        self.bind('<KeyRelease>', self.tkKeyRelease)
        self.bind('<Button-1>', self.tkButton1)
        self.bind('<ButtonRelease-1>', self.tkButtonRelease1)
        self.bind('<B1-Motion>', self.tkButtonMotion1)
        self.bind('<Control-Button-1>', self.tkButton1)
        self.bind('<Control-ButtonRelease-1>', self.tkButtonRelease1)
        self.bind('<Control-B1-Motion>', self.tkCtrlButtonMotion1)
        self.bind('<Option-Button-1>', self.tkAltButton1)
        self.bind('<Option-B1-Motion>', self.tkAltButtonMotion1)
        
    def reset_view_state(self):
        self.view_state = self.raytracing_data.initial_view_state()

    def fix_view_state(self):
        self.view_state = self.raytracing_data.update_view_state(
            self.view_state)

    def tkEnter(self, event):
        self.focus_set()

    def do_movement(self):
        current_time = time.time()

        for k, t in self.time_key_release_received.items():
            if current_time - t > 0.005:
                if k in self.current_keys_pressed:
                    self.current_keys_pressed.remove(k)

        m = matrix([[1.0,0.0,0.0,0.0],
                    [0.0,1.0,0.0,0.0],
                    [0.0,0.0,1.0,0.0],
                    [0.0,0.0,0.0,1.0]])
        
        a = False

        for k in self.current_keys_pressed:
            if k in _key_movement_bindings:
                
                self.last_time[k], diff_time = current_time, current_time - self.last_time[k]

                m = m * _key_movement_bindings[k](
                    diff_time * self.navigation_dict['rotationVelocity'][1],
                    diff_time * self.navigation_dict['translationVelocity'][1])
                a = True

        if not a:
            return

        self.view_state = self.raytracing_data.update_view_state(
            self.view_state, m)

        self.redraw_if_initialized()

        self.after(self.refresh_delay, self.do_movement)

    def tkKeyRelease(self, event):
        self.time_key_release_received[event.keysym] = time.time()

    def tkKeyPress(self, event):
        if event.keysym in _key_movement_bindings:
            if event.keysym in self.time_key_release_received:
                del self.time_key_release_received[event.keysym]

            if not event.keysym in self.current_keys_pressed:
                self.last_time[event.keysym] = time.time()
                self.current_keys_pressed.add(event.keysym)
                self.after(1, self.do_movement)

        if event.keysym == 'u':
            print(self.view_state)

        if event.keysym == 'v':
            self.view = (self.view + 1) % 3
            self.redraw_if_initialized()
            
    def tkButton1(self, event):
        self.mouse_pos_when_pressed = (event.x, event.y)
        self.view_state_when_pressed = self.view_state

    def tkAltButton1(self, event):
        self.make_current()

        self.last_mouse_pos = (event.x, event.y)
        self.view_state_when_pressed = self.view_state

        depth, width, height = self.read_depth_value(event.x, event.y)

        frag_coord = [event.x, height - event.y]
        fov = self.ui_uniform_dict['fov'][1]

        frag_coord[0] -= 0.5 * width 
        frag_coord[1] -= 0.5 * height
        frag_coord[0] /= width
        frag_coord[1] /= width
        
        dir = vector([RF(frag_coord[0]),
                      RF(frag_coord[1]),
                      RF(-0.5 / math.tan(fov / 360.0 * math.pi))]).normalized()
        
        self.orbit_translation = unit_3_vector_and_distance_to_O13_hyperbolic_translation(
            dir, math.atanh(depth))
    
        self.orbit_inv_translation = unit_3_vector_and_distance_to_O13_hyperbolic_translation(
            dir, math.atanh(-depth))
        
        self.orbit_rotation = matrix([[1.0,0.0,0.0,0.0],
                                      [0.0,1.0,0.0,0.0],
                                      [0.0,0.0,1.0,0.0],
                                      [0.0,0.0,0.0,1.0]])
        
    def tkAltButtonMotion1(self, event):
        if self.last_mouse_pos is None:
            return

        delta_x = event.x - self.last_mouse_pos[0]
        delta_y = event.y - self.last_mouse_pos[1]
        
        m = O13_y_rotation(delta_x * 0.01) * O13_x_rotation(delta_y * 0.01)
        self.orbit_rotation = self.orbit_rotation * m

        self.view_state = self.raytracing_data.update_view_state(
            self.view_state_when_pressed,
            self.orbit_translation * self.orbit_rotation * self.orbit_inv_translation)

        self.last_mouse_pos = (event.x, event.y)

        self.redraw_if_initialized()

    def tkButtonMotion1(self, event):
        if self.mouse_pos_when_pressed is None:
            return

        delta_x = event.x - self.mouse_pos_when_pressed[0]
        delta_y = event.y - self.mouse_pos_when_pressed[1]

        amt = math.sqrt(delta_x ** 2 + delta_y ** 2)

        if amt == 0:
            self.view_state = self.view_state_when_pressed
        else:
            m = unit_3_vector_and_distance_to_O13_hyperbolic_translation(
                [-delta_x / amt, delta_y / amt, 0.0], amt * 0.01)

            self.view_state = self.raytracing_data.update_view_state(
                self.view_state_when_pressed, m)

        self.redraw_if_initialized()

    def tkButtonRelease1(self, event):
        self.mouse_pos_when_pressed = None

    def tkCtrlButtonMotion1(self, event):
        if self.mouse_pos_when_pressed is None:
            return

        delta_x = event.x - self.mouse_pos_when_pressed[0]
        delta_y = event.y - self.mouse_pos_when_pressed[1]

        m = O13_y_rotation(-delta_x * 0.01) * O13_x_rotation(-delta_y * 0.01)

        self.view_state = self.raytracing_data.update_view_state(
            self.view_state, m)

        self.mouse_pos_when_pressed = (event.x, event.y)

        self.redraw_if_initialized()
