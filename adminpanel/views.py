from email.headerregistry import Group
from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LogoutView
from django.urls import reverse, reverse_lazy
from .forms import  DoctorBookingForm, DoctorCredentialUpdateForm, DoctorUpdateForm, PatientForm, StaffForm, StaffDepartmentForm, DoctorDepartmentForm, DoctorForm, AppointmentForm, PatientVisitForm, PatientCredentialForm, PatientUpdateForm, StaffCredentialUpdateForm, news_form, VacancyForm, ApplicationForm
from .models import DoctorBooking, DoctorSlot, News, Patient, Staff, StaffDepartment, DoctorDepartment, Doctor, PatientVisit, Vacancy, Application
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.contrib import messages
from datetime import date, datetime, time, timedelta
from django.utils import timezone 
from django.db.models import Q
import logging
from django.core.cache import cache
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test


logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('adminpanel:adminpanelhome')
        messages.error(request, "Invalid credentials")
    
    return render(request, 'siteadmin/loginadminpanel.html') 



def adminpanel_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('adminpanel:login_view')

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def adminpanelhome(request):
    """Admin panel home view with staff and doctor directo`r`ies."""
    context = {
        'staffs': Staff.objects.all(),
        'doctors': Doctor.objects.all(),
        'total_staff': Staff.objects.count(),
        'total_doctors': Doctor.objects.count(),

    
    }
    return render(request, 'siteadmin/adminpanelhome.html', context)

def access_denied(request):
    return render(request, 'siteadmin/access_denied.html')

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('adminpanel:login')
        
@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def staff_department(request):
    """Handles staff department registration."""
    if request.method == 'POST':
        form = StaffDepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('adminpanelhome')
    else:
        form = StaffDepartmentForm()
    return render(request, 'siteadmin/staff_department.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def staff_registration(request):
    if request.method == "POST":
        erp_id = request.POST.get("erp_id")
        name = request.POST.get("name")
        username = request.POST.get("username")  
        password = request.POST.get("password")  
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        department_id = request.POST.get("department")
        profile_picture = request.FILES.get("profile_picture")

        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists. Please choose another username.')
            departments = StaffDepartment.objects.all()
            return render(request, "siteadmin/staffregistration.html", {"departments": departments, "username": username})

        # Create or get the User
        user = None
        if username and password:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password)  
                user.save()

    
        department = StaffDepartment.objects.get(id=department_id)

        staff = Staff(
            erp_id=erp_id,
            name=name,
            user=user,
            email=email,
            phone_number=phone_number,
            department=department,
            profile_picture=profile_picture,
        )
        staff.save()

        return render(request, 'siteadmin/staffview.html', {'staff': staff})  

 
    departments = StaffDepartment.objects.all()
    return render(request, "siteadmin/staffregistration.html", {"departments": departments})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def update_staff_credentials(request, erp_id):
    staff = get_object_or_404(Staff, erp_id=erp_id)
    user = staff.user

    if request.method == 'POST':
        form = StaffCredentialUpdateForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            if 'password' in form.cleaned_data and form.cleaned_data['password']:
                user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Staff credentials updated successfully.")
            return redirect('adminpanel:staff_list')
    else:
        form = StaffCredentialUpdateForm(instance=user)

    return render(request, 'siteadmin/staff_credentials_update.html', {
        'form': form,
        'user': user,
    })


@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def staff_detail(request, staff_id):
    
    staff = get_object_or_404(Staff, erp_id=staff_id)
    
    return render(request, 'siteadmin/staffview.html', {'staff': staff})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def staff_list(request):
    query = request.GET.get('q')
    staffs = Staff.objects.all()

    if query:
        staffs = staffs.filter(
            Q(erp_id__icontains=query) |
            Q(name__icontains=query)
        )

    return render(request, 'siteadmin/staff_list.html', {'staffs': staffs, 'query': query})
