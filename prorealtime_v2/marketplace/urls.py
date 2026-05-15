from django.urls import path

from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('evenements/<slug:slug>/', views.EventDetailView.as_view(), name='event_detail'),
    path('evenements/<slug:slug>/emplacements/<int:spot_id>/reserver/', views.ReservationCreateView.as_view(), name='reserve_spot'),
    path('paiements/<int:pk>/succes/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('reservations/<int:pk>/merci/', views.ReservationSuccessView.as_view(), name='reservation_success'),
    path('organisateur/<int:pk>/dashboard/', views.OrganizerDashboardView.as_view(), name='organizer_dashboard'),
    path('organisateur/evenements/<int:pk>/modifier/', views.OrganizerEventUpdateView.as_view(), name='organizer_event_update'),
    path('organisateur/evenements/<int:event_id>/import-csv/', views.SpotCSVImportView.as_view(), name='spot_import'),
    path('organisateur/evenements/<int:event_id>/carte/', views.MapEditorView.as_view(), name='map_editor'),
]
