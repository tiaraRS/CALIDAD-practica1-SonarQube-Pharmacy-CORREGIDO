from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .decorators import *
from django.contrib.auth.decorators import login_required
from django.utils import timezone, dateformat
from django.core.exceptions import ValidationError
from datetime import datetime
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import datetime
import requests.exceptions
from django.views.decorators.http import require_http_methods

from .forms import *
from .models import *

@require_http_methods(["GET"])
def admin_dashboard(request):
    patients_total = Patients.objects.all().count()

    doctors = Doctor.objects.all().count()
    pharmacist = Pharmacist.objects.all().count()
    receptionist = PharmacyClerk.objects.all().count()
    out_of_stock = Stock.objects.filter(quantity__lte=0).count()
    total_stock = Stock.objects.all().count()

    today = datetime.today()
    for_today = Patients.objects.filter(
        date_admitted__year=today.year, date_admitted__month=today.month, date_admitted__day=today.day).count()
    print(for_today)
    exipred = Stock.objects.annotate(
        expired=ExpressionWrapper(Q(valid_to__lt=Now()),
                                  output_field=BooleanField())
    ).filter(expired=True).count()

    context = {
        "patients_total": patients_total,
        "expired_total": exipred,
        "out_of_stock": out_of_stock,
        "total_drugs": total_stock,
        "all_doctors": doctors,
        "all_pharmacists": pharmacist,
        "all_clerks": receptionist,
        "for_today": for_today

    }
    return render(request, 'hod_templates/admin_dashboard.html', context)

@require_http_methods(["GET"])
def create_patient_form(request):
    form = PatientForm()
    context = {
        "form": form,
        "title": "Add Patient"
    }
    return render(request, 'hod_templates/patient_form.html', context)

@require_http_methods(["POST"])
def create_patient(request):
    form = PatientForm()

    if request.method == "POST":
        form = PatientForm(request.POST, request.FILES)

        if form.is_valid():

            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            address = form.cleaned_data['address']
            phone_number = form.cleaned_data['phone_number']
            dob = form.cleaned_data['dob']
            gender = form.cleaned_data['gender']
            reg_no = form.cleaned_data['reg_no']

            user = CustomUser.objects.create_user(
                username=username, email=email, password=password, last_name=last_name, user_type=5)
            user.patients.address = address
            user.patients.phone_number = phone_number
            user.patients.dob = dob
            user.patients.reg_no = reg_no
            user.patients.first_name = first_name
            user.patients.last_name = last_name
            user.patients.gender = gender

            user.save()
            messages.success(request, username + ' was Successfully Added')

            return redirect('patient_form')

    context = {
        "form": form,
        "title": "Add Patient"
    }

    return render(request, 'hod_templates/patient_form.html', context)


@require_http_methods(["GET"])
def all_patients_form(request):
    form = PatientSearchForm1(request.POST or None)
    patients = Patients.objects.all()
    context = {
        "patients": patients,
        "form": form,
        "title": "Admitted Patients"
    }
    return render(request, 'hod_templates/admited_patients.html', context)

@require_http_methods(["POST"])
def all_patients(request):
    form = PatientSearchForm1(request.POST or None)
    patients = Patients.objects.all()
    context = {
        "patients": patients,
        "form": form,
        "title": "Admitted Patients"
    }
    if request.method == 'POST':
        name = request.POST.get('search')
        patients = Patients.objects.filter(first_name__icontains=name)

        context = {
            "patients": patients,
            form: form
        }
    return render(request, 'hod_templates/admited_patients.html', context)


@require_http_methods(["GET"])
def confirm_delete_form(request, pk):
    try:
        patient = Patients.objects.get(id=pk)
    except requests.exceptions.ConnectTimeout:
        messages.error(request, 'Timeout')
        return redirect('all_patients')
    except requests.exceptions.ConnectionError:
        messages.error(
            request, 'Connection Error, Patient Not Deleted')
        return redirect('all_patients')
    except requests.exceptions.HTTPError:
        messages.error(request, 'HTTP Error, Patient Not Deleted')
        return redirect('all_patients')
    except requests.exceptions.MissingSchema:
        messages.error(
            request, 'Service unavailable, Patient Not Deleted')
        return redirect('all_patients')

    context = {
        "patient": patient,

    }

    return render(request, 'hod_templates/sure_delete.html', context)

