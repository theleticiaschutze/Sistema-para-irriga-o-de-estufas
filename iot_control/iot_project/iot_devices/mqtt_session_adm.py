import requests


def session_mqtt():
    # Obtenha o CSRF token fazendo login primeiro (opcionalmente)
    session = requests.Session()

    # Faça login (se necessário)
    login_url = "http://localhost:8000/accounts/login/"
    payload_login = {
        'username': 'edilson.hipolito',
        'password': 'kxekcw'
    }

    response = session.post(login_url, data=payload_login)
    
    if response.status_code != 200:
        print("Falha no login:", response.status_code)
        return None
    

    # Agora faça a requisição POST com o token CSRF
    #update_url = f"http://localhost:8000/iot/update_sensor/{sensor_id}/"
    #data = {"value": payload_value}

    #response = session.post(update_url, data=data)
    print(response.status_code)
    return session
