"""
Integration tests for NoteIt.

Test cross-module flows: auth + folders + notes working together.
Uses real app, database, and sessions—no mocks.
"""

import pytest
from app.models import User, Folder, Note
from app import db

from app.tests.conftest import (
    URL_LOGIN,
    URL_REGISTER,
    URL_LOGOUT,
    URL_DASHBOARD,
)

URL_FOLDERS = "/folders"
URL_NOTES = "/notes"


# --- Full user journey ---


def test_full_auth_journey_register_login_logout(client, app):
    """User can register, login, access dashboard, and logout."""
    # 1. Register
    register_data = {
        "username": "journeyuser",
        "email": "journey@example.com",
        "password": "securepass123",
    }
    r = client.post(URL_REGISTER, data=register_data)
    assert r.status_code == 302
    assert URL_LOGIN in r.location

    # 2. Login
    r = client.post(URL_LOGIN, data={"username": "journeyuser", "password": "securepass123"})
    assert r.status_code == 302
    assert URL_DASHBOARD in r.location

    # 3. Dashboard loads
    r = client.get(URL_DASHBOARD)
    assert r.status_code == 200
    assert b"dashboard" in r.data.lower() or b"Personal" in r.data

    # 4. Logout
    r = client.post(URL_LOGOUT)
    assert r.status_code == 302
    assert URL_LOGIN in r.location

    # 5. Dashboard no longer accessible
    r = client.get(URL_DASHBOARD)
    assert r.status_code == 302
    assert URL_LOGIN in r.location


def test_full_folder_and_note_flow(client, app, registered_user):
    """Logged-in user can create folder, create note, and fetch folder notes."""
    # 1. Login
    r = client.post(URL_LOGIN, data=registered_user)
    assert r.status_code == 302

    # 2. Create folder
    r = client.post(f"{URL_FOLDERS}/create", json={"name": "Work"})
    assert r.status_code == 201
    data = r.get_json()
    folder_id = data["id"]
    assert data["name"] == "Work"
    assert data["notes_count"] == 0

    # 3. Create note in folder
    r = client.post(
        f"{URL_NOTES}/create",
        json={
            "folder_id": folder_id,
            "title": "My first note",
            "content": "Some content here",
        },
    )
    assert r.status_code == 201
    note_data = r.get_json()["note"]
    assert note_data["title"] == "My first note"
    assert note_data["content"] == "Some content here"
    assert note_data["folder_id"] == folder_id
    note_id = note_data["id"]

    # 4. Get folder notes
    r = client.get(f"{URL_FOLDERS}/{folder_id}/notes")
    assert r.status_code == 200
    notes = r.get_json()["notes"]
    assert len(notes) == 1
    assert notes[0]["title"] == "My first note"
    assert notes[0]["id"] == note_id

    # 5. List folders (includes Personal from fixture + Work)
    r = client.get(URL_FOLDERS + "/")
    assert r.status_code == 200
    folders = r.get_json()["folders"]
    assert any(f["name"] == "Work" for f in folders)
    assert any(f["name"] == "Personal" for f in folders)


def test_protected_routes_redirect_unauthenticated_users(client):
    """Unauthenticated requests to protected routes redirect to login."""
    protected = [
        URL_DASHBOARD,
        f"{URL_FOLDERS}/",
        f"{URL_FOLDERS}/create",
        f"{URL_NOTES}/create",
    ]
    for url in protected:
        r = client.get(url) if url != f"{URL_FOLDERS}/create" else client.post(url, json={})
        method = "GET" if url != f"{URL_FOLDERS}/create" else "POST"
        if method == "POST" and "create" in url:
            r = client.post(url, json={"name": "x"}) if "folders" in url else client.post(url, json={"folder_id": 1})
        assert r.status_code == 302, f"Expected redirect for {url}"
        assert URL_LOGIN in r.location, f"Expected login redirect for {url}"


def test_user_isolation_cannot_access_other_users_folder(client, app, registered_user):
    """User A cannot access User B's folder."""
    # Create user A (from fixture) and login
    r = client.post(URL_LOGIN, data=registered_user)
    assert r.status_code == 302

    # Create folder as user A
    r = client.post(f"{URL_FOLDERS}/create", json={"name": "UserA Folder"})
    assert r.status_code == 201
    folder_id = r.get_json()["id"]

    # Logout
    client.post(URL_LOGOUT)

    # Create and login as user B
    with app.app_context():
        from werkzeug.security import generate_password_hash
        user_b = User(
            username="userb",
            email="userb@example.com",
            password_hash=generate_password_hash("passb"),
            is_active=True,
        )
        db.session.add(user_b)
        db.session.commit()

    r = client.post(URL_LOGIN, data={"username": "userb", "password": "passb"})
    assert r.status_code == 302

    # User B tries to access User A's folder
    r = client.get(f"{URL_FOLDERS}/{folder_id}/notes")
    assert r.status_code == 403
    assert r.get_json().get("error") == "Forbidden"

    # User B tries to rename User A's folder
    r = client.post(f"{URL_FOLDERS}/{folder_id}/rename", json={"name": "Hacked"})
    assert r.status_code == 403

    # User B tries to delete User A's folder
    r = client.delete(f"{URL_FOLDERS}/{folder_id}")
    assert r.status_code == 403


