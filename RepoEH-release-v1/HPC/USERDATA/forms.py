from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Documentacion
from django.core.exceptions import ValidationError

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        help_texts = {'username': "El nombre de usuario deberá ser su DNI"}

    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado')
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if not username.isdigit():
            raise forms.ValidationError('El nombre de usuario debe ser un número.')
        number = int(username)
        if number < 1 or number > 99999999:
            raise forms.ValidationError('El nombre de usuario debe ser un número entre 1 y 99999999.')
        return username




class DocumentacionForm(forms.ModelForm):
    class Meta:
        model = Documentacion
        fields = ['id', 'imagen']

    id = forms.ChoiceField(choices=[])  # Definir como ChoiceField para opciones dinámicas

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tiene_imagen = bool(instance.imagen)
        if commit:
            instance.save()
        return instance



class UploadCertificateForm(forms.Form):
    medical_certificate = forms.ImageField(required=False)
    health_insurance_card = forms.ImageField(required=False)

    def clean_medical_certificate(self):
        medical_certificate = self.cleaned_data.get('medical_certificate')
        if medical_certificate and medical_certificate.size > 1 * 1024 * 1024:
            raise forms.ValidationError("El archivo no puede superar 1 MB.")
        return medical_certificate

    def clean_health_insurance_card(self):
        health_insurance_card = self.cleaned_data.get('health_insurance_card')
        if health_insurance_card and health_insurance_card.size > 1 * 1024 * 1024:
            raise forms.ValidationError("El archivo no puede superar 1 MB.")
        return health_insurance_card
