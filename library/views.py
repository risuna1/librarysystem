from django.shortcuts import redirect, render,HttpResponse
from .models import *
from django.contrib.auth import authenticate, login, logout
from . import forms, models
from datetime import date
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail

def index(request):
    return render(request, "index.html")

@login_required(login_url = '/admin_login')
def add_book(request):
    if request.method == "POST":
        name = request.POST['name']
        author = request.POST['author']
        isbn = request.POST['isbn']
        category = request.POST['category']

        books = Book.objects.create(name=name, author=author, isbn=isbn, category=category)
        books.save()
        alert = True
        return render(request, "add_book.html", {'alert':alert})
    return render(request, "add_book.html")

@login_required(login_url = '/admin_login')
def view_books(request):
    books = Book.objects.all()
    return render(request, "view_books.html", {'books':books})

@login_required(login_url = '/admin_login')
def view_students(request):
    students = Student.objects.all()
    return render(request, "view_students.html", {'students':students})

@login_required(login_url = '/admin_login')
def issue_book(request):
    form = forms.IssueBookForm()
    if request.method == "POST":
        form = forms.IssueBookForm(request.POST)
        if form.is_valid():
            obj = models.IssuedBook()
            obj.student_id = request.POST['name2']
            obj.isbn = request.POST['isbn2']
            obj.save()
            alert = True
            return render(request, "issue_book.html", {'obj':obj, 'alert':alert})
    return render(request, "issue_book.html", {'form':form})

@login_required(login_url = '/admin_login')
def view_issued_book(request):
    issuedBooks = models.IssuedBook.objects.all()
    details = []
    for issued_book in issuedBooks:
        days = (date.today() - issued_book.issued_date).days
        fine = 0
        if days > 14:
            day = days - 14
            fine = day * 5
        books = list(models.Book.objects.filter(isbn=issued_book.isbn))
        students = list(models.Student.objects.filter(user=issued_book.student_id))
        if books and students: 
            book = books[0]
            student = students[0]
            t = (
                student.user, 
                student.user_id, 
                book.name, 
                book.isbn, 
                issued_book.issued_date, 
                issued_book.expiry_date, 
                fine, 
                issued_book.id
            )
            details.append(t)

    return render(request, "view_issued_book.html", {'issuedBooks': issuedBooks, 'details': details})

@login_required(login_url = '/student_login')
def student_issued_books(request):
    student = Student.objects.filter(user_id=request.user.id).first()  # Use .first() to avoid index errors
    if not student:
        return render(request, 'student_issued_books.html', {'li1': [], 'li2': []})  # Handle case where student is not found
    issuedBooks = IssuedBook.objects.filter(student_id=student.user_id)
    li = [] 
    for issued_book in issuedBooks:
        books = Book.objects.filter(isbn=issued_book.isbn)
        for book in books:
            days = (date.today() - issued_book.issued_date).days
            fine = 0
            if days > 15:
                fine = (days - 15) * 5
            t = {
                'user_id': request.user.id,
                'full_name': request.user.get_full_name(),
                'book_name': book.name,
                'book_author': book.author,
                'issued_date': issued_book.issued_date,
                'expiry_date': issued_book.expiry_date,
                'fine': fine,
            }
            li.append(t)

    return render(request, 'student_issued_books.html', {'issued_books': li})

@login_required(login_url = '/student_login')
def profile(request):
    return render(request, "profile.html")

@login_required(login_url = '/student_login')
def edit_profile(request):
    student = Student.objects.get(user=request.user)
    if request.method == "POST":
        email = request.POST['email']
        phone = request.POST['phone']
        branch = request.POST['branch']
        classroom = request.POST['classroom']
        roll_no = request.POST['roll_no']

        student.user.email = email
        student.phone = phone
        student.branch = branch
        student.classroom = classroom
        student.roll_no = roll_no
        student.user.save()
        student.save()
        alert = True
        return render(request, "edit_profile.html", {'alert':alert})
    return render(request, "edit_profile.html")

def delete_book(request, myid):
    books = Book.objects.filter(id=myid)
    books.delete()
    return redirect("/view_books")

def delete_student(request, myid):
    students = Student.objects.filter(id=myid)
    students.delete()
    return redirect("/view_students")

def delete_issue(request, myid):
    issued = IssuedBook.objects.filter(id=myid)
    print(myid)
    issued.delete()
    return redirect('/view_issued_book')

def change_password(request):
    if request.method == "POST":
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        try:
            u = User.objects.get(id=request.user.id)
            if u.check_password(current_password):
                u.set_password(new_password)
                u.save()
                alert = True
                return render(request, "change_password.html", {'alert':alert})
            else:
                currpasswrong = True
                return render(request, "change_password.html", {'currpasswrong':currpasswrong})
        except:
            pass
    return render(request, "change_password.html")

def student_registration(request):
    if request.method == "POST":
        username = request.POST['username']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        phone = request.POST['phone']
        branch = request.POST['branch']
        classroom = request.POST['classroom']
        roll_no = request.POST['roll_no']
        image = request.FILES['image']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            passnotmatch = True
            return render(request, "student_registration.html", {'passnotmatch':passnotmatch})

        user = User.objects.create_user(username=username, email=email, password=password,first_name=first_name, last_name=last_name)
        student = Student.objects.create(user=user, phone=phone, branch=branch, classroom=classroom,roll_no=roll_no, image=image)
        user.save()
        student.save()
        alert = True
        return render(request, "student_registration.html", {'alert':alert})
    return render(request, "student_registration.html")

def student_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            if request.user.is_superuser:
                return HttpResponse("You are not a student!!")
            else:
                return redirect("/profile")
        else:
            alert = True
            return render(request, "student_login.html", {'alert':alert})
    return render(request, "student_login.html")

def admin_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            if request.user.is_superuser:
                return redirect("/add_book")
            else:
                return HttpResponse("You are not an admin.")
        else:
            alert = True
            return render(request, "admin_login.html", {'alert':alert})
    return render(request, "admin_login.html")

def Logout(request):
    logout(request)
    return redirect ("/")

def contact(request):
    if request.method == 'POST':
        subject = request.POST.get('subject', 'No Subject') 
        message = request.POST.get('message', 'No Message')  
        sender_email = request.POST.get('email', 'no-reply@example.com')  

        send_mail(
            subject=subject,
            message=message,
            from_email=sender_email, 
            recipient_list=['dayuantailang1@gmail.com'],  
            fail_silently=False,
        )

        return redirect('contact_success')

    return render(request, 'contact.html')

def contact_success(request):
    return render(request, 'contact_success.html')