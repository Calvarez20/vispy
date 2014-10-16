# -*- coding: utf-8 -*-
# Copyright (c) 2014, Vispy Development Team.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

"""
Vispy backend for the IPython notebook (WebGL approach).
"""

from __future__ import division

from ..base import (BaseApplicationBackend, BaseCanvasBackend,
                    BaseTimerBackend)
from .. import Application, Canvas
from ...util import logger

# Import for displaying Javascript on notebook
import os.path as op

# -------------------------------------------------------------------- init ---

capability = dict(  # things that can be set by the backend
    title=True,  # But it only applies to the dummy window :P
    size=True,  # We cannot possibly say we dont, because Canvas always sets it
    position=True,  # Dito
    show=True,  # Note: we don't alow this, but all scripts call show ...
    vsync=False,
    resizable=True,  # Yes, you can set to not be resizable (it always is)
    decorate=False,
    fullscreen=False,
    context=True,
    multi_window=True,
    scroll=True,
    parent=False,
)


def _set_config(c):
    _app.backend_module._set_config(c)


# Init dummy objects needed to import this module withour errors.
# These are all overwritten with imports from IPython (on success)
DOMWidget = object
Unicode = Int = Float = Bool = lambda *args, **kwargs: None

# Try importing IPython
try:
    import IPython
    if IPython.version_info < (2,):
        raise RuntimeError('ipynb_webgl backend need IPython version >= 2.0')
    from IPython.html import widgets
    from IPython.html.widgets import DOMWidget
    from IPython.utils.traitlets import Unicode, Int, Float, Bool
    from IPython.display import display, Javascript, display_javascript, HTML
    from IPython.html.nbextensions import install_nbextension
    available, testable, why_not, which = True, False, None, None
except Exception as exp:
    raise ImportError("The WebGL backend requires IPython >= 2.0")
    available, testable, why_not, which = False, False, str(exp), None

# ------------------------------------------------------------- application ---
def _prepare_js():
    pkgdir = op.dirname(__file__)
    jsdir = op.join(pkgdir, '../../html/static/js/')
    install_nbextension([op.join(jsdir, 'vispy.min.js'),])

    backend_path = op.join(jsdir, 'webgl-backend.js')
    with open(backend_path, 'r') as f:
        script = f.read()
    display(Javascript(script))


class ApplicationBackend(BaseApplicationBackend):

    def __init__(self):
        BaseApplicationBackend.__init__(self)
        _prepare_js()

    def _vispy_get_backend_name(self):
        return 'ipynb_webgl'

    def _vispy_process_events(self):
        pass

    def _vispy_run(self):
        pass

    def _vispy_quit(self):
        pass

    def _vispy_get_native_app(self):
        return self


# ------------------------------------------------------------------ canvas ---

