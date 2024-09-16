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

from .constants import (
    ACTION_ACCEPT,
    ACTION_REJECT,
    FRIEND_REQUEST_ACCEPTED,
    FRIEND_REQUEST_NOT_FOUND,
    FRIEND_REQUEST_REJECTED,
)

User = get_user_model()


class SignupView(generics.CreateAPIView):
    serializer_class = UserSerializer
    model = User


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
                friend_request = self.get_friend_request(
                    serializer.validated_data["request_id"], request.user
                )
                action = serializer.validated_data["action"]
                if action == ACTION_ACCEPT:
                    self.accept_friend_request(friend_request)
                    return self.create_response(
                        FRIEND_REQUEST_ACCEPTED, status.HTTP_200_OK
                    )
                elif action == ACTION_REJECT:
                    self.reject_friend_request(friend_request)
                    return self.create_response(
                        FRIEND_REQUEST_REJECTED, status.HTTP_200_OK
                    )
            except FriendRequest.DoesNotExist:
                return self.create_response(
                    FRIEND_REQUEST_NOT_FOUND, status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return self.create_response(
                    {"error": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return self.create_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

    def get_friend_request(self, request_id, user):
        return FriendRequest.objects.get(id=request_id, to_user=user)

    def accept_friend_request(self, friend_request):
        friend_request.is_accepted = True
        friend_request.save()

    def reject_friend_request(self, friend_request):
        friend_request.delete()

    def create_response(self, data, status_code):
        return Response(data, status=status_code)


class SendFriendRequestView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        to_user_id = self.get_to_user_id(request)
        if not to_user_id:
            return self.error_response(
                "to_user_id is required", status.HTTP_400_BAD_REQUEST
            )

        if self.exceeds_rate_limit(request):
            return self.error_response(
                "You can only send 3 friend requests per minute",
                status.HTTP_429_TOO_MANY_REQUESTS,
            )

        to_user = self.get_to_user(to_user_id)
        if self.friend_request_already_sent(request.user, to_user):
            return self.error_response(
                "Friend request already sent", status.HTTP_400_BAD_REQUEST
            )

        friend_request = self.create_friend_request(request.user, to_user)
        return Response(
            FriendRequestSerializer(friend_request).data, status.HTTP_201_CREATED
        )

    def get_to_user_id(self, request):
        return request.data.get("to_user_id")

    def error_response(self, error_message, status_code):
        return Response({"error": error_message}, status=status_code)

    def exceeds_rate_limit(self, request):
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        recent_requests = FriendRequest.objects.filter(
            from_user=request.user, created_at__gte=one_minute_ago
        )
        return recent_requests.count() >= 3

    def get_to_user(self, to_user_id):
        try:
            return User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            return self.error_response("User not found", status.HTTP_404_NOT_FOUND)

    def friend_request_already_sent(self, from_user, to_user):
        return FriendRequest.objects.filter(
            from_user=from_user, to_user=to_user
        ).exists()

    def create_friend_request(self, from_user, to_user):
        return FriendRequest.objects.create(from_user=from_user, to_user=to_user)


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
