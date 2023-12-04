import copy
import json
import re

import pytz
from django.contrib import messages
from geopy import distance
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Exists, OuterRef, Q, Subquery
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from geopy.distance import geodesic

from .service import send
from .models import TimeSlot, Gate, Warehouse, Booking, CustomerUser, Provider, ProcedureChoices, VehicleTypeChoises, \
    Delivery, GateTypeChoises, RoleChoices, Shipment, RoutePoint, ReturnArrivalBooking
from django.views.generic import UpdateView, DeleteView, DetailView
from django.contrib.auth.decorators import login_required
from datetime import datetime, time, date
from .forms import BookingForm, GateForm, BookingFilterForm, ProviderForm
from django import forms
from .tables import UserTable


def add_customer_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        role = request.POST.get('role')
        warehouse_id = request.POST.get('warehouse')
        warehouse = Warehouse.objects.get(pk=warehouse_id)

        user = User.objects.create_user(username=username, password=password)
        customer_user = CustomerUser(user=user, name=name, phone=phone, role=role, warehouse=warehouse)
        customer_user.save()
        return redirect('home')

    warehouses = Warehouse.objects.all()
    role_choices = RoleChoices.ROLE_CHOICES

    context = {
        'warehouses': warehouses,
        'role_choices': role_choices
    }
    return render(request, 'main/add_customer_user.html', context)


def users_table(request):
    table = UserTable(User.objects.all())
    return render(request, 'main/users_table.html', {'table': table})


def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        return redirect('users_table')

    return render(request, 'main/edit_user.html', {'user': user})


def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        # Удаление пользователя
        user.delete()
        return redirect('users_table')
    return render(request, 'main/delete_user.html', {'user': user})


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.customeruser.first_login = False
            user.customeruser.save()
            user.save()
            update_session_auth_hash(request, user)
            return HttpResponseRedirect(reverse('home'))
    return render(request, 'main/change_password.html')


@login_required()
def index(request):
    coming_y = Booking.objects.filter(coming=True).count()
    coming_y = int(coming_y)

    coming_n = Booking.objects.filter(coming=False).count()
    coming_n = int(coming_n)

    coming_list = ['Прибыл', 'Не прибыл']
    coming_number = [coming_y, coming_n]
    gate = Gate.objects.all()
    timeslot = TimeSlot.objects.exclude(
        Exists(Booking.objects.filter(timeslot=OuterRef("id")))
    ).order_by("time_start")
    provider = Provider.objects.all()
    warehouse = Warehouse.objects.order_by("-quantity_day")
    booking = Booking.objects.order_by("gate")

    data = {
        "coming_list": coming_list,
        "coming_number": coming_number,
        # 'user': request.user,
        # 'form': form,
        "timeslot": timeslot,
        # 'people': people,
        "provider": provider,
        "gate": gate,
        "warehouse": warehouse,

        "booking": booking,
        'vehicle_types_dict': VehicleTypeChoises.VEHICLE_TYPE_DICT,
        'procedure_dict': ProcedureChoices.PROCEDURE_DICT,
        # 'error': error
    }
    for i in booking:
        b = Booking.objects.get(id=i.id)
        if b.pick_gate != b.pick_begin:
            b.coming = True
            b.save()
    if request.user.customeruser.first_login:
        return redirect('change_password')
    else:
        user = request.user
        if user.is_anonymous == True or (
                user.customeruser.role != 'priemka' and user.customeruser.role != 'dispecher') and \
                user.customeruser.role != 'kpp':
            return render(request, "main/index.html", data)
        elif user.customeruser.role == 'kpp':
            return HttpResponseRedirect(reverse('kpp'))
        else:
            return HttpResponseRedirect(reverse('change_booking'))


