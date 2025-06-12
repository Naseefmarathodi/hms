from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'doctor'
urlpatterns = [
    path('', views.doctor_login_view, name='doctorhome'),
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('logout/', views.doctor_logout, name='doctor_logout'),
    path('bookings/', views.doctor_bookings, name='doctor_bookings'),
    path('visit/<int:booking_id>/', views.add_or_edit_visit, name='add_or_edit_visit'),
    path('visit/search/', views.search_patient_for_visit, name='search_patient_visit'),
    path('visits/completed/', views.completed_visits_view, name='completed_visits'),
    path('visit/<int:visit_id>/view/', views.view_completed_visit, name='view_completed_visit'),
    path('visit/<int:visit_id>/edit/', views.edit_completed_visit, name='edit_completed_visit'),



]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)