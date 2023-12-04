from .models import Booking, TimeSlot , Gate, Provider
from django.forms import ModelForm, DateTimeInput, DateInput, TextInput
from django import forms

class BookingFilterForm(forms.Form):    
    ordering = forms.ChoiceField(label="сортировка", required=False, choices=[
        ["id", "по № от меньшего"],      
        ["-id", "по № от большего"],      
        ["user", "с 'A' по пользователю"],      
        ["-user", "с 'Z' по пользователю"],
        ["-provider", "с 'A' по поставщику"],
        ["provider", "с 'Я' по поставщику"],
        ["-date", "новые сверху"],    
        ["date", "старые сверху"],
    ])


class ProviderForm(forms.Form):  
  provider = forms.ModelChoiceField(queryset=Provider.objects.all())



class GateForm(ModelForm):
    class Meta:
        model = Gate
        fields = ["name","warehouse","active","types"]

class BookingForm(ModelForm):
    class Meta:
        model = Booking
        fields = ["user", "date", "warehouse", "gate", "timeslot"]



    # def __init__(self, *args, **kwargs):
    #     super(BookingForm, self).__init__(*args, **kwargs)
    #     s = self.fields["date"]
    #     print(s)


class TimeSlotForm(ModelForm):
    class Meta:
        model = TimeSlot
        fields = ["warehouse", "time_start", "time_end"]

        widgets = {
            "time_start": DateTimeInput(
                attrs={"class": "form-control", "placeholder": "Дата и время начала"}
            ),
            "time_end": DateTimeInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Дата и время завершения",
                }
            ),
        }
