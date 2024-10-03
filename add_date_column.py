import sqlite3

def add_date_column():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Eğer tablo zaten var ise ve date sütunu eksikse, bu SQL komutu ile sütunu ekleyebilirsiniz.
    cursor.execute('ALTER TABLE journals ADD COLUMN date TEXT')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_date_column()
