from django.shortcuts import render

def base(request):
    return render(request, "base/base.html")

def home(request):
    return render(request, "home.html")

def dashboard(request):
    # Tem que colocar a pasta antes do arquivo
    return render(request, "dashboard.html")    

def pessoas(request):
    return render(request, "pessoas/pessoas.html")  

def relatorios(request):
    return render(request, "relatorios.html")   

def igrejas(request):
    return render(request, "igrejas.html")  

def financeiro(request):
    # Ajustei o nome para bater com a pasta que criamos
    return render(request, "financeiro/financeiro.html")  

def pastoral(request):
    # Se esse estiver solto na pasta templates, pode deixar assim
    return render(request, "pastoral.html")

