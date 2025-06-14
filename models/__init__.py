from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .table import Table
from .reservation import Reservation
from .menu import MenuCategory, MenuItem, Order, OrderItem
from .payment import Payment
from .activity_log import ActivityLog
from .notification import Notification

from . import event_listeners  

login_manager = LoginManager()
login_manager.login_view = 'auth_bp.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))