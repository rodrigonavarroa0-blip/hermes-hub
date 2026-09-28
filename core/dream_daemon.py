"""
dream_daemon.py — Daemon Autónomo de Consolidación Continua en Segundo Plano (Sleep & Dream Daemon).
Ejecuta ciclos de mantenimiento de memoria y plasticidad del grafo en momentos de baja actividad:
1. Poda de sinapsis muertas y decaimiento hebbiano pasivo.
2. Detección y fusión de entidades duplicadas.
3. Descubrimiento de nuevos clusters latentes.
4. Auto-limpieza y compactación del grafo con consumo mínimo (<1% CPU).
"""
import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from core.dream_consolidation import DreamConsolidator
except ImportError:
    from dream_consolidation import DreamConsolidator

HUB_PATH = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()


class DreamConsolidationDaemon:
    """
    Daemon de mantenimiento autónomo de la memoria de Hermes Hub.
    """

    def __init__(self, interval_seconds: int = 120, decay_factor: float = 0.995):
        self.interval_seconds = interval_seconds
        self.decay_factor = decay_factor
        self.consolidator = DreamConsolidator(HUB_PATH)
        self._running = False

    def run_single_cycle(self) -> Dict[str, Any]:
        """Ejecuta un único ciclo de consolidación de memoria."""
        print(f"🌙 [{time.strftime('%Y-%m-%d %H:%M:%S')}] Ejecutando ciclo de consolidación 'Modo Sueño'...")
        result = self.consolidator.run_consolidation(
            dry_run=False,
            decay_factor=self.decay_factor,
            min_threshold=0.10
        )
        print(f"✅ Ciclo finalizado: {result.get('edges_pruned', 0)} sinapsis podadas, {result.get('orphans_reconnected', 0)} huérfanos reconectados.")
        return result

    def start_loop(self):
        """Inicia el bucle continuo del daemon."""
        self._running = True
        print(f"🚀 Hermes Dream Daemon iniciado (Intervalo: {self.interval_seconds}s, CPU < 1%)...")
        try:
            while self._running:
                self.run_single_cycle()
                time.sleep(self.interval_seconds)
        except KeyboardInterrupt:
            print("\n🛑 Hermes Dream Daemon detenido por el usuario.")
            self._running = False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hermes Dream Consolidation Daemon")
    parser.add_argument("--once", action="store_true", help="Ejecutar un solo ciclo y salir")
    parser.add_argument("--interval", type=int, default=120, help="Intervalo en segundos entre ciclos")
    parser.add_argument("--decay", type=float, default=0.995, help="Factor de decaimiento sináptico")
    args = parser.parse_args()

    daemon = DreamConsolidationDaemon(interval_seconds=args.interval, decay_factor=args.decay)
    if args.once:
        daemon.run_single_cycle()
    else:
        daemon.start_loop()
