from django.db import transaction
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
        fields = ("id", "name", "image", "latitude", "longitude")
        read_only_fields = ("image",)


class StationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ("id", "image")


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

    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "train_type",
            "image",
            "cars",
            "seats_in_car",
            "capacity",
        )


class TrainRetrieveSerializer(TrainListSerializer):
    train_type = TrainTypeSerializer(read_only=True)


class TrainImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "image")


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
    train_image = serializers.ImageField(source="train.image", read_only=True)
    train_capacity = serializers.IntegerField(
        source="train.capacity",
        read_only=True,
    )
    crew = serializers.SlugRelatedField(
        slug_field="full_name",
        many=True,
        read_only=True,
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "departure_time",
            "arrival_time",
            "train",
            "train_image",
            "train_capacity",
            "crew",
            "tickets_available",
        )


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
            "car",
            "seat",
            "journey",
        )


class TicketListSerializer(TicketSerializer):
    journey = JourneyListSerializer(read_only=True)


class TicketSeatSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("car", "seat")


class JourneyRetrieveSerializer(JourneySerializer):
    route = RouteListSerializer(read_only=True)
    train = TrainListSerializer(read_only=True)
    crew = CrewMemberListSerializer(many=True, read_only=True)
    taken_seats = TicketSeatSerializer(
        source="tickets",
        many=True,
        read_only=True
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
            "taken_seats",
        )


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")
