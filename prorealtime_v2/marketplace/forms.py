from django import forms

from .models import Reservation


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
