from django import forms

class BusBookingForm(forms.Form):
    seat_id = forms.IntegerField(widget=forms.HiddenInput())
    phone_number = forms.CharField(
        max_length=12,
        min_length=12,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '254XXXXXXXXX',
            'pattern': '^254\d{9}$'
        })
    )

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        if not phone.startswith('254') or not phone[3:].isdigit():
            raise forms.ValidationError("Phone number must start with 254 followed by 9 digits")
        return phone 