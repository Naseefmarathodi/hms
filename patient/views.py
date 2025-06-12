from django.shortcuts import render, redirect
from adminpanel.models import *
from adminpanel.forms import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login
from doctor.views import *
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
import datetime
from django.contrib.auth.models import Group
from .forms import PatientRegistrationForm
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from datetime import datetime



def index(request):
    doctors = Doctor.objects.all()
    news = News.objects.all()
    patient = None
    form = PatientRegistrationForm()
    appointments = DoctorBooking.objects.none()
    if request.user.is_authenticated and hasattr(request.user, 'patient'):
        patient = request.user.patient
        appointments = DoctorBooking.objects.filter(patient=patient)
    
    
    available_slots = []
    is_get_slots = 'get_slots' in request.POST
    is_doctor_available = True 

    if request.method == 'POST':
        patient = Patient.objects.get(user=request.user)
        doctor_id = request.POST.get('doctor')
        appointment_date = request.POST.get('appointment_date')
        slot_id = request.POST.get('slot_time')

        if doctor_id and appointment_date:
            doctor = get_object_or_404(Doctor, id=doctor_id)
            try:
                selected_date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid date format.")
                selected_date_obj = None


            if selected_date_obj and doctor.is_off_day(selected_date_obj.weekday()):
                is_doctor_available = False
                messages.error(request, f"Dr. {doctor.name} is not available on {selected_date_obj.strftime('%A')}.")

            if is_doctor_available and selected_date_obj:

                booked_slot_ids = DoctorBooking.objects.filter(
                    doctor=doctor,
                    booking_date=selected_date_obj
                ).values_list('slot_time__id', flat=True)

                available_slots = DoctorSlot.objects.filter(doctor=doctor).exclude(id__in=booked_slot_ids)


                if not is_get_slots and slot_id:
                    slot = get_object_or_404(DoctorSlot, id=slot_id, doctor=doctor)
                    if DoctorBooking.objects.filter(doctor=doctor, booking_date=selected_date_obj, slot_time=slot).exists():
                        messages.error(request, "This slot is already booked.")
                    else:
                        DoctorBooking.objects.create(
                            doctor=doctor,
                            patient=patient,
                            slot_time=slot,
                            booking_date=selected_date_obj
                        )
                        messages.success(request, "Appointment booked successfully!")
                        return redirect("index")
        else:
            messages.error(request, "Please fill all the fields correctly.")

    return render(request, 'index.html', {
        'doctors': doctors,
        'news': news,
        'appointments': appointments,
        'available_slots': available_slots,
        'form': form,})

def career_view(request):
    return render(request, 'careers.html')

def patient_login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.groups.filter(name="Patient").exists():
                login(request, user)
                return redirect('index')  
            elif user.is_superuser:
                return redirect('adminpanel:adminpanelhome')
            elif user.groups.filter(name="Doctor").exists():
                return redirect('doctor:doctor_dashboard')
            elif user.groups.filter(name="staff").exists():
                return redirect('staff:staff_dashboard')
        messages.error(request, "Invalid credentials or not authorized.")
        return redirect('patient_login')  

    return render(request, 'patient_login.html')



def patient_registration(request):
    if request.method == "POST":
        form = PatientRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            patient = form.save(commit=False)

            first_name = form.cleaned_data.get('first_name').strip().capitalize()
            last_name = form.cleaned_data.get('last_name').strip().capitalize()
            email = form.cleaned_data.get('email')
            dob = form.cleaned_data.get('date_of_birth')

   
            base_username = f"{first_name.lower()}{last_name.lower()}"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            password = f"{first_name.lower()}{dob.year}"

            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name
            )

            group, _ = Group.objects.get_or_create(name='Patient')
            user.groups.add(group)


            patient.user = user
            patient.save()

            if email:
                subject = 'Your Health Portal Login Details'
                message = f'''Dear {first_name},

Your account has been successfully created.

Username: {username}
Password: {password}

Please keep this information safe.

Best regards,
Health City Team'''
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

            messages.success(request, "Registration successful. Login details sent to your email.")
            return redirect('patient_login')
        else:
            doctors = Doctor.objects.all()
            return render(request, "index.html", {"form": form, "doctors": doctors})
    return redirect('index')



def forgot_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_url = request.build_absolute_uri(f'/reset-password/{uid}/{token}/')

            send_mail(
                subject='Password Reset Request',
                message=f'Hi {user.username}, click the link to reset your password:\n{reset_url}',
                from_email='infohealthcitymlp@gmail.com',
                recipient_list=[user.email],
            )

            messages.success(request, 'A password reset link has been sent to your email.')
            return redirect('patient_login')
        except User.DoesNotExist:
            messages.error(request, 'Username not found.')
    
    return render(request, 'forgot_password.html')


def reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if password == confirm_password:
                user.set_password(password)
                user.save()
                messages.success(request, 'Your password has been reset. You can now log in.')
                return redirect('patient_login')
            else:
                messages.error(request, 'Passwords do not match.')
        return render(request, 'reset_password.html', {'validlink': True})
    else:
        messages.error(request, 'Invalid or expired reset link.')
        return render(request, 'reset_password.html', {'validlink': False})
    

def active_vacancy_list(request):
    vacancies = Vacancy.objects.filter(is_active=True, application_deadline__gte=timezone.now().date())
    return render(request, 'active_vacancies.html', {'vacancies': vacancies})



def apply_to_vacancy(request, vacancy_id):
    vacancy = get_object_or_404(Vacancy, id=vacancy_id, is_active=True, application_deadline__gte=timezone.now().date())
    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.vacancy = vacancy
            application.save()
            messages.success(request, "Application submitted successfully.")
            return redirect('active_vacancy_list')
    else:
        form = ApplicationForm()
    return render(request, 'apply_vacancy.html', {'form': form, 'vacancy': vacancy})
