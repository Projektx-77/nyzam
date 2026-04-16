from urllib import request
from django.shortcuts import render, get_object_or_404, redirect
from events.models import Event
from students.models import Student
from .models import Attendance
from django.contrib.auth.decorators import login_required

@login_required
def mark_attendance(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    students = Student.objects.all()

    if event.event_type == 'dorm_male':
        students = students.filter(dormitory='yes', gender='male')

    elif event.event_type == 'dorm_female':
        students = students.filter(dormitory='yes', gender='female')

    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            reason = request.POST.get(f'reason_{student.id}')

            Attendance.objects.update_or_create(
                student=student,
                event=event,
                defaults={
                    'status': status,
                    'reason': reason if status == 'absent' else '',
                    'marked_by': request.user
                }
            )
        # Redirect to the same attendance page because `event_list` URL is not defined.
        return redirect('mark_attendance', event_id=event.id)

    # return render  sul catyar htmly + urls oytyan
    #return render(request, 'attendance/test.html')

    return render(request, 'attendance/mark_attendance.html', {
        'event': event,
        'students': students
    })

