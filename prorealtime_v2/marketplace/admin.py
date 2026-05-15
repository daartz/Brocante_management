from django.contrib import admin

from .models import Event, Organizer, OrganizerSubscription, Payment, Reservation, Spot, SubscriptionPlan, Zone


class SpotInline(admin.TabularInline):
    model = Spot
    extra = 0
    fields = ('number', 'zone', 'price', 'status', 'x', 'y', 'map_width', 'map_height', 'electricity')


@admin.register(Organizer)
class OrganizerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'owner', 'created_at')
    search_fields = ('name', 'email')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'organizer', 'status', 'starts_at', 'reservation_deadline', 'default_map_mode', 'occupancy_rate')
    list_filter = ('status', 'default_map_mode', 'starts_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'venue_name', 'address')
    inlines = [SpotInline]


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'color', 'order')
    list_filter = ('event',)


@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    list_display = ('number', 'event', 'zone', 'price', 'status', 'width_m', 'depth_m', 'electricity', 'vehicle_allowed')
    list_filter = ('event', 'zone', 'status', 'electricity', 'vehicle_allowed')
    search_fields = ('number', 'label', 'notes')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('exhibitor_last_name', 'exhibitor_first_name', 'event', 'spot', 'status', 'total_amount', 'created_at')
    list_filter = ('event', 'status', 'created_at')
    search_fields = ('exhibitor_email', 'exhibitor_last_name', 'business_name', 'spot__number')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'provider', 'status', 'amount', 'provider_reference', 'created_at')
    list_filter = ('provider', 'status')


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'monthly_price', 'max_events', 'max_spots_per_event', 'stripe_price_id', 'highlighted')
    list_filter = ('highlighted',)


@admin.register(OrganizerSubscription)
class OrganizerSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('organizer', 'plan', 'status', 'current_period_end', 'stripe_customer_id', 'stripe_subscription_id')
    list_filter = ('plan', 'status')
