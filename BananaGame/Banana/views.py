from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, CustomTokenObtainPairSerializer, PlayerSerializer, ScoreSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from .models import Player, Score

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({"detail": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError:
        return Response({"detail": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"detail": "Logout successful"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_all(request):
    for token in OutstandingToken.objects.filter(user=request.user):
        _, _ = BlacklistedToken.objects.get_or_create(token=token)

    return Response({"detail": "All sessions logged out"}, status=status.HTTP_200_OK)


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
    serializer = ScoreSerializer(data=request.data)
    if serializer.is_valid():
        score_instance = serializer.save(user=request.user)
        player, created = Player.objects.get_or_create(user=request.user)
        if score_instance.score > player.high_score:
            player.high_score = score_instance.score
            player.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def leaderboard(request):
    scores = Score.objects.order_by('-score')[:10]
    serializer = ScoreSerializer(scores, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


import requests
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
def fetch_puzzle(request):
    """
    Proxy for Banana Puzzle API to bypass CORS and provide puzzle data.
    """
    try:
        res = requests.get("https://marcconrad.com/uob/banana/api.php", timeout=5)
        if res.status_code == 200:
            return JsonResponse(res.json(), safe=False)
        else:
            return JsonResponse({"error": "Failed to fetch puzzle"}, status=res.status_code)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
