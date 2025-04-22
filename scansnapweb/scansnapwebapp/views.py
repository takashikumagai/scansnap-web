from django.http import JsonResponse
from django.shortcuts import render

def hello(request):
    return JsonResponse({"message": "hello"})

def home(request):
    return render(request, "main.html", context={})
