from flask import render_template, request, jsonify, abort
from . import notes_bp
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Folder, Note


def _get_folder_or_404(folder_id):
    folder = db.session.get(Folder, int(folder_id))
    if folder is None:
        abort(404)
    return folder


def _get_note_or_404(note_id):
    note = db.session.get(Note, note_id)
    if note is None:
        abort(404)
    return note

@notes_bp.route('/')
def notes():
    return render_template("/notes.html")

@notes_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_note():
    # HTML page fallback (legacy)
    if request.method != 'POST':
        return render_template("/create_note.html")

    data = request.get_json(silent=True) or {}
    folder_id = data.get('folder_id')
    title = (data.get('title') or 'New Note').strip() or 'New Note'
    content = (data.get('content') or 'Description').strip() or 'Description'

    if not folder_id:
        return jsonify({'error': 'folder_id required'}), 400

    folder = _get_folder_or_404(folder_id)
    if folder.user_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403

    note = Note(title=title, content=content, author=current_user, folder=folder)
    db.session.add(note)
    db.session.commit()

    return jsonify({
        'note': {
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'created_at': note.created_at.isoformat(),
            'folder_id': folder.id,
        }
    }), 201

@notes_bp.route('/<int:note_id>', methods=['GET', 'DELETE'])
@login_required
def note(note_id):
    if request.method == 'DELETE':
        note_obj = _get_note_or_404(note_id)
        if note_obj.user_id != current_user.id:
            return jsonify({'error': 'Forbidden'}), 403
        folder_id = note_obj.folder_id
        db.session.delete(note_obj)
        db.session.commit()
        remaining = 0
        if folder_id:
            remaining = Note.query.filter_by(user_id=current_user.id, folder_id=folder_id).count()
        return jsonify({'ok': True, 'folder_id': folder_id, 'notes_count': remaining})

    return render_template("notes/note.html")

@notes_bp.route('/<int:note_id>/edit', methods=['GET', 'POST'])
def note_edit(note_id: int):
    return render_template('notes/edit.html', note_id=note_id)