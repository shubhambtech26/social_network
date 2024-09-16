from django.urls import path

from .views import (
    FriendListView,
    LoginView,
    ManageFriendRequestView,
    PendingFriendRequestView,
    SendFriendRequestView,
    SignupView,
    UserSearchView,
)

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("search/", UserSearchView.as_view(), name="user-search"),
    path(
        "friend-request/send/",
        SendFriendRequestView.as_view(),
        name="send-friend-request",
    ),
    path(
        "friend-request/manage/",
        ManageFriendRequestView.as_view(),
        name="manage-friend-request",
    ),
    path("friends/", FriendListView.as_view(), name="list-friends"),
    path(
        "friend-requests/pending/",
        PendingFriendRequestView.as_view(),
        name="list-pending-requests",
    ),
]
