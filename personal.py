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
import logging
logging.basicConfig(level=logging.DEBUG , format='%(threadName)s: %(message)s')

class Login(QDialog):
    def __init__(self,parent):
        super(Login,self).__init__(parent)
        uic.loadUi('login.ui',self)

        self.setModal(True)
        self.conexion = None
        self.host = None
        self.puerto = None
        self.actual = None # RUTA DE LA APLICACION
        self.usuario = None
        self.txt_contra.setEchoMode(QLineEdit.Password)
        self.inicializar()
        self.btn_manual.clicked.connect(self.conectar_manual)
        self.btn_iniciar.clicked.connect(self.iniciar)
        self.btn_manual.clicked.connect

    def inicializar(self):
        actual = os.path.abspath(os.getcwd())
        self.actual = actual.replace('\\' , '/')
        ruta = actual + '/icono_imagen/madenco logo.png'
        foto = QPixmap(ruta)
        self.lb_logo.setPixmap(foto)
        if os.path.isfile(actual + '/manifest.txt'):
            print('---- LEYENDO MANIFEST.TXT  -----')
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
            print('--- MANIFEST.TXT NO ENCONTRADO -----')

        if os.path.isfile(actual+ '/registry.txt'):
            print('---- LEYENDO REGISTRY ----')
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
            print('----- REGISTRY.TXT NO ENCONTRADO -----')

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
            try:
                resultado = self.conexion.root.obtener_usuario_activo()
                for item in resultado:
                    if item[0] == usuario and item[1] == contra and item[4] == 'SI' and item[6] =='area': #si es PERSONAL DE AREA SUPER-USUARIO 
                        correcto = True
                        self.usuario = item
                    elif item[0] == usuario and item[1] == contra and item[6] =='area':# SI NO ES PERSONAL DE AREA SUPER-USUARIO 
                        correcto = True
                        self.usuario = item
                        
                if correcto:
                    #self.ventana_principal = Personal(self.conexion, personal ,self.host, self.puerto, self)
                    #self.guardar_datos()
                    #self.hide()
                    #self.ventana_principal.show()
                    self.accept()
                else:
                    QMessageBox.about(self ,'ERROR', 'Personal de área: Usuario o contraseña no validas')

            except EOFError:
                QMessageBox.about(self ,'Conexion', 'Personal de área: El servidor no responde')
        else:
            self.conectar()

    def obt_datos(self):
        return self.usuario , self.conexion ,self.host , self.puerto

class Personal(QMainWindow):
    ventana_login = 0

    def __init__(self):
        super(Personal , self).__init__()
        uic.loadUi('personal.ui' , self)

        self.conexion =None
        self.host = None
        self.puerto = None
        self.usuario = None
        self.func_area = None

        


        self.lb_conexion.setText('CONECTADO')
        self.iniciar_login()
        self.inicializar()
        self.btn_reconectar.clicked.connect(self.reconectar)
        self.btn_buscar.clicked.connect(self.buscar)
        self.btn_salir.clicked.connect(self.salir)
        self.btn_gestion.clicked.connect(self.gestionar)

        # FUNCIONES VISTA BUSCAR ORDEN
        self.area = None
        self.trabajadores = []
        self.detalle = None # usada para asignar parametros al JSON detalle.
        self.btn_atras.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.inicio))
        self.btn_modificar.clicked.connect(self.inicializar_modificar_orden)

        self.btn_dimensionado.clicked.connect(lambda: self.buscar_ordenes_de_trabajo('dimensionado'))
        self.btn_elaboracion.clicked.connect(lambda: self.buscar_ordenes_de_trabajo('elaboracion'))
        self.btn_carpinteria.clicked.connect(lambda: self.buscar_ordenes_de_trabajo('carpinteria'))
        self.btn_pallets.clicked.connect(lambda: self.buscar_ordenes_de_trabajo('pallets'))

        # FUNCIONES VISTA MODIFICAR ORDEN -> AGREGAR NUEVOS DATOS

        self.btn_guardar.clicked.connect(self.guardar)
        self.btn_atras_2.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.buscar_orden))
        self.opcion_datos.currentIndexChanged.connect(self.mostrar_combo_trabajadores)

        # FUNCIONES GESTIONAR TRABAJADOR
        self.btn_registrar.clicked.connect(self.registrar_trabajador)
        self.btn_atras_3.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.inicio))
        self.btn_obtener.clicked.connect(self.obtener_trabajador)
        self.btn_actualizar.clicked.connect(self.modificar_trabajador)
        self.btn_retirar.clicked.connect(self.retirar_trabajador)
# ---------------
        self.r_dim2.toggled.connect(lambda: self.obtener_trabajador_area(self.r_dim2 , 1) )
        self.r_elab2.toggled.connect(lambda: self.obtener_trabajador_area(self.r_elab2, 1) )
        self.r_carp2.toggled.connect(lambda: self.obtener_trabajador_area(self.r_carp2 , 1) )
        self.r_pall2.toggled.connect(lambda: self.obtener_trabajador_area(self.r_pall2, 1) )

        self.r_dim3.toggled.connect(lambda: self.obtener_trabajador_area(self.r_dim3,2)   )
        self.r_elab3.toggled.connect(lambda: self.obtener_trabajador_area(self.r_elab3,2) )
        self.r_carp3.toggled.connect(lambda: self.obtener_trabajador_area(self.r_carp3,2) )
        self.r_pall3.toggled.connect(lambda: self.obtener_trabajador_area(self.r_pall3,2 ) )

    def iniciar_login(self):
        print('----- INICIANDO LOGIN --------')
        self.ventana_login = Login(self)
        self.ventana_login.show()
        salir = self.ventana_login.exec()
        if salir == 0:
            print(' ---- CERRAR APLICACION ------')
            sys.exit()
        elif salir == 1:
            print(' ---- LOGIN EXITOSO ------')
            usuario, conexion ,host, puerto  = self.ventana_login.obt_datos()
            self.usuario = usuario
            self.conexion = conexion
            self.host = host
            self.puerto = puerto
            print('USUARIO: ',usuario)
            print('------ MOSTRANDO MENU PRINCIPAL ------')

    def inicializar(self):
        
        actual = os.path.abspath(os.getcwd())
        actual = actual.replace('\\' , '/')
        ruta = actual + '/icono_imagen/madenco logo.png'
        foto = QPixmap(ruta)
        self.lb_logo.setPixmap(foto)
        self.stackedWidget.setCurrentWidget(self.inicio)

        if self.usuario[4] != 'SI':  #SI NO ES super usuario
            self.btn_gestion.hide()
            detalle = json.loads(self.usuario[7]) #SE CARGAN LAS FUNCIONES OTORGADAS
            func_area = detalle["area"]
            self.func_area = func_area
            print(func_area)
            if 'dimensionado' in func_area: #Solo si es personal de dimensionado, se muestra la opcion para gestionar trabajadores (*) (mejorar)
                self.btn_gestion.show()


    def reconectar(self):
        print('---- RECONECTANDO LA CONEXION AL SERVIDOR -----')
        try:
            self.conexion = rpyc.connect(self.host , self.puerto)
            self.lb_conexion.setText('CONECTADO')

        except ConnectionRefusedError:
            self.lb_conexion.setText('EL SERVIDOR NO RESPONDE')
            
        except socket.error:
            self.lb_conexion.setText('SERVIDOR FUERA DE RED')
    # BUSCAR ORDEN
    def buscar(self):
        self.dateEdit.setDate(datetime.now().date())
        self.dateEdit.setCalendarPopup(True)

        self.r_fecha.setChecked(True)
        self.tableWidget.setColumnWidth(0,70)
        self.tableWidget.setColumnWidth(1,70)
        self.tableWidget.setColumnWidth(2,100)
        self.tableWidget.setColumnWidth(3,170)
        self.tableWidget.setColumnWidth(4,120)
        self.tableWidget.setColumnWidth(5,100)
        self.tableWidget.setColumnWidth(6,100)

        self.stackedWidget.setCurrentWidget(self.buscar_orden)

    def buscar_ordenes_de_trabajo(self,area):
        if self.conexion:
            self.buscar_trabajadores(area)
            self.lb_tipo_orden.setText(area)
            self.tableWidget.setRowCount(0)

            #Busqueda por numero de orden
            if self.r_orden.isChecked(): 
                orden = self.txt_orden.text()
                try:
                    orden = int(orden)
                    if area == 'dimensionado':
                        consulta = self.conexion.root.buscar_orden_dim_numero(orden)
                    if area == 'elaboracion':
                        consulta = self.conexion.root.buscar_orden_general_numero(area,orden)
                    if area == 'carpinteria':
                        consulta = self.conexion.root.buscar_orden_general_numero(area,orden)
                    if area == 'pallets':
                        consulta = self.conexion.root.buscar_orden_general_numero(area,orden)

                    if consulta != None :
                        fila = self.tableWidget.rowCount()
                        self.tableWidget.insertRow(fila)
                        if area == 'dimensionado':

                            self.tableWidget.setItem(fila , 0 , QTableWidgetItem( str(consulta[0]) ))  #nro orden
                            self.tableWidget.setItem(fila , 1 , QTableWidgetItem('" '  + str(consulta[1]) + ' "' ))  #nro interno
                            self.tableWidget.setItem(fila , 2 , QTableWidgetItem( str(consulta[11]) ) )       #fecha creacion
                            self.tableWidget.setItem(fila , 3 , QTableWidgetItem( consulta[3]))       #nombre
                            self.tableWidget.setItem(fila , 4 , QTableWidgetItem( str(consulta[2]) ) )       #fecha venta
                            self.tableWidget.setItem(fila , 5 , QTableWidgetItem( str(consulta[5]) ) )       #fecha estimada
                            if consulta[19]:
                                self.tableWidget.setItem(fila , 6 , QTableWidgetItem( 'ANULADA' ) )       #estado
                            else:
                                self.tableWidget.setItem(fila , 6 , QTableWidgetItem( 'VALIDA' ) )       #estado

                        else:
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
                        QMessageBox.about(self,'Busqueda' ,f'Orden del area {area} NO encontrada')
                    
                except ValueError:
                    QMessageBox.about(self,'ERROR' ,'Ingrese solo numeros en el campo: NRO ORDEN')
                except EOFError:
                    QMessageBox.about(self,'ERROR','Se perdio la conexion con el servidor')

            # BUSCAR POR FECHA
            elif self.r_fecha.isChecked():
                date = self.dateEdit.date()
                aux = date.toPyDate()
                try:
                    if area == 'dimensionado':
                        datos = self.conexion.root.buscar_orden_dim_fecha( str(aux) )
                    if area == 'elaboracion':
                        datos = self.conexion.root.buscar_orden_general_fecha(area , str(aux))
                    if area == 'carpinteria':
                        datos = self.conexion.root.buscar_orden_general_fecha(area , str(aux))
                    if area == 'pallets':
                        datos = self.conexion.root.buscar_orden_general_fecha(area , str(aux))

                    if datos != ():
                        for dato in datos:
                            fila = self.tableWidget.rowCount()
                            self.tableWidget.insertRow(fila)

                            if area == 'dimensionado':
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
                        QMessageBox.about(self ,'Resultado', f'No se encontraron Ordenes de {area}')
                except EOFError:
                    QMessageBox.about(self,'ERROR','Se perdio la conexion con el servidor')

        else:
            QMessageBox.about(self ,'Conexion', 'No se ha establecido la conexion con el servidor')

    def buscar_trabajadores(self,area):
        print('BUSCANDO TRABAJADORES DEL AREA: ' + area)
        self.trabajadores = []
        if self.conexion:
            try:
                resultado = self.conexion.root.obtener_trabajador_activo(area)
                if resultado:
                    for item in resultado:
                        self.trabajadores.append( item[0] )
            except EOFError:
                pass #analisar

    # MODIFICAR ORDEN
    def inicializar_modificar_orden(self):
        seleccion = self.tableWidget.currentRow()
        area = self.lb_tipo_orden.text()

        if seleccion != -1:
            _item = self.tableWidget.item( seleccion, 0) 
            if _item:            
                nro_orden = self.tableWidget.item(seleccion, 0 ).text()
                print(f'------ VISTA MODIFICAR | ORDEN {area} | {str(nro_orden)} ---------')
           
                self.tableWidget_2.setColumnWidth(0,80)
                self.tableWidget_2.setColumnWidth(1,495)
                self.tableWidget_2.setColumnWidth(2,85 )
                self.date_seleccion.setCalendarPopup(True)
                self.date_seleccion.setDate( datetime.now().date() )
                
                self.combo_dimensionador.hide()
                self.combo_dimensionador.clear() #vaciar combobox
                self.tableWidget_2.setRowCount(0) #Vaciar la tabla. 
                self.btn_guardar.setDisabled(True)
                self.date_seleccion.setDisabled(True)
                self.opcion_datos.setCurrentIndex(0) 
                self.lb_nombre_orden.setText(area)
                self.area = area
                self.nro_orden = nro_orden
                self.cargar_datos_modificar_orden()

                self.stackedWidget.setCurrentWidget(self.modificar_orden)
                

            
        else:
            QMessageBox.about(self,'ERROR', 'Seleccione una FILA antes de continuar')

    def cargar_datos_modificar_orden(self):
        self.lb_dim.setText('NO ASIGNADO')   # TRABAJADOR
        self.lb_ing.setText( 'NO ASIGNADO')     # Fecha ingreso
        self.lb_real.setText('NO ASIGNADO')
        self.lb_fecha_termino.setText('NO ASIGNADO')

        for item in self.trabajadores:
                    self.combo_dimensionador.addItem( item ) #comboox de trabajadores

        if self.area == 'dimensionado':
            try:
                resultado = self.conexion.root.buscar_orden_dim_numero(self.nro_orden)

                self.lb_orden.setText( str(resultado[0]) ) 
                self.lb_interno.setText(str( resultado[1] ))

                if resultado[2]:
                    date = datetime.fromisoformat( str( resultado[2] ) )
                    self.lb_fecha_venta.setText( str(date.strftime("%d-%m-%Y %H:%M:%S") ) ) #fecha venta
                else: 
                    date = datetime.now()
                    #self.lb_fecha_venta.setText(str(date.strftime("%d-%m-%Y %H:%M:%S")))
                    self.lb_fecha_venta.setText('No encontrada')

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
                self.detalle = resultado[6]

                cantidades = detalle["cantidades"]
                descripciones = detalle["descripciones"]
                valores_neto = detalle["valores_neto"]
                j = 0
                while j < len( cantidades ):
                    fila = self.tableWidget_2.rowCount()
                    self.tableWidget_2.insertRow(fila)
                    self.tableWidget_2.setItem(fila , 0 , QTableWidgetItem( str( cantidades[j] )) ) 
                    self.tableWidget_2.setItem(fila , 1 , QTableWidgetItem( descripciones[j] ) )
                    self.tableWidget_2.setItem(fila , 2 , QTableWidgetItem( str( valores_neto[j] )) ) 
                    j+=1 

                try:
                    fecha_termino = detalle['fecha_termino']  # FECHA TERMINO
                    fecha_termino = datetime.fromisoformat(  fecha_termino )
                    self.lb_fecha_termino.setText( str(fecha_termino.strftime("%d-%m-%Y"))  )
                except KeyError:
                    print('No se detecto fecha de termino asignada.')

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
                    self.lb_real.setText( str(aux2.strftime("%d-%m-%Y"))  )     #FECHA REAL
                if resultado[15]:
                    self.lb_vend.setText(resultado[15])      #vendedor
                else:
                    self.lb_vend.setText('NO ASIGNADO')      #vendedor

                if resultado[16]:
                    self.lb_dim.setText(resultado[16])      #DIMENSIONADOR
                
                if resultado[17]:
                    aux3 = datetime.fromisoformat(  str(resultado[17]) )
                    self.lb_ing.setText( str(aux3.strftime("%d-%m-%Y"))  )     #fecha ingreso
            
                
            except EOFError:
                QMessageBox.about(self, 'ERROR', 'Se perdio la conexion con el servidor')
        else:
            
            try:
                resultado = self.conexion.root.buscar_orden_general_numero( self.area, self.nro_orden)

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
                self.detalle = resultado[11]

                cantidades = detalle["cantidades"]
                descripciones = detalle["descripciones"]
                valores_neto = detalle["valores_neto"]
                j = 0
                while j < len( cantidades ):
                    fila = self.tableWidget_2.rowCount()
                    self.tableWidget_2.insertRow(fila)
                    self.tableWidget_2.setItem(fila , 0 , QTableWidgetItem( str( cantidades[j] )) ) 
                    self.tableWidget_2.setItem(fila , 1 , QTableWidgetItem( descripciones[j] ) )
                    self.tableWidget_2.setItem(fila , 2 , QTableWidgetItem( str( valores_neto[j] )) ) 
                    j+=1 
                try:
                    fecha_termino = detalle['fecha_termino']
                    fecha_termino = datetime.fromisoformat(  fecha_termino ) # FECHA TERMINO
                    self.lb_fecha_termino.setText( str(fecha_termino.strftime("%d-%m-%Y"))  )
                except KeyError:
                    print('No se detecto fecha de termino asignada.')

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

    def guardar(self):
        opcion = self.opcion_datos.currentText()
        index =  self.opcion_datos.currentIndex()
        print(f'----- GUARDANDO --> {opcion} ------')

        if index == 1 : # REGISTRAR FECHA INGRESO Y PERSONAL
            trabajador = self.combo_dimensionador.currentText()
            fecha_ingreso = str( self.date_seleccion.date().toPyDate() )
            print(f'ORDEN: {self.area} | NRO ORDEN: {str(self.nro_orden)} \nFecha: {fecha_ingreso} | TRABAJADORES: {trabajador}')
            if self.area == 'dimensionado':
                
                if self.conexion.root.actualizar_orden_dim2(self.nro_orden , fecha_ingreso, trabajador ):
                    self.lb_dim.setText(trabajador)
                    fecha = (datetime.fromisoformat(fecha_ingreso)).strftime("%d-%m-%Y")
                    print(fecha)
                    self.lb_ing.setText(fecha)
                    QMessageBox.about(self,'EXITO',f'Fecha de ingreso y dimensionador asignados correctamente. | {self.area}')
                else:
                    QMessageBox.about(self,'ERROR','La orden de dimensionado NO se actualizo debido a que ningun texto fue modificado')

            else: #SI NO ES DE DIMENSIONADO , OSEA ELAB , CARP Y PALL
                if self.conexion.root.actualizar_orden_ingreso_trabajador(self.area ,str(self.nro_orden) , fecha_ingreso ,trabajador ):
                    self.lb_dim.setText(trabajador)
                    fecha = (datetime.fromisoformat(fecha_ingreso)).strftime("%d-%m-%Y")
                    print(fecha)
                    self.lb_ing.setText(fecha)
                    QMessageBox.about(self,'EXITO',f'Fecha ingreso y trabajador asignados correctamente | {self.area}')
                else:
                    QMessageBox.about(self,'ERROR','La orden de '+ self.area +' NO se actualizo debido a que ningun DATO fue modificado o se produjo algun error interno.')

        elif index == 2: # REGISTRAR FECHA REAL
            fecha_real = str (self.date_seleccion.date().toPyDate() )
            
            if self.conexion.root.actualizar_orden_fecha_real( self.area , str(self.nro_orden), fecha_real):
                fecha = (datetime.fromisoformat(fecha_real)).strftime("%d-%m-%Y")
                print(fecha)
                self.lb_real.setText(str(fecha))
                QMessageBox.about(self,'EXITO','Fecha real asignada correctamente')
            else:
                QMessageBox.about(self,'ERROR','La orden de '+ self.area +' NO se actualizo debido a que ningun texto fue modificado o se produjo un error interno')    
            

        elif index == 3: # REGISTRAR FECHA TERMINO
            Y = 0
            fecha_real = str(self.date_seleccion.date().toPyDate() )
            detalle = json.loads(self.detalle)
            detalle['fecha_termino'] = fecha_real
            new_detalle = json.dumps(detalle)
            print(new_detalle)
            if self.conexion.root.actualizar_detalle_orden_trabajo( self.area , new_detalle , self.nro_orden):
                fecha = (datetime.fromisoformat(fecha_real)).strftime("%d-%m-%Y")
                print(fecha)
                self.lb_fecha_termino.setText(str(fecha))
                QMessageBox.about(self,'EXITO','Fecha de termino asignada correctamente')
            else:
                QMessageBox.about(self,'ERROR','La orden de '+ self.area +' NO se actualizo debido a que ningun texto fue modificado o se produjo un error interno')    
            


        print(f' ---- FIN --> {opcion} --------')

    def mostrar_combo_trabajadores(self):
        index = self.opcion_datos.currentIndex()
        print('index, ' ,index)
        if index == 0:
            self.combo_dimensionador.setDisabled(True)
            self.btn_guardar.setDisabled(True)
            self.date_seleccion.setDisabled(True)
        else:
            self.combo_dimensionador.setDisabled(False)
            self.btn_guardar.setDisabled(False)
            self.date_seleccion.setDisabled(False)

        if index == 1 :
            self.combo_dimensionador.show()
        else:
            self.combo_dimensionador.hide()
        

        

    # GESTIONAR TRABAJADORES
    def gestionar(self):
        self.r_inicio.setDate( datetime.now().date() )
        self.r_termino.setDate( datetime.now().date() )
        self.r_inicio.setCalendarPopup(True)
        self.r_termino.setCalendarPopup(True)
        self.m_inicio.setCalendarPopup(True)
        self.r_telefono.setMaxLength(10)
        self.m_telefono.setMaxLength(10)

        # LIMPIAR CACHE
        self.box_dimensionador_2.clear()
        self.box_dimensionador.clear()
        self.r_nombre.setText('')
        self.r_telefono.setText('')
        self.m_nombre.setText('')
        self.m_telefono.setText('')

        self.r_dim2.setChecked(False)
        self.r_elab2.setChecked(False)
        self.r_carp2.setChecked(False)
        self.r_pall2.setChecked(False)

        self.stackedWidget.setCurrentWidget(self.gestionar_trabajador)
    

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
                    self.trabajadores = resultado
                    for item in resultado:
                        if box == 1:
                            self.box_dimensionador.addItem(item[0])
                        elif box == 2:
                            self.box_dimensionador_2.addItem(item[0])

                except EOFError:
                    QMessageBox.about(self,'CONEXION','No se pudo obtener la lista de trabajadores. El servidor no responde') 
            
            else:
                QMessageBox.about(self,'CONEXION','No ha establecido conexion con el servidor.') 

        else:
            area = radio.text()
            print('no buscando: ' + area)
    
    def obtener_trabajador(self):
        nombre = self.box_dimensionador.currentText()
        for datos in self.trabajadores:
            if datos[0] == nombre:
                self.m_nombre.setText(datos[0])
                self.m_telefono.setText(str(datos[1]))
                aux =   datetime.fromisoformat( str(datos[2]) )  
                self.m_inicio.setDate( aux )
                break
    def registrar_trabajador(self):
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
                                self.stackedWidget.setCurrentWidget(self.inicio)
                                
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
    
    def modificar_trabajador(self):
        nombre = self.box_dimensionador.currentText()
        nuevo_nombre = self.m_nombre.text()
        nuevo_telefono = self.m_telefono.text()
        nuevo_inicio = self.m_inicio.date()
        nuevo_inicio = nuevo_inicio.toPyDate()
        nro_dimensionador = 0
        for datos in self.trabajadores:
            if datos[0] == nombre:
                nro_dimensionador = datos[3]
                print(nro_dimensionador)
                break

        if self.conexion:
            if self.trabajadores:
                if nuevo_nombre != '' :
                    if nuevo_telefono != '' :
                        try:
                            nuevo_telefono = int(nuevo_telefono)
                            if self.conexion.root.actualizar_trabajador(nuevo_nombre,nuevo_telefono, str(nuevo_inicio) , nro_dimensionador ) :
                                QMessageBox.about(self,'EXITO','Trabajador ACTUALIZADO correctamente')
                                self.stackedWidget.setCurrentWidget(self.inicio)
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
                QMessageBox.about(self,'ERROR','No se encontraron trabajadores ACTIVOS') 
        else:
            QMessageBox.about(self,'CONEXION','No ha establecido conexion con el servidor.') 

    def retirar_trabajador(self):
        nombre = self.box_dimensionador_2.currentText()    
        termino = self.r_termino.date().toPyDate()   
        nro_dimensionador = 0
        for datos in self.trabajadores:
            if datos[0] == nombre:
                nro_dimensionador = datos[3]
                print(nro_dimensionador)
                break

        if self.conexion:
            if self.trabajadores:
                try:
                    if self.conexion.root.retirar_trabajador(nro_dimensionador , str( termino ) ):
                        QMessageBox.about(self,'EXITO','Trabajador RETIRADO correctamente')
                        self.stackedWidget.setCurrentWidget(self.inicio)
                    else:
                        QMessageBox.about(self,'ERROR','El Dimensionador no se retiro correctamente. Analisar posibles causas...')     
                except EOFError:
                    QMessageBox.about(self,'CONEXION','El servidor no responde')     
            else: 
                QMessageBox.about(self,'ERROR','No se encontraron trabajadores ACTIVOS') 
        else:
            QMessageBox.about(self,'CONEXION','No ha establecido conexion con el servidor.') 



    def salir(self):
        print('saliendo de la app')
        sys.exit(0)
        
class InputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.host = QLineEdit(self)
        self.puerto = QLineEdit(self)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

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
    app.setWindowIcon(QIcon('icono_imagen/area_logo2.png'))
    
    inicio = Personal() # INICIA EL PERSONAL DE AREA
    inicio.show()
    sys.exit(app.exec_())