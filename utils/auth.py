def login(email, password):
    # You can hardcode for now or use Firebase
    dummy_users = {"abc": "def","laya": "laya123"}
    return dummy_users.get(email) == password
