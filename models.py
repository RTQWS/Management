import datetime

from django.utils.safestring import mark_safe

from main.service import send
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


class AutoDateMixin:
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)


class Provider(models.Model):
    name = models.CharField("Наименование", max_length=300)
    rating = models.CharField("Рейтинг", max_length=100, default="0")

    def __str__(self):
        return str(self.name)


class Gates(models.Model):
    gates = models.CharField("Ворота", max_length=50)
    timeslot = models.CharField("Слот", max_length=250)
    bussy = models.CharField("Занятость", max_length=50)
    day = models.DateField("Дата")

    def __str__(self):
        return self.gates


class VehicleTypeChoises:
    THEIR = 'svoi'
    HIRED = 'naem'
    VEHICLE_TYPE_CHOISES = [
        (THEIR, 'Собственные ТС'),
        (HIRED, 'Наемные ТС'),
    ]

    VEHICLE_TYPE_DICT = {
        THEIR: 'Собственные ТС',
        HIRED: 'Наемные ТС',

    }


class GateTypeChoises:
    SHIPMENTS = 'shipments'
    DISCHARGE = 'discharge'
    UNIVERSAL = 'universal'
    GATE_TYPE_CHOISES = [
        (SHIPMENTS, 'Отгрузка'),
        (DISCHARGE, 'Выгрузка'),
        (UNIVERSAL, 'Универсальные'),
    ]

    GATE_TYPE_DICT = {
        SHIPMENTS: 'Отгрузка',
        DISCHARGE: 'Выгрузка',
        UNIVERSAL: 'Универсальные',
    }


class People(AutoDateMixin, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default="1")
    # user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField("Телефон", max_length=100)
    # type_vehicle = models.CharField("Тип тс", max_length=100, choices=VehicleTypeChoices.VEHICLE_TYPE_CHOICES)


class ProcedureChoices:
    Shipment = 'otgruz'
    Loading = 'zagruz'

    PROCEDURE_CHOICES = [

        (Shipment, 'Выгрузка'),
        (Loading, 'Загрузка'),

    ]

    PROCEDURE_DICT = {

        Shipment: 'Выгрузка',
        Loading: 'Загрузка',

    }


class RoleChoices:
    PRIEM = 'priemka'
    MENED = 'menedger'
    ADMIN = 'admin'
    DISPECHER = 'dispecher'
    KPP = 'kpp'
    USER = 'user'

    ROLE_CHOICES = [
        (PRIEM, 'Приемка'),
        (DISPECHER, 'Диспечер'),
        (KPP, 'Служба безопастности'),
        (MENED, 'Менеджер'),
        (ADMIN, 'Админ'),
        (USER, 'Поставщик'),

    ]

    ROLE_DICT = {
        DISPECHER: 'Диспечер',
        KPP: 'Служба безопастности',
        PRIEM: 'Приемка',
        MENED: 'Менеджер',
        ADMIN: 'Админ',
        USER: 'Поставщик',
    }


