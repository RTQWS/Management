
import django_tables2 as tables
from django.contrib.auth.models import User

class UserTable(tables.Table):
    edit = tables.TemplateColumn(
        '<a class="redact" href="{% url "edit_user" record.id %}"><i class="fa-solid fa-pencil"></i></a>',
        verbose_name='Редактировать'
    )
    delete = tables.TemplateColumn(
        '<a class="redact" href="{% url "delete_user" record.id %}"><i class="fa-regular fa-circle-xmark delete"></i></a>',
        verbose_name='Удалить'
    )

    class Meta:
        model = User
        template_name = 'django_tables2/bootstrap.html'  # Используйте примерный шаблон Bootstrap
        fields = ('username', 'email', 'first_name', 'last_name', 'edit', 'delete')