class CanvasBackend(BaseCanvasBackend):

    # args are for BaseCanvasBackend, kwargs are for us.
    def __init__(self, *args, **kwargs):
        BaseCanvasBackend.__init__(self, *args)
        self._initialized = False
        # Test kwargs
        # if kwargs['size']:
        #     raise RuntimeError('ipynb_webgl Canvas is not resizable')
        # if kwargs['position']:
        #     raise RuntimeError('ipynb_webgl Canvas is not positionable')
        # if not kwargs['decorate']:
        #     raise RuntimeError('ipynb_webgl Canvas is not decoratable (or not)')
        # if kwargs['vsync']:
        #     raise RuntimeError('ipynb_webgl Canvas does not support vsync')
        # if kwargs['fullscreen']:
        #     raise RuntimeError('ipynb_webgl Canvas does not support fullscreen')

        # Create real canvas. It is a backend to this backend
        # kwargs['autoswap'] = False

        # Connect to events of canvas to keep up to date with size and draws
        # canvas.events.draw.connect(self._on_draw)
        # canvas.events.resize.connect(self._on_resize)

        # Show the widget, we will hide it after the first time it's drawn
        # self._need_draw = False

        # Create IPython Widget
        self._widget = VispyWidget(self._gen_event)

    @property
    def _vispy_context(self):
        """Context to return for sharing"""
        pass
    
    @_vispy_context.setter
    def _vispy_context(self, context):
        pass
    
    def _vispy_warmup(self):
        pass

    def _vispy_set_current(self):
        pass

    def _vispy_swap_buffers(self):
        pass

    def _vispy_set_title(self, title):
        pass

    def _vispy_set_size(self, w, h):
        pass

    def _vispy_set_position(self, x, y):
        logger.warning('IPython notebook canvas cannot be repositioned.')

    def _vispy_set_visible(self, visible):
        if not visible:
            logger.warning('IPython notebook canvas cannot be hidden.')
        else:
            display(self._widget)

    def _vispy_update(self):
        # self._need_draw = True
        pass

    def _vispy_close(self):
        # self._need_draw = False
        self._widget.quit()

    def _vispy_get_position(self):
        return 0, 0

    def _vispy_get_size(self):
        pass

    def _on_resize(self, event=None):
        # Event handler that is called by the underlying canvas
        if self._vispy_canvas is None:
            return
        # self._widget.size = size
        # self._vispy_canvas.events.resize(size=size)

    def _on_draw(self, event=None):
        # Event handler that is called by the underlying canvas
        if self._vispy_canvas is None:
            return
        # Handle initialization
        if not self._initialized:
            self._initialized = True
            #self._vispy_canvas.events.add(timer=Event)
            self._vispy_canvas.events.initialize()
            self._on_resize()

        # We are drawn, so no need for a redraw
        # self._need_draw = False

        # Normal behavior
        self._vispy_set_current()
        self._vispy_canvas.events.draw(region=None)

    # Generate vispy events according to upcoming JS events
    def _gen_event(self, ev):
        if self._vispy_canvas is None:
            return

        ev = ev.get("event")
        # Parse and generate event
        if ev.get("name") == "MouseEvent":
            mouse = ev.get("properties")
            # Generate
            if mouse.get("type") == "mouse_move":
                self._vispy_mouse_move(native=mouse,
                                       pos=mouse.get("pos"),
                                       modifiers=mouse.get("modifiers"),
                                       )
            elif mouse.get("type") == "mouse_press":
                self._vispy_mouse_press(native=mouse,
                                        pos=mouse.get("pos"),
                                        button=mouse.get("button"),
                                        modifiers=mouse.get("modifiers"),
                                        )
            elif mouse.get("type") == "mouse_release":
                self._vispy_mouse_release(native=mouse,
                                          pos=mouse.get("pos"),
                                          button=mouse.get("button"),
                                          modifiers=mouse.get("modifiers"),
                                          )
            elif mouse.get("type") == "mouse_wheel":
                self._vispy_canvas.events.mouse_wheel(native=mouse,
                                                      delta=mouse.get("delta"),
                                                      pos=mouse.get("pos"),
                                                      modifiers=mouse.get
                                                      ("modifiers"),
                                                      )
        elif ev.get("name") == "KeyEvent":
            key = ev.get("properties")
            if key.get("type") == "key_press":
                self._vispy_canvas.events.key_press(native=key,
                                                    key=key.get("key"),
                                                    text=key.get("text"),
                                                    modifiers=key.get
                                                    ("modifiers"),
                                                    )
            elif key.get("type") == "key_release":
                self._vispy_canvas.events.key_release(native=key,
                                                      key=key.get("key"),
                                                      text=key.get("text"),
                                                      modifiers=key.get
                                                      ("modifiers"),
                                                      )
        # elif ev.get("name") == "PollEvent":  # Ticking from front-end (JS)
        #     # Allthough the event originates from JS, this is basically
        #     # a poll event from IPyhon's event loop, which we use to
        #     # update the backend app and draw stuff if necessary. If we
        #     # succeed to make IPython process GUI app events directly,
        #     # this "JS timer" should not be necessary.
        #     self._vispy_canvas.app.process_events()
        #     if self._need_draw:
        #         self._on_draw()
        #     # Generate a timer event on every poll from JS
        #     # AK: no, just use app.Timer as usual!
        #     #self._vispy_canvas.events.timer(type="timer")



# ------------------------------------------------------------------- timer ---

class TimerBackend(BaseTimerBackend):

    # def __init__(self, vispy_timer):
    #     pass

    def _vispy_start(self, interval):
        pass

    def _vispy_stop(self):
        pass

    def _vispy_timeout(self):
        pass


# ---------------------------------------------------------- IPython Widget ---

class VispyWidget(DOMWidget):
    _view_name = Unicode("VispyView", sync=True)

    # Define the custom state properties to sync with the front-end
    # format = Unicode('png', sync=True)
    width = Int(sync=True)
    height = Int(sync=True)
    # interval = Float(sync=True)
    # is_closing = Bool(sync=True)
    # value = Unicode(sync=True)

    def __init__(self, gen_event, **kwargs):
        super(VispyWidget, self).__init__(**kwargs)
        self.size = kwargs.get("size", (0, 0))
        # self.interval = 50.0
        self.gen_event = gen_event
        self.on_msg(self.events_received)

    def events_received(self, _, msg):
        # if self.is_closing:
        #     return
        if msg['msg_type'] == 'events':
            events = msg['contents']
            self.gen_event(msg)

    @property
    def size(self):
        return self.width, self.height

    @size.setter
    def size(self, size):
        self.width, self.height = size

    def quit(self):
        # self.is_closing = True
        self.close()
