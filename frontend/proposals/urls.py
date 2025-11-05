from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path("propositions/", views.list_proposals, name="list_proposals"),
    path("propositions/<int:id_prop>/decision/", views.decide_proposal, name="decide_proposal"),
    path("propositions/generer_prets/", views.generer_prets, name="generer_prets"),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password/', views.change_password, name='change_password'),
    path('non_autorise/', views.non_autorise_view, name='non_autorise'),
]