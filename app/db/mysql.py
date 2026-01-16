import pymysql
from contextlib import contextmanager
from app.common.mysql import MYSQL_DB,MYSQL_HOST,MYSQL_PORT,MYSQL_USER,MYSQL_PASSWORD



# MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
# MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
# MYSQL_USER = os.getenv("MYSQL_USER", "LoveBreaker")
# MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
# MYSQL_DB = os.getenv("MYSQL_DB", "Number1")


@contextmanager
def get_conn():  # 获取数据库连接
    conn = pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT,
        user=MYSQL_USER, password=MYSQL_PASSWORD,
        database=MYSQL_DB, charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        yield conn
    finally:
        conn.close()