from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from adminpanel.models import Staff
from adminpanel.models import *
from adminpanel.forms import *
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def staff_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None and user.groups.filter(name="Staff").exists():
            login(request, user)
            return redirect('staff:staff_dashboard')
        else:
            messages.error(request, "Invalid credentials or not authorized.")
            return redirect('staff:staffhome')
    return render(request, 'staffpanel/staffhome.html')


@login_required
def staff_dashboard(request):
    if request.user.groups.filter(name="Staff").exists():
        return render(request, 'staffpanel/staffloginhome.html')
    else:
        return HttpResponseForbidden("Access Denied")
    
def staff_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('staff:staffhome')


@login_required
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

                return redirect('staff:patient_list')
    else:
        form = PatientForm()

    return render(request, "staffpanel/patientregistration.html", {"form": form})

@login_required
def patient_list(request):
    query = request.GET.get('q', '')  # Get search query from URL parameters
    patients = Patient.objects.all()


    if query:
        patients = patients.filter(

            Q(mr_no__icontains=query) |  # Search by MR number
            Q(phone_number__icontains=query)  # Search by phone number

        ) 

    return render(request, 'staffpanel/patient_list.html', {'patients': patients, 'query': query})


@login_required
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
            return redirect('staff:patient_list')
    else:
        form = PatientCredentialForm(instance=user)

    return render (request, 'staffpanel/patient_credentials_update.html', {'form': form, 'patient': patient})

@login_required
def patient_detail(request, mr_no):
    patient = get_object_or_404(Patient, mr_no=mr_no)  
    return render(request, 'staffpanel/patient_view.html', {'patient': patient})

@login_required
def update_patient(request, mr_no):
    patient = get_object_or_404(Patient, mr_no=mr_no)

    if request.method == 'POST':
        form = PatientUpdateForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient information updated successfully!')
            return redirect('staff:patient_list')
    else:
        form = PatientUpdateForm(instance=patient)

    return render(request, 'staffpanel/patient_update.html', {
        'form': form,
        'patient': patient
    })


@login_required
def delete_patient(request, mr_no):
    patient = get_object_or_404(Patient, mr_no=mr_no)  
    patient.delete() 
    return redirect('staff:patient_list')  



@login_required
def book_appointment(request, patient_mr_no=None):
    doctors = Doctor.objects.all()
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
        except Patient.DoesNotExist:
            patient_not_found = True
            print(f"Patient with MR No {patient_mr_no} not found")

    if request.method == "POST":
        doctor_id = request.POST.get("doctor")
        selected_date = request.POST.get("appointment_date")

        if not doctor_id or not selected_date:
            messages.error(request, "Please select a doctor and date.")
            return render(request, "staffpanel/book_appointment.html", {
                "doctors": doctors,
                "error_message": "Please select a doctor and date.",
            })

        doctor = get_object_or_404(Doctor, id=doctor_id)

        try:
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect("staff:book_appointment")

        # ✅ Fix: pass weekday() as integer, not day string
        if doctor.is_off_day(selected_date_obj.weekday()):
            is_doctor_available = False
            messages.error(request, f"Dr. {doctor.name} is not available on {selected_date_obj.strftime('%A')}.")
            return render(request, "staffpanel/book_appointment.html", {
                "doctors": doctors,
                "doctor": doctor,
                "selected_date": selected_date_obj,
                "is_doctor_available": is_doctor_available,
                "available_slots": [],
                "patient": patient,
                "patient_not_found": patient_not_found,
                "register_url": reverse("staff:patient_registration"),
            })

        # Get available slots for the selected date
        available_slots = doctor.get_available_slots(selected_date_obj)
        is_doctor_available = bool(available_slots)

        if not available_slots:
            messages.error(request, "No available slots for this doctor on the selected day.")
            return render(request, "staffpanel/book_appointment.html", {
                "doctors": doctors,
                "doctor": doctor,
                "selected_date": selected_date_obj,
                "available_slots": [],
                "is_doctor_available": is_doctor_available,
                "patient": patient,
                "patient_not_found": patient_not_found,
                "register_url": reverse("staff:patient_registration"),
            })


        return render(request, "staffpanel/book_appointment.html", {
            "doctors": doctors,
            "doctor": doctor,
            "available_slots": available_slots,
            "selected_date": selected_date_obj,
            "patient": patient,
            "patient_not_found": patient_not_found,
            "register_url": reverse("staff:patient_registration"),
            "is_doctor_available": is_doctor_available,
        })


    return render(request, "staffpanel/book_appointment.html", {
        "doctors": doctors,
        "patient": patient,
        "patient_not_found": patient_not_found,
        "register_url": reverse("staff:patient_registration"),
    })


