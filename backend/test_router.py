from main import app
print("Testing routes in app:")
for route in app.routes:
    print(route.path)
