import logging
from app.app_window import AppWindow

if __name__ == "__main__":
    # ログ設定（INFO以上を標準出力に）
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

    # エントリーポイント
    app = AppWindow()
    app.mainloop()