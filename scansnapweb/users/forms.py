from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class CreateUserForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            "class": "w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
            "placeholder": "Your username"
        })
        self.fields['email'].widget.attrs.update({
            "class": "w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
            "placeholder": "Your email"
        })
        self.fields['password1'].widget.attrs.update({
            "class": "w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
            "placeholder": "Password"
        })
        self.fields['password2'].widget.attrs.update({
            "class": "w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
            "placeholder": "Confirm your password"
        })

    class Meta:

        model = User
        fields = ["username", "email", "password1", "password2"]


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            "class": "w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
            "placeholder": "Enter your username"
        })
        self.fields['password'].widget.attrs.update({
            "class": "w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
            "placeholder": "Enter your password"
        })