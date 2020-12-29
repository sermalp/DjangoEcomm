import sys
from PIL import Image
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from django.urls import reverse


User = get_user_model()

# Проектируем объекты приложения:
# 1 Category - Категория продукта
# 2 Product - продукт, товар - что продаем
# 3 CartProduct - промежуточный продукт, который относится только к корзине
# 4 Cart - Корзина
# 5 Order - Заказ
# *************
# 6 Customer - Покупатель
# 7 Specification - Характеристики товаров


def get_product_url(obj, viewname):
    ct_model = obj.__class__._meta.model_name
    return reverse(viewname, kwargs={'ct_model': ct_model, 'slug':obj.slug})


class MinResolutinErrorException(Exception):
    pass


class MaxResolutinErrorException(Exception):
    pass


class LatestProductsManager:

    @staticmethod
    def get_products_for_models(*args, **kwargs):
        with_respect_to = kwargs.get('with_respect_to')
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            model_products = ct_model.model_class()._base_manager.all().order_by('-d')[:5]
            products.extend(model_products)

        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists():
                if with_respect_to in args:
                    return sorted(
                        products, key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to), reverse=True
                    )
        return products


class LatestProducts:

    objects = None


class Category(models.Model):

    name = models.CharField(max_length=255, verbose_name='Имя категории')
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):

    MIN_RESOLUTION = (180, 180)
    MAX_RESOLUTION = (800, 800)
    MAX_IMAGE_SIZE = 3145728

    class Meta:
        abstract = True

    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='Наименование')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Изображение')
    description = models.TextField(verbose_name='Описание', null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Цена')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # пример с проверкой минимального и максимального разрешения
        image = self.image
        img = Image.open(image)
        min_height, min_width = self.MIN_RESOLUTION
        max_height, max_width = self.MAX_RESOLUTION
        if img.height < min_height or img.width < min_width:
            raise MinResolutinErrorException('Разрешение изображения меньше минимального')
        if img.height > max_height or img.width > max_width:
            raise MaxResolutinErrorException('Разрешение изображения больше максимального')
        # # пример с обрезкой изображения до нужного разрешения
        # image = self.image
        # img = Image.open(image)
        # max_height, max_width = self.MAX_RESOLUTION
        # if img.height > max_height or img.width > max_width:
        #     new_img = img.convert('RGB')
        #     #print(, self.MAX_RESOLUTION)
        #     resized_new_img = new_img.resize((200, 200), Image.ANTIALIAS)
        #     filestream = BytesIO()
        #     resized_new_img.save(filestream, 'JPEG', quality=80)
        #     filestream.seek(0)
        #     name = '{}.{}'.format(*self.image.name.split('.'))
        #     self.image = InMemoryUploadedFile(
        #         filestream, 'ImageField', name, 'jpeg/image', sys.getsizeof(filestream), None
        #     )
        super().save(*args, **kwargs)


class Notebook(Product):

    diagonal = models.CharField(max_length=255, verbose_name='Диагональ')
    display_type = models.CharField(max_length=255, verbose_name='Тип дисплея')
    processor_freg = models.CharField(max_length=255, verbose_name='Частота процессора')
    ram = models.CharField(max_length=255, verbose_name='Оперативная память')
    video = models.CharField(max_length=255, verbose_name='Видеокарта')
    time_without_charge = models.CharField(max_length=255, verbose_name='Время работы аккумулятора')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class Smartphone(Product):

    diagonal = models.CharField(max_length=255, verbose_name='Диагональ')
    display_type = models.CharField(max_length=255, verbose_name='Тип дисплея')
    resolution = models.CharField(max_length=255, verbose_name='Разрешение экрана')
    accum_volume = models.CharField(max_length=255, verbose_name='Объем батареи')
    ram = models.CharField(max_length=255, verbose_name='Оперативная память')
    sd = models.BooleanField(default=True, verbose_name='Расширяемая память')
    sd_volume = models.CharField(max_length=255, verbose_name='Максимальный объем расширяемой память')
    main_can_up = models.CharField(max_length=255, verbose_name='Главная камера')
    frontal_can_up = models.CharField(max_length=255, verbose_name='Фронтальная камера')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class CardProduct(models.Model):

    user = models.ForeignKey('Customer', on_delete=models.CASCADE, verbose_name='Покупатель')
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, verbose_name='Корзина', related_name='related_products')
    #product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name='Корзина')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Общая цена')


    def __str__(self):
        return "Продукт: {} (для корзины)".format(self.content_object.title)


class Cart(models.Model):

    owner = models.ForeignKey('Customer', verbose_name='Владелец', on_delete=models.CASCADE)
    products = models.ManyToManyField(CardProduct, blank=True, related_name='related_card')
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(verbose_name='Общая цена', max_digits=9, decimal_places=2)
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class Customer(models.Model):

    User = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='Номер телефона')
    address = models.CharField(max_length=255, verbose_name='Адрес')

    def __str__(self):
        return "Покупатель: {} {}".format(self.user.fitst_name, self.user.last_name)


class Specification(models.Model):

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    name = models.CharField(max_length=255, verbose_name='Имя товара для характеристик')

    def __str__(self):
        return "Характеристики для товара {}".format(self.name)