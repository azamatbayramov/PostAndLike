from requests import get

# Тесты API

print('Проверка получения всех пользователей')
print(get('http://localhost:5000/api/users').json())

print('Проверка получения одного пользователя')
print(get('http://localhost:5000/api/users/1').json())

print('Пользователя с таким ID не существует')
print(get('http://localhost:5000/api/users/999999').json())

print('ID некорректный')
print(get('http://localhost:5000/api/users/not_int').json())