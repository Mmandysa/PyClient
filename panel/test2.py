import auth
import connect
import encrypt
import storage
import logging

logging.basicConfig(level=logging.DEBUG)

# # Register
# auth.register("test123", "123456", "test@test.com")

# # Login
# auth.login("email", "test123", "123456")

# # Logout
# auth.logout()

# # # Test CryptoManager
# # encrypt.test_with_plain_text()
# # encrypt.test_with_base64_input()
# # encrypt.test_with_bytes_input()
# # encrypt.remove_pem_file()

# # # Test SecureStorage
# # storage.test_save_and_get()

# # # Test Connect
# # connect.getlist()
# # connect.addfriend("email", "test123")   

# Register
#auth.register("test1", "123456", "test@test.com")

# # Login
# auth.login("username", "test1", "123456")

# # Logout
#auth.logout()

# # Test CryptoManager
# encrypt.test_with_plain_text()
# encrypt.test_with_base64_input()
# encrypt.test_with_bytes_input()
# encrypt.remove_pem_file()

# # Test SecureStorage
# storage.test_save_and_get()

# # Test Connect
# connect.getlist()
# connect.addfriend("email", "test123") 
# 
# # Register
# auth.register("test1", "123456", "test@test.com")

# # Login
# auth.login("username", "test123", "123456")

# # Logout
# auth.logout()

# # Test CryptoManager
# encrypt.test_with_plain_text()
# encrypt.test_with_base64_input()
# encrypt.test_with_bytes_input()
# encrypt.remove_pem_file()

# # Test SecureStorage
# storage.test_save_and_get()

# # Test Connect
# connect.getlist()
# # connect.addfriend("username", "test123")  
# connect.deletefriend("username", "test123")  
# connect.getlist()

# inf = connect.updateinfo("nick")
# print(inf)

# # Test Friend Request
# req = connect.create_friend_request("test123")
# print(req)

# deal = connect.deal_friend_request("test1", 1)
# print(deal)

req_list = connect.show_friend_request_list()
print(req_list)