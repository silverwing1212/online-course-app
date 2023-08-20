from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
# <HINT> Import any new Models here
from .models import Course, Enrollment, Question, Choice, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))



## PROJECT CODE (Uncommented from supplied code)
# Basically if a check box is marked, it will appear in POST
# If it is not marked, it will not appear in POST
def extract_answers(request):
    submitted_answers = []
    for key in request.POST:
        if key.startswith('choice'):
            value = request.POST[key]
            choice_id = int(value)
            submitted_answers.append(choice_id)
    return submitted_answers

## PROJECT CODE
# Submit View
# Creates an exam submission record and redirects to the exam results page
def submit(request, course_id):
    submitted_answers = extract_answers(request)
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    enrollment = Enrollment.objects.filter(user=user, course=course).first()
    submission = Submission(enrollment=enrollment)
    submission.save()
    for answer_id in submitted_answers:
        choice = Choice.objects.filter(pk = answer_id).first()
        submission.chocies.add(choice)
    ##return JsonResponse({ "message": "jj"})
    return HttpResponseRedirect(reverse(viewname='onlinecourse:show_exam_result', args=(course_id, submission.id)))
    

## PROJECT CODE
# Helper methods for compiling exam results

# Object for holding the result of a question from selected choices on an exam submission
class QuestionResult:
    def __init__(self, question_text, correct_answers, chosen_answers, points_earned, points_possible):
        self.question_text = question_text
        self.correct_answers = correct_answers
        self.chosen_answers = chosen_answers
        self.points_earned = points_earned
        self.points_possible = points_possible

# Compiles a map of questions associated to correct choices
def get_correct_answer_object(course):
    correct_answer_object = {}
    for question in course.question_set.all():
        correct_answers = []
        for choice in question.choice_set.all():
            if choice.is_correct:
                correct_answers.append(choice.id)
        correct_answer_object[question.id] = correct_answers
    return { question_id: sorted(correct_answers) for question_id, correct_answers in correct_answer_object.items() }

# Compiles a map of questions associated with choices the user has submitted
def get_chosen_answer_object(correct_answer_object, choice_list):
    chosen_answer_object = { question_id: list() for question_id, answers in correct_answer_object.items() }
    for choice in choice_list:
        choice_question_id = choice.question.id
        chosen_answers = chosen_answer_object[choice_question_id]
        chosen_answers.append(choice.id)
    return { question_id: sorted(chosen_answers) for question_id, chosen_answers in chosen_answer_object.items() }

# Evaluates the points earned for a given question
def get_points_earned(question, correct_answers, chosen_answers):
    if correct_answers == chosen_answers:
        return question.grade
    return 0

# Accesses the text of the choice from a given choice id
def get_choice_text(choice_id):
    return Choice.objects.filter(pk=choice_id).first().choice_text

# Compiles a list of results for each question
def get_question_results(course, choice_list):
    correct_answer_object = get_correct_answer_object(course)
    chosen_answer_object = get_chosen_answer_object(correct_answer_object, choice_list)  
    print(str(correct_answer_object))
    print(str(chosen_answer_object))
    question_results = []
    for question_id in correct_answer_object:
        question = Question.objects.filter(pk=question_id).first()
        question_text = question.question_text
        correct_answers = [get_choice_text(choice_id) for choice_id in correct_answer_object[question_id]]
        chosen_answers = [get_choice_text(choice_id) for choice_id in chosen_answer_object[question_id]]
        points_earned = get_points_earned(question, correct_answers, chosen_answers)
        points_possible = question.grade
        question_results.append(QuestionResult(question_text, correct_answers, chosen_answers, points_earned, points_possible))
    return question_results

# Compiles a grade from 0.0 - 1.0 (1.0 being the max score)
def get_grade(question_results):
    total_points_earned = 0.0
    total_points_possible = 0.000001
    for result in question_results:
        total_points_earned += result.points_earned
        total_points_possible += result.points_possible
    return total_points_earned / total_points_possible


## PROJECT CODE
# Compiles the results of each question
# Renders the exam results page with the results of each question
def show_exam_result(request, course_id, submission_id):
    # Set up relevant data
    course = Course.objects.filter(pk=course_id).first()
    submission = Submission.objects.filter(pk=submission_id).first()

    # Collect results
    question_results = get_question_results(course, submission.chocies.all())
    grade = get_grade(question_results)

    # Set up context
    context = {}
    context['course'] = course
    context['submission'] = submission
    context['question_results'] = question_results
    context['grade'] = int(grade * 100 + 0.001)
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)

