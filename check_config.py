#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ConfigParser,os
"""
Descripcion: Modulo que permite manipular archivos de configuracion.
Autor: Ernesto Crespo
Correo: ecrespo@gmail.com
Licencia: GPL Version 3
Copyright: Copyright (C) 2010 Distrito Socialista Tecnologico AIT PDVSA  Merida
Version: 0.1

"""

class config:

    def __init__(self,cnffile):
        self.__cnffile = cnffile
        self.__config = ConfigParser.ConfigParser()
        self.__config.read(self.__cnffile)


    def ShowItemSection(self,section):
        return self.__config.items(section)

    def ShowValueItem(self,section,option):
        return self.__config.get(section,option)

    def change(self,section,option,value):
        self.__config.set(section,option,value)


    def write(self):
        self.__config.write(open(self.__cnffile,'w'))



