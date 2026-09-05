from flask import abort, session, redirect, current_app, request
from functools import wraps


def check_auth(admin=False, link='/lk'):
    def my_decorator(func):
        @wraps(func)
        def my_wrapper(*args, **kwargs):
            if not request.headers.get('x-real-ip') or 'user' in session:
                if admin:
                    if not request.headers.get('x-real-ip') or session['email'] in current_app.config["admins"]:
                        return func(*args, **kwargs)
                    else:
                        return abort(403, 'This page only for administrators.')
                else:
                    return func(*args, **kwargs)
            else:
                return redirect(link)
        return my_wrapper
    return my_decorator