pool = [1, 2, 3, 4, 5]
lista = []

for num in pool:
    lista.append({'id': num, 'desc': None})

for num in lista:
    print(num["id"])