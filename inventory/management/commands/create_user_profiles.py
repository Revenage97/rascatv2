from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory.models import UserProfile, ActivityLog

class Command(BaseCommand):
    help = 'Creates UserProfile objects for existing users who do not have one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-username',
            type=str,
            help='Username of the user to set as admin',
        )

    def handle(self, *args, **options):
        users_without_profile = []
        profiles_created = 0
        admin_username = options.get('admin_username')
        
        # Get all users
        users = User.objects.all()
        self.stdout.write(f"Found {users.count()} users in the database")
        
        # Check which users don't have a profile
        for user in users:
            try:
                # Try to access the profile
                profile = user.profile
                self.stdout.write(f"User {user.username} already has a profile with role: {profile.role}")
            except UserProfile.DoesNotExist:
                users_without_profile.append(user)
        
        self.stdout.write(f"Found {len(users_without_profile)} users without profiles")
        
        # Create profiles for users who don't have one
        for user in users_without_profile:
            # Determine role - set as admin if specified or default to staff_gudang
            role = 'admin' if admin_username and user.username == admin_username else 'staff_gudang'
            
            # Create profile
            UserProfile.objects.create(
                user=user,
                full_name=user.get_full_name() or user.username,
                role=role
            )
            
            # Log activity
            ActivityLog.objects.create(
                user=user,
                action='create_profile',
                status='success',
                notes=f'Profile created with role {role}'
            )
            
            profiles_created += 1
            self.stdout.write(f"Created profile for {user.username} with role: {role}")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {profiles_created} user profiles'))
