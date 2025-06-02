
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# ONE shared SQLAlchemy() instance
db = SQLAlchemy()

# Import every model here so that db.metadata sees all tables
from .user import User
from .table import Table
from .reservation import Reservation
from .menu_category import MenuCategory
from .menu_item import MenuItem
from .order import Order
from .order_item import OrderItem
from .payment import Payment
from .activity_log import ActivityLog
from .notification import Notification

# Import event listeners last, so models are all registered
from . import event_listeners

login_manager = LoginManager()
# Flask-Login configuration
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
