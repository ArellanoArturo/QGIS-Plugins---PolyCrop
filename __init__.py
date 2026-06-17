# -*- coding: utf-8 -*-
def classFactory(iface):
    from .polycrop import PolyCrop
    return PolyCrop(iface)
