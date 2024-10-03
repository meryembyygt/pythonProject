import streamlit as st
import sqlite3
import hashlib
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime

# Şifreyi hash'leme fonksiyonu
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# Veritabanı bağlantısı oluşturma
def create_connection():
    conn = sqlite3.connect('users.db')
    return conn

# Kullanıcı tablosu oluşturma
def create_user_table():
    conn = create_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.commit()

# Kullanıcı ekleme
def add_user(username, password):
    conn = create_connection()
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()

# Kullanıcı girişi
def login_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    data = cursor.fetchone()
    return data

# Günlük tablosu oluşturma
def create_journal_table():
    conn = create_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS journals (
        username TEXT, 
        entry TEXT, 
        file_path TEXT,
        date TEXT
    )''')
    conn.commit()

# Günlük ekleme
def add_journal_entry(username, entry, file_path=None):
    conn = create_connection()
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Tarih formatı
    conn.execute('INSERT INTO journals (username, entry, file_path, date) VALUES (?, ?, ?, ?)',
                 (username, entry, file_path, current_date))
    conn.commit()

# Günlükleri alma
def get_journal_entries(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT rowid, entry, file_path, date FROM journals WHERE username = ?', (username,))
    data = cursor.fetchall()
    return data

# Günlüğü güncelleme
def update_journal_entry(entry_id, new_entry):
    conn = create_connection()
    conn.execute('UPDATE journals SET entry = ? WHERE rowid = ?', (new_entry, entry_id))
    conn.commit()

# Günlüğü silme
def delete_journal_entry(entry_id):
    conn = create_connection()
    conn.execute('DELETE FROM journals WHERE rowid = ?', (entry_id,))
    conn.commit()

# Tarihe göre günlükleri arama
def search_journal_by_date(username, start_date, end_date):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT rowid, entry, file_path, date 
        FROM journals 
        WHERE username = ? AND date BETWEEN ? AND ?
    ''', (username, start_date, end_date))
    data = cursor.fetchall()
    return data