def new_booking(request):
    coming_y = Booking.objects.filter(coming=True).count()
    coming_y = int(coming_y)

    coming_n = Booking.objects.filter(coming=False).count()
    coming_n = int(coming_n)

    coming_list = ['Прибыл', 'Не прибыл']
    coming_number = [coming_y, coming_n]
    gate = Gate.objects.all()
    timeslot = TimeSlot.objects.exclude(
        Exists(Booking.objects.filter(timeslot=OuterRef("id")))
    ).order_by("time_start")
    provider = Provider.objects.all()
    warehouse = Warehouse.objects.order_by("-quantity_day")
    booking = Booking.objects.order_by("gate")

    data = {
        "coming_list": coming_list,
        "coming_number": coming_number,
        # 'user': request.user,
        # 'form': form,
        "timeslot": timeslot,
        # 'people': people,
        "provider": provider,
        "gate": gate,
        "warehouse": warehouse,
        "booking": booking,
        'vehicle_types_dict': VehicleTypeChoises.VEHICLE_TYPE_DICT,
        'procedure_dict': ProcedureChoices.PROCEDURE_DICT,
        # 'error': error
    }
    user = request.user
    if user.is_anonymous == True or user.customeruser.role != 'priemka' and user.customeruser.role != 'kpp':
        return render(request, "main/new_booking.html", data)
    elif user.customeruser.role == 'kpp':
        return HttpResponseRedirect(reverse('kpp'))
    else:
        return HttpResponseRedirect(reverse('change_booking'))


slot_times = [
    time(hour=8),
    time(hour=10),
    time(hour=12),
    time(hour=14),
    time(hour=16),
    time(hour=18),
]


@require_POST
def free_slots(request):
    # if not request.user.customeruser.type_vehicle:
    #     return HttpResponse("У пользователя не указан тип ТС")
    date = request.POST["date"]
    date_object = datetime.strptime(date, "%Y-%m-%d")

    warehouse_id = request.POST["warehouse"]
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)

    customer_user = request.user.customeruser
    # Получили все занятые брони
    bookings = Booking.objects.filter(
        date=date_object,
        warehouse=warehouse,
    )
    # Получаем склады с типом ТС, как у юзера в виде словвря [3, 4],
    need_gates = Gate.objects.filter(
        warehouse=warehouse, active=True
    ).values_list("id", flat=True)

    gates_all_slots_dict = {}
    for gate_id in need_gates:
        gates_all_slots_dict[gate_id] = list(
            TimeSlot.objects.filter(warehouse=warehouse).values_list(
                "time_start", flat=True
            )
        )

    busy_slots = bookings.values("gate", "timeslot__time_start")
    busy_slots_dict = {}

    for slot in busy_slots:
        if busy_slots_dict.get(slot["gate"]):
            busy_slots_dict[slot["gate"]].append(slot["timeslot__time_start"])
        else:
            busy_slots_dict[slot["gate"]] = [slot["timeslot__time_start"]]

    for gate_id in gates_all_slots_dict:
        for busy_slot in busy_slots_dict.get(gate_id, []):
            if busy_slot in gates_all_slots_dict.get(gate_id, []):
                azaza = gates_all_slots_dict[gate_id]
                azaza.remove(busy_slot)

    free_slots_set = set()
    for gate_id in gates_all_slots_dict:
        [free_slots_set.add(str(elem)) for elem in gates_all_slots_dict[gate_id]]

    return HttpResponse(json.dumps({"slots": sorted(free_slots_set)}))


