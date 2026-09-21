"""迁移脚本：为 case_records 表添加入职/离职日期、平均工资、奖金字段"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "labor_arb.db"

if not DB_PATH.exists():
    print(f"❌ 数据库文件不存在: {DB_PATH}")
    exit(1)

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

# 检查现有列
cur.execute("PRAGMA table_info(case_records)")
existing = {row[1] for row in cur.fetchall()}

migrations = [
    ("entry_date", "VARCHAR(32)"),
    ("quit_date", "VARCHAR(32)"),
    ("average_salary", "VARCHAR(32)"),
    ("bonus_info", "TEXT"),
]

for col_name, col_type in migrations:
    if col_name not in existing:
        print(f"[ADD] Adding column: {col_name} ({col_type})")
        cur.execute(f"ALTER TABLE case_records ADD COLUMN {col_name} {col_type}")
    else:
        print(f"[SKIP] Already exists: {col_name}")

conn.commit()
conn.close()
print("\n[DONE] Migration completed!")
