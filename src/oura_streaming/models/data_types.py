"""Typed models for all 14 Oura Ring API v2 data types.

These models represent the actual metric payloads sent via webhooks.
All fields are optional since webhooks may send partial updates.

Sources:
- https://cloud.ouraring.com/v2/docs
- https://jsr.io/@pinta365/oura-api/doc
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# =============================================================================
# Contributor Models (shared sub-structures)
# =============================================================================


class SleepContributors(BaseModel):
    """Contributors to the daily sleep score."""

    deep_sleep: int | None = None
    efficiency: int | None = None
    latency: int | None = None
    rem_sleep: int | None = None
    restfulness: int | None = None
    timing: int | None = None
    total_sleep: int | None = None


class ActivityContributors(BaseModel):
    """Contributors to the daily activity score."""

    meet_daily_targets: int | None = None
    move_every_hour: int | None = None
    recovery_time: int | None = None
    stay_active: int | None = None
    training_frequency: int | None = None
    training_volume: int | None = None


class ReadinessContributors(BaseModel):
    """Contributors to the daily readiness score."""

    activity_balance: int | None = None
    body_temperature: int | None = None
    hrv_balance: int | None = None
    previous_day_activity: int | None = None
    previous_night: int | None = None
    recovery_index: int | None = None
    resting_heart_rate: int | None = None
    sleep_balance: int | None = None


# =============================================================================
# Daily Metrics
# =============================================================================


class DailySleep(BaseModel):
    """Daily sleep score and contributors.

    Aggregated sleep metrics for a calendar day.
    """

    id: str | None = None
    day: str | None = Field(None, description="Date in YYYY-MM-DD format")
    score: int | None = Field(None, ge=0, le=100, description="Sleep score 0-100")
    timestamp: datetime | None = None
    contributors: SleepContributors | None = None


class DailyActivity(BaseModel):
    """Daily activity metrics and score.

    Tracks movement, calories, and activity levels throughout the day.
    """

    id: str | None = None
    day: str | None = Field(None, description="Date in YYYY-MM-DD format")
    score: int | None = Field(None, ge=0, le=100)
    timestamp: datetime | None = None
    contributors: ActivityContributors | None = None

    # Calories
    active_calories: int | None = Field(None, description="Calories burned from activity")
    total_calories: int | None = Field(None, description="Total calories including BMR")
    target_calories: int | None = None

    # MET (Metabolic Equivalent of Task)
    average_met_minutes: float | None = None
    high_activity_met_minutes: int | None = None
    medium_activity_met_minutes: int | None = None
    low_activity_met_minutes: int | None = None
    sedentary_met_minutes: int | None = None

    # Time in seconds
    high_activity_time: int | None = None
    medium_activity_time: int | None = None
    low_activity_time: int | None = None
    sedentary_time: int | None = None
    resting_time: int | None = None
    non_wear_time: int | None = None

    # Movement
    steps: int | None = None
    equivalent_walking_distance: int | None = Field(None, description="Meters")
    meters_to_target: int | None = None
    target_meters: int | None = None

    # Alerts
    inactivity_alerts: int | None = None

    # 5-minute activity classification string
    class_5_min: str | None = Field(
        None, description="Activity classification per 5-min interval"
    )

    # MET data with timestamps
    met: dict | None = Field(
        None, description="MET values with interval, items, timestamp"
    )


class DailyReadiness(BaseModel):
    """Daily readiness score indicating recovery state.

    Combines HRV, temperature, sleep, and activity balance.
    """

    id: str | None = None
    day: str | None = Field(None, description="Date in YYYY-MM-DD format")
    score: int | None = Field(None, ge=0, le=100)
    timestamp: datetime | None = None
    contributors: ReadinessContributors | None = None

    temperature_deviation: float | None = Field(
        None, description="Deviation from baseline in Celsius"
    )
    temperature_trend_deviation: float | None = Field(
        None, description="Temperature trend deviation"
    )


class DailySpo2(BaseModel):
    """Daily blood oxygen saturation (SpO2) metrics."""

    id: str | None = None
    day: str | None = Field(None, description="Date in YYYY-MM-DD format")

    spo2_percentage: dict | None = Field(
        None, description="SpO2 with 'average' key (0-100)"
    )
    breathing_disturbance_index: float | None = Field(
        None, description="Breathing disturbance events per hour"
    )


class DailyStress(BaseModel):
    """Daily stress summary metrics."""

    id: str | None = None
    day: str | None = Field(None, description="Date in YYYY-MM-DD format")

    stress_high: int | None = Field(None, description="Minutes in high stress")
    recovery_high: int | None = Field(None, description="Minutes in recovery")
    day_summary: str | None = Field(
        None, description="Summary: restored, normal, stressful"
    )


class DailyCyclePhases(BaseModel):
    """Daily menstrual cycle phase information."""

    id: str | None = None
    day: str | None = Field(None, description="Date in YYYY-MM-DD format")

    cycle_day: int | None = Field(None, description="Day within current cycle")
    phase: str | None = Field(
        None, description="menstruation, follicular, ovulation, luteal"
    )
    predicted: bool | None = Field(None, description="Whether phase is predicted")


# =============================================================================
# Sleep Records (detailed per-sleep-period data)
# =============================================================================


class HrvSample(BaseModel):
    """Single HRV measurement sample."""

    interval: float | None = None
    items: list[float | None] | None = None
    timestamp: datetime | None = None


class Sleep(BaseModel):
    """Detailed sleep period data.

    Contains comprehensive metrics for a single sleep period.
    """

    id: str | None = None
    day: str | None = Field(None, description="Date in YYYY-MM-DD format")
    period: int | None = Field(None, description="Sleep period number (0=main)")
    type: str | None = Field(None, description="long_sleep, late_nap, etc.")

    # Timing
    bedtime_start: datetime | None = None
    bedtime_end: datetime | None = None
    time_in_bed: int | None = Field(None, description="Total time in bed (seconds)")

    # Sleep stages (seconds)
    deep_sleep_duration: int | None = None
    light_sleep_duration: int | None = None
    rem_sleep_duration: int | None = None
    awake_time: int | None = None
    total_sleep_duration: int | None = None

    # Quality metrics
    efficiency: int | None = Field(None, ge=0, le=100, description="Sleep efficiency %")
    latency: int | None = Field(None, description="Time to fall asleep (seconds)")
    restless_periods: int | None = None

    # Physiological
    average_breath: float | None = Field(None, description="Breaths per minute")
    average_heart_rate: float | None = Field(None, description="BPM")
    lowest_heart_rate: int | None = Field(None, description="Lowest BPM during sleep")
    average_hrv: int | None = Field(None, description="Average HRV in ms")
    hrv: HrvSample | None = Field(None, description="Detailed HRV samples")

    # Device
    low_battery_alert: bool | None = None

    # 5-minute interval data
    heart_rate: dict | None = Field(None, description="HR samples with timestamps")
    movement_30_sec: str | None = Field(None, description="Movement intensity string")
    sleep_phase_5_min: str | None = Field(
        None, description="Sleep stage per 5-min: 1=deep,2=light,3=rem,4=awake"
    )
    readiness: dict | None = None


# =============================================================================
# Activity Records
# =============================================================================


class Workout(BaseModel):
    """A workout/exercise session tracked by Oura.

    Can be auto-detected or manually entered.
    """

    id: str | None = None
    day: str | None = Field(None, description="Date in YYYY-MM-DD format")

    activity: str | None = Field(None, description="Activity type: running, cycling...")
    label: str | None = Field(None, description="User-provided label")
    source: str | None = Field(None, description="manual, autodetected, etc.")

    start_datetime: datetime | None = None
    end_datetime: datetime | None = None

    calories: int | None = None
    distance: float | None = Field(None, description="Distance in meters")
    intensity: str | None = Field(None, description="easy, moderate, hard")


class Session(BaseModel):
    """A guided session (meditation, breathing, etc.) tracked by Oura."""

    id: str | None = None
    day: str | None = Field(None, description="Date in YYYY-MM-DD format")
    type: str | None = Field(
        None, description="breathing, meditation, nap, relaxation, etc."
    )

    start_datetime: datetime | None = None
    end_datetime: datetime | None = None

    heart_rate: dict | None = Field(None, description="HR data during session")
    heart_rate_variability: dict | None = Field(None, description="HRV data")
    mood: str | None = Field(None, description="User-reported mood after session")
    motion_count: dict | None = Field(None, description="Movement during session")


# =============================================================================
# Tags & Annotations
# =============================================================================


class Tag(BaseModel):
    """A simple tag/annotation for a day."""

    id: str | None = None
    day: str | None = Field(None, description="Date in YYYY-MM-DD format")
    timestamp: datetime | None = None

    text: str | None = Field(None, description="Tag text content")
    tags: list[str] | None = Field(None, description="List of tag labels")


class EnhancedTag(BaseModel):
    """An extended multi-day tag with optional comments.

    Used for tracking events, symptoms, or conditions over time.
    """

    id: str | None = None

    tag_type_code: str | None = Field(None, description="Type identifier")
    custom_name: str | None = Field(None, description="User-defined name")
    comment: str | None = None

    start_day: str | None = Field(None, description="Start date YYYY-MM-DD")
    start_time: str | None = Field(None, description="Start time HH:MM:SS")
    end_day: str | None = Field(None, description="End date YYYY-MM-DD")
    end_time: str | None = Field(None, description="End time HH:MM:SS")


# =============================================================================
# Device & System
# =============================================================================


class RingConfiguration(BaseModel):
    """Information about the Oura ring hardware and setup."""

    id: str | None = None

    color: str | None = Field(None, description="Ring color: silver, black, gold...")
    design: str | None = Field(None, description="Ring design/generation")
    size: int | None = Field(None, ge=4, le=15, description="Ring size (US)")

    hardware_type: str | None = None
    firmware_version: str | None = None
    set_up_at: datetime | None = Field(None, description="Initial setup timestamp")


class RestModeEpisode(BaseModel):
    """A single episode within a rest mode period."""

    tags: list[str] | None = None
    timestamp: datetime | None = None


class RestModePeriod(BaseModel):
    """A period when the user enabled Rest Mode.

    Rest Mode adjusts activity goals during illness/recovery.
    """

    id: str | None = None

    start_day: str | None = Field(None, description="Start date YYYY-MM-DD")
    start_time: str | None = Field(None, description="Start time HH:MM:SS")
    end_day: str | None = Field(None, description="End date YYYY-MM-DD")
    end_time: str | None = Field(None, description="End time HH:MM:SS")

    episodes: list[RestModeEpisode] | None = None


# =============================================================================
# Sleep Time Recommendations
# =============================================================================


class OptimalBedtime(BaseModel):
    """Recommended bedtime window."""

    day_tz: int | None = Field(None, description="Timezone offset in seconds")
    end_offset: int | None = Field(None, description="Latest bedtime offset (seconds)")
    start_offset: int | None = Field(
        None, description="Earliest bedtime offset (seconds)"
    )


class SleepTime(BaseModel):
    """Oura's recommended bedtime for a given day."""

    id: str | None = None
    day: str | None = Field(None, description="Date in YYYY-MM-DD format")

    optimal_bedtime: OptimalBedtime | None = None
    recommendation: str | None = Field(
        None, description="improve_efficiency, earlier_bedtime, etc."
    )
    status: str | None = Field(
        None, description="not_enough_data, low_sleep_scores, good_sleep"
    )


# =============================================================================
# Type mapping for parsing webhook data field
# =============================================================================

DATA_TYPE_MODELS: dict[str, type[BaseModel]] = {
    "tag": Tag,
    "enhanced_tag": EnhancedTag,
    "workout": Workout,
    "session": Session,
    "sleep": Sleep,
    "daily_sleep": DailySleep,
    "daily_readiness": DailyReadiness,
    "daily_activity": DailyActivity,
    "daily_spo2": DailySpo2,
    "sleep_time": SleepTime,
    "rest_mode_period": RestModePeriod,
    "ring_configuration": RingConfiguration,
    "daily_stress": DailyStress,
    "daily_cycle_phases": DailyCyclePhases,
}


def parse_data_payload(data_type: str, data: dict) -> BaseModel | None:
    """Parse a webhook data payload into its typed model.

    Args:
        data_type: One of the 14 Oura data types
        data: The raw data dict from the webhook

    Returns:
        Typed model instance, or None if data_type is unknown
    """
    model_class = DATA_TYPE_MODELS.get(data_type)
    if model_class is None:
        return None
    return model_class.model_validate(data)
