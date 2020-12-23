from django.contrib import admin

# Register your models here.

# Регистрация модулей в админке
from.models import *

admin.site.register(Category)
admin.site.register(Notebook)
admin.site.register(Smartphone)
admin.site.register(CardProduct)
admin.site.register(Cart)
admin.site.register(Customer)