@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def staff_update(request, erp_id):
    staff = get_object_or_404(Staff, erp_id=erp_id)
    
    if request.method == 'POST':
        form = StaffForm(request.POST, request.FILES, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff information updated successfully!')
            return redirect('adminpanel:staff_list')
    else:
        form = StaffForm(instance=staff)
    
    return render(request, 'siteadmin/staff_update.html', {'form': form, 'staff': staff})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def staff_delete(request, erp_id):
    staff = get_object_or_404(Staff, erp_id=erp_id)
    
    if request.method == 'POST':
        staff.delete()
        messages.success(request, 'Staff deleted successfully!')
        return redirect('adminpanel:staff_list')

    return render(request, 'siteadmin/staff_delete_confirm.html', {'staff': staff})




@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def add_department(request):
    if request.method == "POST":
        form = StaffDepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('adminpanel:department_list')  
    else:
        form = StaffDepartmentForm()

    return render(request, "siteadmin/add_department.html", {'form': form})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def department_list(request):
    departments = StaffDepartment.objects.all()  
    return render(request, 'siteadmin/department_list.html', {'departments': departments})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def update_department(request, id):
    department = get_object_or_404(StaffDepartment, id=id)
    
    if request.method == 'POST':
        form = StaffDepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated successfully!')
            return redirect('adminpanel:department_list')
    else:
        form = StaffDepartmentForm(instance=department)
    
    return render(request, 'siteadmin/update_department.html', {'form': form, 'department': department})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def delete_department(request, id):
    department = get_object_or_404(StaffDepartment, id=id)
    department.delete() 
    return redirect('adminpanel:department_list') 

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def add_doctor_department(request):
    if request.method == "POST":
        form = DoctorDepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('adminpanel:doctor_department_list') 
    else:
        form = DoctorDepartmentForm()

    return render(request, "siteadmin/add_doctor_department.html", {'form': form})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def doctor_department_list(request):
    departments = DoctorDepartment.objects.all()  
    return render(request, 'siteadmin/doctor_department_list.html', {'departments': departments})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def update_doctor_department(request, id):
    department = get_object_or_404(DoctorDepartment, id=id)
    
    if request.method == 'POST':
        form = DoctorDepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated successfully!')
            return redirect('adminpanel:doctor_department_list')
    else:
        form = DoctorDepartmentForm(instance=department)
    
    return render(request, 'siteadmin/update_doctor_department.html', {'form': form, 'department': department})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def delete_doctor_department(request, id):
    department = get_object_or_404(DoctorDepartment, id=id)
    department.delete() 
    return redirect('adminpanel:doctor_department_list')  


@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def doctor_list(request):
    query = request.GET.get('q')
    doctors = Doctor.objects.all()

    if query:
        doctors = doctors.filter(
            Q(erp_id__icontains=query) |
            Q(name__icontains=query)
        )

    return render(request, 'siteadmin/doctor_list.html', {'doctors': doctors, 'query': query})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def doctor_detail(request, doctor_erp_id):
    doctor = Doctor.objects.get(erp_id=doctor_erp_id)  # Query by erp_id
    off_days_abbr = doctor.off_days.split(',') if doctor.off_days else []  # Split into list

    # Mapping from string numbers to weekday names
    day_mapping = dict(Doctor.DAY_CHOICES)

    # Convert string day numbers to full names, skip invalid ones
    off_days_full = [day_mapping.get(day.strip()) for day in off_days_abbr if day.strip() in day_mapping]

    return render(request, 'siteadmin/doctorview.html', {
        'doctor': doctor,
        'off_days': off_days_full
    })

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def doctor_registration(request):
    if request.method == "POST":
        form = DoctorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('adminpanel:doctor_list')
    else:
        form = DoctorForm()

    return render(request, "siteadmin/doctorregistration.html", {"form": form})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def doctor_update(request, doctor_erp_id):
    doctor = get_object_or_404(Doctor, erp_id=doctor_erp_id)
    if request.method == "POST":
        form = DoctorUpdateForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Doctor details updated successfully!')
            return redirect('adminpanel:doctor_list')
    else:
        form = DoctorUpdateForm(instance=doctor)
    # day_mapping = dict(Doctor.DAY_CHOICES)
    # off_days_abbr = doctor.off_days.split(',') if doctor.off_days else []
    # off_days_full = [day_mapping.get(day.strip()) for day in off_days_abbr if day.strip() in day_mapping]


    return render(request, 'siteadmin/doctor_update.html', {
        'form': form,
        'doctor': doctor,
        # 'off_days': off_days_full
    })

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def update_doctor_credentials(request, doctor_erp_id):
    doctor = get_object_or_404(Doctor, erp_id=doctor_erp_id)
    user = doctor.user

    if request.method == 'POST':
        form = DoctorCredentialUpdateForm(request.POST, instance=user)
        if form.is_valid():
            user.set_password(form.cleaned_data['password'])  
            user.save()
            return redirect('adminpanel:doctor_list')
    else:
        form = DoctorCredentialUpdateForm(instance=user)

    return render(request, 'siteadmin/doctor_credentials_update.html', {
        'form': form,
        'doctor': doctor
    })

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def doctor_delete(request, doctor_erp_id):
    doctor = get_object_or_404(Doctor, erp_id=doctor_erp_id)
    
    if request.method == 'POST':
        doctor.delete()
        messages.success(request, 'Doctor deleted successfully!')
        return redirect('adminpanel:doctor_list')

    return render(request, 'siteadmin/doctor_delete_confirm.html', {'doctor': doctor})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def patient_registration(request):
    if request.method == "POST":
        form = PatientForm(request.POST, request.FILES)
        if form.is_valid():
            patient = form.save(commit=False)

            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            email = form.cleaned_data.get('email')
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')

            # if username and password:
            #     user = User.objects.create_user(
            #         username=username,
            #         email=email,
            #         password=password,
            #         first_name=first_name,
            #         last_name=last_name
            #     )
            #     group, _ = Group.objects.get_or_create(name='Patient')
            #     user.groups.add(group)

            #     patient.user = user
            #     patient.save()


            if username and password:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                group, _ = Group.objects.get_or_create(name='Patient')
                user.groups.add(group)

                patient.user = user
                patient.save()

                # Send login credentials to the patient's email
                if email:
                    subject = 'Your  Portal Login Details'
                    message = f'''
            Dear {first_name},

            Your  account has been successfully created.

            Username: {username}
            Password: {password}

            Please keep this information safe and do not share it with anyone.


            Best regards,
            Health City Team
            '''
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])


                return redirect('adminpanel:patient_list')
    else:
        form = PatientForm()

    return render(request, "siteadmin/patientregistration.html", {"form": form})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def update_patient_credentials(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    user = patient.user  # Assuming Patient has a OneToOneField to User

    if request.method == 'POST':
        form = PatientCredentialForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            user.save()
            messages.success(request, 'Username and password updated successfully!')
            return redirect('adminpanel:patient_list')
    else:
        form = PatientCredentialForm(instance=user)

    return render (request, 'siteadmin/patient_credentials_update.html', {'form': form, 'patient': patient})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def patient_list(request):
    query = request.GET.get('q', '')  # Get search query from URL parameters
    patients = Patient.objects.all()


    if query:
        patients = patients.filter(

            Q(mr_no__icontains=query) |  # Search by MR number
            Q(phone_number__icontains=query)  # Search by phone number

        )

    return render(request, 'siteadmin/patient_list.html', {'patients': patients, 'query': query})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def patient_detail(request, mr_no):
    patient = get_object_or_404(Patient, mr_no=mr_no)  
    return render(request, 'siteadmin/patient_view.html', {'patient': patient})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def update_patient(request, mr_no):
    patient = get_object_or_404(Patient, mr_no=mr_no)

    if request.method == 'POST':
        form = PatientUpdateForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient information updated successfully!')
            return redirect('adminpanel:patient_list')
    else:
        form = PatientUpdateForm(instance=patient)

    return render(request, 'siteadmin/patient_update.html', {
        'form': form,
        'patient': patient
    })


@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def delete_patient(request, mr_no):
    patient = get_object_or_404(Patient, mr_no=mr_no)  
    patient.delete() 
    return redirect('adminpanel:patient_list')  

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def get_patients_by_phone(request):
    phone_number = request.GET.get('phone_number', '')

    logger.debug(f"Searching for patients with phone number: {phone_number}")


    # Filter patients whose phone number contains the input
    patients = Patient.objects.filter(phone_number__icontains=phone_number).values(
        "mr_no", "first_name", "last_name", "phone_number"
    )

    if patients.exists():
        return JsonResponse({"patients": list(patients)})
    else:
        registration_url = reverse('adminpanel:patient_register')  # Update with your actual registration URL name
        return JsonResponse({
            "patients": [],
            "warning": "Patient not registered.",
            "register_url": registration_url
        })
    


logger = logging.getLogger(__name__)
def book_appointment(request, patient_mr_no=None):
    print("Entered book_appointment view")
    doctors = Doctor.objects.all()
    print(f"Fetched doctors count: {doctors.count()}")
    doctor = None
    available_slots = []
    selected_date = None
    is_doctor_available = True
    patient = None
    patient_not_found = False

    # Fetch the patient if MR number is provided
    if patient_mr_no:
        try:
            patient = Patient.objects.get(mr_no=patient_mr_no)
            print(f"Patient found: {patient.first_name} with MR No: {patient.mr_no}")
        except Patient.DoesNotExist:
            patient_not_found = True
            print(f"Patient with MR No {patient_mr_no} not found")

    if request.method == "POST":
        doctor_id = request.POST.get("doctor")
        selected_date = request.POST.get("appointment_date")
        print(f"POST received: doctor_id={doctor_id}, selected_date={selected_date}")

        if not doctor_id or not selected_date:
            print("Error: Doctor or date not selected")
            messages.error(request, "Please select a doctor and date.")
            return render(request, "siteadmin/book_appointment.html", {
                "doctors": doctors,
                "error_message": "Please select a doctor and date.",
            })

        doctor = get_object_or_404(Doctor, id=doctor_id)
        print(f"Selected Doctor: {doctor.name} (ID: {doctor.id})")

        try:
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            print(f"Parsed selected_date_obj: {selected_date_obj}")
        except ValueError:
            print("Error: Invalid date format")
            messages.error(request, "Invalid date format.")
            return redirect("adminpanel:book_appointment")

        # ✅ Fix: pass weekday() as integer, not day string
        if doctor.is_off_day(selected_date_obj.weekday()):
            is_doctor_available = False
            print(f"Doctor {doctor.name} is off on {selected_date_obj.strftime('%A')}")
            messages.error(request, f"Dr. {doctor.name} is not available on {selected_date_obj.strftime('%A')}.")
            return render(request, "siteadmin/book_appointment.html", {
                "doctors": doctors,
                "doctor": doctor,
                "selected_date": selected_date_obj,
                "is_doctor_available": is_doctor_available,
                "available_slots": [],
                "patient": patient,
                "patient_not_found": patient_not_found,
                "register_url": reverse("adminpanel:patient_registration"),
            })

        # Get available slots for the selected date
        available_slots = doctor.get_available_slots(selected_date_obj)
        print(f"Available slots count: {len(available_slots)}")
        is_doctor_available = bool(available_slots)

        if not available_slots:
            print("No available slots for this doctor on the selected day.")
            messages.error(request, "No available slots for this doctor on the selected day.")
            return render(request, "siteadmin/book_appointment.html", {
                "doctors": doctors,
                "doctor": doctor,
                "selected_date": selected_date_obj,
                "available_slots": [],
                "is_doctor_available": is_doctor_available,
                "patient": patient,
                "patient_not_found": patient_not_found,
                "register_url": reverse("adminpanel:patient_registration"),
            })

        print("Rendering template with available slots")
        return render(request, "siteadmin/book_appointment.html", {
            "doctors": doctors,
            "doctor": doctor,
            "available_slots": available_slots,
            "selected_date": selected_date_obj,
            "patient": patient,
            "patient_not_found": patient_not_found,
            "register_url": reverse("adminpanel:patient_registration"),
            "is_doctor_available": is_doctor_available,
        })

    print("GET request - rendering initial form")
    return render(request, "siteadmin/book_appointment.html", {
        "doctors": doctors,
        "patient": patient,
        "patient_not_found": patient_not_found,
        "register_url": reverse("adminpanel:patient_registration"),
    })




@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def confirm_appointment(request):
    """Handles doctor appointment booking by hospital staff using patient phone number."""

    doctor_id = request.GET.get("doctor") or request.POST.get("doctor")
    selected_date = request.GET.get("date") or request.POST.get("appointment_date")
    patient_phone = request.GET.get("phone") or request.POST.get("phone")
    patient_id = request.GET.get("patient_id") or request.POST.get("patient_id")


    doctor = get_object_or_404(Doctor, id=doctor_id)

   
    try:

        selected_date_obj = datetime.strptime(selected_date, "%B %d, %Y").date()  

    except ValueError:
        messages.error(request, "Invalid date format.")
        return redirect("adminpanel:book_appointment")


    available_slots = doctor.get_available_slots(selected_date_obj)




    if patient_id:
            try:
                patient = Patient.objects.get(id=patient_id)
            except Patient.DoesNotExist:
                messages.error(request, "Invalid patient selected.")
                return redirect("adminpanel:book_appointment")
        

    elif patient_phone:
            matching_patients = Patient.objects.filter(phone_number=patient_phone)

            if not matching_patients.exists():
                messages.error(request, "Patient not found. Please register the patient first.")
                register_url = reverse("adminpanel:patient_registration")
                return render(request, "siteadmin/booking_confirm.html", {
                    "doctor": doctor,
                    "available_slots": available_slots,
                    "selected_date": selected_date,
                    "patient": None,
                    "register_url": register_url,
                })


            if matching_patients.count() > 1 and request.method != "POST":
                return render(request, "siteadmin/booking_patient_select.html", {
                    "patients": matching_patients,
                    "doctor": doctor,
                    "selected_date": selected_date,
                    "phone": patient_phone,
                })

            patient = matching_patients.first()

    else:
            messages.error(request, "No patient information provided.")
            return redirect("adminpanel:book_appointment")



    if request.method == "POST":
        post_data = request.POST.copy()
        post_data["booking_date"] = selected_date_obj  
        post_data["patient"] = patient.id  

        form = DoctorBookingForm(post_data, doctor=doctor)


        selected_slot_id = request.POST.get("slot_time")
        if not selected_slot_id:
            messages.error(request, "Please select a valid time slot.")
            return render(request, "siteadmin/booking_confirm.html", {
                "doctor": doctor,
                "available_slots": available_slots,
                "selected_date": selected_date,
                "form": form,
                "patient": patient,
            })


        selected_slot = DoctorSlot.objects.filter(id=selected_slot_id, doctor=doctor).first()
        if not selected_slot:
            messages.error(request, "Invalid slot selection.")
            return render(request, "siteadmin/booking_confirm.html", {
                "doctor": doctor,
                "available_slots": available_slots,
                "selected_date": selected_date,
                "form": form,
                "patient": patient,
            })


        if form.is_valid():
            booking = form.save(commit=False)
            booking.doctor = doctor
            booking.patient = patient
            booking.slot_time = selected_slot
            booking.booking_date = selected_date_obj
            booking.save()

            messages.success(request, "Appointment booked successfully!")
            return redirect("adminpanel:appointment_summary", appointment_id=booking.id)
        else:
            messages.error(request, "Please correct the errors below.")
           

    else:
        form = DoctorBookingForm(doctor=doctor)

    return render(request, "siteadmin/booking_confirm.html", {
        "doctor": doctor,
        "available_slots": available_slots,
        "selected_date": selected_date,
        "form": form,
        "patient": patient,
    })



@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def booking_details(request, appointment_id):
    appointment = get_object_or_404(DoctorBooking, id=appointment_id)
    return render(request, 'siteadmin/booking_details.html', {'appointment': appointment})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def get_available_slots(request):
    if request.method == 'GET':
        doctor_id = request.GET.get('doctor_id')
        selected_date = request.GET.get('selected_date')

        if doctor_id and selected_date:
            doctor = Doctor.objects.get(id=doctor_id)
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()

           
            available_slots = doctor.get_available_slots(selected_date)
            
            
            selected_slot_id = request.GET.get('selected_slot_id')
            if selected_slot_id:
                available_slots = [slot for slot in available_slots if slot.id != int(selected_slot_id)]
            
          
            slots_data = [{'id': slot.id, 'start_time': slot.start_time.strftime('%I:%M %p')} for slot in available_slots]

            return JsonResponse({'slots': slots_data})

        return JsonResponse({'error': 'Invalid data'}, status=400)

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def booking_update(request, appointment_id):
    appointment = get_object_or_404(DoctorBooking, id=appointment_id)
    selected_date = appointment.booking_date
    print(f"Debug: Updating appointment with ID {appointment_id}")

    doctor = appointment.doctor
    patient = appointment.patient
    print(f"Debug: Doctor selected: {doctor.name}, Patient selected: {patient.first_name} {patient.last_name}")

    selected_date_obj = selected_date

    is_doctor_available = True
    if doctor.is_off_day(selected_date_obj.strftime("%a")):  
        is_doctor_available = False
        messages.error(request, f"Dr. {doctor.name} is not available on {selected_date_obj.strftime('%A')}.")
        print(f"Debug: Dr. {doctor.name} is not available on {selected_date_obj.strftime('%A')}.")
        return render(request, "siteadmin/book_appointment.html", {
            "doctors": Doctor.objects.all(),  
            "error_message": f"Dr. {doctor.name} is not available on {selected_date_obj.strftime('%A')}.",
            "is_doctor_available": is_doctor_available,
        })


    available_slots = doctor.get_available_slots(selected_date)
    print(f"Debug: Available slots fetched: {[slot.start_time for slot in available_slots]}")


    available_slots = [slot for slot in available_slots if slot != appointment.slot_time]
    print(f"Debug: Available slots after removing the selected slot: {[slot.start_time for slot in available_slots]}")


    if request.method == 'POST':
        print(f"Debug: POST data before adding missing fields: {request.POST}")
        if 'doctor' not in request.POST:
            request.POST._mutable = True
            request.POST['doctor'] = doctor.id  
            print(f"Debug: Added doctor ID to POST: {doctor.id}")
        
        if 'patient' not in request.POST:
            request.POST._mutable = True
            request.POST['patient'] = patient.id  
            print(f"Debug: Added patient ID to POST: {patient.id}")


        form = AppointmentForm(request.POST, doctor=doctor, instance=appointment)
        
        if form.is_valid():
            print("Debug: Form is valid")
            form.save()
            print("Debug: Appointment updated successfully")
            return redirect('adminpanel:appointment_list')  
        else:
            print("Debug: Form is invalid")
            print(f"Debug: Form errors: {form.errors}")
    else:
        print("Debug: Rendering form with instance")
        form = AppointmentForm(instance=appointment)

    return render(request, 'siteadmin/booking_update.html', {
        'form': form,
        'appointment': appointment,
        'patient': patient,  
        'doctor': doctor,    
        'available_slots': available_slots,
        'formatted_date': selected_date.strftime('%Y-%m-%d'),  
        'is_doctor_available': is_doctor_available,  
    })





@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def booking_delete(request, appointment_id):
    appointment = get_object_or_404(DoctorBooking, id=appointment_id)
    if request.method == "POST":
        appointment.delete()
        return redirect('adminpanel:appointment_list')
    return render(request, 'siteadmin/booking_delete.html', {'appointment': appointment})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def search_patients(request):
    """AJAX endpoint for searching patients by phone number or MR number."""
    phone_number = request.GET.get('phone_number', '').strip()

    # Return empty list if no phone_number is provided
    if not phone_number:
        return JsonResponse([], safe=False)

    # Perform search based on phone_number or MR number
    patients = Patient.objects.filter(
        Q(mr_no__icontains=phone_number) | Q(phone_number__icontains=phone_number)
    )

    # Return a structured JSON response with the patient details
    return JsonResponse([{
        'mr_no': patient.mr_no,
        'first_name': patient.first_name,
        'last_name': patient.last_name,
        'phone_number': patient.phone_number
    } for patient in patients], safe=False)

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def print_appointment(request, appointment_id):
    """Displays the appointment summary for printing."""
    appointment = get_object_or_404(DoctorBooking, id=appointment_id)
    return render(request, 'siteadmin/appointment_summary.html', {'appointment': appointment})


def appointment_list(request):
    """Displays all booked appointments."""
    appointments = DoctorBooking.objects.all()
    return render(request, 'siteadmin/appointment_list.html', {'appointments': appointments})


def doctor_appointment_list(request, doctor_id):
    """Displays all appointments for a specific doctor."""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    appointments = DoctorBooking.objects.filter(doctor=doctor)
    return render(request, 'siteadmin/doctor_appointment_list.html', {'doctor': doctor, 'appointments': appointments})








logger = logging.getLogger(__name__)

def appointment1(request):
    doctors = Doctor.objects.all()
    available_slots = []
    doctor = None
    selected_date = None
    is_doctor_available = True
    error_message = None

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        selected_date = request.POST.get('appointment_date')

        if not doctor_id or not selected_date:
            error_message = "Please select a doctor and date."
            return render(request, 'siteadmin/appointment1.html', {
                'doctors': doctors,
                'error_message': error_message,
            })

        doctor = get_object_or_404(Doctor, id=doctor_id)
        selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d")

        # Check if the doctor is off on the selected day
        if doctor.is_off_day(selected_date_obj.strftime('%a')):
            is_doctor_available = False
            return render(request, 'siteadmin/appointment1.html', {
                'doctors': doctors,
                'error_message': f"Dr. {doctor.name} is not available on {selected_date_obj.strftime('%A')}.",
                'is_doctor_available': is_doctor_available,
            })

        # Get available slots for the selected doctor and date
        available_slots = doctor.get_available_slots(selected_date_obj)
        is_doctor_available = bool(available_slots)

        if not available_slots:
            error_message = "No available slots for the selected doctor on this day."
            return render(request, 'siteadmin/appointment1.html', {
                'doctors': doctors,
                'error_message': error_message,
                'is_doctor_available': is_doctor_available,
            })

        return render(request, 'siteadmin/appointment1.html', {
            'doctors': doctors,
            'available_slots': available_slots,
            'doctor': doctor,
            'selected_date': selected_date,
            'is_doctor_available': is_doctor_available,
        })

    return render(request, 'siteadmin/appointment1.html', {
        'doctors': doctors,
    })

def appointment_confirm(request):
    doctor_id = request.GET.get('doctor')
    selected_date = request.GET.get('date')
    doctor = get_object_or_404(Doctor, id=doctor_id)
    selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
    available_slots = doctor.get_available_slots(selected_date_obj)

    patients = []

    if request.method == 'POST':
        # Search for patient by phone number or MR number
        patient_identifier = request.POST.get('phone_number')
        patient = Patient.objects.filter(Q(mr_no=patient_identifier) | Q(phone_number=patient_identifier)).first()

        if not patient:
            messages.error(request, "Patient not found. Please enter a valid phone number or MR number.")
            return render(request, 'siteadmin/appointment_confirm.html', {
                'doctor': doctor,
                'available_slots': available_slots,
                'selected_date': selected_date,
            })

        
        #  patient_identifier = request.POST.get('phone_number')
#         patient = Patient.objects.filter(Q(mr_no=patient_identifier) | Q(phone_number=patient_identifier)).first()
#         if not patient:
#             return render(request, 'siteadmin/appointment.html', {
#                 'doctors': doctors,
#                 'available_slots': available_slots,
#                 'error_message': "Patient not found. Please enter a valid phone number or MR number."
#             })

        # Validate slot selection
        selected_slot = request.POST.get('slot_time')
        slot_time = DoctorSlot.objects.filter(start_time=selected_slot).first()

        if not slot_time or DoctorBooking.objects.filter(doctor=doctor, booking_datetime=selected_date_obj.replace(hour=slot_time.start_time.hour, minute=slot_time.start_time.minute)).exists():
            messages.error(request, "The selected slot is already booked.")
            return render(request, 'siteadmin/appointment_confirm.html', {
                'doctor': doctor,
                'available_slots': available_slots,
                'selected_date': selected_date,
            })
        
            

        # Create the booking
        form = DoctorBookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.doctor = doctor
            appointment.slot_time = slot_time
            appointment.booking_datetime = selected_date_obj.replace(hour=slot_time.start_time.hour, minute=slot_time.start_time.minute)
            appointment.save()
            messages.success(request, "Appointment booked successfully!")
            return redirect('adminpanel:appointment_list')

    return render(request, 'siteadmin/appointment_confirm.html', {
        'doctor': doctor,
        'available_slots': available_slots,
        'selected_date': selected_date,
    })


def search_patients(request):
    # Retrieve the phone number from the GET parameters
    phone_number = request.GET.get('phone_number', '')

    # If phone_number is provided, filter patients based on phone number or MR number
    if phone_number:
        patients = Patient.objects.filter(
            Q(mr_no__icontains=phone_number) | Q(phone_number__icontains=phone_number)
        )
    else:
        patients = Patient.objects.none()  # Return an empty queryset if no phone number is provided

    # Prepare patient data for response
    patients_data = [{
        'mr_no': patient.mr_no,
        'first_name': patient.first_name,
        'last_name': patient.last_name,
        'phone_number': patient.phone_number
    } for patient in patients]

    # Return the data as a JSON response
    return JsonResponse(patients_data, safe=False)




def print_appointment(request, appointment_id):
    appointment = get_object_or_404(DoctorBooking, id=appointment_id)
    
    return render(request, 'siteadmin/appointment_summary.html', {
        'appointment': appointment,
    })

def appointment_list(request):
    appointments = DoctorBooking.objects.all() 
    return render(request, 'siteadmin/appointment_list.html', {'appointments': appointments})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def doctor_appointment_list(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    appointments = DoctorBooking.objects.filter(doctor=doctor)
    return render(request, 'siteadmin/doctor_appointment_list.html', {'doctor': doctor, 'appointments': appointments})

def patient_visit_list(request):
    visits = PatientVisit.objects.filter(user=request.user)  # Filter by logged-in user
    return render(request, 'patient_visits.html', {'visits': visits})


def create_patient_visit(request):
    if request.method == "POST":
        form = PatientVisitForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('visit_list') 
    else:
        form = PatientVisitForm(user=request.user)  

    return render(request, 'siteadmin/visit_patient_form.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def news_list(request):
    news = News.objects.all()
    return render(request, 'siteadmin/news_list.html', {'news': news})
@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def create_news(request):
    if request.method == "POST":
        form = news_form(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('adminpanel:news_list')  
    else:
        form = news_form()

    return render(request, 'siteadmin/news_form.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def edit_news(request, news_id):
    news = get_object_or_404(News, id=news_id)
    if request.method == "POST":
        form = news_form(request.POST, request.FILES, instance=news)
        if form.is_valid():
            form.save()
            return redirect('adminpanel:news_list')  
    else:
        form = news_form(instance=news)

    return render(request, 'siteadmin/news_edit.html', {'form': form, 'news': news})

@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def delete_news(request, news_id):
    news = get_object_or_404(News, id=news_id)
    if request.method == "POST":
        news.delete()
        return redirect('adminpanel:news_list')  
    return render(request, 'siteadmin/news_confirm_delete.html', {'news': news})


def deactivate_expired_vacancies():
    today = timezone.now().date()
    Vacancy.objects.filter(application_deadline__lt=today, is_active=True).update(is_active=False)

# 🔹 List vacancies
def vacancy_list(request):
    deactivate_expired_vacancies()
    vacancies = Vacancy.objects.all().order_by('-created_at')
    return render(request, 'siteadmin/vacancy_list.html', {'vacancies': vacancies})


@user_passes_test(lambda u: u.is_superuser, login_url='adminpanel:access_denied')
def create_vacancy(request):
    if request.method == 'POST':
        form = VacancyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Vacancy created successfully.")
            return redirect('adminpanel:vacancy_list')
    else:
        form = VacancyForm()
    return render(request, 'siteadmin/vacancy_form.html', {'form': form})


# 🔹 Edit an existing vacancy
def edit_vacancy(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    if request.method == 'POST':
        form = VacancyForm(request.POST, instance=vacancy)
        if form.is_valid():
            form.save()
            messages.success(request, "Vacancy updated successfully.")
            return redirect('adminpanel:vacancy_list')
    else:
        form = VacancyForm(instance=vacancy)
    return render(request, 'siteadmin/vacancy_edit.html', {'form': form, 'vacancy': vacancy})



def delete_vacancy(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    if request.method == 'POST':
        vacancy.delete()
        messages.success(request, "Vacancy deleted successfully.")
        return redirect('adminpanel:vacancy_list')
    return render(request, 'siteadmin/vacancy_confirm_delete.html', {'vacancy': vacancy})


# 1. List only active vacancies
def active_vacancy_list(request):
    vacancies = Vacancy.objects.filter(is_active=True, application_deadline__gte=timezone.now().date())
    return render(request, 'siteadmin/active_vacancies.html', {'vacancies': vacancies})


# 2. Apply to a specific vacancy
def apply_to_vacancy(request, vacancy_id):
    vacancy = get_object_or_404(Vacancy, id=vacancy_id, is_active=True, application_deadline__gte=timezone.now().date())
    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.vacancy = vacancy
            application.save()
            messages.success(request, "Application submitted successfully.")
            return redirect('adminpanel:active_vacancy_list')
    else:
        form = ApplicationForm()
    return render(request, 'siteadmin/apply_vacancy.html', {'form': form, 'vacancy': vacancy})


# 3. List applications grouped by vacancy
def application_list_by_vacancy(request):
    vacancies = Vacancy.objects.all()
    return render(request, 'siteadmin/application_list.html', {'vacancies': vacancies})

def delete_application(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    if request.method == "POST":
        application.delete()
        messages.success(request, "Application deleted successfully.")
        return redirect('adminpanel:application_list_by_vacancy')
    return render(request, 'siteadmin/application_confirm_delete.html', {'application': application})