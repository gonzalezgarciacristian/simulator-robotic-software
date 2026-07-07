"""
Subset of Arduino/C stdlib helpers used by sketches in the simulator.
"""

import libraries.standard as standard


def get_name():
    return "stdlib"


def get_methods():
    methods = {}
    methods["strtol"] = ("long", "strtol", ["any", "ref", "int"], -1)
    return methods


def get_not_implemented():
    return []


def strtol(value, end=None, base=10):
    return standard.strtol(value, end, base)
