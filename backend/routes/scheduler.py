from logging import exception
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from models import Notification, NotificationUser, User
from extensions import db
from flask import current_app


def send_scheduled_notifications():
    with current_app.app_context():  # Tạo application context
        now = datetime.utcnow()
        notifications = Notification.query.filter(
            Notification.send_option == 'schedule',
            Notification.schedule_time <= now
        ).all()

        for notification in notifications:
            # Xử lý gửi thông báo
            users = User.query.all()  # Ví dụ: gửi đến tất cả người dùng
            for user in users:
                notification_user = NotificationUser(
                    user_id=user.id,
                    notification_id=notification.id
                )
                db.session.add(notification_user)

            # Đánh dấu thông báo đã được gửi
            notification.send_option = 'now'
            db.session.commit()

    
def catch_exception(func):
    def wrapper():
        try:
            func()
        except exception as e:
            print(f'ran into an issue!! {e}')
    return wrapper

scheduler = BackgroundScheduler()
scheduler.add_job(catch_exception(send_scheduled_notifications), 'interval', minutes=1)  # Chạy mỗi phút
