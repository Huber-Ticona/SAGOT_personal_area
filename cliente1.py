import rpyc
import socket
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap , QIcon
import sys
from datetime import datetime,date 
import json
import ctypes
import os

class Login(QMainWindow):
    ventana_principal = 0
    def __init__(self):
        super(Login,self).__init__()
        uic.loadUi('login.ui',self)

        self.conexion = None
        self.host = None
        self.puerto = None
        self.actual = None
        self.txt_contra.setEchoMode(QLineEdit.Password)
        self.logo()
        self.btn_manual.clicked.connect(self.conectar_manual)
        self.btn_iniciar.clicked.connect(self.iniciar)
        self.btn_manual.clicked.connect

    def logo(self):
        actual = os.path.abspath(os.getcwd())
        self.actual = actual.replace('\\' , '/')
        ruta = actual + '/icono_imagen/madenco logo.png'
        foto = QPixmap(ruta)
        self.lb_logo.setPixmap(foto)
        if os.path.isfile(actual + '/manifest.txt'):
            print('encontrado manifest')
            with open(actual + '/manifest.txt' , 'r', encoding='utf-8') as file:
                lines = file.readlines()
                try:
                    n_host = lines[0].split(':')
                    n_host = n_host[1]
                    host = n_host[:len(n_host)-1]

                    n_port = lines[1].split(':')
                    n_port = n_port[1]
                    port = n_port[:len(n_port)-1]

                    self.host = host
                    self.puerto = port
                except IndexError:
                    pass #si no encuentra alguna linea
        else:
            print('manifest no encontrado')

        if os.path.isfile(actual+ '/registry.txt'):
            print('encontrado registry')
            with open(actual + '/registry.txt' , 'r', encoding='utf-8') as file:
                lines = file.readlines()
                try:
                    user = lines[0].split(':')
                    user = user[1]
                    user = user[:len(user)-1]

                    password = lines[1].split(':')
                    password = password[1]
                    password = password[:len(password)-1]
                    self.txt_usuario.setText(user)
                    self.txt_contra.setText(password)

                except IndexError:
                    print('error de indice del registry')
                    pass #si no encuentra alguna linea
        else:
            print('Datos de usuario no encontrados')

    def conectar(self):
        try:
            if self.host and self.puerto:
                self.conexion = rpyc.connect(self.host , self.puerto)
                self.lb_conexion.setText('CONECTADO')
            else:
                QMessageBox.about(self,'ERROR', 'Host y puerto no encontrados en el manifest' )

        except ConnectionRefusedError:
            self.lb_conexion.setText('EL SERVIDOR NO RESPONDE')
            
        except socket.error:
            self.lb_conexion.setText('SERVIDOR FUERA DE RED')

    def conectar_manual(self):
        dialog = InputDialog()

        if dialog.exec():
                hostx , puertox = dialog.getInputs()
                try:
                    puertox = int(puertox)
                    self.host = hostx
                    self.puerto = puertox
                    self.conexion = rpyc.connect(hostx , puertox)
                    self.lb_conexion.setText('CONECTADO')
                except ValueError:
                    QMessageBox.about(self,'ERROR' ,'Ingrese solo numeros en el PUERTO')
                except ConnectionRefusedError:
                    self.lb_conexion.setText('EL SERVIDOR NO RESPONDE')
                    
                except socket.error:
                    self.lb_conexion.setText('SERVIDOR FUERA DE LA RED')
                    #QMessageBox.about(self,'ERROR' ,'No se puede establecer la conexion con el servidor')
    def guardar_datos(self):
        
        if self.checkBox.isChecked():
            print('modificando: '+ self.actual + '/registry.txt')
            with open(self.actual + '/registry.txt' , 'w', encoding='utf-8') as file:
                
                file.write('usuario:'+ self.txt_usuario.text() + '\n')
                file.write('contra:' + self.txt_contra.text()+ '\n')
                file.write('')
    
    def iniciar(self):
        self.conectar()
        if self.conexion != None:
            usuario = self.txt_usuario.text()
            contra = self.txt_contra.text()
            correcto = False
            personal = None
            try:
                resultado = self.conexion.root.obtener_usuario_activo()
                for item in resultado:
                    if item[0] == usuario and item[1] == contra and item[4] == 'SI' and item[6] =='area': #si es PERSONAL DE AREA SUPER-USUARIO 
                        correcto = True
                        personal = item
                    elif item[0] == usuario and item[1] == contra and item[6] =='area':# SI NO ES PERSONAL DE AREA SUPER-USUARIO 
                        correcto = True
                        personal = item
                        
                if correcto:
                    self.ventana_principal = Cliente(self.conexion, personal ,self.host, self.puerto, self)
                    self.guardar_datos()
                    self.hide()
                    self.ventana_principal.show()
                else:
                    QMessageBox.about(self ,'ERROR', 'Personal de área: Usuario o contraseña no validas')

            except EOFError:
                QMessageBox.about(self ,'Conexion', 'Personal de área: El servidor no responde')
        else:
            self.conectar()
            

class Cliente(QMainWindow):
    ventana_buscar = 0
    ventana_gestion = 0
    def __init__(self, conn, usuario ,hostx, puertox, parent):
        super(Cliente , self).__init__(parent)
        uic.loadUi('cliente_menu.ui' , self)

        self.conexion = conn
        self.host = hostx
        self.puerto = puertox
        self.usuario = usuario
        self.func_area = None
        self.lb_conexion.setText('CONECTADO')
        self.inicializar()
        self.btn_reconectar.clicked.connect(self.reconectar)
        self.btn_buscar.clicked.connect(self.buscar)
        self.btn_salir.clicked.connect(self.salir)
        self.btn_gestion.clicked.connect(self.gestionar)

    def inicializar(self):
        
        actual = os.path.abspath(os.getcwd())
        actual = actual.replace('\\' , '/')
        ruta = actual + '/icono_imagen/madenco logo.png'
        foto = QPixmap(ruta)
        self.lb_logo.setPixmap(foto)
        if self.usuario[4] != 'SI':  #si es super usuario
            self.btn_gestion.hide()
            detalle = json.loads(self.usuario[7]) #cargar usuario
            func_area = detalle["area"]
            self.func_area = func_area
            print(func_area)
            if 'dimensionado' in func_area:
                self.btn_gestion.show()


    def reconectar(self):
        try:
            self.conexion = rpyc.connect(self.host , self.puerto)
            self.lb_conexion.setText('CONECTADO')

        except ConnectionRefusedError:
            self.lb_conexion.setText('EL SERVIDOR NO RESPONDE')
            
        except socket.error:
            self.lb_conexion.setText('SERVIDOR FUERA DE RED')

    def buscar(self):
        self.hide()
        self.ventana_buscar = Buscar(self.conexion, self.usuario ,self.func_area , self)
        self.ventana_buscar.show()

    def gestionar(self):
        self.hide()
        self.ventana_gestion = Gestion_dimensionador(self.conexion ,self)
        self.ventana_gestion.show()

    def salir(self):
        self.hide()
        self.parent().show()

