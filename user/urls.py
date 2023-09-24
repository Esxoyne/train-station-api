from django.urls import path

from user.views import CreateTokenView, CreateUserView


urlpatterns = [
    path("register/", CreateUserView.as_view(), name="register"),
    path("login/", CreateTokenView.as_view(), name="login"),
]

app_name = "user"
