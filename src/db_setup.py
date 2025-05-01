import sqlite3

def run_setup():
    conn = sqlite3.connect('microblog.db')
    cursor = conn.cursor()

    with open('db.sql', 'r', encoding='utf-8') as file:
        sql_script = file.read()

    try:
        cursor.executescript(sql_script)
    except Exception:
        pass

    conn.commit()

    cursor.close()
    conn.close()