# Günlük sayısını alma
def get_journal_count(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM journals WHERE username = ?', (username,))
    count = cursor.fetchone()[0]
    return count

# Tarih verilerini ay bazında saymak için fonksiyon
def create_date_series(date_entries):
    dates = [entry[3] for entry in date_entries if entry[3] is not None]
    dates = [datetime.strptime(date.split(' ')[0], '%Y-%m-%d') for date in dates]
    df = pd.DataFrame({'Date': dates})
    df['Month'] = df['Date'].dt.to_period('M')
    date_series = df['Month'].value_counts().sort_index()
    return date_series

# Tarih verilerini hafta bazında saymak için fonksiyon
def create_weekly_series(date_entries):
    dates = [entry[3] for entry in date_entries if entry[3] is not None]
    dates = [datetime.strptime(date.split(' ')[0], '%Y-%m-%d') for date in dates]
    df = pd.DataFrame({'Date': dates})
    df['Week'] = df['Date'].dt.to_period('W').apply(lambda r: f'{r.start_time:%Y-%m-%d}')
    week_series = df['Week'].value_counts().sort_index()
    return week_series

# Yıllık günlük sayıları için fonksiyon
def create_yearly_series(date_entries):
    dates = [entry[3] for entry in date_entries if entry[3] is not None]
    dates = [datetime.strptime(date.split(' ')[0], '%Y-%m-%d') for date in dates]
    df = pd.DataFrame({'Date': dates})
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df_pivot = df.pivot_table(index='Month', columns='Year', aggfunc='size', fill_value=0)
    return df_pivot

# Streamlit uygulaması
def main():
    st.set_page_config(page_title="Kişisel Günlük Uygulaması", layout="wide")

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'page' not in st.session_state:
        st.session_state.page = 0

    st.title("Kişisel Günlük Uygulaması")

    menu = ["Giriş Yap", "Kayıt Ol"]
    if st.session_state.logged_in:
        menu = ["Günlükler", "Çıkış Yap"]

    choice = st.sidebar.selectbox("Menü", menu)

    if choice == "Kayıt Ol":
        st.subheader("Kullanıcı Kayıt")
        with st.form(key='register_form'):
            st.write("Kullanıcı adı ve şifre oluşturun.")
            new_user = st.text_input("Kullanıcı Adı")
            new_password = st.text_input("Parola", type='password')
            confirm_password = st.text_input("Parolayı Onayla", type='password')

            if new_password and new_password != confirm_password:
                st.warning("Parolalar eşleşmiyor.")

            submit_button = st.form_submit_button("Kayıt Ol")
            if submit_button:
                if new_password == confirm_password:
                    hashed_password = hash_password(new_password)
                    add_user(new_user, hashed_password)
                    st.success("Başarıyla kayıt oldunuz!")
                    st.info("Giriş yapmak için menüden 'Giriş Yap' seçeneğini kullanın.")
                else:
                    st.warning("Şifreler eşleşmiyor.")

    elif choice == "Giriş Yap":
        st.subheader("Kullanıcı Girişi")
        with st.form(key='login_form'):
            username = st.text_input("Kullanıcı Adı")
            password = st.text_input("Parola", type='password')
            login_button = st.form_submit_button("Giriş Yap")
            if login_button:
                hashed_password = hash_password(password)
                result = login_user(username, hashed_password)

                if result:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    create_journal_table()  # Günlük tablosunu oluştur
                    st.success(f"Hoşgeldin {username}")
                else:
                    st.warning("Kullanıcı adı veya parola hatalı")

    elif st.session_state.logged_in:
        # Günlükler sayfası
        st.subheader("Günlükler")

        # Yeni günlük ekleme
        with st.form(key='new_journal_form'):
            st.write("Yeni Günlük Ekleyin")
            daily_entry = st.text_area("Bugünkü düşüncelerinizi yazın")
            uploaded_file = st.file_uploader("Bir dosya yükleyin (opsiyonel)", type=["jpg", "png", "pdf"])
            file_path = None
            if uploaded_file is not None:
                file_path = f"uploads/{uploaded_file.name}"
                if not os.path.exists("uploads"):
                    os.makedirs("uploads")
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Dosya yüklendi: {uploaded_file.name}")

            save_button = st.form_submit_button("Günlüğü Kaydet")
            if save_button:
                add_journal_entry(st.session_state.username, daily_entry, file_path)
                st.success("Günlüğünüz başarıyla kaydedildi!")

        # Tarihe göre arama
        st.subheader("Tarihe Göre Ara")
        start_date = st.date_input("Başlangıç Tarihi", value=datetime.now().date())
        end_date = st.date_input("Bitiş Tarihi", value=datetime.now().date())

        if start_date > end_date:
            st.warning("Başlangıç tarihi bitiş tarihinden sonra olamaz.")
        else:
            if st.button("Ara", key="search_button"):
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                search_results = search_journal_by_date(st.session_state.username, start_date_str, end_date_str)

                if search_results:
                    st.write(f"Bulunan günlükler ({len(search_results)} adet):")
                    for result in search_results:
                        st.write(f"**Günlük**")
                        st.write(result[1])
                        if result[2]:
                            st.image(result[2], caption="Eklenen Fotoğraf")
                        st.write(f"Tarih: {result[3]}")
                        st.markdown("---")
                else:
                    st.write("Belirtilen tarihler arasında hiçbir günlük bulunamadı.")

        # Sayfa seçimi (önceki-sonraki butonları)
        entries = get_journal_entries(st.session_state.username)
        entries_per_page = 3
        total_pages = (len(entries) - 1) // entries_per_page + 1

        # Önceki ve Sonraki sayfa butonları
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Önceki Sayfa"):
                if st.session_state.page > 0:
                    st.session_state.page -= 1

        with col2:
            if st.button("Sonraki Sayfa"):
                if st.session_state.page < total_pages - 1:
                    st.session_state.page += 1

        # Mevcut sayfa için günlükleri göster
        start_index = st.session_state.page * entries_per_page
        end_index = start_index + entries_per_page

        for entry in entries[start_index:end_index]:
            st.write(f"**Günlük:** {entry[1]}")
            if entry[2]:
                st.image(entry[2], caption="Eklenen Fotoğraf")
            st.write(f"Tarih: {entry[3]}")
            st.markdown("---")

        # Sayfa numarasını göster
        st.write(f"Sayfa: {st.session_state.page + 1} / {total_pages}")

        # Günlük sayısı
        total_entries = get_journal_count(st.session_state.username)
        st.sidebar.write(f"Toplam Günlük Sayısı: {total_entries}")

        # Günlükler için grafiksel analiz
        st.subheader("Günlüklerinizin Zaman İçindeki Dağılımı")
        date_entries = get_journal_entries(st.session_state.username)

        if date_entries:
            series_type = st.selectbox("Grafik Tipi Seçin", ("Haftalık", "Aylık", "Yıllık"))

            if series_type == "Haftalık":
                weekly_series = create_weekly_series(date_entries)
                fig, ax = plt.subplots()
                sns.lineplot(x=weekly_series.index, y=weekly_series.values, ax=ax, marker='o')
                plt.xticks(rotation=45)
                st.pyplot(fig)

            elif series_type == "Aylık":
                date_series = create_date_series(date_entries)
                fig, ax = plt.subplots()
                sns.barplot(x=date_series.index.astype(str), y=date_series.values, ax=ax)
                plt.xticks(rotation=45)
                st.pyplot(fig)

            elif series_type == "Yıllık":
                yearly_series = create_yearly_series(date_entries)
                fig, ax = plt.subplots()
                sns.heatmap(yearly_series, annot=True, fmt="d", cmap="Blues", ax=ax)
                plt.xticks(rotation=45)
                st.pyplot(fig)

    if choice == "Çıkış Yap":
        st.session_state.logged_in = False
        st.session_state.username = ''
        st.success("Başarıyla çıkış yaptınız.")

if __name__ == '__main__':
    main()
