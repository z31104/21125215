from flask import Flask, request, redirect
import os
import mysql.connector
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError

app = Flask(__name__)


def get_db_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "8625")),
        "user": os.getenv("DB_USER", "flaskuser"),
        "password": os.getenv("DB_PASSWORD", "flask123"),
        "database": os.getenv("DB_NAME", "flaskdb"),
    }


def get_connection():
    return mysql.connector.connect(**get_db_config())


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            age INT NOT NULL
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


@app.route("/")
def home():
    init_db()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users ORDER BY id DESC")
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    html = """
    <h1>我是功能一</h1>

    <h2>新增用戶</h2>
    <form method="POST" action="/add">
        姓名：<input type="text" name="name" required>
        年紀：<input type="number" name="age" required>
        <button type="submit">新增</button>
    </form>

    <h2>用戶列表</h2>
    <table border="1" cellpadding="8">
        <tr>
            <th>ID</th>
            <th>姓名</th>
            <th>年紀</th>
            <th>操作</th>
        </tr>
    """

    for user in users:
        html += f"""
        <tr>
            <td>{user["id"]}</td>
            <td>{user["name"]}</td>
            <td>{user["age"]}</td>
            <td>
                <form method="POST" action="/delete/{user["id"]}">
                    <button type="submit">刪除</button>
                </form>
            </td>
        </tr>
        """

    html += "</table>"

    return html


@app.route("/add", methods=["POST"])
def add_user():
    name = request.form["name"]
    age = request.form["age"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (name, age) VALUES (%s, %s)",
        (name, age)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/")


@app.route("/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM users WHERE id = %s",
        (user_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/")

@app.route("/gcp", methods=["GET", "POST"])
def gcp_storage():
    buckets = []
    error = None
    project_id = ""

    if request.method == "POST":
        project_id = request.form.get("project_id", "").strip()

        try:
            client = storage.Client()
            bucket_list = client.list_buckets(project=project_id)
            buckets = [bucket.name for bucket in bucket_list]

        except DefaultCredentialsError:
            error = "找不到 GCP 開發憑證，請先設定 Application Default Credentials。"

        except Exception as e:
            error = str(e)

    html = """
    <h1>GCP Cloud Storage Bucket 瀏覽</h1>

    <form method="POST" action="/gcp">
        Project ID：
        <input type="text" name="project_id" value="{project_id}" required>
        <button type="submit">查詢 Bucket</button>
    </form>

    <hr>
    """.format(project_id=project_id)

    if error:
        html += f"<p style='color:red;'>錯誤：{error}</p>"

    if buckets:
        html += "<h2>Bucket 清單</h2><ul>"
        for bucket in buckets:
            html += f"<li>{bucket}</li>"
        html += "</ul>"

    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)