class Buscar(QMainWindow):
    ventana_modificar = 0

    def __init__(self, conn, user, funciones ,parent = None):
        super(Buscar , self ).__init__(parent)
        uic.loadUi('cliente_buscar.ui', self)

        self.conexion = conn
        self.usuario = user
        self.dimensionadores = []
        self.func_area = funciones
        self.inicializar()
        self.r_fecha.setChecked(True)
        self.tableWidget.setColumnWidth(0,70)
        self.tableWidget.setColumnWidth(1,70)
        self.tableWidget.setColumnWidth(2,100)
        self.tableWidget.setColumnWidth(3,170)
        self.tableWidget.setColumnWidth(4,120)
        self.tableWidget.setColumnWidth(5,100)
        self.tableWidget.setColumnWidth(6,100)
        self.dateEdit.setDate(datetime.now().date())
        self.dateEdit.setCalendarPopup(True)

        self.btn_dimensionado.clicked.connect(self.buscar_dimensionado)
        self.btn_elaboracion.clicked.connect(self.buscar_elaboracion)
        self.btn_carpinteria.clicked.connect(self.buscar_carpinteria)
        self.btn_pallets.clicked.connect(self.buscar_pallets)

        self.btn_modificar.clicked.connect(self.modificar)
        self.btn_atras.clicked.connect(self.atras)
        self.seleccion = None

    def buscar_trabajadores(self):
        print('buscando... ' + self.seleccion)
        self.dimensionadores = []
        if self.conexion:
            try:
                resultado = self.conexion.root.obtener_trabajador_activo(self.seleccion)
                if resultado:
                    for item in resultado:
                        self.dimensionadores.append( item[0] )
            except EOFError:
                pass #analisar

    def inicializar(self):
        self.btn_dimensionado.setIcon(QIcon('icono_imagen/buscar.ico'))
        self.btn_elaboracion.setIcon(QIcon('icono_imagen/buscar.ico'))
        self.btn_carpinteria.setIcon(QIcon('icono_imagen/buscar.ico'))
        self.btn_pallets.setIcon(QIcon('icono_imagen/buscar.ico'))
        if self.usuario[4] != 'SI':
            self.btn_dimensionado.hide()
            self.btn_elaboracion.hide()
            self.btn_carpinteria.hide()
            self.btn_pallets.hide()
            if 'dimensionado' in self.func_area:
                self.btn_dimensionado.show()
            if 'elaboracion' in self.func_area:
                self.btn_elaboracion.show()
            if 'carpinteria' in self.func_area:
                self.btn_carpinteria.show()
            if 'pallets' in self.func_area:
                self.btn_pallets.show()

        self.btn_modificar.setIcon(QIcon('icono_imagen/editar.ico'))
        self.btn_atras.setIcon(QIcon('icono_imagen/atras.ico'))

    def buscar_dimensionado(self):
        if self.conexion:
            self.seleccion = 'dimensionado'
            self.buscar_trabajadores()
            self.lb_tipo_orden.setText('dimensionado')
            self.tableWidget.setRowCount(0)

            if self.r_orden.isChecked(): #Busqueda por numero de orden
                orden = self.txt_orden.text()
                try:
                    orden = int(orden)
                    consulta = self.conexion.root.buscar_orden_dim_numero(orden)
                    if consulta != None :
                        fila = self.tableWidget.rowCount()
                        self.tableWidget.insertRow(fila)
                        self.tableWidget.setItem(fila , 0 , QTableWidgetItem( str(consulta[0]) ))  #nro orden
                        self.tableWidget.setItem(fila , 1 , QTableWidgetItem('" '  + str(consulta[1]) + ' "' ))  #nro interno
                        self.tableWidget.setItem(fila , 2 , QTableWidgetItem( str(consulta[11]) ) )       #fecha creacion
                        self.tableWidget.setItem(fila , 3 , QTableWidgetItem(consulta[3]))       #nombre
                        self.tableWidget.setItem(fila , 4 , QTableWidgetItem( str(consulta[2]) ) )       #fecha venta
                        self.tableWidget.setItem(fila , 5 , QTableWidgetItem( str(consulta[5]) ) )       #fecha estimada
                        if consulta[19]:
                            self.tableWidget.setItem(fila , 6 , QTableWidgetItem( 'ANULADA' ) )       #estado
                        else:
                            self.tableWidget.setItem(fila , 6 , QTableWidgetItem( 'VALIDA' ) )       #estado
                    else:
                        QMessageBox.about(self,'Busqueda' ,'Orden de dimensionado NO encontrada')
                    
                except ValueError:
                    QMessageBox.about(self,'ERROR' ,'Ingrese solo numeros')
                except EOFError:
                    QMessageBox.about(self,'ERROR','Se perdio la conexion con el servidor')

            elif self.r_fecha.isChecked():
                date = self.dateEdit.date()
                aux = date.toPyDate()
                try:
                    datos = self.conexion.root.buscar_orden_dim_fecha( str(aux) )
                    if datos != ():
                        for dato in datos:
                            fila = self.tableWidget.rowCount()
                            self.tableWidget.insertRow(fila)
                            self.tableWidget.setItem(fila , 0 , QTableWidgetItem( str(dato[0]) ))  #nro orden
                            self.tableWidget.setItem(fila , 1 , QTableWidgetItem('" '  + str(dato[1]) + ' "' ))  #nro interno
                            self.tableWidget.setItem(fila , 2 , QTableWidgetItem( str(dato[4]) ) ) #fecha creacion
                            self.tableWidget.setItem(fila , 3 , QTableWidgetItem(dato[3]))       #nombre
                            self.tableWidget.setItem(fila , 4 , QTableWidgetItem( str(dato[2]) ) )       #fecha venta
                            self.tableWidget.setItem(fila , 5 , QTableWidgetItem( str(dato[5]) ) )       #fecha estimada
                            if dato[6]:
                                self.tableWidget.setItem(fila , 6 , QTableWidgetItem('ANULADA') )       #estado
                            else:
                                self.tableWidget.setItem(fila , 6 , QTableWidgetItem( 'VALIDA' ) )       #estado
                    else:
                        QMessageBox.about(self ,'Resultado', 'No se encontraron Ordenes de dimensionado')
                except EOFError:
                    QMessageBox.about(self,'ERROR','Se perdio la conexion con el servidor')

        else:
            QMessageBox.about(self ,'Conexion', 'No se ha establecido la conexion con el servidor')

    def buscar_elaboracion(self):
        if self.conexion:
            self.seleccion = 'elaboracion'
            self.buscar_trabajadores()
            self.lb_tipo_orden.setText('elaboracion')
            self.tableWidget.setRowCount(0)

            if self.r_orden.isChecked(): #Busqueda por numero de orden
                orden = self.txt_orden.text()
                try:
                    orden = int(orden)
                    consulta = self.conexion.root.buscar_orden_elab_numero(orden)
                    if consulta != None :
                        fila = self.tableWidget.rowCount()
                        self.tableWidget.insertRow(fila)
                        self.tableWidget.setItem(fila , 0 , QTableWidgetItem( str(consulta[0])) )  #nro orden
                        self.tableWidget.setItem(fila , 1 , QTableWidgetItem('" ' + str(consulta[10]) + ' "'  ))  #nro interno
                        self.tableWidget.setItem(fila , 2 , QTableWidgetItem( str(consulta[3]) ) )       #fecha creacion
                        self.tableWidget.setItem(fila , 3 , QTableWidgetItem(consulta[1]))       #nombre
                        self.tableWidget.setItem(fila , 4 , QTableWidgetItem( str(consulta[12]) ) )       #fecha venta
                        self.tableWidget.setItem(fila , 5 , QTableWidgetItem( str(consulta[4]) ) )       #fecha estimada
                        if consulta[16]:
                            self.tableWidget.setItem(fila , 6 , QTableWidgetItem('ANULADA' ) )       #estado
                        else:
                            self.tableWidget.setItem(fila , 6 , QTableWidgetItem( 'VALIDA' ) )       #estado
                    else:
                        QMessageBox.about(self,'Busqueda' ,'Orden de elaboracion NO encontrada')
                    
                except ValueError:
                    QMessageBox.about(self,'ERROR' ,'Ingrese solo numeros')
                except EOFError:
                    QMessageBox.about(self,'ERROR','Se perdio la conexion con el servidor')

            elif self.r_fecha.isChecked():
                date = self.dateEdit.date()
                aux = date.toPyDate()
                try:
                    datos = self.conexion.root.buscar_orden_elab_fecha( str(aux) )
                    if datos != ():
                        for dato in datos:
                            fila = self.tableWidget.rowCount()
                            self.tableWidget.insertRow(fila)
                            self.tableWidget.setItem(fila , 0 , QTableWidgetItem( str(dato[0]) ))  #nro orden
                            self.tableWidget.setItem(fila , 1 , QTableWidgetItem('" '  + str(dato[1]) + ' "' ))  #nro interno
                            self.tableWidget.setItem(fila , 2 , QTableWidgetItem( str(dato[2]) ) ) #fecha venta
                            self.tableWidget.setItem(fila , 3 , QTableWidgetItem(dato[3]))       #nombre
                            self.tableWidget.setItem(fila , 4 , QTableWidgetItem( str(dato[4]) ) )       #fecha venta
                            self.tableWidget.setItem(fila , 5 , QTableWidgetItem( str(dato[5]) ) )       #fecha estimada
                            if dato[6]:
                                self.tableWidget.setItem(fila , 6 , QTableWidgetItem( 'ANULADA' ) )       #estado
                            else:
                                self.tableWidget.setItem(fila , 6 , QTableWidgetItem( 'VALIDA' ) )       #estado
                    else:
                        QMessageBox.about(self ,'Resultado', 'No se encontraron Ordenes de elaboracion')
                except EOFError:
                    QMessageBox.about(self,'ERROR','Se perdio la conexion con el servidor')

        else:
            QMessageBox.about(self ,'Conexion', 'No se ha establecido la conexion con el servidor')
    
    def buscar_pallets(self):
        if self.conexion:
            self.seleccion = 'pallets'
            self.buscar_trabajadores()
            self.lb_tipo_orden.setText('pallets')
            self.tableWidget.setRowCount(0)
            if self.r_orden.isChecked(): #Busqueda por numero de orden
                orden = self.txt_orden.text()
                try:
                    orden = int(orden)
                    consulta = self.conexion.root.buscar_orden_pall_numero(orden)
                    if consulta != None :
                        fila = self.tableWidget.rowCount()
                        self.tableWidget.insertRow(fila)
                        self.tableWidget.setItem(fila , 0 , QTableWidgetItem( str(consulta[0])) )  #nro orden
                        self.tableWidget.setItem(fila , 1 , QTableWidgetItem('" ' + str(consulta[10]) + ' "'  ))  #nro interno
                        self.tableWidget.setItem(fila , 2 , QTableWidgetItem( str(consulta[3]) ) )       #fecha creacion
                        self.tableWidget.setItem(fila , 3 , QTableWidgetItem(consulta[1]))       #nombre
                        self.tableWidget.setItem(fila , 4 , QTableWidgetItem( str(consulta[12]) ) )       #fecha venta
                        self.tableWidget.setItem(fila , 5 , QTableWidgetItem( str(consulta[4]) ) )       #fecha estimada
                        if consulta[16]:
                            self.tableWidget.setItem(fila , 6 , QTableWidgetItem('ANULADA' ) )       #estado
                        else:
                            self.tableWidget.setItem(fila , 6 , QTableWidgetItem( 'VALIDA' ) )       #estado
                    else:
                        QMessageBox.about(self,'Busqueda' ,'Orden de pallets NO encontrada')
                except ValueError:
                    QMessageBox.about(self,'ERROR' ,'Ingrese solo numeros')
                except EOFError:
                    QMessageBox.about(self,'ERROR','Se perdio la conexion con el servidor')
            elif self.r_fecha.isChecked():
                date = self.dateEdit.date()
                aux = date.toPyDate()
                try:
                    datos = self.conexion.root.buscar_orden_pall_fecha( str(aux) )
                    if datos != ():
                        for dato in datos:
                            fila = self.tableWidget.rowCount()
                            self.tableWidget.insertRow(fila)
                            self.tableWidget.setItem(fila , 0 , QTableWidgetItem( str(dato[0]) ))  #nro orden
                            self.tableWidget.setItem(fila , 1 , QTableWidgetItem('" '  + str(dato[1]) + ' "' ))  #nro interno
                            self.tableWidget.setItem(fila , 2 , QTableWidgetItem( str(dato[2]) ) ) #fecha venta
                            self.tableWidget.setItem(fila , 3 , QTableWidgetItem(dato[3]))       #nombre
                            self.tableWidget.setItem(fila , 4 , QTableWidgetItem( str(dato[4]) ) )       #fecha venta
                            self.tableWidget.setItem(fila , 5 , QTableWidgetItem( str(dato[5]) ) )       #fecha estimada
                            if dato[6]:
                                self.tableWidget.setItem(fila , 6 , QTableWidgetItem( 'ANULADA' ) )       #estado
                            else:
                                self.tableWidget.setItem(fila , 6 , QTableWidgetItem( 'VALIDA' ) )       #estado
                    else:
                        QMessageBox.about(self ,'Resultado', 'No se encontraron Ordenes de pallets')
                except EOFError:
                    QMessageBox.about(self,'ERROR','Se perdio la conexion con el servidor')
        else:
            QMessageBox.about(self ,'Conexion', 'No se ha establecido la conexion con el servidor')

    def buscar_carpinteria(self):
        if self.conexion:
            self.seleccion = 'carpinteria'
            self.buscar_trabajadores()
            self.lb_tipo_orden.setText('carpinteria')
            self.tableWidget.setRowCount(0)

            if self.r_orden.isChecked(): #Busqueda por numero de orden
                orden = self.txt_orden.text()
                try:
                    orden = int(orden)
                    consulta = self.conexion.root.buscar_orden_carp_numero(orden)
                    if consulta != None :
                        fila = self.tableWidget.rowCount()
                        self.tableWidget.insertRow(fila)
                        self.tableWidget.setItem(fila , 0 , QTableWidgetItem( str(consulta[0])) )  #nro orden
                        self.tableWidget.setItem(fila , 1 , QTableWidgetItem('" ' + str(consulta[10]) + ' "'  ))  #nro interno
                        self.tableWidget.setItem(fila , 2 , QTableWidgetItem( str(consulta[3]) ) )       #fecha creacion
                        self.tableWidget.setItem(fila , 3 , QTableWidgetItem(consulta[1]))       #nombre
                        self.tableWidget.setItem(fila , 4 , QTableWidgetItem( str(consulta[12]) ) )       #fecha venta
                        self.tableWidget.setItem(fila , 5 , QTableWidgetItem( str(consulta[4]) ) )       #fecha estimada
                        if consulta[16]:
                            self.tableWidget.setItem(fila , 6 , QTableWidgetItem('ANULADA' ) )       #estado
                        else:
                            self.tableWidget.setItem(fila , 6 , QTableWidgetItem( 'VALIDA' ) )       #estado
                    else:
                        QMessageBox.about(self,'Busqueda' ,'Orden de carpinteria NO encontrada')
                    
                except ValueError:
                    QMessageBox.about(self,'ERROR' ,'Ingrese solo numeros')
                except EOFError:
                    QMessageBox.about(self,'ERROR','Se perdio la conexion con el servidor')

            elif self.r_fecha.isChecked():
                date = self.dateEdit.date()
                aux = date.toPyDate()
                try:
                    datos = self.conexion.root.buscar_orden_carp_fecha( str(aux) )
                    if datos != ():
                        for dato in datos:
                            fila = self.tableWidget.rowCount()
                            self.tableWidget.insertRow(fila)
                            self.tableWidget.setItem(fila , 0 , QTableWidgetItem( str(dato[0]) ))  #nro orden
                            self.tableWidget.setItem(fila , 1 , QTableWidgetItem('" '  + str(dato[1]) + ' "' ))  #nro interno
                            self.tableWidget.setItem(fila , 2 , QTableWidgetItem( str(dato[2]) ) ) #fecha venta
                            self.tableWidget.setItem(fila , 3 , QTableWidgetItem(dato[3]))       #nombre
                            self.tableWidget.setItem(fila , 4 , QTableWidgetItem( str(dato[4]) ) )       #fecha venta
                            self.tableWidget.setItem(fila , 5 , QTableWidgetItem( str(dato[5]) ) )       #fecha estimada
                            if dato[6]:
                                self.tableWidget.setItem(fila , 6 , QTableWidgetItem( 'ANULADA' ) )       #estado
                            else:
                                self.tableWidget.setItem(fila , 6 , QTableWidgetItem( 'VALIDA' ) )       #estado
                    else:
                        QMessageBox.about(self ,'Resultado', 'No se encontraron Ordenes de carpinteria')
                except EOFError:
                    QMessageBox.about(self,'ERROR','Se perdio la conexion con el servidor')

        else:
            QMessageBox.about(self ,'Conexion', 'No se ha establecido la conexion con el servidor')
    
    def modificar(self):
        seleccion = self.tableWidget.selectedItems()
        if seleccion != []:
            dato = seleccion[0].text()
            try:
                nro_orden = int(dato)
                self.hide()
                self.ventana_modificar = Modificar( self.conexion, nro_orden, self.dimensionadores, self.seleccion ,self ) 
                self.ventana_modificar.show()

            except ValueError:
                QMessageBox.about(self,'CONSEJO', 'Seleccione solo el Nro de orden asociado a la Orden de dimensionado')
        else:
            QMessageBox.about(self,'ERROR', 'Seleccione un Nro de orden antes de continuar')
        

    def atras(self):
        self.hide()
        self.parent().show()


