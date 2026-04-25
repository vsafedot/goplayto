from django.urls import path
from . import views

urlpatterns = [
    # Merchant endpoints
    path('merchants/',                          views.merchant_list,    name='merchant-list'),
    path('merchants/<uuid:merchant_id>/',       views.merchant_detail,  name='merchant-detail'),
    path('merchants/<uuid:merchant_id>/ledger/',views.merchant_ledger,  name='merchant-ledger'),
    path('merchants/<uuid:merchant_id>/payouts/',views.merchant_payouts, name='merchant-payouts'),

    # Payout endpoints
    path('payouts/',                            views.create_payout_view, name='payout-create'),
    path('payouts/<uuid:payout_id>/',           views.payout_detail,      name='payout-detail'),
]
