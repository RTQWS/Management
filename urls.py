from django.urls import path
from . import views
from .views import profile_view, ChangeGateUpdateView, add_customer_user, change_accepted
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="home"),
    path('update_pick_begin/<int:booking_id>/', views.update_pick_begin, name='update_pick_begin'),
    path('update_pick_end/<int:booking_id>/', views.update_pick_end, name='update_pick_end'),
    path("change_password", views.change_password, name="change_password"),
    path("kpp", views.kpp, name="kpp"),
    path("new_booking", views.new_booking, name="new_booking"),
    path("profile", profile_view, name="profile"),
    path("talon", views.talon, name="talon"),
    path("contact", views.contact, name="contact"),
    path("statistic", views.statistic, name="statistic"),
    path("processing", views.free_slots, name="processing"),
    path("change_booking", views.change_booking, name="change_booking"),
    path("shipments", views.shipments, name="shipments"),
    path("shipment_accept", views.shipment_accept, name="shipment_accept"),
    path("shipment_ready", views.shipment_ready, name="shipment_ready"),
    path("change_gate", views.change_gate, name="change_gate"),
    path("version", views.version, name="version"),
    path("add_gate", views.add_gate, name="add_gate"),
    path('form_submission/', views.form_submission, name='form_submission'),
    path('success_page/', views.success_page, name='success_page'),
    # path('map/', map_view, name='map'),
    path("<int:pk>/gate", ChangeGateUpdateView.as_view(), name="gate"),
    # path('<int:pk>', views.ChangeBookingDetailView.as_view(), name='change_booking_details'),
    path(
        "change_booking/<int:pk>",
        views.ChangeBookingUpdateView.as_view(),
        name="change_booking_update",
    ),
    path(
        "<int:pk>/reception",
        views.ReceptionUpdateView.as_view(),
        name="reception_update",
    ),
    path(
        "change_booking/<int:pk>/delete",
        views.ChangeBookingDeleteView.as_view(),
        name="change_booking_delete",
    ),
    path(
        "<int:pk>/gate_delete",
        views.ChangeGateDeleteView.as_view(),
        name="change_gate_delete",
    ),
    path("refactor", views.ProfileUpdateView.as_view(), name="refactor"),
    path("talon/<int:pk>", views.TalonDetailView.as_view(), name="talon_details"),
    path('users/', views.users_table, name='users_table'),
    path('add_customer_user/', add_customer_user, name='add_customer_user'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('shipment/<int:pk>/', views.shipment_details, name='shipment_details'),
    path('change_accepted/<int:pk>/', change_accepted, name='change_accepted'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
