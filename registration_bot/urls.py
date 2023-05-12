from django.urls import path

from registration_bot.views import BotUsersView, CompanyDataView, BankDataView, WorkWthOL, WorkWthDeal, \
    WorkWthDocuments, start_bitrix, common_bitrix, SomeBtrxMethod, PersData, BotRatingView, AddTaskToLawyer, \
    ReminderManagementView, MarketplaceWorkView

urlpatterns = [
    path('bot_users/', BotUsersView.as_view(), name='bot_users'),
    path('company/', CompanyDataView.as_view(), name='company'),
    path('bank/', BankDataView.as_view(), name='bank'),
    path('open_line/', WorkWthOL.as_view(), name='open_line'),
    path('deal_update/', WorkWthDeal.as_view(), name='deal_update'),
    path('docs_gen/', WorkWthDocuments.as_view(), name='docs_gen'),
    path('prs_dt/', PersData.as_view(), name='prs_dt'),
    path('rating/', BotRatingView.as_view(), name='rating'),
    path('law_task/', AddTaskToLawyer.as_view(), name='law_task'),
    path('remind/', ReminderManagementView.as_view(), name='remind'),
    path('marketplaces/', MarketplaceWorkView.as_view(), name='marketplaces'),
    path('strt_btrx/', start_bitrix, name='strt_btrx'),
    path('cmn_btrx/', common_bitrix, name='cmn_btrx'),
    path('some_btrx_method/', SomeBtrxMethod.as_view(), name='some_btrx_method')
]