def profile_view(request):
    bookin = Booking.objects.filter(user=request.user)
    count_user_success = 0
    count_user_fail = 0
    for booking in bookin:
        pick_gate_time_user = booking.pick_gate.astimezone(pytz.timezone('Europe/Moscow')).strftime(
            "%H:%M")  # Преобразование pick_gate в строку формата "%H:%M"
        timeslot_time_start_user = booking.timeslot.time_start.strftime("%H:%M")
        timeslot_time_end_user = booking.timeslot.time_end.strftime("%H:%M")
        if timeslot_time_start_user <= pick_gate_time_user <= timeslot_time_end_user:
            count_user_success += 1
        else:
            count_user_fail += 1
    customer_user = CustomerUser.objects.all()
    user_id = request.user.id
    booking_count = Booking.objects.filter(user_id=user_id).count()
    if count_user_fail != 0 and count_user_success != 0:
        percentage_booking_not = (count_user_success / booking_count) * 100
        percentage_booking = round(percentage_booking_not, 2)
    else:
        percentage_booking = 0
    data = {
        "user": request.user,
        "customer_user": customer_user,
        "booking_count": booking_count,
        "percentage_booking": percentage_booking,
        "count_user_success": count_user_success,
        "count_user_fail": count_user_fail,
    }
    user = request.user
    if user.customeruser.role == "kpp":
        return HttpResponseRedirect(reverse('kpp'))
    else:
        return render(request, "main/profile.html", data)


class ProfileUpdateView(UpdateView):
    model = CustomerUser
    template_name = "main/refactor.html"


def change_booking(request):
    booking = Booking.objects.order_by("timeslot")
    c_user = CustomerUser.objects.all()
    dt_now = date.today()
    if request.method == 'POST':
        my_date = request.POST['my_date']
        date_object = datetime.strptime(my_date, "%Y-%m-%d").date()
        return render(request, 'main/change_booking.html',
                      {'date_object': date_object, "booking": booking, "dt_now": dt_now, "c_user": c_user})
    else:
        user = request.user
        if user.customeruser.role == "kpp":
            return HttpResponseRedirect(reverse('kpp'))
        else:
            return render(request, 'main/change_booking.html')


def change(request):
    booking = Booking.objects.order_by("timeslot")
    c_user = CustomerUser.objects.all()
    dt_now = date.today()
    print(dt_now)
    return render(request, 'main/version.html', {"booking": booking, "dt_now": dt_now, "c_user": c_user})


def kpp(request):
    booking = Booking.objects.order_by("timeslot")
    c_user = CustomerUser.objects.all()
    from datetime import datetime, date
    dt_now = date.today()
    pick_begin_comparison = datetime(2022, 1, 1, 0, 0)
    return render(request, 'main/kpp.html', {"booking": booking, "dt_now": dt_now, "c_user": c_user,
                                             "pick_begin_comparison": pick_begin_comparison})


def update_pick_begin(request, booking_id):
    booking = Booking.objects.get(pk=booking_id)
    booking.pick_begin = datetime.now()
    booking.save()
    return redirect('kpp')


def update_pick_end(request, booking_id):
    booking = Booking.objects.get(pk=booking_id)
    booking.pick_end = datetime.now()
    booking.save()
    return redirect('kpp')


def change_gate(request):
    gate = Gate.objects.order_by("-warehouse")
    data = {
        "user": request.user,
        "gate": gate,
    }
    user = request.user
    if user.is_anonymous == True or user.customeruser.role != 'menedger' and user.customeruser.role != "kpp":
        return render(request, "main/change_gate.html", data)
    elif user.customeruser.role == "kpp":
        return HttpResponseRedirect(reverse('kpp'))
    else:
        return HttpResponseRedirect(reverse('home'))


