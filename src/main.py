import os
import logging
from app.app_window import AppWindow

# .env の読み込み（存在しない/未インストールでもアプリは起動可能）
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass

if __name__ == "__main__":
    # ログ設定（INFO以上を標準出力に）
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

    # エントリーポイント
    app = AppWindow()
    app.mainloop()
