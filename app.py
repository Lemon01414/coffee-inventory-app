import os
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import logging

app = Flask(__name__)

# ロギングを設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# データベースファイルの絶対パスを設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'cafe.db')

def get_db_connection():
    if not os.path.exists(DATABASE_PATH):
        logger.error(f"データベースファイルが見つかりません: {DATABASE_PATH}")
        raise FileNotFoundError(f"データベースファイルが見つかりません: {DATABASE_PATH}")
    logger.debug(f"データベースファイルが見つかりました: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        if not os.path.exists(DATABASE_PATH):
            logger.debug(f"データベースファイルを作成します: {DATABASE_PATH}")
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        # テーブルを削除して再作成（データのリセット、カテゴリカラムを削除）
        c.execute('DROP TABLE IF EXISTS items')
        c.execute('''
            CREATE TABLE items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                display_name TEXT,
                stock INTEGER,
                unit TEXT
            )
        ''')
        # 初期データを挿入（カテゴリを削除）
        c.execute("INSERT INTO items (name, display_name, stock, unit) VALUES ('ミルク', '牛乳', 10, 'リットル')")
        c.execute("INSERT INTO items (name, display_name, stock, unit) VALUES ('ケーキ', 'チョコケーキ', 10, '個')")
        conn.commit()
        logger.debug("データベースを初期化しました")
    except sqlite3.Error as e:
        logger.error(f"データベース初期化エラー: {e}")
        raise
    finally:
        conn.close()

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT *, (stock < 5) as low_stock FROM items')
        items = [
            {
                'name': row['name'],
                'display_name': row['display_name'],
                'stock': row['stock'],
                'unit': row['unit'],
                'low_stock': row['low_stock']
            }
            for row in c.fetchall()
        ]
        c.execute('SELECT SUM(stock) as total_stock FROM items')
        total_stock = c.fetchone()['total_stock'] or 0
        conn.close()
        return render_template('index.html', items=items, total_stock=total_stock)
    except Exception as e:
        logger.error(f"インデックスエラー: {e}")
        raise

@app.route('/add', methods=['POST'])
def add_item():
    name = request.form['name']
    display_name = request.form['display_name']
    stock = int(request.form['stock'])
    unit = request.form['unit']
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO items (name, display_name, stock, unit) VALUES (?, ?, ?, ?)",
              (name, display_name, stock, unit))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search():
    search_name = request.form['name']
    conn = get_db_connection()
    c = conn.cursor()
    query = "SELECT *, (stock < 5) as low_stock FROM items WHERE 1=1"
    params = []
    if search_name:
        query += " AND (name LIKE ? OR display_name LIKE ?)"
        params.extend(['%' + search_name + '%', '%' + search_name + '%'])
    c.execute(query, params)
    items = [
        {
            'name': row['name'],
            'display_name': row['display_name'],
            'stock': row['stock'],
            'unit': row['unit'],
            'low_stock': row['low_stock']
        }
        for row in c.fetchall()
    ]
    conn.close()
    return render_template('index.html', items=items)

@app.route('/update_stock/<name>', methods=['POST'])
def update_stock(name):
    stock = int(request.form['stock'])
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE items SET stock = ? WHERE name = ?", (stock, name))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/increment_stock/<name>', methods=['POST'])
def increment_stock(name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE items SET stock = stock +1 WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/decrement_stock/<name>', methods=['POST'])
def decrement_stock(name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE items SET stock = stock - 1 WHERE name = ? AND stock > 0", (name,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<name>', methods=['POST'])
def delete(name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM items WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)