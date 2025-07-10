import io
import psycopg2

class PostgresConn:
    def __init__(self, host, database, user, password, port=5432):
        self.conn_params = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port
        }
        self.connection = None


    def connect(self):
        if self.connection is None or self.connection.closed:
            self.connection = psycopg2.connect(**self.conn_params)
        return self.connection


    def close(self):
        if self.connection and not self.connection.closed:
            self.connection.close()
            self.connection = None


    def execute(self, query, params=None, commit=False):
        conn = self.connect()
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if commit:
                conn.commit()


    def fetchall(self, query, params=None):
        conn = self.connect()
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


    def fetchone(self, query, params=None):
        conn = self.connect()
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def upload_dataframe(self, df, table_name):
        conn = self.connect()
        cur = conn.cursor()
        buffer = io.StringIO()

        # Exporta amb header, perquè COPY conegui les columnes
        df.to_csv(buffer, index=False, header=True)
        buffer.seek(0)

        columns = list(df.columns)
        cols_sql = ", ".join(columns)

        copy_sql = f"COPY {table_name} ({cols_sql}) FROM STDIN WITH CSV HEADER"

        try:
            cur.copy_expert(copy_sql, buffer)
            conn.commit()
            print(f"✔️ Dades pujades a la taula '{table_name}' ({len(df)} files).")
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Error pujant a la taula '{table_name}': {e}")
        finally:
            cur.close()
        