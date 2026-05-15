from django import forms
from django.forms import modelformset_factory

from .models import Event, Reservation, Spot


class ReservationForm(forms.ModelForm):
    accept_terms = forms.BooleanField(label="J’accepte le règlement exposant", required=True)

    class Meta:
        model = Reservation
        fields = [
            'exhibitor_first_name',
            'exhibitor_last_name',
            'exhibitor_email',
            'exhibitor_phone',
            'business_name',
            'items_description',
        ]
        labels = {
            'exhibitor_first_name': 'Prénom',
            'exhibitor_last_name': 'Nom',
            'exhibitor_email': 'Email',
            'exhibitor_phone': 'Téléphone',
            'business_name': 'Nom commercial ou association',
            'items_description': 'Objets vendus',
        }
        widgets = {
            'items_description': forms.TextInput(attrs={'placeholder': 'Vêtements, jouets, livres, mobilier…'}),
        }


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'name', 'slug', 'status', 'description', 'venue_name', 'address',
            'starts_at', 'ends_at', 'reservation_deadline', 'default_map_mode',
            'plan_image', 'center_latitude', 'center_longitude', 'terms',
        ]
        widgets = {
            'starts_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'ends_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'reservation_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'terms': forms.Textarea(attrs={'rows': 4}),
        }


class SpotCSVImportForm(forms.Form):
    csv_file = forms.FileField(label='Fichier CSV')
    replace_existing = forms.BooleanField(label='Remplacer les emplacements existants', required=False)

    help_text = 'Colonnes attendues : zone,number,price,x,y,width,height,width_m,depth_m,status,electricity,vehicle_allowed'


class SpotMapForm(forms.ModelForm):
    class Meta:
        model = Spot
        fields = ['id', 'number', 'status', 'x', 'y', 'map_width', 'map_height', 'price', 'electricity', 'vehicle_allowed']


SpotMapFormSet = modelformset_factory(Spot, form=SpotMapForm, extra=0, can_delete=False)
