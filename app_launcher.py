import sys
import threading
import time
from PyQt5 import QtWidgets
import uvicorn

from client.main import LoginWindow
from server.main import app as api_app


def start_api_server() -> None:
    uvicorn.run(api_app, host="127.0.0.1", port=8000, log_level="warning")


if __name__ == "__main__":
    server_thread = threading.Thread(target=start_api_server, daemon=True)
    server_thread.start()
    time.sleep(1)

    app = QtWidgets.QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
