import base64
import math
import os

from app.shemas import Product
from app.models.product import ProductModel

"""
Функции общего назначения
"""


def pagination(list_item: list, page: int, size: int):
    """
    Разделение элементов списка на страницы по заданному количеству и вывод части списка,
    соответствующего номеру переданной страницы.
    :param list_item: Список элементов, который необходимо разбить на страницы.
    :param page: Номер страницы.
    :param size: Количество элементов на странице.
    :return: Список элементов исходного списка соответствующий на указанной странице.
    """
    if page < 0:
        page = 0
    offset_min = page * size
    offset_max = (page + 1) * size
    if offset_min > len(list_item):
        if size > len(list_item):
            offset_min = 0
        else:
            offset_min = len(list_item) - size
    if offset_max > len(list_item):
        offset_max = len(list_item)
    result = list_item[offset_min:offset_max], {
        "page": page,
        "size": size,
        "total": math.ceil(len(list_item) / size) - 1,
        "pages": [x for x in range(math.ceil(len(list_item) / size))]
    }
    return result


def image_to_str(product: Product | ProductModel, key: str):
    """
    Преобразование изображения в строку символов.
    :param product: Модель продукта для которого выполняется преобразование картинки в строку.
    :param key: Ключ определяющий размер картинки для отображения.
    :return: Строка символов соответствующая изображению переданному продукту.
    """
    path = os.getcwd()
    if 'app' not in path:
        path += '/app'
    if key == 'list':
        file_path = os.path.join(path+"/templates/product/image/" + product.name, 'small_' + product.img)
    else:
        file_path = os.path.join(path+"/templates/product/image/" + product.name, product.img)
    try:
        with open(file_path, "rb") as image_file:
            contents = image_file.read()
        base64_encoded_image = base64.b64encode(contents).decode("utf-8")
        _, format_file = os.path.splitext(file_path)
    except Exception:
        base64_encoded_image = ''
        format_file = 'jpeg'
    return base64_encoded_image, format_file
