from datetime import timedelta

from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import FriendRequest

from .serializers import (
    FriendRequestActionSerializer,
    FriendRequestSerializer,
    UserSearchSerializer,
    UserSerializer,
)

User = get_user_model()


class SignupView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email").lower()  # Make email case insensitive
        password = request.data.get("password")
        user = authenticate(request, email=email, password=password)

        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key}, status=status.HTTP_200_OK)
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
        )


class SearchPagination(PageNumberPagination):
    page_size = 10


class UserSearchView(generics.ListAPIView):
    serializer_class = UserSearchSerializer
    pagination_class = SearchPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        query = self.request.query_params.get("q", "").lower()
        return User.objects.filter(
            Q(email__iexact=query) | Q(username__icontains=query)
        )


class ManageFriendRequestView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = FriendRequestActionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                friend_request = FriendRequest.objects.get(
                    id=serializer.validated_data["request_id"], to_user=request.user
                )
                action = serializer.validated_data["action"]
                if action == "accept":
                    friend_request.is_accepted = True
                    friend_request.save()
                    return Response(
                        {"status": "Friend request accepted"}, status=status.HTTP_200_OK
                    )
                elif action == "reject":
                    friend_request.delete()
                    return Response(
                        {"status": "Friend request rejected"}, status=status.HTTP_200_OK
                    )
            except FriendRequest.DoesNotExist:
                return Response(
                    {"error": "Friend request not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendFriendRequestView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        to_user_id = request.data.get("to_user_id")
        if not to_user_id:
            return Response(
                {"error": "to_user_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check rate limit
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        recent_requests = FriendRequest.objects.filter(
            from_user=request.user, created_at__gte=one_minute_ago
        )
        if recent_requests.count() >= 3:
            return Response(
                {"error": "You can only send 3 friend requests per minute"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        to_user = User.objects.get(id=to_user_id)
        if FriendRequest.objects.filter(
            from_user=request.user, to_user=to_user
        ).exists():
            return Response(
                {"error": "Friend request already sent"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        friend_request = FriendRequest.objects.create(
            from_user=request.user, to_user=to_user
        )
        return Response(
            FriendRequestSerializer(friend_request).data, status=status.HTTP_201_CREATED
        )


class FriendListView(ListAPIView):
    serializer_class = UserSearchSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        # Get all users who have accepted a friend request from the current user
        user = self.request.user
        return User.objects.filter(
            sent_requests__to_user=user, sent_requests__is_accepted=True
        )


class PendingFriendRequestView(ListAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        # List all friend requests that the current user has received and are pending
        user = self.request.user
        return FriendRequest.objects.filter(to_user=user, is_accepted=False)
