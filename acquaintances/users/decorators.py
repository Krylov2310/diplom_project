from functools import wraps
from django.http import HttpResponseForbidden


def user_owns_profile(view_func):
    print('\033[31muser_owns_profile\033[0m', view_func)

    @wraps(view_func)
    def wrapper(request, user_id, *args, **kwargs):
        print('\033[31mwrapper\033[0m', user_id)
        if request.user.id != int(user_id):
            return HttpResponseForbidden("Доступ запрещён: вы не владелец этого профиля")
        return view_func(request, user_id, *args, **kwargs)

    return wrapper
