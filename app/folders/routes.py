from flask import render_template, redirect, url_for, flash, request, jsonify
from . import folders_bp
from flask_login import login_required, current_user
from ..models import Folder, Note
from ..extensions import db


    # Replace the current folders() with this API endpoint
@folders_bp.route('/', methods=['GET'])
@login_required
def folders():
    folders = Folder.query.filter_by(user_id=current_user.id).order_by(Folder.created_at.asc()).all()
    result = []
    for i, f in enumerate(folders):
        result.append({
            'id': f.id,
            'name': f.name,
            'notes_count': len(f.notes),
            'is_default': (i == 0)
        })
    return jsonify({'folders': result})


@folders_bp.route('/create', methods=['POST'])
@login_required
def create_folder():
    # Accept JSON or form-encoded payload
    name = (request.form.get('name') if request.form else None) or (request.get_json(silent=True) or {}).get('name')
    if not name or not name.strip():
        return jsonify({'error': 'Name required'}), 400
    name = name.strip()
    folder = Folder(name=name, owner=current_user)
    db.session.add(folder)
    db.session.commit()
    # return created resource with notes count
    return jsonify({'id': folder.id, 'name': folder.name, 'notes_count': len(folder.notes)}), 201


@folders_bp.route('/<int:folder_id>', methods=['GET', 'POST'])
def folder(folder_id):
    return render_template("/folder.html")


@folders_bp.route('/<int:folder_id>/rename', methods=['POST'])
@login_required
def rename_folder(folder_id):
    data = request.get_json() or {}
    new_name = (data.get('name') or '').strip()
    if not new_name:
        return jsonify({'error': 'Name required'}), 400
    folder = Folder.query.get_or_404(folder_id)
    if folder.user_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403
    folder.name = new_name
    db.session.commit()
    return jsonify({'id': folder.id, 'name': folder.name})


@folders_bp.route('/<int:folder_id>', methods=['DELETE'])
@login_required
def delete_folder(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    if folder.user_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403
    db.session.delete(folder)
    db.session.commit()
    return jsonify({'ok': True})


@folders_bp.route('/<int:folder_id>/notes', methods=['GET'])
@login_required
def folder_notes(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    if folder.user_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403
    notes = []
    for n in Note.query.filter_by(folder_id=folder.id, user_id=current_user.id).order_by(Note.created_at.desc()).all():
        notes.append({
            'id': n.id,
            'title': n.title,
            'content': n.content,
            'created_at': n.created_at.isoformat()
        })
    return jsonify({'notes': notes})