def statistic(request):
    # Для стафа
    bookings = Booking.objects.all()
    count_success = 0
    count_fail = 0
    for booking in bookings:
        pick_gate_time = booking.pick_gate.astimezone(pytz.timezone('Europe/Moscow')).strftime(
            "%H:%M")  # Преобразование pick_gate в строку формата "%H:%M"
        timeslot_time_start = booking.timeslot.time_start.strftime("%H:%M")
        timeslot_time_end = booking.timeslot.time_end.strftime("%H:%M")
        if timeslot_time_end > pick_gate_time > timeslot_time_start:
            count_success += 1
            print(count_success)
            print('dfsdfssd')
        else:
            count_fail += 1

    coming_in_out_time_list = ['Прибыл вовремя', 'Опоздал']
    coming_in_out_time_number = [count_success, count_fail]

    booking = Booking.objects.all()
    coming_y = Booking.objects.filter(coming=True).count()
    coming_y = int(coming_y)
    coming_n = Booking.objects.filter(coming=False).count()
    coming_n = int(coming_n)
    coming_list = ['Прибыл', 'Не прибыл']
    coming_number = [coming_y, coming_n]
    for i in booking:
        b = Booking.objects.get(id=i.id)
        if b.pick_gate != b.pick_begin:
            b.coming = True
            b.save()
    # для юзера
    provname = request.user.customeruser.name

    bookin = Booking.objects.all()
    count_user_success = 0
    count_user_fail = 0
    for booking in bookin:
        if booking.provider.name == provname:
            pick_gate_time_user = booking.pick_gate.astimezone(pytz.timezone('Europe/Moscow')).strftime(
                "%H:%M")  # Преобразование pick_gate в строку формата "%H:%M"

            timeslot_time_start_user = booking.timeslot.time_start.strftime("%H:%M")

            timeslot_time_end_user = booking.timeslot.time_end.strftime("%H:%M")
            if (pick_gate_time_user >= timeslot_time_start_user and pick_gate_time_user <= timeslot_time_end_user):
                count_user_success += 1
            else:
                count_user_fail += 1
    coming_in_out_time_user_list = ['Прибыл вовремя', 'Опоздал']
    coming_in_out_time_user_number = [count_user_success, count_user_fail]

    provname = request.user.customeruser.name
    coming_user_y = Booking.objects.filter((Q(coming=True) & Q(provider__name=provname))).count()
    coming_user_y = int(coming_user_y)
    coming_user_n = Booking.objects.filter((Q(coming=False) & Q(provider__name=provname))).count()
    coming_user_n = int(coming_user_n)
    coming_user_list = ['Прибыл', 'Не прибыл']
    coming_user_number = [coming_user_y, coming_user_n]
    if request.method == 'POST':
        form = ProviderForm(request.POST)
        if form.is_valid():
            provider = form.cleaned_data['provider']
            total_bookings = Booking.objects.filter(provider=provider, coming=False).count()
            coming_bookings = Booking.objects.filter(provider=provider, coming=True).count()
            count_in_time = 0
            count_out_time = 0
            provider = form.cleaned_data['provider']
            total_bookings = Booking.objects.filter(provider=provider).count()
            coming_bookings = Booking.objects.filter(provider=provider, coming=True).count()
            bookings = Booking.objects.filter(provider=provider)
            for booking in bookings:
                pick_gate = booking.pick_gate.astimezone(pytz.timezone('Europe/Moscow')).strftime("%H:%M:%S")
                pick_gate_date = booking.pick_gate.strftime('%y-%m-%d')
                date_booking = booking.date.strftime('%y-%m-%d')
                time_start = booking.timeslot.time_start.strftime("%H:%M:%S")
                time_end = booking.timeslot.time_end.strftime("%H:%M:%S")
                if booking.coming:
                    if (time_start <= pick_gate <= time_end) and (pick_gate_date == date_booking):
                        count_in_time += 1
                    else:
                        count_out_time += 1
            data = {
                "form": form,
                'count_in_time': count_in_time,
                'count_out_time': count_out_time,
                "total_bookings": total_bookings,
                "coming_bookings": coming_bookings,
                "coming_in_out_time_list": coming_in_out_time_list,
                "coming_in_out_time_number": coming_in_out_time_number,
                "coming_in_out_time_user_list": coming_in_out_time_user_list,
                "coming_in_out_time_user_number": coming_in_out_time_user_number,
                "coming_user_list": coming_user_list,
                "coming_user_number": coming_user_number,
                "coming_list": coming_list,
                "coming_number": coming_number,
                "count_success": count_success,
                "count_fail": count_fail,
            }
            return render(request, "main/statistic.html", data)
    else:
        form = ProviderForm()
    data = {
        'form': form,
        "coming_in_out_time_list": coming_in_out_time_list,
        "coming_in_out_time_number": coming_in_out_time_number,
        "coming_in_out_time_user_list": coming_in_out_time_user_list,
        "coming_in_out_time_user_number": coming_in_out_time_user_number,
        "coming_user_list": coming_user_list,
        "coming_user_number": coming_user_number,
        "coming_list": coming_list,
        "coming_number": coming_number,
    }
    user = request.user
    if user.customeruser.role == "kpp":
        return HttpResponseRedirect(reverse('kpp'))
    else:
        return render(request, "main/statistic.html", data)


