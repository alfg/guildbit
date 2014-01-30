from functools import wraps

from flask.ext.login import current_user
from flask import redirect


def admin_required(fn):
    """
    View decorator to require an admin. ADMIN is ROLE = 1
    """
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if current_user.get_role() != 1:
            return redirect("/")
        return fn(*args, **kwargs)
    return decorated_view
