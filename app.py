from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('cafe.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = sqlite3.connect('cafe.db')
        c = conn.cursor()
        # テーブルを削除して再作成（データのリセット）
        c.execute('DROP TABLE IF EXISTS items')
        c.execute('''
            CREATE TABLE items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                display_name TEXT,
                category TEXT,
                stock INTEGER
            )
        ''')
        # 初期データを挿入（現在の状態に基づく）
        c.execute("INSERT INTO items (name, display_name, category, stock) VALUES ('ミルク', '牛乳', '飲み物', 10)")
        c.execute("INSERT INTO items (name, display_name, category, stock) VALUES ('ケーキ', 'チョコケーキ', '食べ物', 10)")
        conn.commit()
        print("データベースを初期化しました")
    except sqlite3.Error as e:
        print(f"データベース初期化エラー: {e}")
    finally:
        conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT *, (stock < 5) as low_stock FROM items')
    items = [
        {
            'name': row['name'],
            'display_name': row['display_name'],
            'category': row['category'],
            'stock': row['stock'],
            'low_stock': row['low_stock']
        }
        for row in c.fetchall()
    ]
    c.execute('SELECT SUM(stock) as total_stock FROM items')
    total_stock = c.fetchone()['total_stock'] or 0
    conn.close()
    return render_template('index.html', items=items, total_stock=total_stock)

@app.route('/add', methods=['POST'])
def add_item():
    name = request.form['name']
    display_name = request.form['display_name']
    stock = int(request.form['stock'])
    category = request.form['category']
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO items (name, display_name, category, stock) VALUES (?, ?, ?, ?)",
              (name, display_name, category, stock))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search():
    search_name = request.form['name']
    search_category = request.form['category']
    conn = get_db_connection()
    c = conn.cursor()
    query = "SELECT *, (stock < 5) as low_stock FROM items WHERE 1=1"
    params = []
    if search_name:
        query += " AND (name LIKE ? OR display_name LIKE ?)"
        params.extend(['%' + search_name + '%', '%' + search_name + '%'])
    if search_category:
        query += " AND category LIKE ?"
        params.append('%' + search_category + '%')
    c.execute(query, params)
    items = [
        {
            'name': row['name'],
            'display_name': row['display_name'],
            'category': row['category'],
            'stock': row['stock'],
            'low_stock': row['low_stock']
        }
        for row in c.fetchall()
    ]
    conn.close()
    return render_template('index.html', items=items)

@app.route('/update_category/<name>', methods=['POST'])
def update_category(name):
    category = request.form['category']
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE items SET category = ? WHERE name = ?", (category, name))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/update_stock/<name>', methods=['POST'])
def update_stock(name):
    stock = int(request.form['stock'])
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE items SET stock = ? WHERE name = ?", (stock, name))
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