def contact(request):
    gate = Gate.objects.all()
    warehouse = Warehouse.objects.all()
    data = {
        "user": request.user,
        "gate": gate,
        "warehouse": warehouse,
    }
    user = request.user
    if user.customeruser.role == "kpp":
        return HttpResponseRedirect(reverse('kpp'))
    else:
        return render(request, "main/contact.html", data)


def add_gate(request):
    error = ''
    if request.method == 'POST':
        form = GateForm(request.POST)
        if form.is_valid():
            form.save()
        else:
            error = '404'
    form = GateForm()
    war_name = request.user.customeruser.warehouse.name
    if request.user.customeruser.role != 'admin':
        form.fields['warehouse'].queryset = Warehouse.objects.filter(name=war_name)
    data = {
        "form": form,
        "user": request.user,
        "error": error,
    }
    user = request.user
    if user.customeruser.role == "kpp":
        return HttpResponseRedirect(reverse('kpp'))
    elif user.customeruser.role == "dispatcher" or user.customeruser.role == "menedger":
        return HttpResponseRedirect(reverse('home'))
    else:
        return render(request, "main/add_gate.html", data)


class ChangeGateUpdateView(UpdateView):
    model = Gate
    template_name = "main/change_detail_gate.html"
    fields = ["name", "warehouse", "active", "types"]


class ReceptionUpdateView(UpdateView):
    model = Booking
    template_name = "main/reception.html"
    fields = ["user", "date", "warehouse", "timeslot", "gate", "provider", "supplier", "pick_begin", "pick_gate",
              "pick_end"]

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        if 'pick_gate_button' in request.POST:
            obj.pick_gate = datetime.now()
        elif 'pick_end_button' in request.POST:
            obj.pick_end = datetime.now()

        obj.save()

        return render(request, "main/reception.html")


