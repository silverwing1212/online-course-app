from django.contrib import admin
## PROJECT CODE: Imported new models
from .models import Course, Lesson, Instructor, Learner, Question, Choice

## PROJECT CODE: Added Question and Choice Inline classes
class QuestionInline(admin.StackedInline):
    model = Question
    extra = 10

class ChoiceInline(admin.StackedInline):
    model = Choice



class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 5

# Register your models here.
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline, QuestionInline]
    list_display = ('name', 'pub_date')
    list_filter = ['pub_date']
    search_fields = ['name', 'description']



## PROJECT CODE: Added admin classes
class QuestionAdmin(admin.ModelAdmin):
    model = Question
    inlines = [ChoiceInline]
    list_display = ('question_text', 'grade')
    extra = 10

class ChoiceAdmin(admin.ModelAdmin):
    model = Choice
    list_display = ('choice_text', 'is_correct')





class LessonAdmin(admin.ModelAdmin):
    list_display = ['title']


## PROJECT CODE: Registered new models and admin classes
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)

admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor)
admin.site.register(Learner)
