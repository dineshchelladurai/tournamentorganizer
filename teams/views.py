import random
import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models import User, Invitation, Registration, Post, Comment, Player
from django.contrib.auth import logout, login
from django.utils.timezone import now, timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

def home(request):
    context = {}
    if 'user_id' in request.session:
        user = User.objects.get(id=request.session['user_id'])
        context = {
            'user': user,
            'is_logged_in': True
        }
    else:
        context['is_logged_in'] = False
    return render(request, 'teams/home.html', context)

def signup(request):
    if request.method == 'POST':
        team_name = request.POST['team_name']
        email = request.POST['email']
        phone = request.POST['phone']
        password = request.POST['password']

        # Check if team_name or email already exists
        if User.objects.filter(team_name=team_name).exists():
            messages.error(request, "Team name already exists!")
            return redirect('signup')
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists!")
            return redirect('signup')

        if len(password) <= 8:
            messages.error(request, "password is too short")
            return redirect('signup')
        
        if not (any(c.isalpha() for c in password) and any(c.isdigit() for c in password)):
            messages.error(request, "Password should contain both letters and numbers")
            return redirect('signup')
        if not (any(c.isupper() for c in password)):
            messages.error(request, "should be upper case")
            return redirect('signup')

        # Create new user
        User.objects.create(
            team_name=team_name,
            email=email,
            phone=phone,
            password=password
        )
        messages.success(request, "Signup successful!")
        return redirect('login')
    return render(request, 'teams/signup.html')

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            user = User.objects.get(email=email)
            if check_password(password, user.password):
                request.session['user_id'] = user.id
                messages.success(request, "Login successful!")
                return redirect('home')
            else:
                messages.error(request, "Invalid password!")
        except User.DoesNotExist:
            messages.error(request, "Invalid email!")
        return redirect('login')
    return render(request, 'teams/login.html')

