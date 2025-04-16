from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# 在庫数の警告閾値（5個未満で警告）
STOCK_WARNING_THRESHOLD = 5

# データベース接続を管理する関数
def get_db_connection():
    conn = sqlite3.connect('cafe.db')
    conn.row_factory = sqlite3.Row
    return conn

# データベースを初期化する関数
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventory 
                 (id INTEGER PRIMARY KEY, name TEXT, stock INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS items 
                 (item_id INTEGER PRIMARY KEY, item_name TEXT, category TEXT)''')
    c.execute("INSERT OR IGNORE INTO inventory (id, name, stock) VALUES (1, 'コーヒー', 10)")
    c.execute("INSERT OR IGNORE INTO inventory (id, name, stock) VALUES (2, 'ケーキ', 5)")
    c.execute("INSERT OR IGNORE INTO inventory (id, name, stock) VALUES (3, 'ミルク', 20)")
    c.execute("INSERT OR IGNORE INTO items (item_id, item_name, category) VALUES (1, 'コーヒー', '飲み物')")
    c.execute("INSERT OR IGNORE INTO items (item_id, item_name, category) VALUES (2, 'ケーキ', '食べ物')")
    c.execute("INSERT OR IGNORE INTO items (item_id, item_name, category) VALUES (3, 'ミルク', '飲み物')")
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def home():
    conn = get_db_connection()
    c = conn.cursor()
    
    # 検索パラメータを取得
    search_name = request.form.get('search_name', '') if request.method == 'POST' else request.args.get('search_name', '')
    search_category = request.form.get('search_category', '') if request.method == 'POST' else request.args.get('search_category', '')
    
    # 検索条件を動的に構築
    query = """
        SELECT inv.id, inv.name, inv.stock, i.item_name, i.category 
        FROM inventory inv 
        LEFT JOIN items i ON inv.id = i.item_id
        WHERE 1=1
    """
    params = []
    
    if search_name:
        query += " AND (i.item_name LIKE ? OR inv.name LIKE ?)"
        params.extend([f'%{search_name}%', f'%{search_name}%'])
    
    if search_category:
        query += " AND i.category LIKE ?"
        params.append(f'%{search_category}%')
    
    c.execute(query, params)
    items = c.fetchall()
    
    # 在庫数の合計を計算
    c.execute("SELECT SUM(stock) AS total_stock FROM inventory")
    total_stock = c.fetchone()['total_stock'] or 0
    
    # 警告フラグを追加
    items_with_warning = []
    for item in items:
        item_dict = dict(item)  # SQLiteのRowオブジェクトを辞書に変換
        item_dict['low_stock'] = item['stock'] < STOCK_WARNING_THRESHOLD  # 在庫数が閾値未満か判定
        items_with_warning.append(item_dict)
    
    conn.close()
    
    return render_template('index.html', items=items_with_warning, search_name=search_name, search_category=search_category, total_stock=total_stock)

@app.route('/add', methods=['POST'])
def add_item():
    name = request.form['name']
    stock = int(request.form['stock'])
    category = request.form['category']
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO inventory (name, stock) VALUES (?, ?)", (name, stock))
    new_id = c.lastrowid
    c.execute("INSERT INTO items (item_id, item_name, category) VALUES (?, ?, ?)", (new_id, name, category))
    conn.commit()
    conn.close()
    
    return redirect(url_for('home'))

@app.route('/update/<int:item_id>', methods=['POST'])
def update_item(item_id):
    stock = int(request.form['stock'])
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE inventory SET stock = ? WHERE id = ?", (stock, item_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('home'))

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    c.execute("DELETE FROM items WHERE item_id = ?", (item_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('home'))

@app.route('/edit_category/<int:item_id>', methods=['POST'])
def edit_category(item_id):
    category = request.form['category']
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
    item = c.fetchone()
    if item:
        c.execute("UPDATE items SET category = ? WHERE item_id = ?", (category, item_id))
    else:
        c.execute("SELECT name FROM inventory WHERE id = ?", (item_id,))
        inv_item = c.fetchone()
        if inv_item:
            name = inv_item['name']
            c.execute("INSERT INTO items (item_id, item_name, category) VALUES (?, ?, ?)", (item_id, name, category))
    conn.commit()
    conn.close()
    
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)