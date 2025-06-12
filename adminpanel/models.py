from django.db import models
from datetime import datetime, timedelta
from django.forms import ValidationError
from django.utils import timezone
from django.contrib.auth.models import Group, User
from phonenumber_field.modelfields import PhoneNumberField





class StaffDepartment(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Staff(models.Model):
    erp_id = models.CharField(max_length=10, unique=True, blank=True, null=True)  # Custom ERP ID format
    name = models.CharField(max_length=100)
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True) 
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    department = models.ForeignKey(StaffDepartment, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='staff_images/', null=True, blank=True)

    def delete(self, *args, **kwargs):
        # Delete the associated user first
        if self.user:
            self.user.delete()
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self._state.adding:

            group, created = Group.objects.get_or_create(name="Staff")
            self.user.groups.add(group)

            if not self.erp_id:
                last_erp_id = Staff.objects.all().order_by('erp_id').last()
                if last_erp_id:
                    last_number = int(last_erp_id.erp_id[1:])  # Extract number after 'S'
                    new_erp_id = f"S{last_number + 1}"
                else:
                    new_erp_id = "S1000"  # Start from S1000 if no records exist
                self.erp_id = new_erp_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.erp_id})"

class DoctorDepartment(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class DoctorSlot(models.Model):
    id = models.IntegerField(primary_key=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    booked = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
       if self._state.adding and not self.end_time:
            start_dt = datetime.combine(datetime.today(), self.start_time)
            self.end_time = (start_dt + timedelta(minutes=15)).time()  # Default to 15 minutes after start time

    
       super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
    
class Doctor(models.Model):
    DAY_CHOICES = [
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ]

    id = models.AutoField(primary_key=True)
    erp_id = models.CharField(max_length=10, unique=True, blank=True, null=True)
    name = models.CharField(max_length=100)
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    specialist_department = models.ForeignKey(DoctorDepartment, on_delete=models.CASCADE)
    medical_id = models.CharField(max_length=50, unique=True)
    consulting_hours_start = models.TimeField()
    consulting_hours_end = models.TimeField(blank=True, null=True)
    slots = models.ManyToManyField(DoctorSlot, blank=True)
    profile_picture = models.ImageField(upload_to='doctor_images/', null=True, blank=True)
    off_days = models.CharField(max_length=20, blank=True, null=True)  # stored as "6,7"

    def __str__(self):
        return f"Dr. {self.name} ({self.medical_id}) ({self.erp_id})"

    def delete(self, *args, **kwargs):
        if self.user:
            self.user.delete()
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        from .models import DoctorSlot
        creating = self._state.adding

        if creating:
            if not self.erp_id:
                last = Doctor.objects.order_by('erp_id').last()
                if last and last.erp_id:
                    last_number = int(last.erp_id[1:])
                    self.erp_id = f"D{last_number + 1}"
                else:
                    self.erp_id = "D1000"

            if self.consulting_hours_start and not self.consulting_hours_end:
                dt = datetime.combine(datetime.today(), self.consulting_hours_start)
                dt_end = dt + timedelta(hours=8)
                self.consulting_hours_end = dt_end.time()

        super().save(*args, **kwargs)

        # Assign slots if newly created
        if creating:
            valid_slots = DoctorSlot.objects.filter(
                start_time__gte=self.consulting_hours_start,
                start_time__lt=self.consulting_hours_end
            )
            self.slots.set(valid_slots)

    def is_off_day(self, day):
        return str(day) in self.off_days.split(",") if self.off_days else False

    def get_available_slots(self, date):
        from .models import DoctorBooking

        if self.is_off_day(date.weekday()):  # weekday is 0-6
            return DoctorSlot.objects.none()

        booked_slot_ids = DoctorBooking.objects.filter(
            doctor=self, booking_date=date
        ).values_list("slot_time_id", flat=True)

        return self.slots.filter(
            start_time__gte=self.consulting_hours_start,
            start_time__lt=self.consulting_hours_end
        ).exclude(id__in=booked_slot_ids).order_by("start_time")





class Patient(models.Model):
    mr_no = models.CharField(max_length=12, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=150, default='First')
    last_name = models.CharField(max_length=150, default='Last')
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    date_of_birth = models.DateField()

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Transgender'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    address = models.TextField()
    previous_hospital_history = models.TextField(blank=True, null=True)
    medical_report_pdf = models.FileField(upload_to='patient_reports/', null=True, blank=True)
    profile_image = models.ImageField(upload_to='patient_images/', null=True, blank=True)

    def delete(self, *args, **kwargs):
        # Delete the associated user first
        if self.user:
            self.user.delete()
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.mr_no:
            last_patient = Patient.objects.all().order_by('id').last()
            if last_patient and last_patient.mr_no and last_patient.mr_no[2:].isdigit():
                last_serial_number = int(last_patient.mr_no[2:])
                new_serial_number = last_serial_number + 1
            else:
                new_serial_number = 10000001
            self.mr_no = f"KL{new_serial_number}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.mr_no})"

    @property
    def age(self):
        today = timezone.now().date()
        age = today.year - self.date_of_birth.year
        if today.month < self.date_of_birth.month or (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1
        return age

 

class Appointment(models.Model):
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE)
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    appointment_date = models.DateField()
    slot_time = models.TimeField()
    # Add any other necessary fields

    def __str__(self):
        return f"Appointment for {self.patient} with Dr. {self.doctor} on {self.appointment_date}"
    


class DoctorBooking(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    booking_date = models.DateField()  # Store only the date
    slot_time = models.ForeignKey(DoctorSlot, on_delete=models.CASCADE)  # Store only time from DoctorSlot


    def save(self, *args, **kwargs):


        if not isinstance(self.slot_time, DoctorSlot):
            raise ValidationError("Invalid slot selection. Must be a valid DoctorSlot.")
        

        if DoctorBooking.objects.filter(doctor=self.doctor, booking_date=self.booking_date, slot_time=self.slot_time).exists():
            raise ValidationError("This time slot is already taken.")

 
        booking_day = self.booking_date.weekday() 
        booking_day = int(booking_day)  # Python weekday() is 0-6, 
        if booking_day == 0:
            booking_day = 7

        off_days = [int(d) for d in self.doctor.off_days.split(",") if d.strip().isdigit()] if self.doctor.off_days else []
        if booking_day in off_days:
            raise ValidationError(f"Cannot book appointment on {self.booking_date}, as it is an off day for Dr. {self.doctor.name}.")
     
        super().save(*args, **kwargs)

    def __str__(self):        
        return f"Booking: {self.patient.first_name} {self.patient.last_name} for Dr. {self.doctor.name} on {self.booking_date} at {self.slot_time.start_time}"

    class Meta:
        unique_together = ('doctor', 'booking_date', 'slot_time')  # Ensure no duplicate bookings


class PatientVisit(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    visit_date = models.DateTimeField(default=timezone.now)
    symptoms = models.TextField(blank=True, null=True)
    prescribed_medicines = models.TextField(blank=True, null=True)
    lab_tests = models.TextField(blank=True, null=True)
    scanning_pdf = models.FileField(upload_to='patient_reports/', null=True, blank=True)
    scanning_results = models.TextField(blank=True, null=True)
    next_visit_date = models.DateTimeField(blank=True, null=True)
    visit_completed = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_visits')
    created_at = models.DateTimeField(auto_now_add=True)
    booking = models.OneToOneField(DoctorBooking, on_delete=models.CASCADE, null=True, blank=True)




    def __str__(self):
        return f"Visit for {self.patient.first_name} {self.patient.last_name} with Dr. {self.doctor.name if self.doctor else 'N/A'} on {self.visit_date.strftime('%Y-%m-%d %H:%M') if self.visit_date else 'N/A'} (Entered by {self.created_by.username if self.created_by else 'Unknown'})"

    class Meta:
        ordering = ['-visit_date']  # Order by most recent visit first




class Vacancy(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    department = models.CharField(max_length=100)
    qualifications = models.TextField()
    experience = models.CharField(max_length=100, blank=True, null=True)
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    application_deadline = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.application_deadline < timezone.now().date():
            raise ValidationError("Application deadline cannot be in the past.")
        super().save(*args, **kwargs)


    def __str__(self):
        return self.title

class Application(models.Model):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE)
    applicant_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    cv = models.FileField(upload_to='applications/cvs/')
    applied_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"Application for {self.vacancy.title} by {self.applicant_name}"

class News(models.Model):
    heading = models.CharField(max_length=200)
    description = models.TextField()
    photo = models.ImageField(upload_to='news_photos/')
    created_at = models.DateField() 
    created_by = models.CharField(max_length=100)
    Creater_photo = models.ImageField(upload_to='news_creators_photos/', null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.heading