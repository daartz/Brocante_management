from django.urls import path

from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('evenements/<slug:slug>/', views.EventDetailView.as_view(), name='event_detail'),
    path('evenements/<slug:slug>/emplacements/<int:spot_id>/reserver/', views.ReservationCreateView.as_view(), name='reserve_spot'),
    path('reservations/<int:pk>/merci/', views.ReservationSuccessView.as_view(), name='reservation_success'),
    path('organisateur/<slug:slug>/dashboard/', views.OrganizerDashboardView.as_view(), name='organizer_dashboard'),
]