class ChangeBookingUpdateView(UpdateView):
    model = Booking
    template_name = "main/change_booking_update.html"
    fields = ["user", "date", "warehouse", "timeslot", "gate"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        booking = self.get_object()
        warehouse = booking.warehouse
        form.fields['gate'].queryset = Gate.objects.filter(active=True, warehouse=warehouse)
        form.fields['timeslot'].queryset = TimeSlot.objects.filter(warehouse=warehouse)
        return form

    def create(request):
        error = ""
        if request.method == "POST":
            form = BookingForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect("change_booking")
            else:
                error = "404"

        form = BookingForm
        data = {"form": form, "error": error}
        return render(request, "main/change_booking_update.html", data)


@method_decorator(login_required, name='dispatch')
class ChangeBookingDeleteView(DeleteView):
    model = Booking
    success_url = "/change_booking"
    template_name = "main/delete.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


MY_CHOICES = (
    ("option1", "Option 1"),
    ("option2", "Option 2"),
    ("option3", "Option 3"),
)


class MyForm(forms.Form):
    my_choice = forms.ChoiceField(choices=MY_CHOICES)


@login_required
def talon(request):
    if request.method == "POST":
        print(request.POST)
        time_slot = request.POST["timeslot"]
        time_slot2 = request.POST.get("timeslot2")
        time_slot3 = request.POST.get("timeslot3")
        warehouse_id = request.POST["warehouse"]
        date_slot = request.POST["date"]
        volume = request.POST["volume"]
        procedure_type = request.POST['procedure_type']
        provider_id = request.POST["provider"]
        provider = get_object_or_404(Provider, id=provider_id)
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)
        date = datetime.strptime(date_slot, "%Y-%m-%d")
        time = datetime.strptime(time_slot, "%H:%M:%S").time()

        time2 = None
        time3 = None

        if time_slot2:
            time2 = datetime.strptime(time_slot2, "%H:%M:%S").time()

        if time_slot3:
            time3 = datetime.strptime(time_slot3, "%H:%M:%S").time()

        timeslot = TimeSlot.objects.filter(warehouse=warehouse, time_start=time).first()

        timeslot2 = None
        if time2:
            timeslot2 = TimeSlot.objects.filter(warehouse=warehouse, time_start=time2).first()

        timeslot3 = None
        if time3:
            timeslot3 = TimeSlot.objects.filter(warehouse=warehouse, time_start=time3).first()

        bookings = Booking.objects.filter(
            date=date,
            warehouse=warehouse,
            timeslot=timeslot,
        ).values_list("gate", flat=True)

        need_gates = Gate.objects.filter(
            warehouse=warehouse, active=True
        ).values_list("id", flat=True)

        free_gates = set(need_gates) - set(bookings)
        if not free_gates:
            return HttpResponse("Нет свободных ворот")

        if timeslot2 and timeslot3 and timeslot2 == timeslot and timeslot2 == timeslot3 and len(free_gates) < 3:
            return HttpResponse("Нет 3 свободных ворот на это время")

        if timeslot2 and timeslot2 == timeslot and len(free_gates) < 2:
            return HttpResponse("Нет 2 свободных ворот на это время")

        if timeslot2 == timeslot == timeslot3:
            gate1 = Gate.objects.get(id=list(free_gates)[0])
            gate2 = Gate.objects.get(id=list(free_gates)[1])
            gate3 = Gate.objects.get(id=list(free_gates)[2])

            Booking.objects.create(
                user=request.user,
                date=date,
                provider=provider,
                warehouse=warehouse,
                gate=gate1,
                timeslot=timeslot,
            )
            Booking.objects.create(
                user=request.user,
                date=date,
                provider=provider,
                warehouse=warehouse,
                gate=gate2,
                timeslot=timeslot2,
            )
            Booking.objects.create(
                user=request.user,
                date=date,
                provider=provider,
                warehouse=warehouse,
                gate=gate3,
                timeslot=timeslot3,
            )
            return HttpResponseRedirect(reverse("talon"))

        if timeslot3 == None and timeslot2 == timeslot:
            gate1 = Gate.objects.get(id=list(free_gates)[0])
            gate2 = Gate.objects.get(id=list(free_gates)[1])

            Booking.objects.create(
                user=request.user,
                date=date,
                provider=provider,
                warehouse=warehouse,
                gate=gate1,
                timeslot=timeslot,
            )
            Booking.objects.create(
                user=request.user,
                date=date,
                provider=provider,
                warehouse=warehouse,
                gate=gate2,
                timeslot=timeslot2,
            )
            return HttpResponseRedirect(reverse("talon"))

        gate = Gate.objects.get(id=list(free_gates)[0])
        if timeslot2 == None and timeslot3 == None:
            Booking.objects.create(
                user=request.user,
                volume=volume,
                date=date,
                provider=provider,
                warehouse=warehouse,
                gate=gate,
                timeslot=timeslot,
            )
        elif timeslot2 and timeslot3 == None:
            Booking.objects.create(
                user=request.user,
                date=date,
                provider=provider,
                warehouse=warehouse,
                gate=gate,
                timeslot=timeslot,
            )
            Booking.objects.create(
                user=request.user,
                date=date,
                provider=provider,
                warehouse=warehouse,
                gate=gate,
                timeslot=timeslot2,
            )
        else:
            Booking.objects.create(
                user=request.user,
                date=date,
                provider=provider,
                warehouse=warehouse,
                gate=gate,
                timeslot=timeslot,
            )
            Booking.objects.create(
                user=request.user,
                date=date,
                provider=provider,
                warehouse=warehouse,
                gate=gate,
                timeslot=timeslot2,
            )
            Booking.objects.create(
                user=request.user,
                date=date,
                provider=provider,
                warehouse=warehouse,
                gate=gate,
                timeslot=timeslot3,
            )

    gate = Gate.objects.all()

    timeslot = TimeSlot.objects.all()
    provider = Provider.objects.all()
    warehouse = Warehouse.objects.all()

    from datetime import date
    booking = Booking.objects.order_by("-date")
    form = BookingFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data["ordering"]:
            booking = booking.order_by(form.cleaned_data["ordering"])

    current_date = date.today()
    for i in booking:
        b = Booking.objects.get(id=i.id)
        if b.pick_gate != b.pick_begin:
            b.coming = True
            b.save()
    context = {
        "provider": provider,
        "timeslot": timeslot,
        "gate": gate,
        "warehouse": warehouse,
        "booking": booking,
        "form": form,
        "current_date": current_date,
    }
    user = request.user
    if user.customeruser.role == "kpp":
        return HttpResponseRedirect(reverse('kpp'))
    else:
        return render(request, "main/talon.html", context)


