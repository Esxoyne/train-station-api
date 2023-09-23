from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import (
    CrewMember,
    Station,
    Route,
    TrainType,
    Train,
    Journey,
    Order,
    Ticket,
)


class CrewMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrewMember
        fields = ("id", "first_name", "last_name", "full_name")


class CrewMemberListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrewMember
        fields = ("id", "full_name")


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude")


class RouteSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(RouteSerializer, self).validate(attrs=attrs)
        Route.validate_stations(
            attrs["origin"],
            attrs["destination"],
            ValidationError,
        )
        return data

    class Meta:
        model = Route
        fields = ("id", "origin", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    origin = serializers.StringRelatedField()
    destination = serializers.StringRelatedField()


class RouteRetrieveSerializer(RouteSerializer):
    origin = StationSerializer(read_only=True)
    destination = StationSerializer(read_only=True)


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "train_type",
            "cars",
            "seats_in_car",
            "capacity",
        )


class TrainListSerializer(TrainSerializer):
    train_type = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True,
    )


class TrainRetrieveSerializer(TrainSerializer):
    train_type = TrainTypeSerializer(read_only=True)


class JourneySerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(JourneySerializer, self).validate(attrs=attrs)
        Journey.validate_time(
            attrs["departure_time"],
            attrs["arrival_time"],
            ValidationError,
        )
        return data

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "departure_time",
            "arrival_time",
            "train",
            "crew",
        )


class JourneyListSerializer(JourneySerializer):
    route = serializers.StringRelatedField()
    train = serializers.StringRelatedField()
    train_capacity = serializers.IntegerField(
        source="train.capacity",
        read_only=True,
    )

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "departure_time",
            "arrival_time",
            "train",
            "train_capacity",
        )


class JourneyRetrieveSerializer(JourneySerializer):
    route = RouteListSerializer(read_only=True)
    train = TrainListSerializer(read_only=True)
    crew = serializers.SlugRelatedField(
        slug_field="full_name",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "departure_time",
            "arrival_time",
            "train",
            "crew",
        )


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("id", "created_at", "user")


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["car"],
            attrs["seat"],
            attrs["journey"].train,
            ValidationError,
        )
        return data

    class Meta:
        model = Ticket
        fields = (
            "id",
            "order",
            "car",
            "seat",
            "journey",
        )


class TicketListSerializer(TicketSerializer):
    journey = JourneyListSerializer(read_only=True)