@login_required
def confirm_appointment(request):
    """Handles doctor appointment booking by hospital staff using patient phone number."""

    doctor_id = request.GET.get("doctor") or request.POST.get("doctor")
    selected_date = request.GET.get("date") or request.POST.get("appointment_date")
    patient_phone = request.GET.get("phone") or request.POST.get("phone")
    patient_id = request.GET.get("patient_id") or request.POST.get("patient_id")

    doctor = get_object_or_404(Doctor, id=doctor_id)

    # Ensure the date format is correct
    try:
        # selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
        selected_date_obj = datetime.strptime(selected_date, "%B %d, %Y").date()  

    except ValueError:
        messages.error(request, "Invalid date format.")
        return redirect("staff:book_appointment")

    # Fetch available slots
    available_slots = doctor.get_available_slots(selected_date_obj)

    if patient_id:
            try:
                patient = Patient.objects.get(id=patient_id)
            except Patient.DoesNotExist:
                messages.error(request, "Invalid patient selected.")
                return redirect("staff:book_appointment")
        
        # If no patient_id, search by phone number
    elif patient_phone:
            matching_patients = Patient.objects.filter(phone_number=patient_phone)

            if not matching_patients.exists():
                messages.error(request, "Patient not found. Please register the patient first.")
                register_url = reverse("staff:patient_registration")
                return render(request, "staffpanel/booking_confirm.html", {
                    "doctor": doctor,
                    "available_slots": available_slots,
                    "selected_date": selected_date,
                    "patient": None,
                    "register_url": register_url,
                })

            # If multiple patients, ask for selection
            if matching_patients.count() > 1 and request.method != "POST":
                return render(request, "staffpanel/booking_patient_select.html", {
                    "patients": matching_patients,
                    "doctor": doctor,
                    "selected_date": selected_date,
                    "phone": patient_phone,
                })

            patient = matching_patients.first()

    else:
            messages.error(request, "No patient information provided.")
            return redirect("staff:book_appointment")

        





    # Fetch the patient by phone number
    # patient = Patient.objects.filter(phone_number=patient_phone).first()

    # if not patient:
    #     messages.error(request, "Patient not found. Please register the patient first.")
    #     register_url = reverse("staff:patient_registration")
    #     return render(request, "staffpanel/booking_confirm.html", {
    #         "doctor": doctor,
    #         "available_slots": available_slots,
    #         "selected_date": selected_date,
    #         "patient": None,
    #         "register_url": register_url,
    #     })

    if request.method == "POST":
        post_data = request.POST.copy()
        post_data["booking_date"] = selected_date_obj  # Add booking date to form data
        post_data["patient"] = patient.id  # Add the patient ID to the form data explicitly

        form = DoctorBookingForm(post_data, doctor=doctor)

        # Check if a slot was selected
        selected_slot_id = request.POST.get("slot_time")
        if not selected_slot_id:
            messages.error(request, "Please select a valid time slot.")
            return render(request, "staffpanel/booking_confirm.html", {
                "doctor": doctor,
                "available_slots": available_slots,
                "selected_date": selected_date,
                "form": form,
                "patient": patient,
            })

        # Validate the selected slot
        selected_slot = DoctorSlot.objects.filter(id=selected_slot_id, doctor=doctor).first()
        if not selected_slot:
            messages.error(request, "Invalid slot selection.")
            return render(request, "staffpanel/booking_confirm.html", {
                "doctor": doctor,
                "available_slots": available_slots,
                "selected_date": selected_date,
                "form": form,
                "patient": patient,
            })

        # If the form is valid, save the appointment
        if form.is_valid():
            booking = form.save(commit=False)
            booking.doctor = doctor
            booking.patient = patient
            booking.slot_time = selected_slot
            booking.booking_date = selected_date_obj
            booking.save()

            messages.success(request, "Appointment booked successfully!")
            return redirect("staff:appointment_summary", appointment_id=booking.id)
        else:
            messages.error(request, "Please correct the errors below.")
            print(f"Form Errors: {form.errors}")  # Debug form errors

    else:
        form = DoctorBookingForm(doctor=doctor)

    return render(request, "staffpanel/booking_confirm.html", {
        "doctor": doctor,
        "available_slots": available_slots,
        "selected_date": selected_date,
        "form": form,
        "patient": patient,
    })


