from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import BlogEntry, TempHumidity


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'first_name', 'last_name', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class EntrySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BlogEntry
        fields = ('title', 'entry_text', 'create_time', 'author')


class TempHumSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempHumidity
        fields = ('reading_time', 'temperature', 'humidity')