class Modificar(QMainWindow):

    def __init__(self, conn , orden , trabajadores, selec ,parent = None):
        super(Modificar , self).__init__(parent)
        uic.loadUi('cliente_modificar_2.ui' , self)

        self.conexion = conn
        self.seleccion = selec
        self.trabajadores = trabajadores
        self.tableWidget.setColumnWidth(0,80)
        self.tableWidget.setColumnWidth(1,495)
        self.tableWidget.setColumnWidth(2,85 )
        self.nro_orden = orden
        self.inicializar()
        self.date_ingreso.setCalendarPopup(True)
        self.date_real.setCalendarPopup(True)
        self.date_real.setDate( datetime.now().date() )
        self.date_ingreso.setDate( datetime.now().date() )
        self.btn_guardar.clicked.connect(self.guardar)
        self.btn_atras.clicked.connect(self.atras)
    
    def inicializar(self):
        self.btn_guardar.setIcon(QIcon('icono_imagen/guardar.ico'))
        self.btn_atras.setIcon(QIcon('icono_imagen/atras.ico'))
        self.lb_nombre_orden.setText((self.seleccion).upper())
        for item in self.trabajadores:
                    self.combo_dimensionador.addItem( item ) #comboox de trabajadores

        if self.seleccion == 'dimensionado':
            self.date_ingreso.setDate( datetime.now().date() )
            self.date_real.setDate( datetime.now().date() )
            try:
                
                resultado = self.conexion.root.buscar_orden_dim_numero(self.nro_orden)

                self.lb_orden.setText( str(resultado[0]) ) 
                self.lb_interno.setText(str( resultado[1] ))

                if resultado[2]:
                    date = datetime.fromisoformat( str( resultado[2] ) )
                    self.lb_fecha_venta.setText( str(date.strftime("%d-%m-%Y %H:%M:%S") ) ) #fecha venta
                else: 
                    date = datetime.now()
                    self.lb_fecha_venta.setText(str(date.strftime("%d-%m-%Y %H:%M:%S")))

                self.lb_nombre.setText(resultado[3]) #nombre
                self.lb_telefono.setText( str(resultado[4]) ) #telefono

                aux = datetime.fromisoformat(  str(resultado[5]) )
                self.lb_fecha_est.setText( str(aux.strftime("%d-%m-%Y")) ) #fecha estimada
                if resultado[7]:
                    self.lb_doc.setText( resultado[7] )             # tipo documento
                else:
                    self.lb_doc.setText('NO ASIGNADA')            # tipo documento

                if resultado[8]:     
                    self.lb_documento.setText( str( resultado[8] ))   #numero documento
                else:
                    self.lb_documento.setText('NO ASIGNADA')   #numero documento
                
                detalle = json.loads( resultado[6] ) #detalle
                
                cantidades = detalle["cantidades"]
                descripciones = detalle["descripciones"]
                valores_neto = detalle["valores_neto"]
                j = 0
                while j < len( cantidades ):
                    fila = self.tableWidget.rowCount()
                    self.tableWidget.insertRow(fila)
                    self.tableWidget.setItem(fila , 0 , QTableWidgetItem( str( cantidades[j] )) ) 
                    self.tableWidget.setItem(fila , 1 , QTableWidgetItem( descripciones[j] ) )
                    self.tableWidget.setItem(fila , 2 , QTableWidgetItem( str( valores_neto[j] )) ) 
                    j+=1 
                if resultado[9] == 'SI' :
                    self.lb_enchapado.setText('SI')
                else:
                    self.lb_enchapado.setText('NO')
                if resultado[10] == 'SI' :
                    self.lb_despacho.setText('SI')
                else:
                    self.lb_despacho.setText('NO')
                if resultado[12] != '':
                    self.lb_contacto.setText( resultado[12] ) #contacto
                if resultado[13] != '':
                    self.lb_oce.setText( resultado[13] )   #ORDEN compra
                if resultado[14]:
                    aux2 = datetime.fromisoformat(  str(resultado[14]) )
                    self.lb_real.setText( str(aux2.strftime("%d-%m-%Y"))  )     #ffecha real
                if resultado[15]:
                    self.lb_vend.setText(resultado[15])      #vendedor
                else:
                    self.lb_vend.setText('NO ASIGNADO')      #vendedor

                if resultado[16]:
                    self.lb_dim.setText(resultado[16])      #DIMENSIONADOR
                if resultado[17]:
                    aux3 = datetime.fromisoformat(  str(resultado[17]) )
                    self.lb_ing.setText( str(aux3.strftime("%d-%m-%Y"))  )     #ffecha ingreso
            
                
            except EOFError:
                QMessageBox.about(self, 'ERROR', 'Se perdio la conexion con el servidor')
        else:
            
            try:
                if self.seleccion == 'elaboracion':
                    resultado = self.conexion.root.buscar_orden_elab_numero(self.nro_orden)
                elif self.seleccion == 'carpinteria':
                    resultado = self.conexion.root.buscar_orden_carp_numero(self.nro_orden)
                elif self.seleccion == 'pallets':
                    resultado = self.conexion.root.buscar_orden_pall_numero(self.nro_orden)
                
                self.lb_orden.setText( str(resultado[0]) ) 
                self.lb_nombre.setText(resultado[1]) #nombre
                self.lb_telefono.setText( str(resultado[2]) ) #telefono
                
                
                aux = datetime.fromisoformat(  str(resultado[4]) )
                self.lb_fecha_est.setText( str(aux.strftime("%d-%m-%Y")) ) #fecha estimada
                if resultado[5]:
                    self.lb_documento.setText( str( resultado[5] ))   #numero documento
                else:
                    self.lb_documento.setText('NO ASIGNADA')   #numero documento

                if resultado[6]:
                    self.lb_doc.setText( resultado[6] )             # tipo documento  
                else:
                    self.lb_doc.setText('NO ASIGNADA')             # tipo documento  

                if resultado[7] != '':
                    self.lb_contacto.setText( resultado[7] )  #CONTACTO

                if resultado[8] != '':
                    self.lb_oce.setText( resultado[8] )        #ORDEN DE COMPRA    
                if resultado[9] == 'SI' :
                    self.lb_despacho.setText('SI')
                else:
                    self.lb_despacho.setText('NO')

                self.lb_interno.setText(str( resultado[10] ))   #NRO INTERNO
               
                detalle = json.loads( resultado[11] ) #detalle
                
                cantidades = detalle["cantidades"]
                descripciones = detalle["descripciones"]
                valores_neto = detalle["valores_neto"]
                j = 0
                while j < len( cantidades ):
                    fila = self.tableWidget.rowCount()
                    self.tableWidget.insertRow(fila)
                    self.tableWidget.setItem(fila , 0 , QTableWidgetItem( str( cantidades[j] )) ) 
                    self.tableWidget.setItem(fila , 1 , QTableWidgetItem( descripciones[j] ) )
                    self.tableWidget.setItem(fila , 2 , QTableWidgetItem( str( valores_neto[j] )) ) 
                    j+=1 
                self.label_22.setHidden(True)
                self.lb_enchapado.setHidden(True)
                '''self.lb_enchapado.setHidden(True)
                self.label_14.setHidden(True)
                self.label_4.setHidden(True)
                self.r_opc1.setHidden(True)
                self.combo_dimensionador.setHidden(True)
                self.date_ingreso.setHidden(True)'''

                if resultado[12]:
                    date = datetime.fromisoformat( str( resultado[12] ) )
                    self.lb_fecha_venta.setText( str(date.strftime("%d-%m-%Y %H:%M:%S") ) ) #fecha venta
                else: 
                    date = datetime.now()
                    self.lb_fecha_venta.setText(str(date.strftime("%d-%m-%Y %H:%M:%S")))

                if resultado[13]:
                    aux2 = datetime.fromisoformat(  str(resultado[13]) )
                    self.lb_real.setText( str(aux2.strftime("%d-%m-%Y"))  )     #ffecha real
                else:
                    self.lb_real.setText( 'NO ASIGNADA' )     #ffecha real
                if resultado[14]:
                    self.lb_vend.setText(resultado[14])      #vendedor
                else: 
                    self.lb_vend.setText('NO ASIGNADO')      #vendedor
                if resultado[17]:
                    aux2 = datetime.fromisoformat(  str(resultado[17]) )
                    self.lb_ing.setText( str(aux2.strftime("%d-%m-%Y")) )      #fecha de ingreso
                if resultado[18]:
                    self.lb_dim.setText(resultado[18])      #trabajador asignado

                #self.groupBox_2.hide()
            except EOFError:
                QMessageBox.about(self, 'ERROR', 'Se perdio la conexion con el servidor')

