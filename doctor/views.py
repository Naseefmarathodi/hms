from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib import messages
from django.http import HttpResponseForbidden
from adminpanel.models import Doctor, Patient, Appointment, DoctorBooking
from adminpanel.models import *
from adminpanel.forms import DoctorForm, PatientForm, AppointmentForm, DoctorBookingForm
from adminpanel.forms import *
from datetime import date

def doctor_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None and user.groups.filter(name="Doctor").exists():
            login(request, user)
            return redirect('doctor:doctor_dashboard')
        else:
            messages.error(request, "Invalid credentials or not authorized.")
            return redirect('doctor:doctorhome')
    return render(request, 'doctor/doctorhome.html')

@login_required
def doctor_dashboard(request):
    if request.user.groups.filter(name="Doctor").exists():
        return render(request, 'doctor/doctorloginhome.html')
    else:
        return HttpResponseForbidden("Access Denied")
    

def doctor_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('doctor:doctorhome')


@login_required
def doctor_bookings(request):
    if request.user.groups.filter(name="Doctor").exists():
        doctor = Doctor.objects.get(user=request.user)
        bookings = DoctorBooking.objects.filter(
            doctor=doctor
        ).select_related('slot_time', 'patient').order_by('booking_date', 'slot_time__start_time')

        # Calculate age for each booking
        for booking in bookings:
            dob = booking.patient.date_of_birth
            today = date.today()
            booking.patient_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        return render(request, 'doctor/booking_list.html', {'bookings': bookings})

    return redirect('doctor:doctor_login')


@login_required
def add_or_edit_visit(request, booking_id):
    booking = get_object_or_404(DoctorBooking, id=booking_id)

    if booking.doctor.user != request.user:
        return render(request, 'doctor/error.html', {'message': 'Unauthorized access to booking.'})

    patient = booking.patient
    doctor = booking.doctor

    visit = PatientVisit.objects.filter(
        patient=patient, doctor=doctor, visit_date__date=booking.booking_date
    ).first()

    if request.method == 'POST':
        form = PatientVisitForm(request.POST, request.FILES, instance=visit)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.patient = patient
            visit.doctor = doctor
            visit.created_by = request.user
            visit.save()

            if visit.visit_completed in ['True', True, '1']:  # Handle string from ChoiceField
                booking.delete()

            return redirect('doctor:doctor_bookings')
    else:
        form = PatientVisitForm(instance=visit)

    return render(request, 'doctor/visit_form.html', {
        'form': form,
        'patient': patient,
        'booking': booking,
    })


@login_required
def search_patient_for_visit(request):
    patient = None
    booking = None
    visit = None
    form = None
    phone_query = request.GET.get('phone')

    if phone_query:
        try:
            patient = Patient.objects.get(phone_number=phone_query)
            booking = DoctorBooking.objects.filter(patient=patient, doctor__user=request.user).order_by('-booking_date').first()

            if not booking:
                return render(request, 'doctor/error.html', {'message': 'No booking found for this patient.'})

            visit = PatientVisit.objects.filter(
                patient=patient,
                doctor=booking.doctor,
                visit_date__date=booking.booking_date
            ).first()

            if request.method == 'POST':
                form = PatientVisitForm(request.POST, request.FILES, instance=visit)
                if form.is_valid():
                    visit = form.save(commit=False)
                    visit.patient = patient
                    visit.doctor = booking.doctor
                    visit.created_by = request.user
                    visit.booking = booking  
                    visit.save()

                    if visit.visit_completed:
                        booking.delete()
                    return redirect('doctor:doctor_bookings')  # Adjust to your actual name
            else:
                form = PatientVisitForm(instance=visit)
        except Patient.DoesNotExist:
            return render(request, 'doctor/error.html', {'message': 'Patient with this phone number not found.'})

    return render(request, 'doctor/visit_search_form.html', {
        'form': form,
        'patient': patient,
        'phone_query': phone_query,
        'booking': booking,
        'visit': visit,
    })


@login_required
def completed_visits_view(request):
    phone = request.GET.get('phone')
    completed_visits = PatientVisit.objects.filter(visit_completed=True)
    if phone:
        completed_visits = completed_visits.filter(patient__phone_number=phone)

    return render(request, 'doctor/patient_visit_list.html', {
        'completed_visits': completed_visits,
        'phone': phone,
       
        })

@login_required
def view_completed_visit(request, visit_id):
    visit = get_object_or_404(PatientVisit, id=visit_id)
    if visit.visit_completed:
        return render(request, 'doctor/view_completed_visit.html', {'visit': visit})
    else:
        return render(request, 'doctor/error.html', {'message': 'This visit is not completed.'})
    

@login_required
def edit_completed_visit(request, visit_id):
    visit = get_object_or_404(PatientVisit, id=visit_id)

    if visit.created_by != request.user:
        return HttpResponseForbidden("You are not allowed to edit this visit.")

    if request.method == 'POST':
        form = PatientVisitForm(request.POST, request.FILES, instance=visit)
        if form.is_valid():
            form.save()
            messages.success(request, "Visit updated successfully.")
            return redirect('doctor:view_completed_visit', visit_id=visit.id)
    else:
        form = PatientVisitForm(instance=visit)

    return render(request, 'doctor/edit_visit.html', {'form': form, 'visit': visit})