import os
import re
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QDoubleSpinBox, QComboBox, 
    QDateEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QGroupBox, QAbstractItemView,
    QProgressBar, QDialog, QGridLayout, QCheckBox
)
from PySide6.QtCore import Qt, QDate
from database.connection import Database

class DialogoCalendario(QDialog):
    def __init__(self, parent, fecha_base, dias_activos):
        super().__init__(parent)
        self.setWindowTitle(f"Editar Asistencia - {fecha_base.toString('MM/yyyy')}")
        self.setModal(True)
        self.setFixedSize(380, 250)
        self.dias_seleccionados = []
        
        layout = QVBoxLayout(self)
        lbl_instruccion = QLabel("Desmarca los días que NO asististe:")
        lbl_instruccion.setStyleSheet("font-weight: bold; margin-bottom: 5px; color: #2C3E50;")
        layout.addWidget(lbl_instruccion)
        
        grid = QGridLayout()
        grid.setSpacing(5)
        dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for i, d in enumerate(dias_semana):
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #7F8C8D; font-weight: bold; font-size: 11px;")
            grid.addWidget(lbl, 0, i)
            
        dias_totales = fecha_base.daysInMonth()
        primer_dia_semana = QDate(fecha_base.year(), fecha_base.month(), 1).dayOfWeek() - 1
        
        self.checkboxes = {}
        row, col = 1, primer_dia_semana
        
        for dia in range(1, dias_totales + 1):
            chk = QCheckBox(str(dia))
            chk.setStyleSheet("spacing: 0px; margin: 2px;")
            if dia in dias_activos:
                chk.setChecked(True)
            self.checkboxes[dia] = chk
            grid.addWidget(chk, row, col, alignment=Qt.AlignCenter)
            
            col += 1
            if col > 6:
                col = 0
                row += 1
                
        layout.addLayout(grid)
        layout.addStretch()
        
        btn_aceptar = QPushButton("Confirmar Cambios")
        btn_aceptar.setCursor(Qt.PointingHandCursor)
        btn_aceptar.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold; padding: 8px;")
        btn_aceptar.clicked.connect(self.aceptar)
        layout.addWidget(btn_aceptar)

    def aceptar(self):
        self.dias_seleccionados = [dia for dia, chk in self.checkboxes.items() if chk.isChecked()]
        self.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.setWindowTitle("Control y Gestión de Gastos Universitarios")
        self.resize(1200, 780)
        
        self.dias_seleccionados_actuales = []
        
        self._init_ui()
        self._aplicar_estilos()
        self._cargar_categorias()
        self._actualizar_lista_meses()
        self._cargar_gastos()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # CABECERA
        header_layout = QHBoxLayout()
        lbl_titulo = QLabel("Gestión Financiera Mensual")
        lbl_titulo.setObjectName("tituloPrincipal")
        
        layout_presupuesto = QHBoxLayout()
        layout_presupuesto.addWidget(QLabel("Presupuesto del Mes:"))
        self.spin_presupuesto = QDoubleSpinBox()
        self.spin_presupuesto.setRange(1.0, 999999.0)
        self.spin_presupuesto.setPrefix("C$ ")
        self.spin_presupuesto.setValue(3000.00) 
        self.spin_presupuesto.valueChanged.connect(self._cargar_gastos)
        layout_presupuesto.addWidget(self.spin_presupuesto)

        header_layout.addWidget(lbl_titulo)
        header_layout.addStretch()
        header_layout.addLayout(layout_presupuesto)
        main_layout.addLayout(header_layout)

        # BARRA DE PROGRESO Y TEXTOS
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.progress_bar)

        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 5, 0, 10)
        self.lbl_alerta = QLabel("") 
        self.lbl_alerta.setStyleSheet("color: #E74C3C; font-weight: bold; font-size: 14px;")
        self.lbl_diario = QLabel("") 
        self.lbl_diario.setStyleSheet("color: #2980B9; font-weight: bold; font-size: 14px;")
        
        info_layout.addStretch()
        info_layout.addWidget(self.lbl_alerta)
        info_layout.addSpacing(30)
        info_layout.addWidget(self.lbl_diario)
        info_layout.addStretch()
        main_layout.addLayout(info_layout)

        # FORMULARIO DE INGRESO (SOLUCIÓN DEL DISEÑO USANDO GRID)
        form_group = QGroupBox("Registrar Gasto o Proyección Mensual")
        form_layout = QGridLayout(form_group)
        form_layout.setSpacing(10)

        # Fila 0: Etiquetas (Todas perfectamente alineadas)
        form_layout.addWidget(QLabel("Concepto:"), 0, 0)
        form_layout.addWidget(QLabel("Detalle:"), 0, 1)
        form_layout.addWidget(QLabel("Monto (día):"), 0, 2)
        form_layout.addWidget(QLabel("Frecuencia:"), 0, 3)
        form_layout.addWidget(QLabel("Categoría:"), 0, 4)
        form_layout.addWidget(QLabel("Fecha base:"), 0, 5)

        # Fila 1: Controles interactivos
        self.txt_concepto = QLineEdit()
        self.txt_concepto.setPlaceholderText("Ej: Pasaje...")
        form_layout.addWidget(self.txt_concepto, 1, 0)
        
        self.combo_detalle = QComboBox()
        self.combo_detalle.addItems(["", "Ida", "Vuelta", "Ida y Vuelta", "Snack", "Materiales", "Otros"])
        form_layout.addWidget(self.combo_detalle, 1, 1)

        self.spin_monto = QDoubleSpinBox()
        self.spin_monto.setRange(0.01, 99999.99)
        self.spin_monto.setPrefix("C$ ")
        self.spin_monto.setDecimals(2)
        form_layout.addWidget(self.spin_monto, 1, 2)

        # Frecuencia compleja agrupada horizontalmente en el grid
        sub_layout_frec = QHBoxLayout()
        sub_layout_frec.setContentsMargins(0, 0, 0, 0)
        self.combo_frecuencia = QComboBox()
        self.combo_frecuencia.addItems(["Gasto Único", "Días de clase (Lun a Vie)", "Fines de semana", "Diario (Todo el mes)"])
        self.combo_frecuencia.currentTextChanged.connect(self._actualizar_dias_frecuencia)
        sub_layout_frec.addWidget(self.combo_frecuencia)
        
        self.btn_calendario = QPushButton("🗓️")
        self.btn_calendario.setCursor(Qt.PointingHandCursor)
        self.btn_calendario.setVisible(False)
        self.btn_calendario.clicked.connect(self._abrir_calendario)
        sub_layout_frec.addWidget(self.btn_calendario)
        
        self.lbl_dias_calc = QLabel("")
        self.lbl_dias_calc.setStyleSheet("color: #7F8C8D; font-weight: bold; margin-left: 5px;")
        sub_layout_frec.addWidget(self.lbl_dias_calc)
        form_layout.addLayout(sub_layout_frec, 1, 3)

        self.combo_categoria = QComboBox()
        form_layout.addWidget(self.combo_categoria, 1, 4)
        
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.dateChanged.connect(self._actualizar_dias_frecuencia)
        form_layout.addWidget(self.date_picker, 1, 5)

        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setCursor(Qt.PointingHandCursor)
        self.btn_guardar.clicked.connect(self._guardar_gasto)
        form_layout.addWidget(self.btn_guardar, 1, 6)

        # Proporciones del Grid
        form_layout.setColumnStretch(0, 3)
        form_layout.setColumnStretch(1, 2)
        form_layout.setColumnStretch(2, 2)
        form_layout.setColumnStretch(3, 4)
        form_layout.setColumnStretch(4, 2)
        form_layout.setColumnStretch(5, 2)

        main_layout.addWidget(form_group)

        # TABLA Y FILTRO
        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Filtrar Registros por Mes:"))
        self.combo_filtro_mes = QComboBox()
        self.combo_filtro_mes.setMinimumWidth(180)
        self.combo_filtro_mes.currentIndexChanged.connect(self._cargar_gastos)
        filtro_layout.addWidget(self.combo_filtro_mes)
        filtro_layout.addStretch()
        main_layout.addLayout(filtro_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Día y Fecha", "Concepto de Gasto", "Categoría", "Monto Total"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        main_layout.addWidget(self.table)

        # BOTONES INFERIORES: EDITAR Y ELIMINAR
        bottom_layout = QHBoxLayout()
        self.lbl_total = QLabel("Total Mostrado: C$ 0.00")
        self.lbl_total.setObjectName("etiquetaTotal")
        
        self.btn_editar = QPushButton("✏️ Editar Asistencia")
        self.btn_editar.setCursor(Qt.PointingHandCursor)
        self.btn_editar.setStyleSheet("background-color: #F39C12; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        self.btn_editar.clicked.connect(self._editar_gasto)

        self.btn_eliminar = QPushButton("🗑️ Eliminar Seleccionado")
        self.btn_eliminar.setObjectName("btnEliminar")
        self.btn_eliminar.setCursor(Qt.PointingHandCursor)
        self.btn_eliminar.setStyleSheet("background-color: #E74C3C; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        self.btn_eliminar.clicked.connect(self._eliminar_gasto)

        bottom_layout.addWidget(self.lbl_total)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_editar)
        bottom_layout.addWidget(self.btn_eliminar)
        main_layout.addLayout(bottom_layout)

    def _aplicar_estilos(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        qss_path = os.path.join(base_dir, "assets", "style.qss")
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except: pass

    def _cargar_categorias(self):
        self.combo_categoria.clear()
        for cat in self.db.get_categorias():
            self.combo_categoria.addItem(cat["nombre"], cat["id"])

    def _actualizar_lista_meses(self):
        self.combo_filtro_mes.blockSignals(True)
        self.combo_filtro_mes.clear()
        self.combo_filtro_mes.addItem("Mostrar Todos los Gastos", "TODOS")
        
        meses_unicos = {str(g["fecha"])[:7] for g in self.db.get_gastos()}
        nombres = {"01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril", "05": "Mayo", "06": "Junio", 
                   "07": "Julio", "08": "Agosto", "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"}
            
        for m in sorted(list(meses_unicos), reverse=True):
            anio, mes_num = m.split('-') 
            self.combo_filtro_mes.addItem(f"{nombres.get(mes_num, mes_num)} {anio}", m)
            
        index = self.combo_filtro_mes.findData(QDate.currentDate().toString("yyyy-MM"))
        if index >= 0: self.combo_filtro_mes.setCurrentIndex(index)
        self.combo_filtro_mes.blockSignals(False)

    def _actualizar_dias_frecuencia(self):
        frecuencia = self.combo_frecuencia.currentText()
        fecha_sel = self.date_picker.date()
        self.dias_seleccionados_actuales = []
        
        if frecuencia == "Gasto Único":
            self.btn_calendario.setVisible(False)
            self.lbl_dias_calc.setText("")
        else:
            self.btn_calendario.setVisible(True)
            for d in range(1, fecha_sel.daysInMonth() + 1):
                dia_semana = QDate(fecha_sel.year(), fecha_sel.month(), d).dayOfWeek()
                if frecuencia == "Días de clase (Lun a Vie)" and dia_semana <= 5:
                    self.dias_seleccionados_actuales.append(d)
                elif frecuencia == "Fines de semana" and dia_semana > 5:
                    self.dias_seleccionados_actuales.append(d)
                elif frecuencia == "Diario (Todo el mes)":
                    self.dias_seleccionados_actuales.append(d)
            self.lbl_dias_calc.setText(f"({len(self.dias_seleccionados_actuales)} días)")

    def _abrir_calendario(self):
        dialog = DialogoCalendario(self, self.date_picker.date(), self.dias_seleccionados_actuales)
        if dialog.exec() == QDialog.Accepted:
            self.dias_seleccionados_actuales = dialog.dias_seleccionados
            self.lbl_dias_calc.setText(f"({len(self.dias_seleccionados_actuales)} días)")
            self.lbl_dias_calc.setStyleSheet("color: #27AE60; font-weight: bold; margin-left: 5px;")

    def _cargar_gastos(self):
        if not hasattr(self, 'combo_filtro_mes'): return
        todos_los_gastos = self.db.get_gastos()
        filtro = self.combo_filtro_mes.currentData()
        
        gastos_filtrados = [g for g in todos_los_gastos if str(g["fecha"]).startswith(filtro)] if filtro != "TODOS" else todos_los_gastos
        self.table.setRowCount(len(gastos_filtrados))
        total = 0.0
        dias_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

        for row_idx, gasto in enumerate(gastos_filtrados):
            total += float(gasto["monto"])
            fecha_obj = QDate.fromString(str(gasto["fecha"]), "yyyy-MM-dd")
            fecha_texto = f"{dias_es[fecha_obj.dayOfWeek() - 1]}, {fecha_obj.toString('dd/MM/yyyy')}"
            
            concepto_texto = gasto["concepto"]
            if gasto.get("dias_detalle"):
                concepto_texto += " 📅"
                
            concepto_item = QTableWidgetItem(concepto_texto)
            if gasto.get("dias_detalle"):
                concepto_item.setToolTip(f"Días asistidos: {gasto['dias_detalle']}")
                
            monto_item = QTableWidgetItem(f"C$ {float(gasto['monto']):.2f}")
            monto_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            id_item = QTableWidgetItem(str(gasto["id"]))
            id_item.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row_idx, 0, id_item)
            self.table.setItem(row_idx, 1, QTableWidgetItem(fecha_texto))
            self.table.setItem(row_idx, 2, concepto_item)
            self.table.setItem(row_idx, 3, QTableWidgetItem(gasto["categoria"]))
            self.table.setItem(row_idx, 4, monto_item)

        self.lbl_total.setText(f"Total Mostrado: C$ {total:.2f}")
        
        presupuesto = self.spin_presupuesto.value()
        porcentaje = (total / presupuesto) * 100 if presupuesto > 0 else 0
        self.progress_bar.setValue(min(max(int(porcentaje), 0), 100))

        if porcentaje >= 100:
            color, alerta = "#C0392B", "⚠️ Has agotado tu presupuesto mensual."
        elif porcentaje >= 80:
            color, alerta = "#E67E22", f"⚠️ Cuidado: Has consumido el {porcentaje:.1f}% del presupuesto."
        else:
            color, alerta = "#27AE60", ""
            
        self.lbl_alerta.setText(alerta)
        self.progress_bar.setStyleSheet(f"QProgressBar {{ border: 1px solid #BDC3C7; border-radius: 5px; text-align: center; background-color: #ECF0F1; color: #2C3E50; font-weight: bold; height: 25px; }} QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}")

        mes_actual_str = QDate.currentDate().toString("yyyy-MM")
        if filtro == mes_actual_str or filtro == "TODOS":
            dias_restantes = QDate.currentDate().daysInMonth() - QDate.currentDate().day() + 1 
            dinero_restante = presupuesto - total
            if dinero_restante > 0 and dias_restantes > 0:
                self.lbl_diario.setText(f"💡 Restan C$ {dinero_restante:.2f}. Límite sugerido: C$ {dinero_restante / dias_restantes:.2f} / día.")
            else:
                self.lbl_diario.setText("❌ Ya no cuentas con límite diario sugerido.")
        else:
            self.lbl_diario.setText("")

    def _guardar_gasto(self):
        concepto_base = self.txt_concepto.text().strip()
        detalle = self.combo_detalle.currentText()
        frecuencia = self.combo_frecuencia.currentText()
        monto_ingresado = self.spin_monto.value()
        fecha_str = self.date_picker.date().toString("yyyy-MM-dd")
        categoria_id = self.combo_categoria.currentData()

        if not concepto_base:
            return QMessageBox.warning(self, "Validación", "Por favor ingresa un concepto.")

        concepto_final = f"{concepto_base} - {detalle}" if detalle else concepto_base
        monto_final = monto_ingresado
        dias_bd = None

        if frecuencia != "Gasto Único":
            multiplicador = len(self.dias_seleccionados_actuales)
            if multiplicador == 0:
                return QMessageBox.warning(self, "Aviso", "No has dejado ningún día marcado.")
                
            monto_final = monto_ingresado * multiplicador
            dias_bd = ", ".join(map(str, sorted(self.dias_seleccionados_actuales)))
            concepto_final += f" [x{multiplicador} días]"

        if self.db.registrar_gasto(concepto_final, monto_final, fecha_str, categoria_id, dias_bd):
            self.txt_concepto.clear()
            self.combo_frecuencia.setCurrentIndex(0)
            self.spin_monto.setValue(0.0)
            self._actualizar_lista_meses() 
            self._cargar_gastos()
        else:
            QMessageBox.critical(self, "Error", "Fallo al registrar en la base de datos.")

    def _editar_gasto(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Selecciona en la tabla el gasto que deseas editar.")
            
        gasto_id = int(self.table.item(row, 0).text())
        gasto = self.db.get_gasto(gasto_id)
        
        # Validación: Solo se editan los que tienen días de calendario guardados
        if not gasto or not gasto.get("dias_detalle"):
            return QMessageBox.information(self, "Aviso", "Solo puedes editar la asistencia de los gastos mensuales proyectados. Para gastos únicos usa el botón Eliminar.")
            
        dias_actuales = [int(d.strip()) for d in gasto["dias_detalle"].split(",")]
        if len(dias_actuales) == 0: return
        
        # Algoritmo matemático para recuperar cuánto valía el día individualmente
        monto_total_actual = float(gasto["monto"])
        monto_diario_original = monto_total_actual / len(dias_actuales)
        fecha_base = QDate.fromString(str(gasto["fecha"]), "yyyy-MM-dd")
        
        dialog = DialogoCalendario(self, fecha_base, dias_actuales)
        if dialog.exec() == QDialog.Accepted:
            nuevos_dias = dialog.dias_seleccionados
            if len(nuevos_dias) == 0:
                return QMessageBox.warning(self, "Aviso", "No puedes dejar el registro sin días. Si quieres borrarlo usa el botón rojo de Eliminar.")
            
            # Recalcular el nuevo dinero
            nuevo_monto_total = monto_diario_original * len(nuevos_dias)
            nuevos_dias_str = ", ".join(map(str, sorted(nuevos_dias)))
            
            # Actualizar la etiqueta del concepto (Ej: cambia de [x21 días] a [x20 días])
            nuevo_concepto = re.sub(r'\[x\d+ días\]', f'[x{len(nuevos_dias)} días]', gasto["concepto"])
            
            if self.db.actualizar_dias_gasto(gasto_id, nuevo_concepto, nuevo_monto_total, nuevos_dias_str):
                self._cargar_gastos()
                QMessageBox.information(self, "Actualizado", f"Asistencia editada con éxito.\nEl nuevo total es de C$ {nuevo_monto_total:.2f}")
            else:
                QMessageBox.critical(self, "Error", "No se pudo actualizar en la base de datos.")

    def _eliminar_gasto(self):
        row = self.table.currentRow()
        if row < 0: return QMessageBox.warning(self, "Aviso", "Selecciona una fila para eliminar.")
        gasto_id = int(self.table.item(row, 0).text())
        if QMessageBox.question(self, "Confirmar", "¿Eliminar el registro seleccionado?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.eliminar_gasto(gasto_id)
            self._actualizar_lista_meses() 
            self._cargar_gastos()