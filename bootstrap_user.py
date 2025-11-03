from utils.auth import register, load_users

username = "leetcodescamp"
password = "leetcodescamp"

ok = register(username, password, name="LeetCode Scamp")
print("User created?" , ok)
print(load_users())
