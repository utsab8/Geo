from django.urls import path
from .views import SignupView, LoginView, LoginPageView, SignupPageView, DebugView, InlineView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup_api'),
    path('login/', LoginView.as_view(), name='login_api'),
    path('signup-page/', SignupPageView.as_view(), name='signup_page'),
    path('login-page/', LoginPageView.as_view(), name='login_page'),
    path('debug/', DebugView.as_view(), name='debug'),
    path('inline/', InlineView.as_view(), name='inline'),
] 