@method_decorator(login_required, name='dispatch')
class TalonDetailView(DetailView):
    model = Booking
    template_name = 'main/talon_details.html'
    context_object_name = 'booking'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


def version(request):
    now = datetime.now()
    date = now.strftime('%Y-%m-%d')
    customeruser = CustomerUser.objects.all()
    delivery = Delivery.objects.all()
    gate = Gate.objects.all()
    timeslot = TimeSlot.objects.exclude(
        Exists(Booking.objects.filter(timeslot=OuterRef("id")))
    ).order_by("time_start")
    provider = Provider.objects.all()
    warehouse = Warehouse.objects.order_by("-quantity_day")
    booking = Booking.objects.order_by("gate")
    if request.method == 'POST':

        my_date = request.POST['zakaz']
        # date_object = datetime.strptime(my_date, "%Y-%m-%d").date()
        data = {
            'date': date,
            'delivery': delivery,
            'gate': gate,
            'my_date': my_date,
            "booking": booking,
            "timeslot": timeslot,
            "customeruser": customeruser,
            "provider": provider,
            "warehouse": warehouse,
            'procedure_dict': ProcedureChoices.PROCEDURE_DICT,
        }
        return render(request, 'main/version.html', data)
    else:
        return render(request, 'main/version.html')


class ChangeGateDeleteView(DeleteView):
    model = Gate
    success_url = "/timeslots/change_gate"
    template_name = "main/gate_delete.html"


def shipments(request):
    shipment = Shipment.objects.all()
    data = {
        "user": request.user,
        "shipment": shipment,
    }
    user = request.user
    if user.is_anonymous == True or user.customeruser.role != 'menedger' and user.customeruser.role != "kpp":
        return render(request, "main/shipment.html", data)
    elif user.customeruser.role == "kpp":
        return HttpResponseRedirect(reverse('kpp'))
    else:
        return HttpResponseRedirect(reverse('home'))


