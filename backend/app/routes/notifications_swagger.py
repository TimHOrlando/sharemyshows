"""
Notifications API Routes - Flask-RESTX Implementation
Handles in-app notification CRUD operations
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db, Notification

api = Namespace('notifications', description='Notification operations')


@api.route('')
class NotificationList(Resource):
    @api.doc('get_notifications', security='jwt')
    @jwt_required()
    def get(self):
        """Get paginated notifications for current user"""
        current_user_id = int(get_jwt_identity())
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        pagination = Notification.query.filter_by(user_id=current_user_id)\
            .order_by(Notification.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

        return {
            'notifications': [n.to_dict() for n in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages,
        }


@api.route('/unread-count')
class UnreadCount(Resource):
    @api.doc('get_unread_count', security='jwt')
    @jwt_required()
    def get(self):
        """Get count of unread notifications"""
        current_user_id = int(get_jwt_identity())
        count = Notification.query.filter_by(
            user_id=current_user_id,
            read=False
        ).count()
        return {'unread_count': count}


@api.route('/mark-read')
class MarkAllRead(Resource):
    @api.doc('mark_all_read', security='jwt')
    @jwt_required()
    def put(self):
        """Mark all notifications as read"""
        current_user_id = int(get_jwt_identity())
        Notification.query.filter_by(
            user_id=current_user_id,
            read=False
        ).update({'read': True}, synchronize_session='fetch')
        db.session.commit()
        return {'message': 'All notifications marked as read'}


@api.route('/<int:notification_id>/read')
class MarkOneRead(Resource):
    @api.doc('mark_one_read', security='jwt')
    @jwt_required()
    def put(self, notification_id):
        """Mark a single notification as read"""
        current_user_id = int(get_jwt_identity())
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user_id
        ).first()

        if not notification:
            return {'error': 'Notification not found'}, 404

        notification.read = True
        db.session.commit()
        return notification.to_dict()
