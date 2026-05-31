import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"


def login(username, password):
    return requests.post(
        f"{BASE_URL}/login",
        json={"username": username, "password": password},
        timeout=10,
    )


def get_documents():
    response = requests.get(f"{BASE_URL}/documents", timeout=10)
    response.raise_for_status()
    return response.json()


def download_document(document_id, username, password):
    return requests.get(
        f"{BASE_URL}/download/{document_id}",
        params={"username": username, "password": password},
        stream=True,
        timeout=20,
    )


def update_document(document_id, username, title=None, password=None):
    payload = {"username": username, "title": title, "password": password}
    return requests.put(f"{BASE_URL}/update/{document_id}", json=payload, timeout=10)


def delete_document(document_id, username):
    return requests.delete(
        f"{BASE_URL}/delete/{document_id}",
        params={"username": username},
        timeout=10,
    )


def get_history(document_id):
    response = requests.get(f"{BASE_URL}/history/{document_id}", timeout=10)
    response.raise_for_status()
    return response.json()


def get_users(admin_username):
    response = requests.get(
        f"{BASE_URL}/users",
        params={"admin_username": admin_username},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def create_user(admin_username, username, password, role):
    response = requests.post(
        f"{BASE_URL}/users",
        params={"admin_username": admin_username},
        json={"username": username, "password": password, "role": role},
        timeout=10,
    )
    return response


def update_user(admin_username, user_id, username=None, password=None, role=None):
    payload = {"username": username, "password": password, "role": role}
    return requests.put(
        f"{BASE_URL}/users/{user_id}",
        params={"admin_username": admin_username},
        json={k: v for k, v in payload.items() if v is not None},
        timeout=10,
    )


def delete_user(admin_username, user_id):
    return requests.delete(
        f"{BASE_URL}/users/{user_id}",
        params={"admin_username": admin_username},
        timeout=10,
    )


def upload_document(title, uploader, password, file_path):
    with open(file_path, "rb") as file_handle:
        files = {"file": (Path(file_path).name, file_handle)}
        data = {"title": title, "uploader": uploader, "password": password}
        return requests.post(f"{BASE_URL}/upload", data=data, files=files, timeout=20)