@login_required
def booking_details(request, appointment_id):
    appointment = get_object_or_404(DoctorBooking, id=appointment_id)
    return render(request, 'staffpanel/booking_details.html', {'appointment': appointment})

@login_required
def booking_update(request, appointment_id):
    # Fetch the appointment object by ID
    appointment = get_object_or_404(DoctorBooking, id=appointment_id)
    selected_date = appointment.booking_date


    # Fetch the doctor and patient for display in the form
    doctor = appointment.doctor
    patient = appointment.patient


    # Format selected date to match the format used in the is_off_day method
    selected_date_obj = selected_date

    # Check if doctor is available on the selected date (off days)
    is_doctor_available = True
    if doctor.is_off_day(selected_date_obj.strftime("%a")):  # Check availability by day abbreviation (e.g., 'Mon', 'Tue')
        is_doctor_available = False
        messages.error(request, f"Dr. {doctor.name} is not available on {selected_date_obj.strftime('%A')}.")
        
        return render(request, "staffpanel/book_appointment.html", {
            "doctors": Doctor.objects.all(),  # Pass all doctors for context
            "error_message": f"Dr. {doctor.name} is not available on {selected_date_obj.strftime('%A')}.",
            "is_doctor_available": is_doctor_available,
        })

    # Get available slots for the selected date, excluding the current slot
    available_slots = doctor.get_available_slots(selected_date)
    

    # Remove the selected slot from the available slots (if it exists)
    available_slots = [slot for slot in available_slots if slot != appointment.slot_time]
    

    # Handle form submission
    if request.method == 'POST':
        # Add doctor and patient to POST data explicitly if missing
        
        if 'doctor' not in request.POST:
            request.POST._mutable = True
            request.POST['doctor'] = doctor.id  # Set doctor ID manually if not provided
            
        
        if 'patient' not in request.POST:
            request.POST._mutable = True
            request.POST['patient'] = patient.id  # Set patient ID manually if not provided
            

        # Now pass the modified POST data to the form
        form = AppointmentForm(request.POST, doctor=doctor, instance=appointment)
        
        if form.is_valid():
            
            form.save()
            
            return redirect('staff:appointment_list')  # Redirect after saving
        
        
    else:

        form = AppointmentForm(instance=appointment)

    # Render the update appointment page
    return render(request, 'staffpanel/booking_update.html', {
        'form': form,
        'appointment': appointment,
        'patient': patient,  # Pass patient object for display
        'doctor': doctor,    # Pass doctor object for display
        'available_slots': available_slots,
        'formatted_date': selected_date.strftime('%Y-%m-%d'),  # Format date to 'YYYY-MM-DD'
        'is_doctor_available': is_doctor_available,  # Pass the availability status
    })


@login_required
def booking_delete(request, appointment_id):
    appointment = get_object_or_404(DoctorBooking, id=appointment_id)
    if request.method == "POST":
        appointment.delete()
        return redirect('staff:appointment_list')
    return render(request, 'staffpanel/booking_delete.html', {'appointment': appointment})

@login_required
def print_appointment(request, appointment_id):
    """Displays the appointment summary for printing."""
    appointment = get_object_or_404(DoctorBooking, id=appointment_id)
    return render(request, 'staffpanel/appointment_summary.html', {'appointment': appointment})

@login_required
def appointment_list(request):
    """Displays all booked appointments."""
    appointments = DoctorBooking.objects.all()
    return render(request, 'staffpanel/appointment_list.html', {'appointments': appointments})
