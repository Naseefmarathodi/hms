from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('careers/', views.career_view, name='career'),
    path('register/', views.patient_registration, name='patient_registration'),
    path('patient/login/', views.patient_login_view, name='patient_login'),

    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),

    path('vacancies/apply/<int:vacancy_id>/', views.apply_to_vacancy, name='apply_to_vacancy'),
    path('vacancies/active/', views.active_vacancy_list, name='active_vacancy_list'),

    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  