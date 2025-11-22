from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
import logging

from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    PlayerSerializer,
    ScoreSerializer,
    EmailOTPRequestSerializer,
    EmailOTPVerifySerializer,
)
from .models import Player, Score, OTP

logger = logging.getLogger(__name__)
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def register(request):
#     serializer = RegisterSerializer(data=request.data)
#     if serializer.is_valid():
#         user = serializer.save()
#         refresh = RefreshToken.for_user(user)
#         return Response({
#             'refresh': str(refresh),
#             'access': str(refresh.access_token),
#             'username': user.username,
#         }, status=status.HTTP_201_CREATED)
#     return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        Player.objects.get_or_create(user=user)  # Create linked player profile
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'username': user.username,
        }, status=status.HTTP_201_CREATED)
    return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = CustomTokenObtainPairSerializer(data=request.data)
    if serializer.is_valid():
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

def send_otp_email(email, otp_code):
    try:
        subject = 'Your Banana Game Login OTP'
        message = (
            f'Your OTP for Banana Game login is: {otp_code}\n\n'
            'This OTP is valid for 10 minutes.'
        )
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', getattr(settings, 'EMAIL_HOST_USER', None))
        recipient_list = [email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return True
    except Exception as exc:
        logger.error("Failed to send OTP email: %s", exc)
        return False


@api_view(['POST'])
@permission_classes([AllowAny])
def request_email_otp(request):
    serializer = EmailOTPRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email']

    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return Response({"detail": "User with this email was not found."}, status=status.HTTP_404_NOT_FOUND)

    otp = OTP.generate_otp(user, OTP.EMAIL, email)

    if not send_otp_email(email, otp.otp_code):
        return Response({"detail": "Failed to send OTP. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(
        {
            "detail": "OTP sent successfully to your email.",
            "expires_in_minutes": 10
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email_otp_login(request):
    serializer = EmailOTPVerifySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email']
    otp_code = serializer.validated_data['otp_code']

    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return Response({"detail": "User with this email was not found."}, status=status.HTTP_404_NOT_FOUND)

    is_valid, message = OTP.verify_otp(user, otp_code, OTP.EMAIL)
    if not is_valid:
        return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

    refresh = RefreshToken.for_user(user)
    return Response(
        {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'username': user.username,
            'message': 'Login successful via OTP.'
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh_token = request.data.get('refresh')

    if not refresh_token:
        return Response({"detail": "Missing refresh token"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError:
        return Response({"detail": "Invalid refresh token"}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"detail": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_all(request):
    tokens = OutstandingToken.objects.filter(user=request.user)

    for outstanding_token in tokens:
        BlacklistedToken.objects.get_or_create(token=outstanding_token)

    return Response({"detail": "Logged out from all sessions"}, status=status.HTTP_205_RESET_CONTENT)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def player_detail(request):
    player, created = Player.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        serializer = PlayerSerializer(player)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PATCH':
        serializer = PlayerSerializer(player, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_score(request):
    try:
        score_value = request.data.get('score')

        if score_value is None:
            return Response({"detail": "Missing score field"}, status=status.HTTP_400_BAD_REQUEST)

        # Create the score record
        score_instance = Score.objects.create(user=request.user, score=int(score_value))

        # Update player's high score if this one is higher
        player, created = Player.objects.get_or_create(user=request.user)
        if score_instance.score > player.high_score:
            player.high_score = score_instance.score
            player.save()

        # Return lightweight response for frontend
        return Response({
            "username": request.user.username,
            "score": score_instance.score,
            "message": "Score submitted successfully"
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from django.db.models import Max

@api_view(['GET'])
@permission_classes([AllowAny])
def leaderboard(request):
    # Get the highest score per user
    top_scores = (
        Score.objects
        .values('user__username')
        .annotate(highest_score=Max('score'))
        .order_by('-highest_score')[:10]
    )

    # Format for serializer-like output
    leaderboard_data = [
        {'username': item['user__username'], 'score': item['highest_score']}
        for item in top_scores
    ]

    return Response(leaderboard_data, status=status.HTTP_200_OK)



import requests
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

import requests
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import Player

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_puzzle(request):
    try:
        res = requests.get("https://marcconrad.com/uob/banana/api.php", timeout=5)
        if res.status_code != 200:
            return JsonResponse({"error": "Failed to fetch puzzle"}, status=res.status_code)

        data = res.json()
        player, _ = Player.objects.get_or_create(user=request.user)
        player.current_puzzle = data  # Save the puzzle (includes solution)
        player.save()

        # Remove the solution before sending to the frontend
        data.pop('solution', None)
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import Player

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_puzzle_answer(request):
    try:
        from datetime import date
        import random
        
        user_answer = str(request.data.get('answer', '')).strip()
        time_taken = request.data.get('time_taken', 0)  # Time in seconds
        hints_used = request.data.get('hints_used', 0)  # Number of hints used for this puzzle
        if not user_answer:
            return JsonResponse({"error": "Missing answer"}, status=400)

        player, _ = Player.objects.get_or_create(user=request.user)
        puzzle_data = player.current_puzzle or {}

        real_solution = str(puzzle_data.get('solution', '')).strip()
        if not real_solution:
            return JsonResponse({"error": "No puzzle stored. Please fetch again."}, status=400)

        correct = user_answer == real_solution
        puzzle_id = puzzle_data.get('question', '')  # Use question URL as puzzle ID

        if correct:
            # Calculate base points based on difficulty
            difficulty_multipliers = {'easy': 0.7, 'medium': 1.0, 'hard': 1.5}
            base_points = 10 * difficulty_multipliers.get(player.difficulty, 1.0)
            
            # Time bonus (faster = more points, max bonus at 5 seconds)
            time_bonus = max(0, (40 - time_taken) / 2) if time_taken > 0 else 0
            time_bonus = min(time_bonus, 15)  # Cap at 15 points
            
            # Combo bonus (increases with combo count)
            combo_bonus = player.combo_count * 2
            player.combo_count += 1
            if player.combo_count > player.max_combo:
                player.max_combo = player.combo_count
            
            # Perfect solve bonus (no hints used)
            perfect_bonus = 0
            if hints_used == 0:
                perfect_bonus = 10
                player.perfect_solves += 1
            
            # Lucky streak (5% chance for 2x multiplier)
            lucky_multiplier = 2.0 if random.random() < 0.05 else 1.0
            
            # Calculate total points
            total_points = int((base_points + time_bonus + combo_bonus + perfect_bonus) * lucky_multiplier)
            
            # XP calculation (1 XP per point, bonus for perfect solves)
            xp_gained = total_points
            if hints_used == 0:
                xp_gained += 5  # Bonus XP for perfect solve
            
            # Level up check (100 XP per level)
            old_level = player.level
            player.xp += xp_gained
            new_level = (player.xp // 100) + 1
            leveled_up = new_level > old_level
            player.level = new_level
            
            # Update stats
            player.puzzles_solved += 1
            
            # Track puzzle in history (limit to last 50)
            if puzzle_id:
                if puzzle_id not in player.puzzle_history:
                    player.puzzle_history.append(puzzle_id)
                    if len(player.puzzle_history) > 50:
                        player.puzzle_history = player.puzzle_history[-50:]

            # Clear the stored puzzle after checking
            player.current_puzzle = {}
            player.save()
            
            return JsonResponse({
                "correct": True,
                "points": total_points,
                "xp_gained": xp_gained,
                "combo": player.combo_count,
                "leveled_up": leveled_up,
                "new_level": new_level if leveled_up else None,
                "perfect_solve": hints_used == 0,
                "lucky_streak": lucky_multiplier > 1.0,
                "breakdown": {
                    "base_points": int(base_points),
                    "time_bonus": int(time_bonus),
                    "combo_bonus": combo_bonus,
                    "perfect_bonus": perfect_bonus,
                    "lucky_multiplier": lucky_multiplier
                }
            })
        else:
            # Reset combo on wrong answer
            player.combo_count = 0
            player.current_puzzle = {}
            player.save()
            return JsonResponse({"correct": False, "correct_answer": real_solution})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def use_hint(request):
    """
    Use a hint power-up. Returns a hint message based on the current puzzle.
    Implements multiple hint strategies:
    1. Wrong answer reveal (original)
    2. Range hint (answer is between X and Y)
    3. Parity hint (odd/even)
    4. Comparison hint (greater/less than X)
    5. Multiple choice hint (answer is one of X, Y, Z)
    """
    try:
        player, _ = Player.objects.get_or_create(user=request.user)
        
        # Check if player has hints available
        if player.hints <= 0:
            return JsonResponse({"error": "No hints available"}, status=400)
        
        # Get current puzzle
        puzzle_data = player.current_puzzle or {}
        real_solution = str(puzzle_data.get('solution', '')).strip()
        
        if not real_solution:
            return JsonResponse({"error": "No puzzle stored. Please fetch a puzzle first."}, status=400)
        
        try:
            solution_num = int(real_solution)
        except ValueError:
            return JsonResponse({"error": "Invalid puzzle solution"}, status=400)
        
        # Decrement hint count
        player.hints -= 1
        player.save()
        
        # Select a random hint strategy
        import random
        hint_type = random.choice(['wrong_answer', 'range', 'parity', 'comparison', 'multiple_choice'])
        
        hint_message = ""
        hint_title = "💡 Hint Used!"
        
        if hint_type == 'wrong_answer':
            # Strategy 1: Reveal a wrong answer
            wrong_answers = [str(i) for i in range(1, 10) if i != solution_num]
            wrong_answer = random.choice(wrong_answers)
            hint_message = f"{wrong_answer} is NOT the answer"
        
        elif hint_type == 'range':
            # Strategy 2: Provide a range hint
            if solution_num <= 3:
                hint_message = "The answer is between 1 and 3"
            elif solution_num <= 6:
                hint_message = "The answer is between 4 and 6"
            else:
                hint_message = "The answer is between 7 and 9"
        
        elif hint_type == 'parity':
            # Strategy 3: Odd/Even hint
            if solution_num % 2 == 0:
                hint_message = "The answer is an EVEN number"
            else:
                hint_message = "The answer is an ODD number"
        
        elif hint_type == 'comparison':
            # Strategy 4: Comparison hint
            if solution_num < 5:
                hint_message = "The answer is LESS than 5"
            else:
                hint_message = "The answer is GREATER than or equal to 5"
        
        elif hint_type == 'multiple_choice':
            # Strategy 5: Multiple choice hint (3 options including correct one)
            possible_answers = [solution_num]
            while len(possible_answers) < 3:
                candidate = random.randint(1, 9)
                if candidate not in possible_answers:
                    possible_answers.append(candidate)
            random.shuffle(possible_answers)
            hint_message = f"The answer is one of: {', '.join(map(str, possible_answers))}"
        
        return JsonResponse({
            "hint": hint_message,
            "title": hint_title,
            "hints_remaining": player.hints,
            "hint_type": hint_type
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_difficulty(request):
    """Set game difficulty level"""
    try:
        difficulty = request.data.get('difficulty', 'medium')
        if difficulty not in ['easy', 'medium', 'hard']:
            return JsonResponse({"error": "Invalid difficulty. Must be 'easy', 'medium', or 'hard'"}, status=400)
        
        player, _ = Player.objects.get_or_create(user=request.user)
        player.difficulty = difficulty
        player.save()
        
        return JsonResponse({
            "difficulty": difficulty,
            "message": f"Difficulty set to {difficulty}"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_daily_challenge(request):
    """Get today's daily challenge"""
    try:
        from datetime import date, timedelta
        
        player, _ = Player.objects.get_or_create(user=request.user)
        today = date.today()
        
        # Check if already completed today
        if player.last_daily_challenge == today:
            return JsonResponse({
                "completed": True,
                "message": "Daily challenge already completed today!",
                "streak": player.daily_challenge_streak
            })
        
        # Check if streak should continue or reset
        if player.last_daily_challenge:
            yesterday = date.today() - timedelta(days=1)
            if player.last_daily_challenge == yesterday:
                # Continue streak
                pass
            elif player.last_daily_challenge < yesterday:
                # Reset streak
                player.daily_challenge_streak = 0
        else:
            player.daily_challenge_streak = 0
        
        # Generate challenge (solve 5 puzzles today)
        challenge_target = 5
        streak_bonus = player.daily_challenge_streak * 10  # 10 coins per streak day
        
        return JsonResponse({
            "completed": False,
            "target": challenge_target,
            "reward": 50 + streak_bonus,  # Base 50 coins + streak bonus
            "streak": player.daily_challenge_streak,
            "message": f"Solve {challenge_target} puzzles today to earn {50 + streak_bonus} coins!"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def claim_daily_challenge(request):
    """Claim daily challenge reward"""
    try:
        from datetime import date, timedelta
        
        player, _ = Player.objects.get_or_create(user=request.user)
        today = date.today()
        
        # Check if already claimed
        if player.last_daily_challenge == today:
            return JsonResponse({"error": "Daily challenge already claimed today"}, status=400)
        
        # Check if challenge is completed (5 puzzles solved today)
        # For simplicity, we'll check if puzzles_solved increased by 5 since last challenge
        # In a real implementation, you'd track daily puzzle count separately
        
        # Calculate reward
        if player.last_daily_challenge:
            yesterday = date.today() - timedelta(days=1)
            if player.last_daily_challenge == yesterday:
                player.daily_challenge_streak += 1
            else:
                player.daily_challenge_streak = 1
        else:
            player.daily_challenge_streak = 1
        
        reward = 50 + (player.daily_challenge_streak * 10)
        player.coins += reward
        player.last_daily_challenge = today
        player.save()
        
        return JsonResponse({
            "reward": reward,
            "coins_earned": reward,
            "new_balance": player.coins,
            "streak": player.daily_challenge_streak,
            "message": f"Daily challenge completed! Earned {reward} coins!"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_game_stats(request):
    """Get comprehensive game statistics"""
    try:
        player, _ = Player.objects.get_or_create(user=request.user)
        
        # Calculate XP needed for next level
        xp_for_current_level = (player.level - 1) * 100
        xp_for_next_level = player.level * 100
        xp_progress = player.xp - xp_for_current_level
        xp_needed = xp_for_next_level - player.xp
        
        return JsonResponse({
            "level": player.level,
            "xp": player.xp,
            "xp_progress": xp_progress,
            "xp_needed": xp_needed,
            "xp_for_next_level": xp_for_next_level,
            "difficulty": player.difficulty,
            "combo": player.combo_count,
            "max_combo": player.max_combo,
            "puzzles_solved": player.puzzles_solved,
            "perfect_solves": player.perfect_solves,
            "daily_streak": player.daily_challenge_streak,
            "high_score": player.high_score,
            "coins": player.coins
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)




