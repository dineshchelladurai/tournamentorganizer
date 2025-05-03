from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('post-invitation/', views.post_invitation, name='post_invitation'),
    path('view-invitations/', views.view_invitations, name='view_invitations'),
    path('logout/', views.logout_view, name='logout'),
    path('register-invitation/<int:invitation_id>/', views.register_invitation, name='register_invitation'),
    path('my-invitations/', views.my_invitations, name='my_invitations'),
    path('download-registrations/<int:invitation_id>/', views.download_registrations, name='download_registrations'),
    path('generate-fixtures/<int:invitation_id>/', views.generate_fixtures, name='generate_fixtures'),
    path('community/', views.community, name='community'),
    path('community/create/', views.create_post, name='create_post'),
    path('community/post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('community/post/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('manage-players/', views.manage_players, name='manage_players'),
    path('edit-player/<int:player_id>/', views.edit_player, name='edit_player'),
    path('delete-player/<int:player_id>/', views.delete_player, name='delete_player'),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)