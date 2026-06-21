import os
import sys
import time
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_PORT = int(os.getenv("DATABASE_PORT", 3306))
DB_USER = os.getenv("DATABASE_USER", "root")
DB_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
DB_NAME = os.getenv("DATABASE_NAME", "fish_tank_db")


def wait_for_mysql():
    print(f"等待 MySQL 连接: {DB_HOST}:{DB_PORT}...")
    for i in range(30):
        try:
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                charset="utf8mb4",
            )
            conn.close()
            print("MySQL 连接成功!")
            return True
        except pymysql.err.OperationalError as e:
            print(f"尝试 {i+1}/30 失败: {e}")
            time.sleep(2)
    print("无法连接到 MySQL")
    return False


def create_database():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset="utf8mb4",
        )
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
            f"DEFAULT CHARACTER SET utf8mb4 "
            f"DEFAULT COLLATE utf8mb4_unicode_ci"
        )
        print(f"数据库 {DB_NAME} 已创建或已存在")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"创建数据库失败: {e}")
        return False


if __name__ == "__main__":
    if not wait_for_mysql():
        sys.exit(1)
    if not create_database():
        sys.exit(1)
    print("数据库初始化完成")
