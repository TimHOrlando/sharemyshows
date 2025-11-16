from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Comment, Show

comments_bp = Blueprint('comments', __name__, url_prefix='/api/comments')

@comments_bp.route('', methods=['POST'])
@jwt_required()
def create_comment():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data or not all(k in data for k in ('show_id', 'text')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    show = Show.query.get(data['show_id'])
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    comment = Comment(
        user_id=user_id,
        show_id=data['show_id'],
        text=data['text']
    )
    
    try:
        db.session.add(comment)
        db.session.commit()
        return jsonify(comment.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create comment', 'details': str(e)}), 500

@comments_bp.route('/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    user_id = int(get_jwt_identity())
    comment = Comment.query.filter_by(id=comment_id, user_id=user_id).first()
    
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404
    
    data = request.get_json()
    
    if 'text' in data:
        comment.text = data['text']
    
    try:
        db.session.commit()
        return jsonify(comment.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update comment', 'details': str(e)}), 500

@comments_bp.route('/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    user_id = int(get_jwt_identity())
    comment = Comment.query.filter_by(id=comment_id, user_id=user_id).first()
    
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404
    
    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'message': 'Comment deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete comment', 'details': str(e)}), 500

@comments_bp.route('/show/<int:show_id>', methods=['GET'])
@jwt_required()
def get_show_comments(show_id):
    show = Show.query.get(show_id)
    
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    comments = Comment.query.filter_by(show_id=show_id).order_by(Comment.created_at.desc()).all()
    return jsonify([comment.to_dict() for comment in comments]), 200
