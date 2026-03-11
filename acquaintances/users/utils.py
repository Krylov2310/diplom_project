import os
import uuid


def user_directory_path_gallery(instance, filename):
    """
    Возвращает путь для сохранения файла: images/{user_id}/{filename}
    Для Gallery instance — это объект Gallery, поэтому берём author.id
    """
    print('\033[31muser_directory_path_gallery\033[0m', instance, filename)

    # Получаем автора галереи (пользователя)
    if hasattr(instance, 'author') and instance.author:
        user_id = instance.author.id
        username = str(user_id)
    else:
        # Если автор не назначен, генерируем уникальный идентификатор
        username = f'unknown_{uuid.uuid4().hex[:8]}'

    # Формируем путь: images/{user_id}/{filename}
    return os.path.join('images', username, filename)
