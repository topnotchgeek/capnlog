from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from .serializers import UserSerializer, GroupSerializer, EntrySerializer, TempHumSerializer
from .models import BlogEntry, TempHumidity


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class EntryViewSet(viewsets.ModelViewSet):
    queryset = BlogEntry.objects.all().order_by('-create_time')
    serializer_class = EntrySerializer


class TempHumViewSet(viewsets.ModelViewSet):
    queryset = TempHumidity.objects.order_by('-reading_time')[:24]
    serializer_class = TempHumSerializer