# NUEVA VERSION DE GUARDADO -------

    def guardar(self):
        tipo = (self.seleccion).lower()

        if self.r_opc1.isChecked():
            trabajador = self.combo_dimensionador.currentText()
            fecha_ingreso = str( self.date_ingreso.date().toPyDate() )

            if self.seleccion == 'dimensionado':
                print('modficando fecha ingreso y trabajador asignado de ' + self.seleccion +' ....')
                if self.conexion.root.actualizar_orden_dim2(self.nro_orden , fecha_ingreso, trabajador ):
                    self.lb_dim.setText(trabajador)
                    fecha = (datetime.fromisoformat(fecha_ingreso)).strftime("%d-%m-%Y")
                    print(fecha)
                    self.lb_ing.setText(fecha)
                    QMessageBox.about(self,'EXITO','Fecha de ingreso y dimensionador asignados correctamente')
                else:
                    QMessageBox.about(self,'ERROR','La orden de dimensionado NO se actualizo debido a que ningun texto fue modificado')

            else: #SI NO ES DE DIMENSIONADO , OSEA ELAB , CARP Y PALL
                if self.conexion.root.actualizar_orden_ingreso_trabajador(tipo ,str(self.nro_orden) , fecha_ingreso ,trabajador ):
                    self.lb_dim.setText(trabajador)
                    fecha = (datetime.fromisoformat(fecha_ingreso)).strftime("%d-%m-%Y")
                    print(fecha)
                    self.lb_ing.setText(fecha)
                    QMessageBox.about(self,'EXITO','Fecha ingreso y traajador asignados correctamente')
                else:
                    QMessageBox.about(self,'ERROR','La orden de '+ tipo +' NO se actualizo debido a que ningun DATO fue modificado o se produjo algun error interno.')
                print('modficando fecha ingreso y trabajador asignado de ' + self.seleccion +' ....')

        elif self.r_opc2.isChecked():
            fecha_real = str (self.date_real.date().toPyDate() )
            
            if self.conexion.root.actualizar_orden_fecha_real( tipo, str(self.nro_orden), fecha_real):
                fecha = (datetime.fromisoformat(fecha_real)).strftime("%d-%m-%Y")
                print(fecha)
                self.lb_real.setText(str(fecha))
                QMessageBox.about(self,'EXITO','Fecha real asignada correctamente')
            else:
                QMessageBox.about(self,'ERROR','La orden de '+ tipo+' NO se actualizo debido a que ningun texto fue modificado o se produjo un error interno')    
            print('modficando fecha real de ' + self.seleccion +' ....')
        else:
            QMessageBox.about(self,'CONSEJO','Seleccione un los datos que desea registrar, si fecha de ingreso y trabajador o solo la fecha real')
    #----- VERSION ANTIGUA GUARDAR2 -------
    def guardar2(self):
        if self.seleccion == 'dimensionado':
            dimensionador = self.combo_dimensionador.currentText()
            fecha_ingreso = str( self.date_ingreso.date().toPyDate() )
            fecha_real = str (self.date_real.date().toPyDate() )
            if self.r_opc1.isChecked():
                if self.conexion.root.actualizar_orden_dim2(self.nro_orden , fecha_ingreso, dimensionador ):
                    self.lb_dim.setText(dimensionador)
                    self.lb_ing.setText(fecha_ingreso)
                    QMessageBox.about(self,'EXITO','Fecha de ingreso y dimensionador asignados correctamente')
                else:
                    QMessageBox.about(self,'ERROR','La orden de dimensionado NO se actualizo debido a que ningun texto fue modificado')

            elif self.r_opc2.isChecked():
                if self.conexion.root.actualizar_orden_dim3(self.nro_orden , fecha_real ):
                    self.lb_real.setText(fecha_real)
                    QMessageBox.about(self,'EXITO','Fecha real asignada correctamente')
                else:
                    QMessageBox.about(self,'ERROR','La orden de dimensionado NO se actualizo debido a que ningun texto fue modificado')
            else:
                QMessageBox.about(self,'ERROR','Primero seleccione los datos que se guardarán y luego proceda a guardarlos')
        else:
            if self.r_opc2.isChecked():
                fecha_real = str (self.date_real.date().toPyDate() )
                try:
                    if self.seleccion == 'elaboracion':
                        if self.conexion.root.actualizar_orden_elab2(self.nro_orden , fecha_real):
                            self.lb_real.setText(fecha_real)
                            QMessageBox.about(self,'EXITO','Fecha real asignada correctamente')
                        else:
                            QMessageBox.about(self,'ERROR','La orden de elaboracion NO se actualizo debido a que ningun texto fue modificado')
                    
                    elif self.seleccion == 'carpinteria':
                        if self.conexion.root.actualizar_orden_carp2(self.nro_orden , fecha_real ):
                            self.lb_real.setText(fecha_real)
                            QMessageBox.about(self,'EXITO','Fecha real asignada correctamente')
                        else:
                            QMessageBox.about(self,'ERROR','La orden de carpinteria NO se actualizo debido a que ningun texto fue modificado')
                    
                    elif self.seleccion == 'pallets':
                        if self.conexion.root.actualizar_orden_pall2(self.nro_orden , fecha_real ):
                            self.lb_real.setText(fecha_real)
                            QMessageBox.about(self,'EXITO','Fecha real asignada  correctamente')
                        else:
                            QMessageBox.about(self,'ERROR','La orden de pallets NO se actualizo debido a que ningun texto fue modificado')
                        
                except EOFError:
                    QMessageBox.about(self,'ERROR','Se perdio la conexion con el servidor')
            else:
                QMessageBox.about(self,'ERROR','Primero seleccione el item que se va a agregar.')

    def atras(self):
        self.hide()
        self.parent().show()

