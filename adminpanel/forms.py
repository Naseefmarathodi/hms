from django import forms
from .models import *
from django.core.exceptions import ValidationError
from django.db.models import UniqueConstraint
from django.contrib.auth.models import Group


class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['erp_id', 'name', 'email', 'phone_number', 'department', 'profile_picture']
        widgets = {
            'erp_id': forms.TextInput(attrs={'readonly': 'readonly'}),  # Prevent manual entry of erp_id
            'name': forms.TextInput(attrs={'placeholder': 'Enter staff name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter email address'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Enter phone number'}),
            
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and len(phone_number) < 10:
            raise forms.ValidationError("Phone number must be at least 10 digits long.")
        return phone_number

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # If a password is provided, update the user's password
        if not instance.erp_id:
            last = Staff.objects.order_by('erp_id').last()
            if last and last.erp_id:
                last_num = int(last.erp_id[1:])
                instance.erp_id = f"S{last_num + 1}"
            else:
                instance.erp_id = "S1000"

        # Add selected user to Staff group
        if instance.user:
            group, _ = Group.objects.get_or_create(name="Staff")
            instance.user.groups.add(group)

            # Optionally update password
            password = self.cleaned_data.get('password')
            if password:
                instance.user.set_password(password)
                instance.user.save()

        if commit:      
            instance.save()
        return instance

class StaffCredentialUpdateForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New Password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'password']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
        }

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 6:
            raise forms.ValidationError("Password must be at least 6 characters.")
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            user.set_password(password)

        if commit:
            user.save()
        return user

class StaffDepartmentForm(forms.ModelForm):
    class Meta:
        model = StaffDepartment
        fields = ['name']



class DoctorForm(forms.ModelForm):
   
    user = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        required=True
    )
    consulting_hours_start = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    off_days = forms.MultipleChoiceField(
        choices=Doctor.DAY_CHOICES,  
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )
    class Meta:
        model = Doctor
        fields = [
            'name', 'email', 'phone_number', 'specialist_department', 'medical_id',
            'consulting_hours_start','profile_picture', 'off_days',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'specialist_department': forms.Select(attrs={'class': 'form-control'}),
            'medical_id': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert comma-separated string to list of integers for initial values
        if self.instance and self.instance.off_days:
            self.initial['off_days'] = list(map(int, self.instance.off_days.split(',')))

    def clean_user(self):
        username = self.cleaned_data['user']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username



    def save(self, commit=True):
        doctor = super().save(commit=False)

        # Create user
        username = self.cleaned_data['user']
        password = self.cleaned_data['password']
        user = User.objects.create_user(username=username, password=password)
        user.save()

        # Assign to "Doctor" group
        group, _ = Group.objects.get_or_create(name='Doctor')
        user.groups.add(group)

        doctor.user = user

        # Convert list of selected off days into comma-separated string
        off_days_list = self.cleaned_data.get('off_days', [])
        # doctor.off_days = ",".join(off_days_list)
        doctor.off_days = ",".join(str(day) for day in off_days_list)


        if commit:
            doctor.save()
            self.save_m2m()

        return doctor

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     if self.instance and self.instance.off_days:
    #         self.initial['off_days'] = self.instance.off_days.split(',')



class DoctorUpdateForm(forms.ModelForm):
    off_days = forms.MultipleChoiceField(
        choices=Doctor.DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Doctor
        fields = [
            'name', 'email', 'phone_number', 'specialist_department', 'medical_id',
            'consulting_hours_start', 'consulting_hours_end', 'profile_picture', 'off_days'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If we are editing an instance, convert off_days string to list for the form field
        if self.instance and self.instance.off_days:
            self.initial['off_days'] = self.instance.off_days.split(',')

    def clean_off_days(self):
        off_days_list = self.cleaned_data.get('off_days')
        # join list to comma-separated string to save to model
        return ",".join(off_days_list) if off_days_list else ""


class DoctorCredentialUpdateForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'})
    )

    class Meta:
        model = User
        fields = ['username', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 6:
            raise forms.ValidationError("Password must be at least 6 characters.")
        return password

class PatientForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Password'
        })
    )

    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control'
        })
    )

    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender',
            'phone_number', 'email', 'address', 'previous_hospital_history',
            'medical_report_pdf', 'profile_image'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'previous_hospital_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medical_report_pdf': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class PatientCredentialForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'})
    )

    class Meta:
        model = User
        fields = ['username', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 6:
            raise forms.ValidationError("Password must be at least 6 characters.")
        return password
    
# class PatientForm(forms.ModelForm):
#     user = forms.CharField(
#         max_length=150,
#         required=True,
#         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
#     )
#     password = forms.CharField(
#         widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
#         required=True
#     )
#     date_of_birth = forms.DateField(
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
#     )

#     class Meta:
#         model = Patient
#         fields = [
#             'first_name', 'last_name', 'date_of_birth', 'gender', 
#             'phone_number', 'email', 'address', 'previous_hospital_history', 
#             'medical_report_pdf', 'profile_image',
#         ]
#         widgets = {
#             'first_name': forms.TextInput(attrs={'class': 'form-control'}),
#             'last_name': forms.TextInput(attrs={'class': 'form-control'}),
#             'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#             'gender': forms.Select(attrs={'class': 'form-control'}),
#             'email': forms.EmailInput(attrs={'class': 'form-control'}),
#             'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
#             'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'previous_hospital_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'medical_report_pdf': forms.ClearableFileInput(attrs={'class': 'form-control'}),
#             'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
#         }

#     def clean_user(self):
#         username = self.cleaned_data['user']
#         if User.objects.filter(username=username).exists():
#             raise forms.ValidationError("Username already exists.")
#         return username

#     def save(self, commit=True):
#         Patient = super().save(commit=False)

#         # # Create user
#         # username = self.cleaned_data['user']
#         # password = self.cleaned_data['password']
#         # user = User.objects.create_user(username=username, password=password)
#         # user.save()

#         # Assign to "Patient" group
#         if Patient.user:
#             group, _ = Group.objects.get_or_create(name='Patient')
#             Patient.user.groups.add(group)

#         # Link user to patient
#         # Patient.user = user

#         # optionally update password
#         if self.cleaned_data.get('password'):
#             user = Patient.user
#             if user:
#                 user.set_password(self.cleaned_data['password'])
#                 user.save()

#         if commit:
#             Patient.save()

#         return Patient

class PatientUpdateForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 
            'phone_number', 'email', 'address', 'previous_hospital_history', 
            'medical_report_pdf', 'profile_image'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'previous_hospital_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medical_report_pdf': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }



