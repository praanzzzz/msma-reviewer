from django.urls import path
from appReviewer import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('my_login/', views.my_login, name='my_login'),
    path('my_logout/', views.my_logout, name='my_logout'),
    path('my_register/', views.my_register, name='my_register'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('profile/', views.profile, name='profile'),
    path('reviewer/', views.reviewer, name='reviewer'),


    # partial pages
    path('generate_questions/', views.generate_questions, name='generate_questions'),
    path('submit_quiz/', views.submit_quiz, name="submit_quiz"),
    path('fetchquizresult/<int:quiz_id>/', views.fetchquizresult, name='fetchquizresult'),
    path('fetch_subjects/<int:course_id>/', views.fetch_subjects, name="fetch_subjects"),
    path('view_feedback/', views.view_feedback, name="view_feedback"),
]

# it enables django to fetch static files during developmemt phase.
# on production phase, must use static and media file server (aws)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)