class Gestion_dimensionador(QMainWindow):

    def __init__(self , conn ,parent = None):
        super(Gestion_dimensionador , self).__init__(parent)
        uic.loadUi('gestionar_dimensionador.ui' , self)


        self.conexion = conn

        self.dimensionadores = []
        #self.inicializar()
        self.r_inicio.setDate( datetime.now().date() )
        self.r_termino.setDate( datetime.now().date() )
        self.r_inicio.setCalendarPopup(True)
        self.r_termino.setCalendarPopup(True)
        self.m_inicio.setCalendarPopup(True)

        self.btn_registrar.clicked.connect(self.registrar)
        self.btn_atras.clicked.connect(self.volver)
        self.btn_obtener.clicked.connect(self.obtener)
        self.btn_actualizar.clicked.connect(self.modificar)
        self.btn_retirar.clicked.connect(self.retirar)
# ---------------
        self.r_dim2.toggled.connect(lambda: self.obtener_trabajador_area(self.r_dim2 , 1) )
        self.r_elab2.toggled.connect(lambda: self.obtener_trabajador_area(self.r_elab2, 1) )
        self.r_carp2.toggled.connect(lambda: self.obtener_trabajador_area(self.r_carp2 , 1) )
        self.r_pall2.toggled.connect(lambda: self.obtener_trabajador_area(self.r_pall2, 1) )

        self.r_dim3.toggled.connect(lambda: self.obtener_trabajador_area(self.r_dim3,2)   )
        self.r_elab3.toggled.connect(lambda: self.obtener_trabajador_area(self.r_elab3,2) )
        self.r_carp3.toggled.connect(lambda: self.obtener_trabajador_area(self.r_carp3,2) )
        self.r_pall3.toggled.connect(lambda: self.obtener_trabajador_area(self.r_pall3,2 ) )

        self.btn_atras.setIcon(QIcon('icono_imagen/atras.ico'))
        self.btn_registrar.setIcon(QIcon('icono_imagen/guardar.ico'))
        self.btn_actualizar.setIcon(QIcon('icono_imagen/guardar.ico'))

    def inicializar(self):
        #inicializa los trabajadores activos del sistema.
        if self.conexion:
            try:
                resultado = self.conexion.root.obtener_dimensionador_activo()
                self.dimensionadores = resultado
                for item in resultado:
                    self.box_dimensionador.addItem(item[0])
                    self.box_dimensionador_2.addItem(item[0])

            except EOFError:
                QMessageBox.about(self,'CONEXION','No se pudo obtener la lista de dimensionadores. El servidor no responde') 
        
        else:
            QMessageBox.about(self,'CONEXION','No ha establecido conexion con el servidor.') 

    def registrar(self):
        if self.conexion:
            nombre = self.r_nombre.text()
            telefono = self.r_telefono.text()
            inicio = self.r_inicio.date()
            inicio = inicio.toPyDate()
            area = ''
            if self.r_dim.isChecked():
                area = self.r_dim.text()
                print(area)
            elif self.r_elab.isChecked():
                area = self.r_elab.text()
                print(area)
            elif self.r_carp.isChecked():
                area = self.r_carp.text()
                print(area)
            elif self.r_pall.isChecked():
                area = self.r_pall.text()
                print(area)

            
            if area != '':
                area = area.lower()
                print(area)
                if nombre != '' :
                    if telefono != '' :
                        try:
                            telefono = int(telefono)
                            if self.conexion.root.registrar_trabajador(nombre,telefono, str(inicio), area ) :
                                QMessageBox.about(self,'EXITO','TRABAJADOR registrado correctamente')
                                self.hide()
                                self.parent().show()
                            else:
                                QMessageBox.about(self,'ERROR','Problemas al registrar al TRABAJADOR en la base de datos.')


                        except ValueError:
                            QMessageBox.about(self,'DATOS ERRONEO','Ingrese solo numeros en el campo telefono')           

                    else: 
                        QMessageBox.about(self,'DATOS INCOMPLETOS','Ingrese un telefono antes de registrar')           
                else:
                    QMessageBox.about(self,'DATOS INCOMPLETOS','Ingrese un nombre antes de registrar') 
            else:
                    QMessageBox.about(self,'DATOS INCOMPLETOS','Seleccione el area del trabajador a registrar.') 
        else:
            QMessageBox.about(self,'CONEXION','No ha establecido conexion con el servidor.') 
    
    def obtener(self):
        nombre = self.box_dimensionador.currentText()
        for datos in self.dimensionadores:
            if datos[0] == nombre:
                self.m_nombre.setText(datos[0])
                self.m_telefono.setText(str(datos[1]))
                aux =   datetime.fromisoformat( str(datos[2]) )  
                self.m_inicio.setDate( aux )
                break
    def obtener_trabajador_area(self, radio,box):
        #inicializa los trabajadores activos del sistema.
        self.box_dimensionador.clear()
        self.box_dimensionador_2.clear()
        if radio.isChecked():
            area = radio.text()
            print('obteniendo trabajadores de area: ' + area )
            if self.conexion:
                try:
                    resultado = self.conexion.root.obtener_trabajador_activo(area)
                    self.dimensionadores = resultado
                    for item in resultado:
                        if box == 1:
                            self.box_dimensionador.addItem(item[0])
                        elif box == 2:
                            self.box_dimensionador_2.addItem(item[0])

                except EOFError:
                    QMessageBox.about(self,'CONEXION','No se pudo obtener la lista de dimensionadores. El servidor no responde') 
            
            else:
                QMessageBox.about(self,'CONEXION','No ha establecido conexion con el servidor.') 

        else:
            area = radio.text()
            print('no buscando: ' + area)
        
        

    def modificar(self):
        nombre = self.box_dimensionador.currentText()
        nuevo_nombre = self.m_nombre.text()
        nuevo_telefono = self.m_telefono.text()
        nuevo_inicio = self.m_inicio.date()
        nuevo_inicio = nuevo_inicio.toPyDate()
        nro_dimensionador = 0
        for datos in self.dimensionadores:
            if datos[0] == nombre:
                nro_dimensionador = datos[3]
                print(nro_dimensionador)
                break

        if self.conexion:
            if self.dimensionadores:
                if nuevo_nombre != '' :
                    if nuevo_telefono != '' :
                        try:
                            nuevo_telefono = int(nuevo_telefono)
                            if self.conexion.root.actualizar_trabajador(nuevo_nombre,nuevo_telefono, str(nuevo_inicio) , nro_dimensionador ) :
                                QMessageBox.about(self,'EXITO','Trabajador ACTUALIZADO correctamente')
                                self.hide()
                                self.parent().show()
                            else:
                                QMessageBox.about(self,'ERROR','No se detectaron cambios. Intente modificando algun dato')
                                
                        except ValueError:
                            QMessageBox.about(self,'DATOS ERRONEO','Ingrese solo numeros en el campo telefono')    
                        except EOFError:
                            QMessageBox.about(self,'CONEXION','El servidor no responde')        

                    else: 
                        QMessageBox.about(self,'DATOS INCOMPLETOS','Ingrese un telefono antes de registrar')           
                else:
                    QMessageBox.about(self,'DATOS INCOMPLETOS','Ingrese un nombre antes de registrar') 
            else:
                QMessageBox.about(self,'ERROR','No se encontraron dimensionadores ACTIVOS') 
        else:
            QMessageBox.about(self,'CONEXION','No ha establecido conexion con el servidor.') 

    def retirar(self):
        nombre = self.box_dimensionador_2.currentText()    
        termino = self.r_termino.date().toPyDate()   
        nro_dimensionador = 0
        for datos in self.dimensionadores:
            if datos[0] == nombre:
                nro_dimensionador = datos[3]
                print(nro_dimensionador)
                break

        if self.conexion:
            if self.dimensionadores:
                try:
                    if self.conexion.root.retirar_trabajador(nro_dimensionador , str( termino ) ):
                        QMessageBox.about(self,'EXITO','Trabajador RETIRADO correctamente')
                        self.hide()
                        self.parent().show()
                    else:
                        QMessageBox.about(self,'ERROR','El Dimensionador no se retiro correctamente. Analisar posibles causas...')     
                except EOFError:
                    QMessageBox.about(self,'CONEXION','El servidor no responde')     
            else: 
                QMessageBox.about(self,'ERROR','No se encontraron dimensionadores ACTIVOS') 
        else:
            QMessageBox.about(self,'CONEXION','No ha establecido conexion con el servidor.') 

    def volver(self):
        self.hide()
        self.parent().show()

class InputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.host = QLineEdit(self)
        self.puerto = QLineEdit(self)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self);

        layout = QFormLayout(self)
        layout.addRow("HOST:", self.host)
        layout.addRow("PUERTO:", self.puerto)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return self.host.text(), self.puerto.text()

if __name__ == '__main__':
    myappid = 'madenco.personal.area' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid) 
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icono_imagen/madenco logo.ico'))
    
    inicio = Login()
    inicio.show()
    sys.exit(app.exec_())