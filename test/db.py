import argparse
import os
import sys
import pyodbc
from pathlib import Path

# Define paths
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / '.env'
SQL_DIR = Path(__file__).resolve().parent / "sql"

def load_env_file(filepath):
    """Load environment variables from a .env file."""
    if not filepath.exists():
        print(f"Warning: .env file not found at {filepath}")
        return
    
    print(f"Loading environment from {filepath}")
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip()
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                os.environ[key.strip()] = value

def get_connection():
    # Load env vars
    load_env_file(ENV_PATH)
    
    server = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT', '1433')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    trust_cert = os.getenv('DB_TRUST_CERT', 'no')
    
    if not all([server, database, username, password]):
        print("Error: Missing database credentials in .env file.")
        sys.exit(1)

    # Construct connection string
    # Note: ODBC Driver 18 requires TrustServerCertificate=yes for self-signed certs or encryption settings
    conn_str = (
        f'DRIVER={{{driver}}};'
        f'SERVER={server},{port};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password};'
        f'TrustServerCertificate={trust_cert};'
    )
    
    try:
        conn = pyodbc.connect(conn_str)
        return conn
    except pyodbc.Error as ex:
        print(f"Error connecting to database: {ex}")
        sys.exit(1)

def run_sql_file(filename):
    file_path = SQL_DIR / filename
    if not file_path.exists():
        # Try looking in the current directory if not found in sql dir
        file_path = Path(filename)
        if not file_path.exists():
            print(f"Error: File {filename} not found in {SQL_DIR} or current directory.")
            sys.exit(1)

    print(f"Executing {filename}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Split by GO command if it exists (common in T-SQL scripts)
        # Use a regex or simple split, simple split is usually enough for basic scripts
        # but we need to be careful about GO inside comments or strings.
        # For now, simple split by newline+GO+newline or similar.
        # A robust parser is complex, we'll stick to simple 'GO' on its own line.
        
        commands = []
        current_command = []
        
        for line in sql_script.splitlines():
            if line.strip().upper() == 'GO':
                if current_command:
                    commands.append('\n'.join(current_command))
                    current_command = []
            else:
                current_command.append(line)
        
        if current_command:
            commands.append('\n'.join(current_command))
        
        for command in commands:
            if command.strip():
                # print(f"Running: {command[:50]}...")
                cursor.execute(command)
                # Fetch results if any (for SELECT statements like check_schema)
                if cursor.description:
                    columns = [column[0] for column in cursor.description]
                    print(f"\nResult for: {command[:30]}...")
                    print(" | ".join(columns))
                    print("-" * (len(" | ".join(columns))))
                    rows = cursor.fetchall()
                    for row in rows:
                        print(" | ".join(str(x) for x in row))
                    print(f"({len(rows)} rows affected)")
                
                conn.commit()
        
        print("\nExecution successful.")
    except pyodbc.Error as ex:
        print(f"Error executing SQL: {ex}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Run SQL scripts.')
    parser.add_argument('filename', help='The SQL file to run (e.g., test.sql)')
    args = parser.parse_args()

    # Handle the --test.sql format if passed directly
    filename = args.filename
    if filename.startswith('--'):
        filename = filename[2:]

    run_sql_file(filename)

if __name__ == "__main__":
    main()