class Warehouse(AutoDateMixin, models.Model):
    name = models.CharField("Название", max_length=150)  # blank=True
    quantity_day = models.CharField("Количество дней брони на перед", max_length=100)
    address = models.CharField("Адрес", max_length=100, blank=True)
    href_script = models.CharField("Ссылка из скрипта", max_length=300, blank=True)
    href_map = models.CharField("Ссылка на карту ", max_length=300, blank=True)
    contact_menedger = models.CharField("Контакт менеджера", max_length=100, blank=True)
    contact_rc = models.CharField("Контакт РЦ", max_length=100, blank=True)
    coordinates = models.CharField("Координаты", max_length=100, blank=True)
    image = models.ImageField(upload_to='images/')

    def display_image(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="200px" height="auto">')
        return "No Image"

    display_image.short_description = "Изображение"

    def __str__(self):
        return self.name


class CustomerUser(AutoDateMixin, models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE, default='1')
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField("Название компании", max_length=100, default="-")
    phone = models.CharField("Телефон", max_length=100)

    role = models.CharField("Роль", max_length=100, choices=RoleChoices.ROLE_CHOICES)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    first_login = models.BooleanField(default=True)


class Gate(AutoDateMixin, models.Model):
    name = models.CharField("Название", max_length=250)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    types = models.CharField("Тип ворот", max_length=100, choices=GateTypeChoises.GATE_TYPE_CHOISES)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return ""


#   def save(self, *args, **kwargs):
#      prev_instance = Gate.objects.get(id=self.id)
#     super().save(*args, **kwargs)
#
#       if not self.active and prev_instance.active:
#          emails = Booking.objects.filter(
#             date__lte=datetime.date.today(),
#            gate=self
#       ).values_list(
#          'user__email',
#         flat=True
#    )
#   for email in set(emails):
#      send(email)


class TimeSlot(AutoDateMixin, models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    time_start = models.TimeField()
    time_end = models.TimeField()

    def __str__(self):
        return str(self.time_start)


# class SlotTimeChoices:
#     EIGHT = 'eight'
#     TEN = 'ten'
#     TWELVE = 'twelve'
#     FOURTEEN = 'fourteen'
#     SIXTEEN = 'sixteen'
#     EIGHTEEN = 'eighteen'
#     SLOT_TIME_CHOICES = [
#         (EIGHT,'8:00'),
#         (TEN,'10:00'),
#         (TWELVE,'12:00'),
#         (FOURTEEN,'14:00'),
#         (SIXTEEN,'16:00'),
#         (EIGHTEEN,'18:00'),
#
#
#     ]

# time(hour=10),
# time(hour=12),
# time(hour=14),
# time(hour=16),
# time(hour=18),

class Booking(AutoDateMixin, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    gate = models.ForeignKey(Gate, on_delete=models.CASCADE, default="0")  # null=True
    # choices=slot_times
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, default="0")
    supplier = models.CharField("Статус", max_length=200, default="-")
    volume = models.IntegerField("Объем", default="0")
    pick_begin = models.DateTimeField(default="2022-01-01")
    pick_gate = models.DateTimeField(default="2022-01-01")
    pick_end = models.DateTimeField(default="2022-01-01")
    coming = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    message = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return str(self.user)

    def get_absolute_url(self):
        return "/timeslots"


@receiver(pre_save, sender=Booking)
def update_booking_message(sender, instance, **kwargs):
    # Проверяем, изменилось ли поле date
    if instance.pk:  # если объект уже существует
        old_date = Booking.objects.get(pk=instance.pk).date
        old_timeslot = Booking.objects.get(pk=instance.pk).timeslot
        if instance.date != old_date:
            # Обновляем поле message
            instance.message = 'Дата была изменена с {} на {}'.format(old_date, instance.date)
        if instance.timeslot != old_timeslot:
            # Обновляем поле message
            instance.message = 'Временной слот был изменен с {} на {}'.format(old_timeslot, instance.timeslot)
        if instance.timeslot != old_timeslot and instance.date != old_date:
            # Обновляем поле message
            instance.message = 'Временной слот был изменен с {} на {} и дата изменена с {} на {}'.format(old_timeslot,
                                                                                                         instance.timeslot,
                                                                                                         old_date,
                                                                                                         instance.date)


class Delivery(AutoDateMixin, models.Model):
    provider_id = models.IntegerField()
    provider_name = models.CharField("Название поставщика", max_length=200, default="-")
    store_id = models.IntegerField()
    store_name = models.CharField("Название склада", max_length=200, default="-")
    volume = models.IntegerField()
    weight_gross = models.IntegerField()
    delivery_name = models.CharField("Тип доставки", max_length=200, default="-")
    provider_manager = models.CharField("Менеджер", max_length=200, default="-")
    driver_id = models.IntegerField()
    driver_name = models.CharField("Водитель", max_length=200, default="-")
    expected_date = models.DateField(default="2022-01-01")
    docnumber = models.CharField("Приходная накладная", max_length=200, default="-")


class Car(AutoDateMixin, models.Model):
    state_number = models.CharField("ГОС Номер", max_length=50, default="АА111А")
    name = models.CharField("Наименование машины", max_length=75, default="машина")
    transport_company = models.CharField("", max_length=150, default="-")
    max_volume = models.IntegerField(null=True)

    def __str__(self):
        return str(self.state_number + self.name)


class Driver(AutoDateMixin, models.Model):
    fio = models.CharField("ФИО", max_length=300, default='Петров Петр Петрович')
    max_driving_time = models.TimeField()
    car = models.ForeignKey(Car, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.fio)


class Shipment(AutoDateMixin, models.Model):
    id_ship = models.IntegerField(null=True)
    name = models.CharField("Название маршрута", max_length=350, null=True)
    start_point = models.ForeignKey(Warehouse, on_delete=models.CASCADE, null=True, related_name='start_shipments')
    end_point = models.ForeignKey(Warehouse, on_delete=models.CASCADE, null=True, related_name='end_shipments')
    volume = models.IntegerField()
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, null=True)
    arrival_start_point = models.DateTimeField(null=True)
    arrival_end_point = models.DateTimeField(null=True)
    return_arrival = models.DateTimeField(null=True, blank=True)
    max_distance_from_route = models.IntegerField(null=True)
    сurrent_volume = models.IntegerField(null=True)

    def save(self, *args, **kwargs):
        if self.arrival_start_point and self.arrival_end_point:
            time_difference = self.arrival_end_point - self.arrival_start_point

            if self.volume < 12:
                time_difference += datetime.timedelta(minutes=30)
            elif 12 <= self.volume < 28:
                time_difference += datetime.timedelta(minutes=50)
            elif 45 <= self.volume < 80:
                time_difference += datetime.timedelta(hours=1, minutes=30)
            else:
                time_difference += datetime.timedelta(hours=2)

            self.return_arrival = self.arrival_end_point + time_difference

        super().save(*args, **kwargs)


class RoutePoint(models.Model):
    id_route = models.IntegerField(null=True)
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()


class ReturnArrivalBooking(models.Model):
    number_arrival = models.IntegerField()
    address = models.CharField("Адрес", max_length=255)
    phone = models.IntegerField()
    type_cargo = models.CharField("Тип груза", max_length=255)
    volume_cargo = models.IntegerField()
    accepted = models.BooleanField(default=False)
    number_shipment = models.ForeignKey(Shipment,on_delete=models.CASCADE, null=True, related_name='shipment')
    menedger = models.CharField("Кто забронировал",  max_length=255, null=True)
