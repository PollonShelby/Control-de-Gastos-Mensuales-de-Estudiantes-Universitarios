import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'Marcelo12*', 
            'database': 'control_gastos_db',
            'port': 3306
        }

    def get_connection(self):
        try:
            return mysql.connector.connect(**self.config)
        except Error as err:
            print(f"Error MySQL: {err}")
            return None

    def get_categorias(self):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre FROM categorias ORDER BY nombre ASC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    def get_gastos(self):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT g.id, g.concepto, g.monto, g.fecha, g.dias_detalle, c.nombre AS categoria
            FROM gastos g
            INNER JOIN categorias c ON g.categoria_id = c.id
            ORDER BY g.fecha DESC, g.id DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    def get_gasto(self, gasto_id):
        conn = self.get_connection()
        if not conn: return None
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM gastos WHERE id = %s", (gasto_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row

    def registrar_gasto(self, concepto, monto, fecha, categoria_id, dias_detalle=None):
        conn = self.get_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            query = "INSERT INTO gastos (concepto, monto, fecha, categoria_id, dias_detalle) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (concepto, monto, fecha, categoria_id, dias_detalle))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as err:
            print(f"Error al registrar: {err}")
            conn.close()
            return False

    def actualizar_dias_gasto(self, gasto_id, nuevo_concepto, nuevo_monto, nuevos_dias_detalle):
        conn = self.get_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            query = "UPDATE gastos SET concepto = %s, monto = %s, dias_detalle = %s WHERE id = %s"
            cursor.execute(query, (nuevo_concepto, nuevo_monto, nuevos_dias_detalle, gasto_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as err:
            print(err)
            conn.close()
            return False

    def eliminar_gasto(self, gasto_id):
        conn = self.get_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM gastos WHERE id = %s", (gasto_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error:
            conn.close()
            return False