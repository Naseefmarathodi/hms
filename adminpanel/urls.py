from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import CustomLogoutView, appointment1, appointment_confirm, book_appointment, confirm_appointment, delete_patient, doctor_appointment_list, get_available_slots, login_view, adminpanelhome, print_appointment,  staff_registration, staff_detail, staff_list, staff_update, staff_delete, update_patient
from .views import add_department, update_department, delete_department, department_list
from .views import add_doctor_department, doctor_department_list, update_doctor_department, delete_doctor_department
from .views import doctor_registration, doctor_list, doctor_detail, doctor_update, doctor_delete, update_doctor_credentials
from .views import patient_registration, patient_list, patient_detail
from .views import get_patients_by_phone, appointment_list
from . import views

app_name = 'adminpanel'

urlpatterns = [
    
    path('', login_view, name='login_view'),
    path('adminpanelhome/', adminpanelhome, name='adminpanelhome'),
    # path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('access-denied/', views.access_denied, name='access_denied'),
    path('logout/', views.adminpanel_logout, name='adminpanel_logout'),
    


    path('staff_registration/', staff_registration, name='staff_registration'),
    path('staff/<str:staff_id>/', staff_detail, name='staff_detail'),
    path('staff/', staff_list, name='staff_list'),
    path('staff/update/<str:erp_id>/', staff_update, name='staff_update'),
    path('staff/delete/<str:erp_id>/', staff_delete, name='staff_delete'),
    path('staff/<str:erp_id>/update-credentials/', views.update_staff_credentials, name='staff_credentials_update'),
    
    
    path('add/', add_department, name='add_department'),  
    path('<int:id>/update/', update_department, name='update_department'), 
    path('<int:id>/delete/', delete_department, name='delete_department'),  
    path('list/', department_list, name='department_list'),  

    path('add_doctor_department/', add_doctor_department, name='add_doctor_department'),
    path('doctor/department/', doctor_department_list, name='doctor_department_list'),
    path('update_doctor_department/<int:id>/', update_doctor_department, name='update_doctor_department'),
    path('delete_doctor_department/<int:id>/', delete_doctor_department, name='delete_doctor_department'),

    path('doctor_registration/', doctor_registration, name='doctor_registration'),
    path('doctor/', doctor_list, name='doctor_list'),
    # path('doctor/<str:doctor_id>/', doctor_detail, name='doctor_detail'),
    path('doctor/<str:doctor_erp_id>/', views.doctor_detail, name='doctor_detail'),
    path('doctor/update/<str:doctor_erp_id>/', doctor_update, name='doctor_update'),
    path('doctor/delete/<str:doctor_erp_id>/', doctor_delete, name='doctor_delete'),
    path('doctor/<int:doctor_id>/update_credentials/', update_doctor_credentials, name='doctor_credentials_update'),
    path('doctor/<str:doctor_erp_id>/credentials/', update_doctor_credentials, name='update_doctor_credentials'),



    path('patient_registration/', patient_registration, name='patient_registration'),
    path('patient/', patient_list, name='patient_list'),
    path('patients/<int:pk>/update-credentials/', views.update_patient_credentials, name='patient_credentials_update'),
    path('patient/<str:mr_no>/', patient_detail, name='patient_detail'),
    path('patient/update/<str:mr_no>/', update_patient, name='patient_update'),
    path('patient/delete/<str:mr_no>/', delete_patient, name='patient_delete'),
    


    # path('appointment/', book_appointment, name='book_appointment'),
    # path('appointment/<int:doctor_id>/', book_appointment, name='book_appointment'),
     # path("get-patients/", get_patients_by_phone, name="get_patients_by_phone"), # type: ignore
    # path("get-patients/<str:phone>/", get_patients_by_phone, name="get_patients_by_phone"), # type: ignore
    path('appointments/doctor/<int:doctor_id>/', doctor_appointment_list, name='doctor_appointment_list'),
    path('appointment_list/', appointment_list, name='appointment_list'),
    path('print-appointment/<int:appointment_id>/', print_appointment, name='print_appointment'),
    # path("get-available-slots/", get_available_slots, name="get_available_slots"),
    path('appointment/book/', appointment1, name='appointment1'),
    path('appointment/confirm/', appointment_confirm, name='appointment_confirm'),
    path('get-patients/', get_patients_by_phone, name='get_patients_by_phone'),
    path('book_appointment/<str:patient_mr_no>/', book_appointment, name='book_appointment_with_patient'),
    path('book_appointment/', book_appointment, name='book_appointment'),
    path("confirm-appointment/", confirm_appointment, name="confirm_appointment"),
    path('print-appointment/<int:appointment_id>/', print_appointment, name='appointment_summary'),
    path('appointments/', appointment_list, name='appointment_list'),
    
    path('appointments/<int:appointment_id>/details/', views.booking_details, name='booking_details'),
    path('appointments/<int:appointment_id>/update/', views.booking_update, name='booking_update'),
    path('appointments/<int:appointment_id>/delete/', views.booking_delete, name='booking_delete'),
    path('get-available-slots/', get_available_slots, name='get_available_slots'),

    path('create-news', views.create_news, name='create_news'),
    path('news-list', views.news_list, name='news_list'),
    path('news/<int:news_id>/update/', views.edit_news, name='edit_news'),
    path('news/<int:news_id>/delete/', views.delete_news, name='delete_news'),

    path('vacancies/', views.vacancy_list, name='vacancy_list'),
    path('vacancies/create/', views.create_vacancy, name='create_vacancy'),
    path('vacancies/edit/<int:pk>/', views.edit_vacancy, name='edit_vacancy'),
    path('vacancies/delete/<int:pk>/', views.delete_vacancy, name='delete_vacancy'),

    path('vacancies/apply/<int:vacancy_id>/', views.apply_to_vacancy, name='apply_to_vacancy'),
    path('vacancies/active/', views.active_vacancy_list, name='active_vacancy_list'),
    path('applications/', views.application_list_by_vacancy, name='application_list_by_vacancy'),
    path('applications/delete/<int:application_id>/', views.delete_application, name='delete_application'),




]




if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)