"""
SafetyManager - Servicio de computo puro para evaluacion de seguridad cinematica.
Sin estado propio; delega en workspace_singularity.
"""
from motor3d.safety.workspace_singularity import in_workspace, near_singularity


class SafetyManager:

    def evaluate(self, points, max_reach, model=None):
        """
        Evalua el estado de seguridad del brazo.

        Args:
            points   : lista de posiciones articulares [[x,y,z], ...]
            max_reach: alcance maximo teorico
            model    : estado cinematico opcional para evaluar singularidad

        Returns:
            Dict con claves:
                'in_workspace' : bool
                'singular'     : bool
                'blocked'      : bool  (True si hay que bloquear la simulacion)
                'message'      : str   (mensaje de aviso o cadena vacia)
        """
        workspace_ok = in_workspace(points, max_reach)
        singular = near_singularity(points, model=model)

        # Solo se bloquea la ejecucion cuando el efector esta fuera del workspace.
        # La singularidad es un aviso informativo: puede afectar a la precision
        # local del movimiento, pero no impide ejecutar el sketch.
        blocked = not workspace_ok
        message = ""

        if not workspace_ok:
            message = "Posicion fuera del espacio de trabajo del robot."
        elif singular:
            message = "Aviso: configuracion cercana a singularidad. El movimiento puede ser impreciso."

        return {
            'in_workspace': workspace_ok,
            'singular': singular,
            'blocked': blocked,
            'message': message,
        }