@require_http_methods(["POST"])
def confirm_delete(request, pk):
    try:
        patient = Patients.objects.get(id=pk)
        if request.method == 'POST':
            patient.delete()
            return redirect('all_patients')
    except requests.exceptions.ConnectTimeout:
        messages.error(request, 'Timeout')
        return redirect('all_patients')
    except requests.exceptions.ConnectionError:
        messages.error(
            request, 'Connection Error, Patient Not Deleted')
        return redirect('all_patients')
    except requests.exceptions.HTTPError:
        messages.error(request, 'HTTP Error, Patient Not Deleted')
        return redirect('all_patients')
    except requests.exceptions.MissingSchema:
        messages.error(
            request, 'Service unavailable, Patient Not Deleted')
        return redirect('all_patients')

@login_required
@require_http_methods(["POST"])
def create_pharmacist(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')

        user = CustomUser.objects.create_user(
            username=username, email=email, password=password, first_name=first_name, last_name=last_name, user_type=2)
        user.first_name = first_name
        user.last_name = last_name
        user.pharmacist.address = address
        user.pharmacist.mobile = mobile

        user.save()
        messages.success(request, "Staff Added Successfully!")
        return redirect('add_pharmacist')


@login_required
@require_http_methods(["GET"])
def create_pharmacist_form(request):
    context = {
        "title": "Add Pharmacist"

    }
    return render(request, 'hod_templates/pharmacist_form.html', context)

@require_http_methods(["GET"])
def manage_pharmacist(request):
    staffs = Pharmacist.objects.all()
    context = {
        "staffs": staffs,
        "title": "Manage Pharmacist"
    }

    return render(request, 'hod_templates/all_pharmacist.html', context)

@require_http_methods(["GET"])
def create_doctor_form(request):

    context = {
        "title": "Add Doctor"

    }

    return render(request, 'hod_templates/add_doctor.html', context)

@require_http_methods(["POST"])
def create_doctor(request):
    if request.method == "POST":

        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')

        try:
            user = CustomUser.objects.create_user(
                username=username, email=email, password=password, first_name=first_name, last_name=last_name, user_type=3)
            user.doctor.address = address
            user.doctor.mobile = mobile

            user.save()
            messages.success(request, "Staff Added Successfully!")
            return redirect('add_doctor')
        except requests.exceptions.ConnectTimeout:
            messages.error(request, 'Timeout')
            return redirect('add_doctor')
        except requests.exceptions.ConnectionError:
            messages.error(
                request, 'Connection Error,  Staff Not Added')
            return redirect('add_doctor')
        except requests.exceptions.HTTPError:
            messages.error(request, 'HTTP Error,  Staff Not Added')
            return redirect('add_doctor')
        except requests.exceptions.MissingSchema:
            messages.error(
                request, 'Service unavailable, Staff Not Added')
            return redirect('add_doctor')

@require_http_methods(["GET"])
def manage_doctor(request):
    staffs = Doctor.objects.all()

    context = {
        "staffs": staffs,
        "title": "Dotors Details"

    }

    return render(request, 'hod_templates/manage_doctor.html', context)

@require_http_methods(["GET"])
def create_pharmacy_clerk_form(request):
    
    context = {
        "title": "Add Pharmacy Clerk"

    }

    return render(request, 'hod_templates/add_pharmacyClerk.html', context)

@require_http_methods(["POST"])
def create_pharmacy_clerk(request):

    if request.method == "POST":

        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')

        try:
            user = CustomUser.objects.create_user(
                username=username, email=email, password=password, first_name=first_name, last_name=last_name, user_type=4)
            user.pharmacyclerk.address = address
            user.pharmacyclerk.mobile = mobile

            user.save()
            messages.success(request, "Staff Added Successfully!")
            return redirect('add_pharmacyClerk')
        except requests.exceptions.ConnectTimeout:
            messages.error(request, 'Timeout, Failed to Add Staff')
            return redirect('add_pharmacyClerk')
        except requests.exceptions.ConnectionError:
            messages.error(
                request, 'Connection Error, Failed to Add Staff')
            return redirect('add_pharmacyClerk')
        except requests.exceptions.HTTPError:
            messages.error(request, 'HTTP Error, Failed to Add Staff')
            return redirect('add_pharmacyClerk')
        except requests.exceptions.MissingSchema:
            messages.error(
                request, 'Service unavailable, Failed to Add Staff')
            return redirect('add_pharmacyClerk')

@require_http_methods(["GET"])
def manage_pharmacy_clerk(request):

    staffs = PharmacyClerk.objects.all()
    context = {
        "staffs": staffs,
        "title": "Manage PharmacyClerk"
    }

    return render(request, 'hod_templates/manage_pharmacyClerk.html', context)

@require_http_methods(["GET"])
def add_stock_form(request):
    form = StockForm(request.POST, request.FILES)
    context = {
        "form": form,
        "title": "Add New Drug"
    }
    return render(request, 'hod_templates/add_stock.html', context)


@require_http_methods(["POST"])
def add_stock(request):
    form = StockForm(request.POST, request.FILES)
    if form.is_valid():
        form = StockForm(request.POST, request.FILES)

        form.save()
        return redirect('add_stock')

    context = {
        "form": form,
        "title": "Add New Drug"
    }
    return render(request, 'hod_templates/add_stock.html', context)

@require_http_methods(["GET"])
def manage_stock(request):
    stocks = Stock.objects.all().order_by("-id")
    ex = Stock.objects.annotate(
        expired=ExpressionWrapper(
            Q(valid_to__lt=Now()), output_field=BooleanField())
    ).filter(expired=True)
    eo = Stock.objects.annotate(
        expired=ExpressionWrapper(
            Q(valid_to__lt=Now()), output_field=BooleanField())
    ).filter(expired=False)

    context = {
        "stocks": stocks,
        "expired": ex,
        "expa": eo,
        "title": "Manage Stocked Drugs"
    }

    return render(request, 'hod_templates/manage_stock.html', context)

@require_http_methods(["GET"])
def add_category_form(request):
    try:
        form = CategoryForm(request.POST or None)
    except requests.exceptions.ConnectTimeout:
        messages.error(request, 'Timeout, Failed to Add Category')
        return redirect('add_category')
    except requests.exceptions.ConnectionError:
        messages.error(
            request, 'Connection Error, Failed to Add Category')
        return redirect('add_category')
    except requests.exceptions.HTTPError:
        messages.error(request, 'HTTP Error, Failed to Add Category')
        return redirect('add_category')
    except requests.exceptions.MissingSchema:
        messages.error(
            request, 'Service unavailable, Failed to Add Category')
        return redirect('add_category')
    context = {
        "form": form,
        "title": "Add a New Drug Category"
    }
    return render(request, 'hod_templates/add_category.html', context)


@require_http_methods(["POST"])
def add_category(request):
    try:
        form = CategoryForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            form.save()
            messages.success(request, "Category added Successfully!")
            return redirect('add_category')
    except requests.exceptions.ConnectTimeout:
        messages.error(request, 'Timeout, Failed to Add Category')
        return redirect('add_category')
    except requests.exceptions.ConnectionError:
        messages.error(
            request, 'Connection Error, Failed to Add Category')
        return redirect('add_category')
    except requests.exceptions.HTTPError:
        messages.error(request, 'HTTP Error, Failed to Add Category')
        return redirect('add_category')
    except requests.exceptions.MissingSchema:
        messages.error(
            request, 'Service unavailable, Failed to Add Category')
        return redirect('add_category')


def add_prescription(request):
    form = PrescriptionForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('prescribe')

    context = {
        "form": form,
        "title": "Prescribe Drug"
    }
    return render(request, 'hod_templates/prescribe.html', context)


@require_http_methods(["GET"])
def edit_patient_form(request, patient_id):
    # adds patient id into session variable
    request.session['patient_id'] = patient_id

    patient = Patients.objects.get(admin=patient_id)

    form = EditPatientForm()

    # filling the form with data from the database
    form.fields['email'].initial = patient.admin.email
    form.fields['username'].initial = patient.admin.username
    form.fields['first_name'].initial = patient.first_name
    form.fields['last_name'].initial = patient.last_name
    form.fields['address'].initial = patient.address
    form.fields['gender'].initial = patient.gender
    form.fields['phone_number'].initial = patient.phone_number
    form.fields['dob'].initial = patient.dob
    
    context = {
        "id": patient_id,
        # "username": patient.admin.username,
        "form": form,
        "title": "Edit Patient"
    }
    return render(request, "hod_templates/edit_patient.html", context)


@require_http_methods(["POST"])
def edit_patient(request, patient_id):
    # adds patient id into session variable
    request.session['patient_id'] = patient_id

    patient = Patients.objects.get(admin=patient_id)

    form = EditPatientForm()

    # filling the form with data from the database
    form.fields['email'].initial = patient.admin.email
    form.fields['username'].initial = patient.admin.username
    form.fields['first_name'].initial = patient.first_name
    form.fields['last_name'].initial = patient.last_name
    form.fields['address'].initial = patient.address
    form.fields['gender'].initial = patient.gender
    form.fields['phone_number'].initial = patient.phone_number
    form.fields['dob'].initial = patient.dob
    if request.method == "POST":
        if patient_id == None:
            return redirect('all_patients')
        form = EditPatientForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            address = form.cleaned_data['address']
            gender = form.cleaned_data['gender']
            dob = form.cleaned_data['dob']
            phone_number = form.cleaned_data['phone_number']

            try:
                # First Update into Custom User Model
                user = CustomUser.objects.get(id=patient_id)
                user.username = username

                user.email = email
                user.save()

                # Then Update Students Table
                patients_edit = Patients.objects.get(admin=patient_id)
                patients_edit.address = address
                patients_edit.gender = gender
                patients_edit.dob = dob
                patients_edit.phone_number = phone_number
                patients_edit.first_name = first_name
                patients_edit.last_name = last_name

                patients_edit.save()
                messages.success(request, "Patient Updated Successfully!")
                return redirect('all_patients')
            except requests.exceptions.ConnectTimeout:
                messages.error(request, 'Timeout, Failed to Update Patient')
                return redirect('all_patients')
            except requests.exceptions.ConnectionError:
                messages.error(
                    request, 'Connection Error, Failed to Update Patient')
                return redirect('all_patients')
            except requests.exceptions.HTTPError:
                messages.error(request, 'HTTP Error, Failed to Update Patient')
                return redirect('all_patients')
            except requests.exceptions.MissingSchema:
                messages.error(
                    request, 'Service unavailable, Failed to Update Patient')
                return redirect('all_patients')

    context = {
        "id": patient_id,
        # "username": patient.admin.username,
        "form": form,
        "title": "Edit Patient"
    }
    return render(request, "hod_templates/edit_patient.html", context)


def patient_personal_records(request, pk):
    patient = Patients.objects.get(id=pk)
    prescrip = patient.prescription_set.all()
    stocks = patient.dispense_set.all()

    context = {
        "patient": patient,
        "prescription": prescrip,
        "stocks": stocks

    }
    return render(request, 'hod_templates/patient_personalRecords.html', context)


def delete_prescription(request, pk):
    prescribe = Prescription.objects.get(id=pk)
    if request.method == 'POST':
        prescribe.delete()
        return redirect('all_patients')

    context = {
        "patient": prescribe
    }

    return render(request, 'hod_templates/sure_delete.html', context)


def hod_profile(request):
    customuser = CustomUser.objects.get(id=request.user.id)
    staff = AdminHOD.objects.get(admin=customuser.id)

    form = HodForm()
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        address = request.POST.get('address')
        mobile = request.POST.get('mobile')

        customuser = CustomUser.objects.get(id=request.user.id)
        customuser.first_name = first_name
        customuser.last_name = last_name
        customuser.save()

        staff = AdminHOD.objects.get(admin=customuser.id)
        form = HodForm(request.POST, request.FILES, instance=staff)
        staff.address = address

        staff.mobile = mobile
        staff.save()

        if form.is_valid():
            form.save()

    context = {
        "form": form,
        "staff": staff,
        "user": customuser
    }

    return render(request, 'hod_templates/hod_profile.html', context)


@require_http_methods(["GET"])
def delete_doctor_form(request, pk):
    return render(request, 'hod_templates/sure_delete.html')

@require_http_methods(["POST"])
def delete_doctor(request, pk):
    try:
        doctor = Doctor.objects.get(id=pk)
        if request.method == 'POST':
            doctor.delete()
            messages.success(request, "Doctor  deleted successfully")

            return redirect('manage_doctor')

    except requests.exceptions.ConnectTimeout:
        messages.error(request, 'Timeout, Failed to Delete Doctor')
        return redirect('manage_doctor')
    except requests.exceptions.ConnectionError:
        messages.error(
            request, 'Connection Error, Failed to Delete Doctor')
        return redirect('manage_doctor')
    except requests.exceptions.HTTPError:
        messages.error(request, 'HTTP Error, Failed to Delete Doctor')
        return redirect('manage_doctor')
    except requests.exceptions.MissingSchema:
        messages.error(
            request, 'Service unavailable, Failed to Delete Doctor')
        return redirect('manage_doctor')

@require_http_methods(["GET"])
def delete_pharmacist_form(request, pk):
    return render(request, 'hod_templates/sure_delete.html')

@require_http_methods(["POST"])
def delete_pharmacist(request, pk):
    try:
        pharmacist = Pharmacist.objects.get(id=pk)
        if request.method == 'POST':
            pharmacist.delete()
            messages.success(request, "Pharmacist  deleted successfully")

            return redirect('manage_pharmacist')

    except requests.exceptions.ConnectTimeout:
        messages.error(request, 'Timeout, Failed to Delete Pharmacist')
        return redirect('manage_pharmacist')
    except requests.exceptions.ConnectionError:
        messages.error(
            request, 'Connection Error, Failed to Delete Pharmacist')
        return redirect('manage_pharmacist')
    except requests.exceptions.HTTPError:
        messages.error(request, 'HTTP Error, Failed to Delete Pharmacist')
        return redirect('manage_pharmacist')
    except requests.exceptions.MissingSchema:
        messages.error(
            request, 'Service unavailable, Failed to Delete Pharmacist')
        return redirect('manage_pharmacist')

@require_http_methods(["GET"])
def delete_pharmacy_clerk_form(request, pk):
    return render(request, 'hod_templates/sure_delete.html')

@require_http_methods(["POST"])
def delete_pharmacy_clerk(request, pk):
    try:
        clerk = PharmacyClerk.objects.get(id=pk)
        if request.method == 'POST':

            clerk.delete()
            messages.success(request, "Pharmacy Clerk  deleted   successfully")

            return redirect('manage_pharmacyClerk')

    except requests.exceptions.ConnectTimeout:
        messages.error(request, 'Timeout, Failed to Delete Pharmacy Clerk')
        return redirect('manage_pharmacyClerk')
    except requests.exceptions.ConnectionError:
        messages.error(
            request, 'Connection Error, Failed to Delete Pharmacy Clerk')
        return redirect('manage_pharmacyClerk')
    except requests.exceptions.HTTPError:
        messages.error(request, 'HTTP Error, Failed to Delete Pharmacy Clerk')
        return redirect('manage_pharmacyClerk')
    except requests.exceptions.MissingSchema:
        messages.error(
            request, 'Service unavailable, Failed to Delete Pharmacy Clerk')
        return redirect('manage_pharmacyClerk')

@require_http_methods(["GET"])
def edit_pharmacist_form(request, staff_id):
    staff = Pharmacist.objects.get(admin=staff_id)
    context = {
        "staff": staff,
        "id": staff_id,
        'title': "Edit Pharmacist "

    }
    return render(request, "hod_templates/edit_pharmacist.html", context)


@require_http_methods(["POST"])
def edit_pharmacist(request, staff_id):
    staff = Pharmacist.objects.get(admin=staff_id)
    if request.method == "POST":

        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')

        # INSERTING into Customuser Model
        user = CustomUser.objects.get(id=staff_id)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.username = username
        user.save()

        # INSERTING into Staff Model
        staff = Pharmacist.objects.get(admin=staff_id)
        staff.address = address
        staff.save()

        messages.success(request, "Staff Updated Successfully.")
        return redirect('manage_pharmacist')


@require_http_methods(["GET"])
def edit_doctor_form(request, doctor_id):
    staff = Doctor.objects.get(admin=doctor_id)
    context = {
        "staff": staff,
        "title": "Edit Doctor"
    }
    return render(request, "hod_templates/edit_doctor.html", context)


@require_http_methods(["POST"])
def edit_doctor(request, doctor_id):
    staff = Doctor.objects.get(admin=doctor_id)
    if request.method == "POST":

        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')

        # INSERTING into Customuser Model
        user = CustomUser.objects.get(id=doctor_id)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.username = username
        user.save()

        # INSERTING into Staff Model
        staff = Doctor.objects.get(admin=doctor_id)
        staff.address = address
        staff.save()

        messages.success(request, "Staff Updated Successfully.")

    context = {
        "staff": staff,
        "title": "Edit Doctor"
    }
    return render(request, "hod_templates/edit_doctor.html", context)

@require_http_methods(["GET"])
def edit_pharmacy_clerk_form(request, clerk_id):
    clerk = PharmacyClerk.objects.get(admin=clerk_id)
    
    context = {
        "staff": clerk,
        "title": "Edit PharmacyClerk"


    }
    return render(request, 'hod_templates/edit_clerk.html', context)


@require_http_methods(["POST"])
def edit_pharmacy_clerk(request, clerk_id):
    clerk = PharmacyClerk.objects.get(admin=clerk_id)
    if request.method == "POST":
        username = request.POST.get('username')
        last_name = request.POST.get('last_name')
        first_name = request.POST.get('first_name')
        address = request.POST.get('address')
        mobile = request.POST.get('mobile')
        gender = request.POST.get('gender')
        email = request.POST.get('email')

        try:
            user = CustomUser.objects.get(id=clerk_id)
            user.email = email
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            clerk = PharmacyClerk.objects.get(admin=clerk_id)
            clerk.address = address
            clerk.mobile = mobile
            clerk.gender = gender
            clerk.save()

            messages.success(request, 'Receptionist Updated Succefully')
        except requests.exceptions.ConnectTimeout:
            messages.error(request, 'Timeout, Failed to Update Receptionist')
            return redirect('manage_recpetionist')
        except requests.exceptions.ConnectionError:
            messages.error(
                request, 'Connection Error, Failed to Update Receptionist')
            return redirect('manage_recpetionist')
        except requests.exceptions.HTTPError:
            messages.error(
                request, 'HTTP Error, Failed to Update Receptionist')
            return redirect('manage_recpetionist')
        except requests.exceptions.MissingSchema:
            messages.error(
                request, 'Service unavailable, Failed to Update Receptionist')
            return redirect('manage_recpetionist')

    context = {
        "staff": clerk,
        "title": "Edit PharmacyClerk"


    }
    return render(request, 'hod_templates/edit_clerk.html', context)


@require_http_methods(["GET"])
def edit_admin_form(request):
    customuser = CustomUser.objects.get(id=request.user.id)
    staff = AdminHOD.objects.get(admin=customuser.id)
    form = HodForm()
    context = {
        "form": form,
        "staff": staff,
        "user": customuser
    }

    return render(request, 'hod_templates/edit-profile.html', context)


@require_http_methods(["POST"])
def edit_admin(request):
    customuser = CustomUser.objects.get(id=request.user.id)
    staff = AdminHOD.objects.get(admin=customuser.id)

    form = HodForm()
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        address = request.POST.get('address')
        mobile = request.POST.get('mobile')

        customuser = CustomUser.objects.get(id=request.user.id)
        customuser.first_name = first_name
        customuser.last_name = last_name
        customuser.save()

        staff = AdminHOD.objects.get(admin=customuser.id)
        form = HodForm(request.POST, request.FILES, instance=staff)
        staff.address = address

        staff.mobile = mobile
        staff.save()

        if form.is_valid():
            form.save()

    context = {
        "form": form,
        "staff": staff,
        "user": customuser
    }

    return render(request, 'hod_templates/edit-profile.html', context)



@require_http_methods(["GET"])
def edit_stock_form(request, pk):
    drugs = Stock.objects.get(id=pk)
    form = StockForm(request.POST or None, instance=drugs)

    context = {
        "drugs": drugs,
        "form": form,
        "title": "Edit Stock"

    }
    return render(request, 'hod_templates/edit_drug.html', context)


@require_http_methods(["POST"])
def edit_stock(request, pk):
    drugs = Stock.objects.get(id=pk)
    form = StockForm(request.POST or None, instance=drugs)

    if request.method == "POST" and form.is_valid():
        form = StockForm(request.POST or None, instance=drugs)
        category = request.POST.get('category')
        drug_name = request.POST.get('drug_name')
        quantity = request.POST.get('quantity')

        try:
            drugs = Stock.objects.get(id=pk)
            drugs.drug_name = drug_name
            drugs.quantity = quantity
            drugs.save()
            form.save()
            messages.success(request, 'Stock Updated Succefully')
        except requests.exceptions.ConnectTimeout:
            messages.error(request, 'Timeout, Failed to Update Stock')
            return redirect('manage_stock')
        except requests.exceptions.ConnectionError:
            messages.error(
                request, 'Connection Error, Failed to Update Stock')
            return redirect('manage_stock')
        except requests.exceptions.HTTPError:
            messages.error(request, 'HTTP Error, Failed to Update Stock')
            return redirect('manage_stock')
        except requests.exceptions.MissingSchema:
            messages.error(
                request, 'Service unavailable, Failed to Update Stock')
            return redirect('manage_stock')

    context = {
        "drugs": drugs,
        "form": form,
        "title": "Edit Stock"

    }
    return render(request, 'hod_templates/edit_drug.html', context)


@require_http_methods(["GET"])
def delete_drug_form(request, pk):
    return render(request, 'hod_templates/sure_delete.html')


@require_http_methods(["POST"])
def delete_drug(request, pk):
    try:

        drugs = Stock.objects.get(id=pk)
        if request.method == 'POST':

            drugs.delete()
            messages.success(request, "Pharmacist  deleted successfully")

            return redirect('manage_stock')

    except requests.exceptions.ConnectTimeout:
        messages.error(request, 'Timeout, Failed to Delete Stock')
        return redirect('manage_stock')
    except requests.exceptions.ConnectionError:
        messages.error(
            request, 'Connection Error, Failed to Delete Stock')
        return redirect('manage_stock')
    except requests.exceptions.HTTPError:
        messages.error(request, 'HTTP Error, Failed to Delete Stock')
        return redirect('manage_stock')
    except requests.exceptions.MissingSchema:
        messages.error(
            request, 'Service unavailable, Failed to Delete Stock')
        return redirect('manage_stock')


def receive_drug(request, pk):
    receive = Stock.objects.get(id=pk)
    form = ReceiveStockForm()
    try:
        form = ReceiveStockForm(request.POST or None)

        if form.is_valid():
            form = ReceiveStockForm(request.POST or None, instance=receive)

            instance = form.save(commit=False)
            instance.quantity += instance.receive_quantity
            instance.save()
            form = ReceiveStockForm()

            messages.success(request, str(instance.receive_quantity) +
                             " " + instance.drug_name + " " + "drugs added successfully")

            return redirect('manage_stock')

    except requests.exceptions.ConnectTimeout:
        messages.error(request, 'Timeout, Failed to Add Stock')
        return redirect('manage_stock')
    except requests.exceptions.ConnectionError:
        messages.error(
            request, 'Connection Error, Failed to Delete Stock')
        return redirect('manage_stock')
    except requests.exceptions.HTTPError:
        messages.error(request, 'HTTP Error, Failed to Delete Stock')
        return redirect('manage_stock')
    except requests.exceptions.MissingSchema:
        messages.error(
            request, 'Service unavailable, Failed to Delete Stock')
        return redirect('manage_stock')
    context = {
        "form": form,
        "title": "Add Drug"

    }
    return render(request, 'hod_templates/modal_form.html', context)


def reorder_level(request, pk):
    queryset = Stock.objects.get(id=pk)
    form = ReorderLevelForm(request.POST or None, instance=queryset)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.save()
        messages.success(request, "Reorder level for " + str(instance.drug_name) +
                         " is updated to " + str(instance.reorder_level))

        return redirect("manage_stock")
    context = {
        "instance": queryset,
        "form": form,
        "title": "Reorder Level"
    }

    return render(request, 'hod_templates/reorder_level.html', context)


def drug_details(request, pk):
    stocks = Stock.objects.get(id=pk)

    context = {
        "stocks": stocks,

    }
    return render(request, 'hod_templates/view_drug.html', context)