VISIT_STATUS_CHOICES = (
    (True, 'Completed'),
    (False, 'Still Pending'),
)


class PatientVisitForm(forms.ModelForm):
    visit_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )
    scanning_pdf = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    next_visit_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    visit_completed = forms.ChoiceField(
        choices=[(False, 'Still Pending'), (True, 'Completed')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = PatientVisit
        exclude = ['patient', 'doctor', 'created_by', 'created_at','booking']  # Ensure 'patient' is excluded


# class PatientVisitForm(forms.ModelForm):
#     visit_date = forms.DateTimeField(
#         widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
#     )
#     scanning_pdf = forms.FileField(
#         required=False,
#         widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
#     )
#     next_visit_date = forms.DateField(
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
#     )
#     visit_completed = forms.BooleanField(
#         required=False,
#         widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
#     )
#     patient = forms.ModelChoiceField(
#         queryset=Patient.objects.none(),  # Set empty queryset initially
#         required=True,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )

#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)  # Get the logged-in user
#         super().__init__(*args, **kwargs)

#         # Restrict patients based on the logged-in user (if needed)
#         if self.user and not self.user.is_superuser:  # Allow all patients for superusers
#             self.fields['patient'].queryset = Patient.objects.filter(assigned_doctor=self.user.doctor)
#         else:
#             self.fields['patient'].queryset = Patient.objects.all()

#     class Meta:
#         model = PatientVisit
#         fields = [
#             'patient', 'visit_date', 'symptoms', 'prescribed_medicines',
#             'lab_tests', 'scanning_pdf', 'scanning_results', 'next_visit_date', 'visit_completed'
#         ]



class DoctorBookingForm(forms.ModelForm):
    class Meta:
        model = DoctorBooking
        fields = ['patient', 'doctor', 'booking_date', 'slot_time']


    def __init__(self, *args, **kwargs):
        self.doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        if self.doctor:
            self.fields['slot_time'].queryset = DoctorSlot.objects.filter(doctor=self.doctor)
        else:
            self.fields['slot_time'].queryset = DoctorSlot.objects.none()

        self.fields['patient'].required = True
        self.fields['doctor'].required = True
        self.fields['booking_date'].required = True
        self.fields['slot_time'].required = True



    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get("booking_date")
        slot_time = cleaned_data.get("slot_time")

        if not booking_date:
            raise forms.ValidationError("Booking date is required.")

        if not self.doctor:
            raise forms.ValidationError("Doctor is required for booking.")

        if not slot_time:
            raise forms.ValidationError("Slot time is required.")

        if DoctorBooking.objects.filter(doctor=self.doctor, booking_date=booking_date, slot_time=slot_time).exists():
            raise forms.ValidationError("This time slot is already taken.")

        # booking_day = booking_date.strftime('%a')
        booking_day = str(booking_date.weekday())


        if self.doctor.is_off_day(booking_day):
            raise forms.ValidationError(f"Cannot book appointment on {booking_day}, as it is an off day for Dr. {self.doctor.name}.")

        return cleaned_data






class AppointmentForm(forms.ModelForm):
    class Meta:
        model = DoctorBooking
        fields = ['doctor', 'patient', 'booking_date', 'slot_time']
        widgets = {
            'booking_date': forms.DateInput(attrs={'type': 'date'}),
            'slot_time': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        if self.doctor:
            self.fields['slot_time'].queryset = DoctorSlot.objects.filter(doctor=self.doctor)
        else:
            self.fields['slot_time'].queryset = DoctorSlot.objects.none()

        self.fields['patient'].required = True
        self.fields['doctor'].required = True
        self.fields['booking_date'].required = True
        self.fields['slot_time'].required = True

    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get("booking_date")
        slot_time = cleaned_data.get("slot_time")

        if not booking_date:
            raise forms.ValidationError("Booking date is required.")

        if not self.doctor:
            raise forms.ValidationError("Doctor is required for booking.")

        if not slot_time:
            raise forms.ValidationError("Slot time is required.")

        if DoctorBooking.objects.filter(doctor=self.doctor, booking_date=booking_date, slot_time=slot_time).exists():
            raise forms.ValidationError("This time slot is already taken.")

        booking_day = booking_date.strftime('%a')
        if self.doctor.is_off_day(booking_day):
            raise forms.ValidationError(f"Cannot book appointment on {booking_day}, as it is an off day for Dr. {self.doctor.name}.")

        return cleaned_data




class DoctorDepartmentForm(forms.ModelForm):
    class Meta:
        model = DoctorDepartment
        fields = ['name']

class VacancyForm(forms.ModelForm):
    class Meta:
        model = Vacancy
        fields = [
            'title', 'description', 'department', 'qualifications',
            'experience', 'salary_range', 'application_deadline', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'qualifications': forms.Textarea(attrs={'rows': 3}),
            'application_deadline': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_application_deadline(self):
        deadline = self.cleaned_data['application_deadline']
        if deadline < timezone.now().date():
            raise ValidationError("Deadline cannot be in the past.")
        return deadline
    

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['vacancy', 'applicant_name', 'phone_number', 'email', 'cv']
        widgets = {
            'cv': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class DoctorDepartmentForm(forms.ModelForm):
    class Meta:
        model = DoctorDepartment
        fields = ['name']

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['applicant_name', 'phone_number', 'email', 'cv']
        widgets = {
            'cv': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class news_form(forms.ModelForm):
    class Meta:
        model = News
        fields = ['heading', 'description', 'photo', 'created_at', 'created_by','Creater_photo', 'designation']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }