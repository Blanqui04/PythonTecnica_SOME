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
    
    def get_table_primary_keys(self, table_name):
        """Get primary key columns for a table"""
        query = """
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid
                           AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = %s::regclass
          AND i.indisprimary;
        """
        try:
            result = self.fetchall(query, (table_name,))
            return [row[0] for row in result]
        except Exception:
            return []
    
    def upload_dataframe(self, df, table_name, mode='upsert'):
        """Upload dataframe with support for INSERT, UPSERT, or REPLACE modes"""
        conn = self.connect()
        cur = conn.cursor()
        
        try:
            if mode == 'insert':
                # Original INSERT behavior (will fail on duplicates)
                self._upload_insert_only(df, table_name, cur, conn)
            elif mode == 'upsert':
                # UPSERT behavior (INSERT or UPDATE on conflict)
                self._upload_upsert(df, table_name, cur, conn)
            elif mode == 'replace':
                # DELETE existing and INSERT new
                self._upload_replace(df, table_name, cur, conn)
            else:
                raise ValueError(f"Invalid mode: {mode}. Use 'insert', 'upsert', or 'replace'")
                
            print(f"✔️ Dades pujades a la taula '{table_name}' ({len(df)} files) - Mode: {mode}")
            
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Error pujant a la taula '{table_name}': {e}")
        finally:
            cur.close()
    
    def _upload_insert_only(self, df, table_name, cur, conn):
        """Original INSERT-only behavior"""
        buffer = io.StringIO()
        df.to_csv(buffer, index=False, header=True)
        buffer.seek(0)
        
        columns = list(df.columns)
        cols_sql = ", ".join(columns)
        copy_sql = f"COPY {table_name} ({cols_sql}) FROM STDIN WITH CSV HEADER"
        
        cur.copy_expert(copy_sql, buffer)
        conn.commit()
    
    def _upload_upsert(self, df, table_name, cur, conn):
        """UPSERT behavior using ON CONFLICT DO UPDATE"""
        # Get primary keys for the table
        primary_keys = self.get_table_primary_keys(table_name)
        
        if not primary_keys:
            # Fallback to INSERT if no primary keys found
            print(f"⚠️ No primary keys found for {table_name}, using INSERT mode")
            return self._upload_insert_only(df, table_name, cur, conn)
        
        columns = list(df.columns)
        cols_sql = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        
        # Build conflict resolution
        conflict_cols = ", ".join(primary_keys)
        update_cols = ", ".join([f"{col} = EXCLUDED.{col}" for col in columns if col not in primary_keys])
        
        if update_cols:  # Only if there are non-primary key columns to update
            upsert_sql = f"""
            INSERT INTO {table_name} ({cols_sql}) 
            VALUES ({placeholders})
            ON CONFLICT ({conflict_cols}) 
            DO UPDATE SET {update_cols}
            """
        else:  # All columns are primary keys, just ignore conflicts
            upsert_sql = f"""
            INSERT INTO {table_name} ({cols_sql}) 
            VALUES ({placeholders})
            ON CONFLICT ({conflict_cols}) 
            DO NOTHING
            """
        
        # Execute batch insert
        data = [tuple(row) for row in df.values]
        cur.executemany(upsert_sql, data)
        conn.commit()
    
    def _upload_replace(self, df, table_name, cur, conn):
        """Replace all data in table"""
        # First, delete all existing data
        cur.execute(f"DELETE FROM {table_name}")
        
        # Then insert new data
        self._upload_insert_only(df, table_name, cur, conn)
        