def shipment_details(request, pk):
    shipment = Shipment.objects.get(pk=pk)
    distanceinkm = 0
    flag = ''

    if request.method == 'POST':
        start_location = request.POST.get("start_location")
        number_arrival = request.POST.get("number_arrival")
        adres = request.POST.get("adres")
        phone = request.POST.get("phone")
        vol = request.POST.get("vol")
        type_cargo = request.POST.get("type_cargo")

        # Обработка формы
        if start_location:
            route_points = RoutePoint.objects.filter(id_route=shipment.id_ship)
            for point in route_points:
                pointlocation = (point.latitude, point.longitude)
                distanceinkm = distance.distance(start_location, pointlocation).km

            if distanceinkm < 15:
                shipment = get_object_or_404(Shipment, id=pk)  # Получение объекта Shipment по номеру перевозки
                if shipment.сurrent_volume >= int(vol):
                    if not is_valid_phone(phone):
                        messages.error(request, 'Ошибка! Неправильно введен телефон.')
                    else:
                        # Создание экземпляра ReturnArrivalBooking и сохранение его в базе данных
                        rab = ReturnArrivalBooking(
                            number_arrival=number_arrival,
                            address=adres,
                            phone=phone,
                            volume_cargo=vol,
                            type_cargo=type_cargo,
                            accepted=False,
                            number_shipment=shipment
                        )
                        rab.save()
                        shipment = get_object_or_404(Shipment, id=pk)
                        print(shipment)

                        if shipment.сurrent_volume >= int(vol):
                            shipment.сurrent_volume -= int(vol)
                            shipment.save()
                        return redirect('shipments')

                else:
                    messages.error(request, "слишком большой объем")
            else:
                messages.error(request, "Слишком далеко находятся координаты")

    data = {
        "shipment": shipment,
        "distanceinkm": distanceinkm,
        "flag": flag,
    }
    return render(request, "main/shipment_details.html", data)


def success_page(request):
    return render(request, 'main/success.html')


def is_valid_phone(phone):
    # Паттерн для проверки телефона: должно начинаться с "+" и содержать только цифры и знаки -, (, )
    pattern = r'^\+[\d()-]+$'
    return re.match(pattern, phone) is not None


def form_submission(request):
    error = ''
    if request.method == 'POST':
        arrival = request.POST.get('number_arrival')
        adres = request.POST.get('adres')
        phone = request.POST.get('phone')
        vol = request.POST.get('vol')
        type_cargo = request.POST.get('type_cargo')

        shipment = get_object_or_404(Shipment, id=arrival)
        if shipment.сurrent_volume >= int(vol):
            if is_valid_phone(phone):  # Проверка валидности телефона
                return_booking = ReturnArrivalBooking(
                    number_arrival=arrival,
                    address=adres,
                    phone=phone,
                    type_cargo=type_cargo,
                    volume_cargo=vol
                )
                return_booking.save()
                return redirect('success_page')
            else:
                error = 'Ошибка! Неправильно введен телефон.'
        else:
            error = 'Ошибка! В фуре недостаточно места !'
        shipment.save()

    return render(request, 'main/arrivalform.html', {'error': error})


def shipment_accept(request):
    return_arrival_booking = ReturnArrivalBooking.objects.all()
    total_entries = return_arrival_booking.count()
    accepted_entries = return_arrival_booking.filter(accepted=False).count()

    data = {
        "user": request.user,
        "return_arrival_booking": return_arrival_booking,
        "total_entries": total_entries,
        "accepted_entries": accepted_entries,
    }

    return render(request, "main/shipment_accept.html", data)


def change_accepted(request, pk):
    rab = ReturnArrivalBooking.objects.get(pk=pk)
    print(pk)
    if "cancel" in request.POST:
        print('otmen')
        current_shipment = rab.number_shipment
        current_shipment.сurrent_volume += rab.volume_cargo
        current_shipment.save()
        rab.delete()
    elif "confirm" in request.POST:
        print('prin')
        username = request.POST.get("user")
        print(username)
        rab.menedger = username
        rab.accepted = True
        rab.save()
    return redirect('shipment_accept')


def shipment_ready(request):
    return_arrival_booking_ids = ReturnArrivalBooking.objects.filter().order_by('-id')[:10].values_list('id', flat=True)
    return_arrival_booking = ReturnArrivalBooking.objects.filter(id__in=Subquery(return_arrival_booking_ids))

    total_entries = return_arrival_booking.count()
    accepted_entries = return_arrival_booking.filter(accepted=True).count()
    data = {
        "user": request.user,
        "return_arrival_booking": return_arrival_booking,
        "total_entries": total_entries,
        "accepted_entries": accepted_entries,
    }

    return render(request, "main/shipment_ready.html", data)
