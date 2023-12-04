import copy
import json

from django.db.models import Exists, OuterRef
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import TimeSlot, Gate, Warehouse, Booking, CustomerUser, VehicleTypeChoices, Provider
from django.views.generic import UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from datetime import datetime, time, date
from .forms import BookingForm, CustomerForm
from django import forms

"""
 {%for elem in timeslot%}
        {{elem.time_start}}
        {{elem.time_end}}
    {%endfor%}
    {"gate" : gate} 
"""


def index(request):
    gate = Gate.objects.all()
    timeslot = TimeSlot.objects.exclude(
        Exists(Booking.objects.filter(timeslot=OuterRef("id")))
    ).order_by("time_start")
    provider = Provider.objects.all()
    warehouse = Warehouse.objects.all()
    booking = Booking.objects.order_by("gate")

    data = {
        # 'user': request.user,
        # 'form': form,
        "timeslot": timeslot,
        # 'people': people,
        "provider": provider,
        "gate": gate,
        "warehouse": warehouse,
        "booking": booking,
        'vehicle_types_dict': VehicleTypeChoices.VEHICLE_TYPE_DICT
        # 'error': error
    }

    return render(request, "main/index.html", data)


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

    vehicle_type = request.POST["vehicle_type"]
    customer_user = request.user.customeruser
    # Получили все занятые брони
    bookings = Booking.objects.filter(
        date=date_object,

        warehouse=warehouse,
        gate__type_vehicle=vehicle_type,
    )

    # Получаем склады с типом ТС, как у юзера в виде словвря [3, 4],
    need_gates = Gate.objects.filter(
        type_vehicle=vehicle_type, warehouse=warehouse
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


# class GateDetailView(DetailView):
#     model = Gate
#     template_name = 'main/details_view.html'
#     context_object_name = 'gate'


@login_required
def profile_view(request):
    # if request.method == 'POST':

    customer_user = CustomerUser.objects.all()
    data = {
        "user": request.user,
        "customer_user": customer_user,
    }
    return render(request, "main/profile.html", data)


class ProfileUpdateView(UpdateView):
    model = CustomerUser
    template_name = "main/refactor.html"


def change_booking(request):
    booking = Booking.objects.order_by("-timeslot")
    c_user = CustomerUser.objects.all()
    dt_now = date.today()
    flag = datetime(2022, 1, 1, 3,0,0)

    print(flag)
    if request.method == 'POST':
        my_date = request.POST['my_date']
        date_object = datetime.strptime(my_date, "%Y-%m-%d").date()
        print(my_date)
        print(date_object)
        return render(request, 'main/change_booking.html', {'date_object': date_object,"flag" : flag ,"booking": booking, "dt_now": dt_now, "c_user": c_user})
    else:
        return render(request, 'main/change_booking.html')


# class ChangeBookingDetailView(DetailView):
#     model = Booking
#     template_name = 'main/change_booking_details.html'
#     context_object_name = 'booking'
class ReceptionUpdateView(UpdateView):
    dt_now = date.today()
    model = Booking
    template_name = "main/reception.html"
    fields = ["user", "date", "warehouse", "timeslot", "gate","provider","supplier","pick_begin","pick_gate","pick_end"]



class ChangeBookingUpdateView(UpdateView):
    model = Booking
    template_name = "main/change_booking_update.html"
    fields = ["user", "date", "warehouse", "timeslot", "gate"]
    # model = CustomerUser
    # template_name = "main/change_booking_update.html"
    # fields = ["user", "name", "phone", "type_vehicle"]


class ChangeBookingDeleteView(DeleteView):
    model = Booking
    success_url = "/"
    template_name = "main/delete.html"


MY_CHOICES = (
    ("option1", "Option 1"),
    ("option2", "Option 2"),
    ("option3", "Option 3"),
)


class MyForm(forms.Form):
    my_choice = forms.ChoiceField(choices=MY_CHOICES)


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


@login_required
def talon(request):
    if request.method == "POST":
        time_slot = request.POST["timeslot"]
        warehouse_id = request.POST["warehouse"]
        date_slot = request.POST["date"]

        vehicle_type = request.POST['vehicle_type']
        provider_id = request.POST["provider"]

        provider = get_object_or_404(Provider, id=provider_id)
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)
        date = datetime.strptime(date_slot, "%Y-%m-%d")
        time = datetime.strptime(time_slot, "%H:%M:%S").time()

        timeslot = TimeSlot.objects.filter(warehouse=warehouse, time_start=time).first()

        bookings = Booking.objects.filter(
            date=date,

            provider = provider,
            warehouse=warehouse,
            gate__type_vehicle=vehicle_type,
            timeslot=timeslot,
        ).values_list("gate", flat=True)

        need_gates = Gate.objects.filter(
            type_vehicle=vehicle_type, warehouse=warehouse
        ).values_list("id", flat=True)
        now = date.today()
        free_gates = set(need_gates) - set(bookings)
        if not free_gates:
            return HttpResponse("Нет свободных ворот")

        gate = Gate.objects.get(id=list(free_gates)[0])

        new_booking = Booking(
            user=request.user,
            date=date,

            provider = provider,
            warehouse=warehouse,
            gate=gate,
            timeslot=timeslot,
        )
        new_booking.save()

        return HttpResponseRedirect(reverse("talon"))

    gate = Gate.objects.all()
    timeslot = TimeSlot.objects.all()
    provider = Provider.objects.all()
    warehouse = Warehouse.objects.all()
    booking = Booking.objects.all()
    from datetime import date

    current_date = date.today()

    context = {
        "provider": provider,
        "timeslot": timeslot,
        "gate": gate,
        "warehouse": warehouse,
        "booking": booking,
        "current_date": current_date,
    }

    return render(request, "main/talon.html", context)
