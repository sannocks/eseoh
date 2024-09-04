from django.shortcuts import render

def home(request):
    return render(request, 'index/home.html')

def contact(request):
    return render(request, 'index/contact.html')

def pricing(request):
    return render(request, 'index/pricing.html')
