from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import BlogEntry, TempHumidity, Webcam, Snapshot, Station


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


class TempHumSerializer(serializers.HyperlinkedModelSerializer):
    station = serializers.ReadOnlyField(source='station.name')
    class Meta:
        model = TempHumidity
        fields = ('reading_time', 'temperature', 'humidity', 'station')


class StationSerializer(serializers.HyperlinkedModelSerializer):
    readings = TempHumSerializer(many=True, read_only=True)
    class Meta:
        model = Station
        fields = ('name', 'status', 'flag', 'readings')


class SnapshotSerializer(serializers.HyperlinkedModelSerializer):
    webcam = serializers.ReadOnlyField(source='webcam.slug')
    class Meta:
        model = Snapshot
        fields = ('url', 'ts_create', 'image_url', 'webcam')


class WebcamSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Webcam
        fields = ('url', 'name', 'description', 'schedule', 'latitude', 'longitude')
