import inspect
from functools import wraps

from flask import request, redirect, session

import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError

# Try to retrieve the logger from the existing Flask app, or else use the
# standard Python logging
try:
    from .main import app
    logger = app.logger

except:
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

if not firebase_admin._apps:
    cred = credentials.Certificate("credentials/firebase-adminsdk.json")
    fb_app = firebase_admin.initialize_app(credential=cred, name='watchdog')


def auth_required(func):
    """
    Method that checks and validates the Firebase token and returns the user
    data if everything's ok, or a 403 if not.

    Note that this decorator injects a new parameter 'user' to the original
    function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):

        # Retrieve the token from the cookie session
        id_token = session.get('id_token')

        # Verify the token and return the user data if correct
        user = verify_token(request, id_token)
        logger.info(f'Verified user/token: {user}')

        if not user:
            #return {'msg': 'No user'}, 403
            session['last_url_in_request'] = request.url
            return redirect("/login", code=302)

        if 'user' in inspect.signature(func).parameters:
            kwargs['user'] = user

        return func(*args, **kwargs)

    return wrapper


def verify_token(request, id_token):
    """
    Method that uses the Firebase Admin Authentication module to verify the
    token and decode it, returning the user's data if correct.

    Args:
        request (Flask request): incoming Flask request
        id_token (str): ID of the Firebase token to verify

    Returns:
        dict: user data or None
    """
    try:
        decoded_token = auth.verify_id_token(id_token, fb_app)
        return decoded_token

    except ValueError as e:
        logger.error(f'{e}')

    except ExpiredIdTokenError as e:
        logger.error(f'Expired token: {e}')

    except InvalidIdTokenError as e:
        logger.error(f'Invalid token: {e}')
