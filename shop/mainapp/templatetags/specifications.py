from django import template
from django.utils.safestring import mark_safe


register = template.Library()


TABLE_HEAD = """
                <table class="table">
                    <tbody>
            """

TABLE_CONTENT = """
                        <tr>
                            <td>{name}</td>
                            <td>{value}</td>
                        </tr>
            """

TABLE_TAIL = """
                    </tbody>
                </table>
            """

PRODUCT_SPEC = {

    "notebook": {
        'Диагональ': 'diagonal',
        'Тип дисплея': 'display_type',
        'Процессор': 'processor_freg',
        'Оперативная память': 'ram',
        'Видеокарта': 'video',
        'Время работы аккумалятора': 'time_without_charge'
    },
    "smartphone": {
        'Диагональ': 'diagonal',
        'Тип дисплея': 'display_type',
        'Разрешение экрана': 'resolution',
        'Заряд аккумулятора': 'accum_volume',
        'Оперативная память': 'ram',
        'Наличие слота для внешней карты памяти': 'sd',
        'Максимальный объем внешней карты памяти': 'sd_volume',
        'Камера, Мп': 'main_can_up',
        'Фронтальная камера, Мп': 'frontal_can_up'
    }

}


def get_product_spec(product, module_name):
    table_content = ''
    print('+++')
    for name, value in PRODUCT_SPEC[module_name].items():
        sTab = TABLE_CONTENT.format(name=name, value=getattr(product, value))
        table_content += sTab
    return table_content


@register.filter
def product_spec(product):
    model_name = product.__class__._meta.model_name
    return mark_safe(TABLE_HEAD + get_product_spec(product, model_name) + TABLE_TAIL)