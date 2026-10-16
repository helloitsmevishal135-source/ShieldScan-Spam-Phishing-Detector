import mongoengine
from flask_login import LoginManager

# MongoEngine connection is initialised in create_app() via mongoengine.connect()
# This module exposes a thin helper so the rest of the code can call
# db.session.add / db.session.commit style helpers without breaking.
class _MongoSessionShim:
    """Minimal shim so legacy db.session.add/commit calls are no-ops with MongoEngine."""
    def add(self, obj): pass
    def commit(self): pass
    def rollback(self): pass

class _MongoDB:
    session = _MongoSessionShim()

db = _MongoDB()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
