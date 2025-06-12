from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name= 'staff'
urlpatterns = [
    path('', views.staff_login_view, name='staffhome'),
    path('dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('logout/', views.staff_logout, name='staff_logout'),
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/add/', views.patient_registration, name='patient_registration'),
    path('patient/<str:mr_no>/', views.patient_detail, name='patient_detail'),
    path('patient/update/<str:mr_no>/', views.update_patient, name='patient_update'),
    path('patient/delete/<str:mr_no>/', views.delete_patient, name='patient_delete'),
    path('patients/<int:pk>/update-credentials/', views.update_patient_credentials, name='patient_credentials_update'),


    path('book_appointment/<str:patient_mr_no>/', views.book_appointment, name='book_appointment_with_patient'),
    path('book_appointment/', views.book_appointment, name='book_appointment'),
    path("confirm-appointment/", views.confirm_appointment, name="confirm_appointment"),
    path('print-appointment/<int:appointment_id>/', views.print_appointment, name='appointment_summary'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('book_appointment/<str:patient_mr_no>/', views.book_appointment, name='book_appointment_with_patient'),
    
    path('appointments/<int:appointment_id>/details/', views.booking_details, name='booking_details'),
    path('appointments/<int:appointment_id>/update/', views.booking_update, name='booking_update'),
    path('appointments/<int:appointment_id>/delete/', views.booking_delete, name='booking_delete'),
    # path('get-available-slots/', views.get_available_slots, name='get_available_slots'),

    



]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)