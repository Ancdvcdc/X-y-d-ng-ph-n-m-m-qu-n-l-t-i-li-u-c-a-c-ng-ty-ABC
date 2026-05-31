import os
import sys
from pathlib import Path

from PyQt5 import QtWidgets, uic
from client import api


def resource_path(relative_path: str) -> str:
    if getattr(sys, "_MEIPASS", None):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)


class UploadDocumentDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tải lên tài liệu")
        self.setMinimumWidth(420)
        layout = QtWidgets.QFormLayout(self)

        self.titleInput = QtWidgets.QLineEdit()
        self.passwordInput = QtWidgets.QLineEdit()
        self.passwordInput.setEchoMode(QtWidgets.QLineEdit.Password)
        self.filePathInput = QtWidgets.QLineEdit()
        self.filePathInput.setReadOnly(True)
        browse_button = QtWidgets.QPushButton("Chọn tệp")
        browse_button.clicked.connect(self.browse_file)

        file_layout = QtWidgets.QHBoxLayout()
        file_layout.addWidget(self.filePathInput)
        file_layout.addWidget(browse_button)

        layout.addRow("Tên tài liệu:", self.titleInput)
        layout.addRow("Mật khẩu bảo mật:", self.passwordInput)
        layout.addRow("Tệp tải lên:", file_layout)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def browse_file(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Chọn tệp để tải lên")
        if file_name:
            self.filePathInput.setText(file_name)

    def get_data(self):
        return self.titleInput.text().strip(), self.passwordInput.text().strip(), self.filePathInput.text().strip()


class EditDocumentDialog(QtWidgets.QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sửa tài liệu")
        self.setMinimumWidth(360)
        layout = QtWidgets.QFormLayout(self)

        self.titleInput = QtWidgets.QLineEdit(title)
        self.passwordInput = QtWidgets.QLineEdit()
        self.passwordInput.setEchoMode(QtWidgets.QLineEdit.Password)

        layout.addRow("Tên tài liệu:", self.titleInput)
        layout.addRow("Mật khẩu mới:", self.passwordInput)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_data(self):
        return self.titleInput.text().strip(), self.passwordInput.text().strip()


class UserDialog(QtWidgets.QDialog):
    def __init__(self, username="", role="Nhân viên", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quản lý tài khoản")
        self.setMinimumWidth(360)
        layout = QtWidgets.QFormLayout(self)

        self.usernameInput = QtWidgets.QLineEdit(username)
        self.passwordInput = QtWidgets.QLineEdit()
        self.passwordInput.setEchoMode(QtWidgets.QLineEdit.Password)
        self.roleInput = QtWidgets.QComboBox()
        self.roleInput.addItems(["Admin", "Giám đốc", "Trưởng phòng", "Nhân viên"])
        if role:
            index = self.roleInput.findText(role)
            if index >= 0:
                self.roleInput.setCurrentIndex(index)

        layout.addRow("Tên đăng nhập:", self.usernameInput)
        layout.addRow("Mật khẩu:", self.passwordInput)
        layout.addRow("Vai trò:", self.roleInput)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_data(self):
        return (
            self.usernameInput.text().strip(),
            self.passwordInput.text().strip(),
            self.roleInput.currentText(),
        )


class LoginWindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        ui_path = resource_path("login.ui")
        uic.loadUi(ui_path, self)
        self.loginButton.clicked.connect(self.login)

    def login(self):
        username = self.usernameInput.text().strip()
        password = self.passwordInput.text().strip()
        if not username or not password:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên đăng nhập và mật khẩu")
            return

        try:
            response = api.login(username, password)
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không thể kết nối tới server")
            return

        if response.status_code == 200:
            data = response.json()
            self.main_window = MainWindow(data["username"], data["role"])
            self.main_window.show()
            self.close()
        elif response.status_code == 401:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Sai tài khoản hoặc mật khẩu")
        else:
            QtWidgets.QMessageBox.warning(self, "Lỗi", f"Lỗi kết nối: {response.status_code}")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, username, role):
        super().__init__()
        ui_path = resource_path("mainwindow.ui")
        uic.loadUi(ui_path, self)
        self.username = username
        self.role = role
        self.current_page = "documents"
        self.usernameLabel.setText(f"Xin chào {username} - Quyền: {role}")
        self._setup_table()
        self.uploadButton.clicked.connect(self.upload_document)
        self.addUserButton.clicked.connect(self.add_user)
        self.searchInput.textChanged.connect(self.on_search_changed)
        self.homeButton.clicked.connect(self.show_home)
        self.docsButton.clicked.connect(self.show_documents)
        self.historyButton.clicked.connect(self.show_history_page)
        self.manageButton.clicked.connect(self.show_manage)
        if self.role.strip().lower() != "admin":
            self.manageButton.hide()
        self.show_documents()

    def _setup_table(self, headers=None):
        if headers is None:
            headers = ["ID", "Tên tài liệu", "Người tải lên", "Ngày tải lên", "Hành động"]
        self.tableWidget.setColumnCount(len(headers))
        self.tableWidget.setHorizontalHeaderLabels(headers)
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setVisible(False)

    def load_documents(self):
        try:
            docs = api.get_documents()
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không thể tải danh sách tài liệu")
            return

        query = self.searchInput.text().strip().lower()
        if query:
            docs = [d for d in docs if query in d["title"].lower() or query in d["uploader"].lower()]

        self.tableWidget.setRowCount(len(docs))
        for row, doc in enumerate(docs):
            self.tableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(str(doc["id"])))
            self.tableWidget.setItem(row, 1, QtWidgets.QTableWidgetItem(doc["title"]))
            self.tableWidget.setItem(row, 2, QtWidgets.QTableWidgetItem(doc["uploader"]))
            self.tableWidget.setItem(row, 3, QtWidgets.QTableWidgetItem(str(doc["date"])))
            self.tableWidget.setCellWidget(row, 4, self._create_action_widget(doc))

    def load_users(self):
        try:
            users = api.get_users(self.username)
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không thể tải danh sách người dùng")
            return

        query = self.searchInput.text().strip().lower()
        if query:
            users = [u for u in users if query in u["username"].lower() or query in u["role"].lower()]

        self.tableWidget.setRowCount(len(users))
        for row, user in enumerate(users):
            self.tableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(str(user["id"])))
            self.tableWidget.setItem(row, 1, QtWidgets.QTableWidgetItem(user["username"]))
            self.tableWidget.setItem(row, 2, QtWidgets.QTableWidgetItem(user["role"]))
            self.tableWidget.setCellWidget(row, 3, self._create_action_widget(user))

    def on_search_changed(self):
        if self.current_page == "users":
            self.load_users()
        else:
            self.load_documents()

    def show_home(self):
        self.current_page = "home"
        self.pageTitleLabel.setText("Trang chủ")
        self.homeContentLabel.setText(
            "Chào mừng Admin!\n\n"
            "Ở đây bạn có thể xem tổng quan hệ thống, tải lên tài liệu mới, "
            "xem lịch sử thao tác và quản lý dữ liệu.\n\n"
            "Nhấn Tài liệu để xem chi tiết danh sách tài liệu."
        )
        self.homeContentLabel.show()
        self.tableWidget.hide()
        self.searchInput.hide()
        self.uploadButton.hide()
        self.addUserButton.hide()

    def show_documents(self):
        self.current_page = "documents"
        self.pageTitleLabel.setText("Tài liệu")
        self.homeContentLabel.hide()
        self.tableWidget.show()
        self.searchInput.show()
        self.uploadButton.show()
        self.addUserButton.hide()
        self.searchInput.setPlaceholderText("Tìm kiếm tài liệu...")
        self._setup_table(["ID", "Tên tài liệu", "Người tải lên", "Ngày tải lên", "Hành động"])
        self.load_documents()

    def show_history_page(self):
        if self.tableWidget.currentRow() < 0:
            QtWidgets.QMessageBox.information(self, "Lịch sử", "Vui lòng chọn một tài liệu trong danh sách trước.")
            self.show_documents()
            return

        row = self.tableWidget.currentRow()
        doc_id = int(self.tableWidget.item(row, 0).text())
        doc_title = self.tableWidget.item(row, 1).text()
        try:
            records = api.get_history(doc_id)
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không thể lấy lịch sử tài liệu")
            return

        if not records:
            QtWidgets.QMessageBox.information(self, "Lịch sử", f"Không có lịch sử cho tài liệu '{doc_title}'")
            return

        lines = [f"{r['timestamp']} - {r['user']}: {r['action']}" for r in records]
        QtWidgets.QMessageBox.information(self, f"Lịch sử '{doc_title}'", "\n".join(lines))

    def show_manage(self):
        self.current_page = "users"
        self.pageTitleLabel.setText("Quản lý tài khoản")
        self.homeContentLabel.hide()
        self.tableWidget.show()
        self.searchInput.show()
        self.uploadButton.hide()
        self.addUserButton.show()
        self.searchInput.setPlaceholderText("Tìm kiếm tài khoản...")
        self._setup_table(["ID", "Tên đăng nhập", "Quyền", "Hành động"])
        self.load_users()

    def _create_action_widget(self, item):
        actions = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(actions)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        if self.current_page == "users":
            edit_btn = QtWidgets.QPushButton("Sửa")
            edit_btn.clicked.connect(lambda _, u=item: self.edit_user(u))
            layout.addWidget(edit_btn)

            if item["username"] != self.username:
                delete_btn = QtWidgets.QPushButton("Xóa")
                delete_btn.clicked.connect(lambda _, u=item: self.delete_user(u))
                layout.addWidget(delete_btn)

            actions.setLayout(layout)
            return actions

        role = self.role.strip().lower()
        can_download = role in ["admin", "giám đốc", "trưởng phòng", "nhân viên"]
        can_detail = role in ["admin", "giám đốc", "trưởng phòng"]
        can_edit = role in ["admin", "giám đốc"]
        can_delete = role in ["admin"]

        if can_download:
            download_btn = QtWidgets.QPushButton("Tải xuống")
            download_btn.clicked.connect(lambda _, d=item: self.download_document(d))
            layout.addWidget(download_btn)

        if can_detail:
            detail_btn = QtWidgets.QPushButton("Chi tiết")
            detail_btn.clicked.connect(lambda _, d=item: self.show_history(d))
            layout.addWidget(detail_btn)

        if can_edit:
            edit_btn = QtWidgets.QPushButton("Sửa")
            edit_btn.clicked.connect(lambda _, d=item: self.edit_document(d))
            layout.addWidget(edit_btn)

        if can_delete:
            delete_btn = QtWidgets.QPushButton("Xóa")
            delete_btn.clicked.connect(lambda _, d=item: self.delete_document(d))
            layout.addWidget(delete_btn)

        actions.setLayout(layout)
        return actions

    def download_document(self, doc):
        password, ok = QtWidgets.QInputDialog.getText(self, "Mật khẩu tải xuống", "Nhập mật khẩu tài liệu:", QtWidgets.QLineEdit.Password)
        if not ok or not password.strip():
            return

        try:
            response = api.download_document(doc["id"], self.username, password.strip())
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không thể kết nối tới server để tải xuống")
            return

        if response.status_code != 200:
            message = response.text or f"Lỗi: {response.status_code}"
            QtWidgets.QMessageBox.warning(self, "Lỗi", message)
            return

        suggested_name = f"{doc['title'].replace(' ', '_')}{Path(doc.get('file_path', doc['title'])).suffix or '.bin'}"
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Lưu tệp", suggested_name)
        if not save_path:
            return

        try:
            with open(save_path, "wb") as buffer:
                buffer.write(response.content)
            QtWidgets.QMessageBox.information(self, "Thành công", "Tải xuống hoàn tất")
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không thể lưu tệp")

    def upload_document(self):
        dialog = UploadDocumentDialog(self)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        title, password, file_path = dialog.get_data()
        if not title or not password or not file_path:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng điền đầy đủ thông tin và chọn tệp")
            return

        try:
            response = api.upload_document(title, self.username, password, file_path)
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không thể kết nối tới server để tải lên")
            return

        if response.status_code in (200, 201):
            QtWidgets.QMessageBox.information(self, "Thành công", "Tải lên tài liệu thành công")
            self.load_documents()
        else:
            QtWidgets.QMessageBox.warning(self, "Lỗi", response.text or f"Lỗi: {response.status_code}")

    def edit_document(self, doc):
        dialog = EditDocumentDialog(doc["title"], self)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        new_title, new_password = dialog.get_data()
        if not new_title:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Tên tài liệu không được để trống")
            return

        try:
            response = api.update_document(doc["id"], self.username, title=new_title, password=new_password)
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không thể kết nối tới server để cập nhật")
            return

        if response.status_code == 200:
            QtWidgets.QMessageBox.information(self, "Thành công", "Cập nhật tài liệu thành công")
            self.load_documents()
        else:
            QtWidgets.QMessageBox.warning(self, "Lỗi", response.text or f"Lỗi: {response.status_code}")

    def delete_document(self, doc):
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Xác nhận xóa",
            f"Bạn có chắc muốn xóa tài liệu '{doc['title']}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if confirm != QtWidgets.QMessageBox.Yes:
            return

        try:
            response = api.delete_document(doc["id"], self.username)
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không thể kết nối tới server để xóa")
            return

        if response.status_code == 200:
            QtWidgets.QMessageBox.information(self, "Thành công", "Xóa tài liệu thành công")
            self.load_documents()
        else:
            QtWidgets.QMessageBox.warning(self, "Lỗi", response.text or f"Lỗi: {response.status_code}")

    def show_history(self, doc):
        try:
            records = api.get_history(doc["id"])
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không thể lấy lịch sử tài liệu")
            return

        if not records:
            QtWidgets.QMessageBox.information(self, "Lịch sử", "Không có hoạt động nào")
            return

        lines = []
        for record in records:
            lines.append(f"{record['timestamp']} - {record['user']}: {record['action']}")

        QtWidgets.QMessageBox.information(self, "Lịch sử", "\n".join(lines))

    def add_user(self):
        dialog = UserDialog(parent=self)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        username, password, role = dialog.get_data()
        if not username or not password:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng điền đầy đủ tên đăng nhập và mật khẩu")
            return

        try:
            response = api.create_user(self.username, username, password, role)
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không thể kết nối tới server để tạo người dùng")
            return

        if response.status_code in (200, 201):
            QtWidgets.QMessageBox.information(self, "Thành công", "Tạo tài khoản thành công")
            self.load_users()
        else:
            QtWidgets.QMessageBox.warning(self, "Lỗi", response.text or f"Lỗi: {response.status_code}")

    def edit_user(self, user):
        dialog = UserDialog(username=user["username"], role=user["role"], parent=self)
        dialog.passwordInput.setPlaceholderText("Để trống nếu không đổi")
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        username, password, role = dialog.get_data()
        if not username:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Tên đăng nhập không được để trống")
            return

        try:
            response = api.update_user(
                self.username,
                user["id"],
                username=username,
                password=password if password else None,
                role=role,
            )
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không thể kết nối tới server để cập nhật người dùng")
            return

        if response.status_code == 200:
            QtWidgets.QMessageBox.information(self, "Thành công", "Cập nhật tài khoản thành công")
            self.load_users()
        else:
            QtWidgets.QMessageBox.warning(self, "Lỗi", response.text or f"Lỗi: {response.status_code}")

    def delete_user(self, user):
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Xác nhận xóa",
            f"Bạn có chắc muốn xóa tài khoản '{user['username']}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if confirm != QtWidgets.QMessageBox.Yes:
            return

        try:
            response = api.delete_user(self.username, user["id"])
        except Exception:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Không thể kết nối tới server để xóa người dùng")
            return

        if response.status_code == 200:
            QtWidgets.QMessageBox.information(self, "Thành công", "Xóa tài khoản thành công")
            self.load_users()
        else:
            QtWidgets.QMessageBox.warning(self, "Lỗi", response.text or f"Lỗi: {response.status_code}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
