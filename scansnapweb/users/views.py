from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView

from .forms import StyledAuthenticationForm
from .forms import CreateUserForm, StyledAuthenticationForm


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = StyledAuthenticationForm

    # Skip login page if already logged in
    redirect_authenticated_user = True


def register(request):
    form = CreateUserForm()

    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("scansnapweb-login")

    context = {"registration_form": form}
    return render(request, "registration/register.html", context=context)


# def scansnapweb_login(request):
#     if request.user.is_authenticated:
#         return redirect("home")  # or wherever you want

#     form = StyledAuthenticationForm()

#     if request.method == "POST":
#         form = StyledAuthenticationForm(request, data=request.POST)
#         # Note that authenticate() is used under the hood by form.is_valid()
#         if form.is_valid():
#             user = form.get_user()
#             login(request, user)
#             return redirect("home")  # or whatever success URL
#         else:
#             messages.error(request, "Invalid username or password.")

#     return render(request, "registration/login.html", {"form": form})


def scansnapweb_logout(request):
    logout(request)
    return redirect("scansnapweb-login")
