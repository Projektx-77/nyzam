from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import User

class UserCreationForm(forms.ModelForm):
    """Форма для создания нового пользователя с правильным хэшированием пароля"""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email', 'role')  # добавляем role, если нужно

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords don't match")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # хэшируем пароль
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    """Форма для редактирования существующего пользователя"""
    password = ReadOnlyPasswordHashField(label="Password",
        help_text="Пароль хранится в зашифрованном виде, изменить его можно через отдельную форму.")

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password', 'is_active', 'is_staff', 'is_superuser')