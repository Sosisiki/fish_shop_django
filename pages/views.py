from django.shortcuts import render

def home(request):
    return render(request, 'pages/home.html')

def about(request):
    return render(request, 'pages/about.html')

def support(request):
    return render(request, 'pages/support.html')

def delivery(request):
    return render(request, 'pages/delivery.html')

def returns(request):
    return render(request, 'pages/returns.html')

def guarantee(request):
    return render(request, 'pages/guarantee.html')