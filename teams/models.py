from django.db import models
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password

class User(models.Model):
    team_name = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    password = models.CharField(max_length=128)

    def __str__(self):
        return self.team_name

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

class Invitation(models.Model):
    SPORT_CHOICES = [
        ('cricket', 'Cricket'),
        ('kabaddi', 'Kabaddi'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team_name = models.CharField(max_length=150)
    sport = models.CharField(max_length=10, choices=SPORT_CHOICES)
    venue = models.CharField(max_length=200)
    date = models.DateField(default=now)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    entry_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    phone = models.CharField(max_length=15)
    team_limit = models.IntegerField(null=True, blank=True)
    invitation_file = models.FileField(upload_to='invitations/', null=True, blank=True)

    def __str__(self):
        return f"{self.team_name} - {self.venue}"

    def get_registered_teams_count(self):
        return Registration.objects.filter(invitation=self).count()

    def is_registration_full(self):
        if self.team_limit is None:
            return False
        return self.get_registered_teams_count() >= self.team_limit

class Registration(models.Model):
    invitation = models.ForeignKey(Invitation, on_delete=models.CASCADE)
    team_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.team_name} registered for {self.invitation.team_name}'s invitation"

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_posts')
    sport = models.CharField(max_length=10, choices=Invitation.SPORT_CHOICES)


    def __str__(self):
        return self.title

    def get_likes_count(self):
        return self.likes.count()

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    file = models.FileField(upload_to='comment_files/', blank=True, null=True)
    def __str__(self):
        return f"Comment by {self.user.team_name} on {self.post.title}"

    class Meta:
        ordering = ['-created_at']

class Player(models.Model):
    CRICKET_ROLES = [
        ('batsman', 'Batsman'),
        ('bowler', 'Bowler'),
        ('all_rounder', 'All Rounder'),
        ('wicket_keeper', 'Wicket Keeper'),
    ]
    
    KABADDI_ROLES = [
        ('raider', 'Raider'),
        ('defender', 'Defender'),
        ('all_rounder', 'All Rounder'),
    ]

    SPORT_CHOICES = [
        ('cricket', 'Cricket'),
        ('kabaddi', 'Kabaddi')
    ]

    team = models.ForeignKey(User, on_delete=models.CASCADE, related_name='players')
    name = models.CharField(max_length=100)
    jersey_number = models.IntegerField()
    sport = models.CharField(max_length=10, choices=SPORT_CHOICES, default='cricket')
    role = models.CharField(max_length=20)
    profile_image = models.ImageField(upload_to='player_profiles/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_sport_display(self):
        return dict(self.SPORT_CHOICES)[self.sport]