def test_user_isolation_cannot_access_other_users_note(client, app, registered_user):
    """User A cannot access or delete User B's note."""
    # Login as user A, create folder and note
    r = client.post(URL_LOGIN, data=registered_user)
    assert r.status_code == 302
    r = client.post(f"{URL_FOLDERS}/create", json={"name": "A Folder"})
    folder_id = r.get_json()["id"]
    r = client.post(
        f"{URL_NOTES}/create",
        json={"folder_id": folder_id, "title": "A Note", "content": "secret"},
    )
    assert r.status_code == 201
    note_id = r.get_json()["note"]["id"]

    # Logout, create and login as user B
    client.post(URL_LOGOUT)
    with app.app_context():
        from werkzeug.security import generate_password_hash
        user_b = User(
            username="userb2",
            email="userb2@example.com",
            password_hash=generate_password_hash("passb"),
            is_active=True,
        )
        db.session.add(user_b)
        db.session.flush()  # assign user_b.id before creating folder
        personal = Folder(name="Personal", owner=user_b)
        db.session.add(personal)
        db.session.commit()

    r = client.post(URL_LOGIN, data={"username": "userb2", "password": "passb"})
    assert r.status_code == 302

    # User B tries to delete User A's note
    r = client.delete(f"{URL_NOTES}/{note_id}")
    assert r.status_code == 403


def test_folder_crud_flow(client, app, registered_user):
    """User can create, rename, and delete a folder."""
    r = client.post(URL_LOGIN, data=registered_user)
    assert r.status_code == 302

    # Create
    r = client.post(f"{URL_FOLDERS}/create", json={"name": "ToRename"})
    assert r.status_code == 201
    folder_id = r.get_json()["id"]

    # Rename
    r = client.post(f"{URL_FOLDERS}/{folder_id}/rename", json={"name": "Renamed"})
    assert r.status_code == 200
    assert r.get_json()["name"] == "Renamed"

    # Verify in list
    r = client.get(f"{URL_FOLDERS}/")
    folders = r.get_json()["folders"]
    assert any(f["name"] == "Renamed" for f in folders)

    # Delete (must not delete Personal - we're deleting "Renamed")
    r = client.delete(f"{URL_FOLDERS}/{folder_id}")
    assert r.status_code == 200
    assert r.get_json()["ok"] is True

    # Gone from list
    r = client.get(f"{URL_FOLDERS}/")
    folders = r.get_json()["folders"]
    assert not any(f["name"] == "Renamed" for f in folders)


def test_note_create_and_delete(client, app, registered_user):
    """User can create and delete a note."""
    r = client.post(URL_LOGIN, data=registered_user)
    assert r.status_code == 302

    # Get Personal folder id (first in list)
    r = client.get(f"{URL_FOLDERS}/")
    folders = r.get_json()["folders"]
    personal = next(f for f in folders if f["name"] == "Personal")
    folder_id = personal["id"]

    # Create note
    r = client.post(
        f"{URL_NOTES}/create",
        json={"folder_id": folder_id, "title": "To Delete", "content": "content"},
    )
    assert r.status_code == 201
    note_id = r.get_json()["note"]["id"]

    # Delete note
    r = client.delete(f"{URL_NOTES}/{note_id}")
    assert r.status_code == 200
    assert r.get_json()["ok"] is True

    # Note gone from folder
    r = client.get(f"{URL_FOLDERS}/{folder_id}/notes")
    notes = r.get_json()["notes"]
    assert not any(n["id"] == note_id for n in notes)


def test_new_user_gets_personal_folder_on_register(client, app):
    """Registering creates a user and default Personal folder."""
    r = client.post(
        URL_REGISTER,
        data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass",
        },
    )
    assert r.status_code == 302

    r = client.post(URL_LOGIN, data={"username": "newuser", "password": "securepass"})
    assert r.status_code == 302

    r = client.get(f"{URL_FOLDERS}/")
    assert r.status_code == 200
    folders = r.get_json()["folders"]
    assert len(folders) >= 1
    assert any(f["name"] == "Personal" for f in folders)