def post_invitation(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = User.objects.get(id=request.session['user_id'])
    
    if request.method == 'POST':
        venue = request.POST['venue']
        date = request.POST['date']
        price = request.POST['price']
        entry_fee = request.POST['entry_fee']
        phone = request.POST['phone']
        sport = request.POST['sport']  # Get sport from form
        team_limit = request.POST.get('team_limit')

        if team_limit == '':
            team_limit = None
        else:
            team_limit = int(team_limit)

        invitation_file = request.FILES.get('invitation_file')
        
        invitation = Invitation.objects.create(
            user=user,
            team_name=user.team_name,
            sport=sport,  # Save sport from form
            venue=venue,
            date=date,
            price=price,
            entry_fee = entry_fee,
            phone=phone,
            team_limit=team_limit
        )
        
        if invitation_file:
            invitation.invitation_file = invitation_file
            invitation.save()
            
        messages.success(request, "Invitation posted successfully!")
        return redirect('home')

    context = {
        'team_name': user.team_name,
        'phone': user.phone,
        'is_logged_in': True
    }
    return render(request, 'teams/post_invitation.html', context)

def view_invitations(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = User.objects.get(id=request.session['user_id'])
    
    # Get all invitations including host's invitations
    invitations = Invitation.objects.all().order_by('-id')  # Most recent first
    
    # Get list of invitations user has already registered for
    registered_invitations = Registration.objects.filter(
        team_name=user.team_name
    ).values_list('invitation_id', flat=True)
    
    context = {
        'invitations': invitations,
        'registered_invitations': list(registered_invitations),
        'is_logged_in': True,
        'user': user
    }
    return render(request, 'teams/view_invitations.html', context)

def register_invitation(request, invitation_id):
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = User.objects.get(id=request.session['user_id'])
    invitation = Invitation.objects.get(id=invitation_id)

    # Check if already registered
    if Registration.objects.filter(invitation=invitation, team_name=user.team_name).exists():
        messages.error(request, "You have already registered for this invitation!")
        return redirect('view_invitations')

    if request.method == 'POST':
        phone = request.POST.get('phone', user.phone)
        
        # Create registration
        Registration.objects.create(
            invitation=invitation,
            team_name=user.team_name,
            phone=phone
        )
        
        messages.success(request, "Registration successful!")
        return redirect('view_invitations')

    context = {
        'invitation': invitation,
        'team_name': user.team_name,
        'phone': user.phone,
        'is_logged_in': True
    }
    return render(request, 'teams/register_invitation.html', context)

def my_invitations(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = User.objects.get(id=request.session['user_id'])
    invitations = Invitation.objects.filter(user=user)
    
    context = {
        'invitations': invitations,
        'is_logged_in': True,
        'user': user
    }
    return render(request, 'teams/my_invitations.html', context)

def download_registrations(request, invitation_id):
    try:
        # Get registrations from database
        registrations = Registration.objects.filter(invitation_id=invitation_id).values(
            'team_name', 
            'phone', 
            'registration_date'
        )
        
        if not registrations:
            messages.warning(request, "No registrations found for this invitation.")
            return redirect('my_invitations')

        # Create DataFrame and export to Excel
        df = pd.DataFrame(list(registrations))
        # Format the date column
        df['registration_date'] = df['registration_date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename=registrations_{invitation_id}.xlsx'
        df.to_excel(response, index=False, columns=['team_name', 'phone', 'registration_date'])
        return response
        
    except Exception as e:
        messages.error(request, f"Error downloading registrations: {str(e)}")
        return redirect('my_invitations')

def generate_fixtures(request, invitation_id):
    if 'user_id' not in request.session:
        return redirect('login')
    
    invitation = Invitation.objects.get(id=invitation_id)
    registrations = Registration.objects.filter(invitation=invitation)
    
    if not invitation.is_registration_full():
        messages.error(request, "Registration is not full yet!")
        return redirect('my_invitations')
    
    # Get all registered teams
    teams = list(registrations.values_list('team_name', flat=True))
    
    # Shuffle teams randomly
    random.shuffle(teams)
    
    # Create fixtures
    fixtures = []
    total_teams = len(teams)
    
    for i in range(0, total_teams - 1, 2):
        team1 = teams[i]
        team2 = teams[i + 1] if i + 1 < total_teams else "BYE"
        match_no = (i // 2) + 1
        fixtures.append({
            'Match': f'Match {match_no}',
            'Team 1': team1,
            'Team 2': team2,
            'Venue': invitation.venue,
            'Date': invitation.date
        })
    
    # Create Excel file
    df = pd.DataFrame(fixtures)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename=fixtures_{invitation_id}.xlsx'
    df.to_excel(response, index=False)
    
    return response

def community(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    posts = Post.objects.all().order_by('-created_at')
    sport_filter = request.GET.get('sport', None)
    
    if sport_filter:
        posts = posts.filter(sport=sport_filter)
    
    context = {
        'posts': posts,
        'is_logged_in': True,
        'sport_choices': Invitation.SPORT_CHOICES
    }
    return render(request, 'teams/community.html', context)

def create_post(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = User.objects.get(id=request.session['user_id'])
    
    if request.method == 'POST':
        title = request.POST['title']
        content = request.POST['content']
        sport = request.POST['sport']
        
        Post.objects.create(
            user=user,
            title=title,
            content=content,
            sport=sport
        )
        messages.success(request, "Post created successfully!")
        return redirect('community')
    
    context = {
        'is_logged_in': True,
        'sport_choices': Invitation.SPORT_CHOICES
    }
    return render(request, 'teams/create_post.html', context)

def post_detail(request, post_id):
    # Check for authenticated user
    if 'user_id' not in request.session:
        return redirect('login')
    
    post = get_object_or_404(Post, id=post_id)
    user = User.objects.get(id=request.session['user_id'])
    
    # Handle comment submission
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            # Create new comment
            comment = Comment.objects.create(
                post=post,
                user=user,
                content=content,
                file=request.FILES.get('file') if request.FILES else None
            )
            messages.success(request, 'Comment added successfully!')
        return redirect('post_detail', post_id=post_id)
    
    # For GET requests, display post and comments
    comments = post.comments.filter(parent=None).order_by('-created_at')
    context = {
        'post': post,
        'comments': comments,
        'user': user,
        'is_logged_in': True
    }
    return render(request, 'teams/post_detail.html', context)

@require_POST
def toggle_like(request, post_id):
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not logged in'}, status=403)
    user = User.objects.get(id=request.session['user_id'])
    post = Post.objects.get(id=post_id)
    if user in post.likes.all():
        post.likes.remove(user)
        liked = False
    else:
        post.likes.add(user)
        liked = True
    return JsonResponse({'likes': post.get_likes_count(), 'liked': liked})

def manage_players(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = User.objects.get(id=request.session['user_id'])
    
    if request.method == 'POST':
        player_id = request.POST.get('player_id')  # Add this to track if editing
        name = request.POST['name']
        jersey_number = request.POST['jersey_number']
        sport = request.POST['sport']  # Get the selected sport
        role = request.POST['role']
        profile_image = request.FILES.get('profile_image')

        try:
            if player_id:  # Editing existing player
                player = Player.objects.get(id=player_id, team=user)
                player.name = name
                player.jersey_number = jersey_number
                player.sport = sport  # Save the selected sport
                player.role = role
                if profile_image:
                    player.profile_image = profile_image
                player.save()
                messages.success(request, "Player updated successfully!")
            else:  # Adding new player
                player = Player.objects.create(
                    team=user,
                    name=name,
                    jersey_number=jersey_number,
                    sport=sport,  # Save the selected sport
                    role=role
                )
                if profile_image:
                    player.profile_image = profile_image
                    player.save()
                messages.success(request, "Player added successfully!")
        except Exception as e:
            messages.error(request, "Error: Jersey number already exists!")
        return redirect('manage_players')

    players = Player.objects.filter(team=user).order_by('jersey_number')
    context = {
        'players': players,
        'is_logged_in': True,
        'user': user,
        'cricket_roles': Player.CRICKET_ROLES,
        'kabaddi_roles': Player.KABADDI_ROLES
    }
    return render(request, 'teams/manage_players.html', context)

def edit_player(request, player_id):
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = User.objects.get(id=request.session['user_id'])
    player = get_object_or_404(Player, id=player_id, team=user)
    
    if request.method == 'POST':
        player.name = request.POST['name']
        player.jersey_number = request.POST['jersey_number']
        player.role = request.POST['role']
        try:
            player.save()
            messages.success(request, "Player updated successfully!")
        except:
            messages.error(request, "Jersey number already exists!")
        return redirect('manage_players')
        
    return JsonResponse({
        'id': player.id,
        'name': player.name,
        'jersey_number': player.jersey_number,
        'role': player.role
    })

def delete_player(request, player_id):
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = User.objects.get(id=request.session['user_id'])
    player = get_object_or_404(Player, id=player_id, team=user)
    player.delete()
    messages.success(request, "Player deleted successfully!")
    return redirect('manage_players')

def logout_view(request):
    logout(request)
    return redirect('home')

