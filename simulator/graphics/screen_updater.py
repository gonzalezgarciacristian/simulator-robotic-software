import time
import threading
import graphics.layers as layers


layer: layers.Layer = None
last_update = 0
view = None
controller = None  # Referencia al RobotsController, necesaria para debug_line()


def refresh(force=False):
    global layer
    global last_update
    global view
    if layer is None or view is None:
        return
    curr_time = time.time_ns() / 1000000
    if force or last_update + 16 <= curr_time:
        layer.move(view.keys_used, view.move_WASD)
        view.update_idletasks()
        last_update = time.time_ns() / 1000000


def update():
    """Alias de refresh() — llamado desde código generado en bucles for/do-while."""
    refresh()


def _block_until_resumed():
    """Bloquea el hilo de fondo en su posición actual hasta que se reanude la ejecución."""
    if threading.current_thread() is threading.main_thread():
        return  # Nunca bloquear el hilo principal
    while (
        controller is not None
        and getattr(controller, "paused", False)
        and getattr(controller, "executing", True)
    ):
        time.sleep(0.02)


def debug_line(line_no):
    """Llamado desde el código transpilado antes de cada sentencia.
    Funciona tanto desde el hilo principal como desde el hilo de fondo (Loop).
    Si hay que pausar:
      - Hilo principal (setup): lanza ExecutionPaused para interrumpir la llamada.
      - Hilo de fondo (loop): bloquea el hilo EN SU POSICIÓN ACTUAL para que
        el paso-a-paso avance a la sentencia siguiente, no a la primera de loop()."""
    if threading.current_thread() is threading.main_thread():
        refresh()
    ctrl = controller
    if ctrl is None:
        return
    if not getattr(ctrl, "executing", True):
        if threading.current_thread() is not threading.main_thread():
            from compiler.commands import ExecutionPaused
            raise ExecutionPaused(line_no)
        return
    if ctrl.debug_should_pause_at_line(line_no):
        # Actualizar el highlight SINCRÓNICAMENTE: el usuario ve la nueva línea
        # antes de que el hilo se bloquee (no hay race con after()).
        if view is not None and hasattr(view, "editor_frame"):
            if threading.current_thread() is threading.main_thread():
                view.editor_frame.set_current_exec_line(line_no)
            else:
                done = threading.Event()
                def _set(ln=line_no, ev=done):
                    view.editor_frame.set_current_exec_line(ln)
                    ev.set()
                view.after(0, _set)
                done.wait(timeout=0.5)
        if threading.current_thread() is threading.main_thread():
            # setup() corre en el hilo principal: usar excepción como antes
            from compiler.commands import ExecutionPaused
            raise ExecutionPaused(line_no)
        else:
            # loop() corre en hilo de fondo: bloquear aquí para preservar la pila
            _block_until_resumed()
            # Si se detuvo la simulación mientras estábamos bloqueados, salir
            if controller is None or not getattr(controller, "executing", True):
                from compiler.commands import ExecutionPaused
                raise ExecutionPaused(line_no)
