from django.urls import path

from service_desk_bot.views import get_filling_an_app, post_filling_an_app, TestBitrixMethod, CheckUserInBitrix, test_page

app_name = 'service_desk_bot'

urlpatterns = [
    path('fill_an_app/', get_filling_an_app, name='fill_an_app'),
    path('create_new_app/', post_filling_an_app, name='create_new_app'),
    path('check_user/', CheckUserInBitrix.as_view(), name='check_user'),

    path('test_bitrix_method/', TestBitrixMethod.as_view(), name='test_bitrix_method'),
    path('test_page/', test_page, name='test_page'),
]
